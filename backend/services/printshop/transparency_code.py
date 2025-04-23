import datetime
import hashlib
import os.path
import re
from typing import List, Dict, Tuple
from fastapi import HTTPException
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction
from api.v1.routes.common import UPLOAD_DIR
from core.log import logger
from crud.lingxing import AsyncLingxingListingDB, AsyncLingxingBasicDataDB, AsyncLingxingInventoryDB
from models import TransparencyCodeModel, TransparencyCodePrintLogModel
from models.amazon_print import (TransparencyCodePrintLog_Pydantic,
                                 TransparencyCode_Pydantic,
                                 TransparencyCodeStatus, ActionType)
import utils.utilpdf as utilpdf
from schemas.common import UTCModel
from utils.stringutils import format_ranges

class BatchInformation(UTCModel):
    batch_id: str
    listing_id: str
    seller_sku: str
    created_at: datetime.datetime
    hash: str
    filename: str
    total: int
    used: int
    locked: int
    deleted: int


class TransparencyCodeService:

    def __init__(self):
        self.listing_mdb = AsyncLingxingListingDB()
        self.basic_mdb = AsyncLingxingBasicDataDB()
        self.inventory_mdb = AsyncLingxingInventoryDB()

    async def __aenter__(self):
        await self.listing_mdb.__aenter__()
        await self.basic_mdb.__aenter__()
        await self.inventory_mdb.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.listing_mdb.__aexit__(exc_type, exc_val, exc_tb)
        await self.basic_mdb.__aexit__(exc_type, exc_val, exc_tb)
        await self.inventory_mdb.__aexit__(exc_type, exc_val, exc_tb)

    async def save_transparency_batch(self, filename: str, listing_id: str, created_by: str) -> Dict:
        """
        Save a transparency code batch to the database
        :param file_path: file path of the transparency code batch
        :param listing_id: listing id on Amazon
        :param created_by: user who created the transparency code batch
        :return:
        """
        # Read the transparency code batch file (pdf)
        logger.info(
            f"Saving transparency code batch (filename={filename}, listing_id={listing_id}, created_by={created_by})")
        file_path = UPLOAD_DIR + filename
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File (name={filename}) does not exist.")

        with open(file_path, "rb") as f:
            content = f.read()

        if not content:
            raise HTTPException(status_code=404, detail=f"Empty transparency code batch file (path={file_path})")
        else:
            md5_hash = hashlib.md5(content).hexdigest()
            total_pages = utilpdf.count_pages(content)

        if total_pages < 1:
            raise HTTPException(status_code=400, detail=f"Transparency code batch file (path={file_path}) has no pages")

        # Read listing from mongodb
        listings = await self.listing_mdb.query_listings_by_listing_ids([listing_id])
        if not listings:
            raise HTTPException(status_code=404, detail=f"Listing (id={listing_id}) not found")
        listing = listings[0]['data']
        now_ = datetime.datetime.now()

        # Query one by filename to check if it already exists
        transparency_code = await TransparencyCodeModel.filter(hash=md5_hash).first()
        if transparency_code:
            await TransparencyCodeModel.filter(hash=md5_hash).update(
                asin=listing['asin'],
                fnsku=listing['fnsku'],
                seller_sku=listing['seller_sku'],
                sku=listing['local_sku'],
                filename=filename,
                listing_id=listing['listing_id'],
                updated_by=created_by,
                updated_at=now_,
            )
            logger.info(f"Transparency code (sku={listing['seller_sku']}, batch_id={transparency_code.batch_id}) "
                        f"already exists. "
                        f"Updated asin, fnsku, seller_sku, listing_id, updated_by, updated_at.")
            return {
                "batch_id": transparency_code.batch_id,
                "listing_id": listing_id,
                "filename": filename,
                "total": total_pages,
            }

        # Preprocess to save (insert) the transparency codes to the database
        batch_id = f"BA{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        item_list = []
        item = dict(
            asin=listing["asin"],
            fnsku=listing["fnsku"],
            seller_sku=listing["seller_sku"],
            sku=listing["local_sku"],
            listing_id=listing["listing_id"],
            code=None,
            hash=md5_hash,
            filename=filename,
            batch_id=batch_id,
            page=1,
            total=total_pages,
            created_at=now_,
            created_by=created_by,
            updated_at=now_,
            updated_by=created_by,  # status=TransparencyCodeStatus.UNUSED,
        )
        for i in range(1, total_pages + 1):
            item['page'] = i
            item_list.append(TransparencyCodeModel(**item))
        # Save (insert) the transparency codes to the database
        await TransparencyCodeModel.bulk_create(item_list)
        filename2 = filename.split("/")[-1]
        logger.info(
            f"Transparency codes were saved (filename={filename}, listing_id={listing_id}, created_by={created_by}) ")
        await self.create_print_log(
            listing_id=listing_id,
            seller_sku=listing["seller_sku"],
            batch_id=batch_id,
            created_by=created_by,
            action=ActionType.CREATE,
            content=f"{len(item_list)} Transparency codes were uploaded (file={filename2}).",
        )
        return {
            "batch_id": batch_id,
            "listing_id": listing_id,
            "filename": filename,
            "total": total_pages,
        }


    async def smart_save_transparency_batch(self, filenames: str, created_by: str) -> Dict:
        """
        Save a transparency code batch to the database
        :param filenames: file names of the transparency code batch (Format: TCodes_PID\d{19}_(.+?)_\d{14}_\d{12}\.pdf)
        :param created_by: user who created the transparency code batch
        :return:
        """
        # 正则表达式检验, 提取seller_sku
        pattern = r"TCodes_PID\d{19}_(.+?)_\d{14}_\d{12}\.pdf"
        file_dict = {}
        for filename in filenames:
            logger.info(f"Validate filename (name={filename}) with pattern={pattern}")
            match = re.search(pattern, filename)
            if not match:
                raise HTTPException(status_code=400, detail=f"Invalid filename (name={filename}). "
                                                            f"Please ensure the filename is in the "
                                                            f"correct format ({pattern}).")
            seller_sku = match.group(1)
            print(f"seller_sku={seller_sku}, filename={filename}")
            file_dict[filename] = file_dict.get(filename, {})
            file_dict[filename]['sku'] = seller_sku
        logger.info(f"All filenames are validated.")

        # 验证seller_sku是否存在，唯一性
        for filename in filenames:
            logger.info(f"Validate seller_sku (sku={file_dict[filename]['sku']})")
            seller_sku = file_dict[filename]['sku']
            listings = await self.listing_mdb.query_listings_by_seller_sku(seller_sku)
            listings = list(filter(lambda a: a['data']['marketplace'] == "德国", listings))
            if not listings or len(listings) > 1:
                raise HTTPException(status_code=404, detail=f"Product with Seller SKU [{seller_sku}] not found or not unique")
            listing = listings[0]
            file_dict[filename]['listing_id'] = listing['data']['listing_id']
        logger.info(f"All seller_skus are validated.")

        # Save to database
        result_list = []
        for filename, item in file_dict.items():
            res = await self.save_transparency_batch(filename, item['listing_id'], created_by)
            result_list.append(res)
        return {
            "data": result_list,
            "total": len(result_list),
        }



    async def get_transparency_codes_by_bid(self, batch_id: str) -> Dict:
        """
        Get transparency code by batch id
        :param batch_id: batch id of the transparency code batch
        :return:
        """
        try:
            transparency_codes = await TransparencyCodeModel.filter(batch_id=batch_id).all()
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Transparency code batch (batch_id={batch_id}) not found")
        # To pydantics
        code_list = []
        for code in transparency_codes:
            code_list.append(TransparencyCode_Pydantic.from_orm(code))
        return {
            "data": code_list,
            "total": len(code_list),
        }

    async def get_batch_information_by_lid(self, listing_id: str):
        """
        Summarize batch information by listing id
        :param listing_id: listing id on Amazon
        :return:  batch information
        """
        sql = """
        SELECT 
            batch_id,
            MIN(listing_id) as listing_id ,
            MIN(seller_sku) as seller_sku,
            MIN(hash) as hash,
            MIN(filename) as filename,
            MIN(created_at) as created_at,
            COUNT(*) AS total,
            SUM(CASE WHEN status = %s THEN 1 ELSE 0 END) AS used,
            SUM(CASE WHEN status = %s THEN 1 ELSE 0 END) AS locked,
            SUM(CASE WHEN status = %s THEN 1 ELSE 0 END) AS deleted
        FROM transparency_code
        WHERE listing_id = %s
        GROUP BY batch_id
        """
        try:
            async with in_transaction() as conn:
                result = await conn.execute_query_dict(sql, [TransparencyCodeStatus.USED.value,
                                                             TransparencyCodeStatus.LOCKED.value,
                                                             TransparencyCodeStatus.DELETED.value,
                                                             listing_id])
                # To pydantics
                batch_list = []
                for batch in result:
                    batch_list.append(BatchInformation(**batch))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {
            "data": batch_list,
            "total": len(batch_list),
        }

    async def get_batch_information(self):
        """
        Summarize batch information
        :return:
        """
        sql = """
        SELECT 
            batch_id,
            MIN(listing_id) as listing_id ,
            MIN(seller_sku) as seller_sku,
            MIN(hash) as hash,
            MIN(filename) as filename,
            MIN(created_at) as created_at,
            COUNT(*) AS total,
            SUM(CASE WHEN status = %s THEN 1 ELSE 0 END) AS used,
            SUM(CASE WHEN status = %s THEN 1 ELSE 0 END) AS locked,
            SUM(CASE WHEN status = %s THEN 1 ELSE 0 END) AS deleted
        FROM transparency_code
        GROUP BY 
            batch_id
        ORDER BY  
	        created_at desc;
        """
        try:
            async with in_transaction() as conn:
                result = await conn.execute_query_dict(sql, [TransparencyCodeStatus.USED.value,
                                                             TransparencyCodeStatus.LOCKED.value,
                                                             TransparencyCodeStatus.DELETED.value])
                # To pydantics
                batch_list = []
                for batch in result:
                    batch_list.append(BatchInformation(**batch))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {
            "data": batch_list,
            "total": len(batch_list),
        }

    async def get_unused_transparency_codes_by_bid(self, batch_id: str, quantity: int) -> Dict:
        """
        Get unused transparency codes by batch id given quantity
        :param batch_id: batch id of the transparency code batch
        :param quantity: quantity of the transparency code needed
        :return: (
            batch_id,
            filename,
            page,
        )
        """
        logger.info(f"Query {quantity} unused transparency codes by batch id (batch_id={batch_id})")
        result = await (TransparencyCodeModel.filter(
            batch_id=batch_id,
            status=TransparencyCodeStatus.UNUSED)
                        .limit(quantity).all())

        if not result or len(result) < quantity:
            raise HTTPException(status_code=404, detail=f"Not enough unused transparency codes found"
                                                        f"Please contact the seller for more codes.")

        # To pydantics
        code_list = []
        for code in result:
            code_list.append(TransparencyCode_Pydantic.from_orm(code))
        return {
            "data": code_list,
            "total": len(code_list),
        }

    async def get_unused_transparency_codes_by_lid(self, listing_id: str, quantity: int) -> Dict:
        """
        Get unused transparency codes by listing id given quantity
        :param listing_id: listing id on Amazon
        :param quantity: quantity of the transparency code needed
        :return:
        """
        logger.info(f"Query {quantity} unused transparency codes by listing id (listing_id={listing_id})")
        result = await (TransparencyCodeModel.filter(
            listing_id=listing_id,
            status=TransparencyCodeStatus.UNUSED)
                        .limit(quantity).all())
        if not result or len(result) < quantity:
            raise HTTPException(status_code=404, detail=f"Not enough unused transparency codes "
                                                        f"found for listing (id={listing_id}, quantity={quantity})."
                                                        f"Please contact the seller for more codes.")

        # To pydantics
        code_list = []
        for code in result:
            code_list.append(TransparencyCode_Pydantic.from_orm(code))
        return {
            "data": code_list,
            "total": len(code_list),
        }

    async def update_transparency_codes_status(self, code_ids: List[int],
                                               status: TransparencyCodeStatus,
                                               updated_by: str):
        """
        Mark transparency codes as used
        :param code_ids: list of transparency code ids
        :return:
        """
        logger.info(f"Update transparency codes status (ids={code_ids}, status={status.name}, updated_by={updated_by})")
        now_ = datetime.datetime.now()
        result = await (TransparencyCodeModel.filter(id__in=code_ids)
                        .update(status=status,
                                updated_by=updated_by,
                                updated_at=now_))
        if not result:
            raise HTTPException(status_code=404, detail=f"No transparency codes found (ids={code_ids})")

        # Query transparency codes by id list
        transparency_codes = await TransparencyCodeModel.filter(id__in=code_ids).all()
        # To pydantics
        code_list = []
        for code in transparency_codes:
            code_list.append(TransparencyCode_Pydantic.from_orm(code))

        page_list = [code.page for code in code_list]
        page_ranges = format_ranges(page_list)

        await self.create_print_log(
            listing_id=code_list[0].listing_id,
            batch_id=code_list[0].batch_id,
            seller_sku=code_list[0].seller_sku,
            created_by=updated_by,
            action=ActionType.UPDATE,
            content=f"Transparency codes were marked as {status.name} (pages: {page_ranges}) . ",
        )
        return {
            "data": code_list,
            "status": status.value,
            "status_name": status.name,
            "total": len(code_list),
        }

    async def generate_transparency_pdf_by_ids(self, code_ids: List[int],
                                               crop_box: Tuple[int, int, int, int] = None) -> bytes:
        id_set = set(code_ids)
        if len(id_set) != len(code_ids):
            raise HTTPException(status_code=400, detail=f"Duplicate transparency code ids found in the list.")

        result = await (TransparencyCodeModel.filter(id__in=code_ids)
                        .order_by('id').all())
        if not result:
            raise HTTPException(status_code=404, detail=f"No transparency codes found (ids={code_ids})")

        if len(result) != len(code_ids):
            raise HTTPException(status_code=400, detail=f"Some transparency codes not found in the list.")

        # To pydantics
        code_list = []
        for code in result:
            if code.status == TransparencyCodeStatus.UNUSED:
                code_list.append(TransparencyCode_Pydantic.from_orm(code))
            else:
                raise HTTPException(status_code=400,
                                    detail=f"Failed to generate PDF. Reason: "
                                           f"transparency code (id={code.id}) has been used.")

        if not code_list:
            raise HTTPException(status_code=400, detail=f"No unused transparency codes found in the batch.")
        # Generate PDF
        batch_dict = {}
        for code in code_list:
            li = batch_dict.get(code.batch_id, [])
            li.append(code)
            batch_dict[code.batch_id] = li

        pdf_list = []
        final_page_list = []
        for batch_id, li in batch_dict.items():
            filename = UPLOAD_DIR + li[0].filename
            lid = li[0].listing_id
            page_list = [code.page for code in li]
            # Get product information
            product_info = await self.__query_product_info_by_lid(lid)
            fnsku = product_info['fnsku']
            sku = product_info['sku']
            seller_sku = product_info['seller_sku']
            seller_name = product_info['seller.name']
            seller_account_name = product_info['seller.account_name']
            if fnsku != li[0].fnsku or sku != li[0].sku or seller_sku != li[0].seller_sku:
                logger.error(
                    f"Product information not match. lid={lid}, fnsku={fnsku}, sku={sku}, seller_sku={seller_sku}")
            page_ranges = format_ranges(page_list)
            pdf = utilpdf.extract_pdf_pages(
                file=filename,
                page_list=page_list,
                extra_info=f"SKU: {li[0].sku}\n"
                           f"SellerSKU: {li[0].seller_sku}\n"
                           f"FNSKU: {li[0].fnsku}\n"
                           f"BID: {li[0].batch_id}\n"
                           f"Range: {', '.join(page_ranges)}\n"
                           f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                           f"Seller: {seller_name}, {seller_account_name}\n"
                           f"Quantity: {len(li)}\n"
            )
            final_page_list.extend(page_list + [-1])
            pdf_list.append(pdf)

            await self.create_print_log(
                listing_id=lid,
                batch_id=li[0].batch_id,
                seller_sku=seller_sku,
                created_by="system",
                action=ActionType.CALCULATE,
                content=f"{len(page_list)} Transparency codes were generated (pages: {page_ranges}) . ",
            )

        final_pdf = utilpdf.concat_pdfs(pdf_list)

        if isinstance(crop_box, tuple) and len(crop_box) == 4:
            crop_box = utilpdf.mm(*crop_box)  # convert mm to pt
            final_pdf = utilpdf.crop_pdf_area(final_pdf, crop_box)
            final_pdf = utilpdf.add_page_numbers(final_pdf,
                                                 font_size=7,
                                                 position=utilpdf.mm(15.0, 3.0),
                                                 page_list=final_page_list)

        return final_pdf

    async def delete_transparency_code_by_batch_id(self, bid):
        # Query
        result = await TransparencyCodeModel.filter(batch_id=bid).first()
        # Delete all transparency codes in a batch
        count = await TransparencyCodeModel.filter(batch_id=bid).delete()

        if result:
            await self.create_print_log(
                batch_id=bid,
                listing_id=result.listing_id,
                seller_sku=result.seller_sku,
                action=ActionType.DELETE,
                created_by="system",
                content=f"{count} Transparency codes were deleted in batch (batch_id={bid}). ",
            )
        return {
            "count": count,
            "batch_id": bid,
        }

    async def delete_transparency_code_by_hash(self, hash_):
        # Query
        result = await TransparencyCodeModel.filter(hash=hash_).first()
        # Delete transparency code by hash
        count = await TransparencyCodeModel.filter(hash=hash_).delete()

        if result:
            await self.create_print_log(
                batch_id=result.batch_id,
                listing_id=result.listing_id,
                seller_sku=result.seller_sku,
                action=ActionType.DELETE,
                created_by="system",
                content=f"{count} Transparency codes were deleted (hash={hash_}). ",
            )
        return {
            "count": count,
            "hash": hash_,
        }

    async def __query_product_info_by_lid(self, listing_id: str):
        result = {}
        listings = await self.listing_mdb.query_listings_by_listing_ids([listing_id])
        if not listings:
            raise RuntimeError(f"Listing (id={listing_id}) not found")
        listing = listings[0]['data']
        seller_id = listing['sid']
        seller = await self.basic_mdb.query_seller(seller_id)

        if not seller:
            raise RuntimeError(f"Seller (id={seller_id}) not found")
        seller = seller['data']

        result['sku'] = listing['local_sku']
        result['fnsku'] = listing['fnsku']
        result['seller_sku'] = listing['seller_sku']
        result['item_name'] = listing['item_name']
        result['asin'] = listing['asin']
        result['seller.account_name'] = seller['account_name']
        result['seller.name'] = seller['name']
        return result

    async def create_print_log(self, batch_id: str, listing_id: str, seller_sku: str,
                               action: ActionType,
                               created_by: str,
                               content: str):
        """
        Create a print log for transparency code batch
        :return:
        """
        result = await TransparencyCodePrintLogModel.create(
            batch_id=batch_id,
            listing_id=listing_id,
            seller_sku=seller_sku,
            action=action.value,
            created_by=created_by,
            content=content,
        )
        return result

    #
    async def get_print_logs(self, listing_id: str):
        # Query print logs by listing id
        results = await (TransparencyCodePrintLogModel
                         .filter(listing_id=listing_id)
                         .limit(25)
                         .all())
        logs = [TransparencyCodePrintLog_Pydantic.from_orm(log) for log in results]
        return {
            "data": logs,
            "total": len(logs),
        }

    #
    # async def delete_transparency_code_by_batch_id(self, batch_id: str):
    #     # Delete all transparency codes in a batch
    #     pass
