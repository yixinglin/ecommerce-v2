import os
import time
from io import BytesIO
from starlette.responses import StreamingResponse
from typing import List, Union
from fastapi import APIRouter, Query, Body, Path
from starlette.requests import Request
from starlette.templating import Jinja2Templates
import utils.time as utils_time
from core.config import settings
from core.exceptions import ShipmentExistsException
from core.log import logger
from models.shipment import StandardShipment
from rest.gls.DataManager import GlsShipmentMongoDBManager
from schemas.basic import ResponseSuccess, ResponseFailure, CodeEnum, BasicResponse
from vo.carriers import ShipmentVO, CreatedShipmentVO, PickSlipItemVO

gls = APIRouter(prefix="/gls", tags=["GLS Services"], )

@gls.get("/shipments",
         summary="Get a GLS Shipment by reference from database",
         response_model=BasicResponse[Union[ShipmentVO, None]])
def get_gls_shipment_by_reference(reference: str = Query(None, description="GLS Shipment reference"),
                                  labels: bool = Query(False, description="Whether to include labels in the response")):
    """
    Get a GLS Shipment by reference from database

    Args:
        reference (str): GLS Shipment reference
        labels (bool, optional): Whether to include labels in the response. Defaults to False.


    Returns:
        BasicResponse[Union[ShipmentVO, None]]: ShipmentVO object if found, otherwise None

    :return:
    """
    with GlsShipmentMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                                   key_index=settings.GLS_ACCESS_KEY_INDEX) as man:
        shipment = man.find_shipment_by_id(reference)
        if shipment is None:
            return ResponseFailure(code=CodeEnum.NotFound, message="Shipment not found")
        references = shipment.references   # shipment["_id"].split(";")
        carrier_name = shipment.carrier # shipment["carrier"].upper()
        trackNumbers = [p.trackNumber for p in shipment.parcels]  # [item['trackId'] for item in shipment['data']['parcels']]
        trackingUrls = [p.locationUrl for p in shipment.parcels]
        createdAt = shipment.createdAt
        consignee = shipment.consignee
        if labels:
            labelsData = shipment.label
        else:
            labelsData = ""
        current_time = utils_time.now()
        new = False if utils_time.diff_datetime(current_time, createdAt) > 1 else True
        # alias = shipment["alias"].upper()
        messages = []
        contents = [item.content for item in shipment.parcels]

        vo = ShipmentVO(
            references=references,
            carrier_name=carrier_name,
            trackNumbers=trackNumbers,
            trackingUrls=trackingUrls,
            createdAt=createdAt,
            labels=labelsData,
            new=new,
            alias="?",
            messages=messages,
            contents=contents,

            name1=consignee.name1,
            name2=consignee.name2,
            name3=consignee.name3,
            street1=consignee.street1,
            zipCode=consignee.zipCode,
            city=consignee.city,
            province=consignee.province,
            country=consignee.country,

        )
        return ResponseSuccess(data=vo)

@gls.get("/shipments/view",
         summary="Displace a GLS Shipment by reference from database to HTML view")
def get_gls_shipments_html(request: Request,
                           reference: str = Query(None, description="GLS Shipment reference"), ):
    response = get_gls_shipment_by_reference(reference, labels=True)
    if response.code == CodeEnum.Success:
        data = response.data
    else:
        return "Internal Server Error"
    templates = Jinja2Templates(directory=os.path.join("assets", "templates", "web"))
    return templates.TemplateResponse(name="ShipmentView.html",
                                      request=request,
                                      context={"data": data})

@gls.post("/shipments",
          summary="Create a GLS Shipment using GLS-WebAPI",
          response_model=BasicResponse[CreatedShipmentVO])
def create_gls_shipment(shipment: StandardShipment =
                        Body(None, description="StandardShipment object including "
                                                "all necessary information about the shipment")):
    """
    Create a GLS Shipment using GLS-WebAPI

    Args:
        shipment (StandardShipment): StandardShipment object

    Returns:
        BasicResponse[CreatedShipmentVO]: CreatedShipmentVO object
    """
    with GlsShipmentMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                                   key_index=settings.GLS_ACCESS_KEY_INDEX) as man:
        try:
            id = man.save_shipment(shipment)
            time.sleep(0.2)
            status = 0
            message = "New shipment created"
        except ShipmentExistsException as e:
            logger.info(e)
            id = man.join_shipment_id(shipment)
            status = 1
            message = ("Shipment already exists. The system won't create a new one "
                       "unless you delete the existing one first.")

    data = CreatedShipmentVO(id=id, status=status, message=message)
    return ResponseSuccess(data=data)


@gls.post("/shipments/bulk",
          summary="Create multiple GLS Shipments using GLS-WebAPI",
          response_model=BasicResponse[List[CreatedShipmentVO]])
def create_gls_shipment_bulk(shipments: List[StandardShipment]
      = Body(None, description="List of StandardShipment objects including "
                                "all necessary information about the shipments about the shipment")):
    data = []
    for i, shipment in enumerate(shipments):
        data.append(create_gls_shipment(shipment=shipment).data)
    return ResponseSuccess(data=data, size=len(data))


# @gls.get("/shipments/pick", summary="List GLS Shipments by references",
#          response_model=BasicResponse[List[PickSlipItemVO]],
#          deprecated=True)
# def get_gls_pick_slip_by_references(refs: str):
#     """
#     List GLS Shipments by references
#     :param references:
#     :return:
#     """
#     refs = refs.split(";")
#     with PickPackDataManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
#         vo = man.get_pick_slip_items(refs)
#     return ResponseSuccess(data=vo, size=len(vo))

# @gls.get("/shipments/batch-pick", summary="Btach Pick Slips by sku",
#          response_model=BasicResponse[List[dict]])
# def get_gls_batch_pick_slip_by_references(refs: str):
#     """
#     List GLS Shipments by references
#     :param references:
#     :return:
#     """
#     refs = refs.split(";")
#     with PickPackDataManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
#         vo = man.get_batch_pick_slip(refs)
#     return ResponseSuccess(data=vo, size=len(vo))

# @gls.get("/shipments/report", summary="Report GLS Shipments by Excel",
#          response_class=StreamingResponse, deprecated=True)
# def report_shipment_by_excel(refs: str = Query(None, description="GLS Shipment references separated by semicolon")):
#     references = refs.split(";")
#     with PickPackDataManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
#         vo = man.get_pick_slip_items(references)
#         excelData = man.pick_slip_to_excel(vo)
#         filename = f"gls-{utils_time.now(pattern='%Y%m%d-%H%M%S')}.xlsx"
#         headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
#         return StreamingResponse(BytesIO(excelData),
#                                  media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                                  headers=headers)

@gls.get("/shipments/bulk-labels",
         summary="Download GLS Shipment labels",
         response_class=StreamingResponse)
def download_labels(request: Request,
                    refs: str = Query(None, description="GLS Shipment references separated by semicolon")):
    """
    开启一个页面，显示所有的PDF运单，方便下载
    :param refs: GLS Shipment references separated by semicolon
    :return: ResponseSuccess
    """
    references = refs.split(";")
    if len(references) != len(set(references)):
        raise RuntimeError("Duplicate references found. Please check and remove them first.")

    with GlsShipmentMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                                   key_index=settings.GLS_ACCESS_KEY_INDEX) as man:
        pdfs = man.get_bulk_shipments_labels(references)
    filename = f"GLS_BULK_{utils_time.now(pattern='%Y%m%d%H%M%S')}.pdf"
    headers = {'Content-Disposition': f'inline; filename="{filename}.pdf"'}
    return StreamingResponse(BytesIO(pdfs),
                             media_type="application/pdf", headers=headers)

@gls.delete("/shipments/{id}",
            summary="Delete a GLS Shipment by ID from database",
            response_model=BasicResponse[dict])
def delete_gls_shipment(id: str = Path(description="GLS Shipment ID to delete")):

    with GlsShipmentMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT,
                                   key_index=settings.GLS_ACCESS_KEY_INDEX) as man:
        count = man.delete_shipment(id)
    data = dict(deletedCount=count)
    return ResponseSuccess(data=data)
