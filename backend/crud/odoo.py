from typing import List, Optional

from pymongo import UpdateOne

from core.db import MongoDBDataManager


class OdooContactMongoDB(MongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "odoo_data"
        self.db_collection_name = "res.partner"

    def get_db_collection(self):
        return self.db_client[self.db_name][self.db_collection_name]

    def query_contacts(self, offset: int = 0, limit: int = None, *args, **kwargs):
        collection = self.get_db_collection()
        results = collection.find(**kwargs)
        if limit is not None:
            results = results.limit(limit)
        if offset > 0:
            results = results.skip(offset)
        return list(results)

    def query_contact_by_ids(self, ids: List[int]):
        filter_ = {"_id": {"$in": ids}}
        contacts = list(self.query_contacts(filter=filter_, limit=len(ids)))
        # TODO Sort the contacts by the given ids
        # if len(contacts) > 0:
        #     contact_dict = {}
        return contacts

    def query_contact_by_id(self, id: int):
        result = self.query_contact_by_ids(ids=[id])
        return result[0] if result else None

    def save_contact(self, contact_id, document):
        collection = self.get_db_collection()
        result = collection.update_one(
            {"_id": contact_id},
            {"$set": document},
            upsert=True
        )
        return result

    def to_standard_contact(self, contact: dict):
        # TODO: To Standard Contact Object
        pass

    def delete_random_documents(self, **kwargs) -> Optional[int]:
        return super().delete_random_documents(
            database_name=self.db_name,
            collection_name=self.db_collection_name,
            **kwargs,
        )


class OdooProductTemplateMongoDB(MongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "odoo_data"
        self.db_collection_name = "product.template"

    def get_db_collection(self):
        return self.db_client[self.db_name][self.db_collection_name]

    def query_product_templates(self, offset: int = 0, limit=None, *args, **kwargs):
        collection = self.get_db_collection()
        result = collection.find(**kwargs)
        if offset > 0:
            result = result.skip(offset)
        if limit is not None:
            result = result.limit(limit)
        return list(result)

    def query_product_template_by_ids(self, ids: List[int]):
        filter_ = {"_id": {"$in": ids}}
        product_templates = list(self.query_product_templates(filter=filter_, limit=len(ids)))
        return product_templates

    def query_product_template_by_id(self, id: int):
        result = self.query_product_template_by_ids(ids=[id])
        return result[0] if result else None

    def save_product_template(self, product_templ_id, document):
        collection = self.get_db_collection()
        result = collection.update_one(
            {"_id": product_templ_id},
            {"$set": document},
            upsert=True
        )
        return result

    def to_standard_product(self, product_template: dict):
        #TODO: To Standard Product Object
        raise NotImplementedError

    def delete_random_documents(self, **kwargs) -> Optional[int]:
        return super().delete_random_documents(
            database_name=self.db_name,
            collection_name=self.db_collection_name,
            **kwargs,
        )


class OdooProductMongoDB(OdooProductTemplateMongoDB):

    def __init__(self):
        super().__init__()
        self.db_collection_name = "product.product"

    def query_products(self, offset: int = 0, limit=None, *args, **kwargs):
        # TODO: 实现查询产品的功能
        # return super().query_product_templates(offset, limit, *args, **kwargs)

        collection = self.get_db_collection()
        result = collection.find(**kwargs)
        if offset > 0:
            result = result.skip(offset)
        if limit is not None:
            result = result.limit(limit)
        return list(result)

    def query_product_by_ids(self, ids: List[int]):
        # TODO: 实现查询产品的功能
        filter_ = {"_id": {"$in": ids}}
        products = list(self.query_products(filter=filter_, limit=len(ids)))
        return products

    def query_product_by_id(self, id: int):
        # TODO: 实现查询产品的功能
        result = self.query_product_by_ids(ids=[id])
        return result[0] if result else None

    def save_product(self, product_id, document):
        # return super().save_product_template(product_id, document)
        collection = self.get_db_collection()
        result = collection.update_one(
            {"_id": product_id},
            {"$set": document},
            upsert=True
        )
        return result

    def to_standard_product(self, product_template: dict):
        #TODO: To Standard Product Object
        raise NotImplementedError

    def delete_random_documents(self,  **kwargs) -> Optional[int]:
        return super().delete_random_documents(
            **kwargs,
        )


class OdooPackagingMongoDB(MongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "odoo_data"
        self.db_collection_name = "product.packaging"

    def get_db_collection(self):
        return self.db_client[self.db_name][self.db_collection_name]

    def query_packagings(self, offset: int = 0, limit=None, *args, **kwargs):
        collection = self.get_db_collection()
        results = collection.find(**kwargs)
        if limit is not None:
            results = results.limit(limit)
        if offset > 0:
            results = results.skip(offset)
        return list(results)

    def query_packaging_by_ids(self, ids: List[int]):
        filter_ = {"_id": {"$in": ids}}
        packagings = list(self.query_packagings(filter=filter_, limit=len(ids)))
        return packagings

    def query_packaging_by_id(self, id: int):
        result = self.query_packaging_by_ids(ids=[id])
        return result[0] if result else None

    def save_packaging(self, packaging_id, document):
        collection = self.get_db_collection()
        result = collection.update_one(
            {"_id": packaging_id},
            {"$set": document},
            upsert=True
        )
        return result

    def delete_random_documents(self, **kwargs) -> Optional[int]:
        return super().delete_random_documents(
            database_name=self.db_name,
            collection_name=self.db_collection_name,
            **kwargs,
        )



class OdooStorageLocationMongoDB(MongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "odoo_data"
        self.db_collection_name = "stock.location"

    def get_db_collection(self):
        return self.db_client[self.db_name][self.db_collection_name]

    def query_storage_locations(self, offset: int = 0, limit=None, *args, **kwargs):
        collection = self.get_db_collection()
        results = collection.find(**kwargs)
        if limit is not None:
            results = results.limit(limit)
        if offset > 0:
            results = results.skip(offset)
        return list(results)

    def query_storage_location_by_ids(self, ids: List[int]):
        filter_ = {"_id": {"$in": ids}}
        storage_locations = list(self.query_storage_locations(filter=filter_, limit=len(ids)))
        return storage_locations

    def query_storage_location_by_id(self, id: int):
        result = self.query_storage_location_by_ids(ids=[id])
        return result[0] if result else None

    def save_storage_location(self, storage_location_id, document):
        collection = self.get_db_collection()
        result = collection.update_one(
            {"_id": storage_location_id},
            {"$set": document},
            upsert=True
        )
        return result

    def to_standard_storage_location(self, storage_location: dict):
        #TODO: To Standard Storage Location Object
        pass

    def delete_random_documents(self, **kwargs) -> Optional[int]:
        return super().delete_random_documents(
            database_name=self.db_name,
            collection_name=self.db_collection_name,
            **kwargs,
        )


class OdooPutawayRuleMongoDB(MongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "odoo_data"
        self.db_collection_name = "stock.putaway.rule"

    def get_db_collection(self):
        return self.db_client[self.db_name][self.db_collection_name]

    def query_putaway_rules(self, offset: int = 0, limit=None, *args, **kwargs):
        collection = self.get_db_collection()
        results = collection.find(**kwargs)
        if limit is not None:
            results = results.limit(limit)
        if offset > 0:
            results = results.skip(offset)
        return list(results)


    def query_putaway_rule_by_ids(self, ids: List[int]):
        filter_ = {"_id": {"$in": ids}}
        putaway_rules = list(self.query_putaway_rules(filter=filter_, limit=len(ids)))
        return putaway_rules

    def query_putaway_rule_by_id(self, id: int):
        result = self.query_putaway_rule_by_ids(ids=[id])
        return result[0] if result else None

    def save_putaway_rule(self, putaway_rule_id, document):
        collection = self.get_db_collection()
        result = collection.update_one(
            {"_id": putaway_rule_id},
            {"$set": document},
            upsert=True
        )
        return result

    def delete_random_documents(self, **kwargs) -> Optional[int]:
        return super().delete_random_documents(
            database_name=self.db_name,
            collection_name=self.db_collection_name,
            **kwargs,
        )


class OdooQuantMongoDB(MongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "odoo_data"
        self.db_collection_name = "stock.quant"


    def get_db_collection(self):
        return self.db_client[self.db_name][self.db_collection_name]

    def query_quants(self, offset: int = 0, limit=None, *args, **kwargs):
        collection = self.get_db_collection()
        results = collection.find(**kwargs)
        if limit is not None:
            results = results.limit(limit)
        if offset > 0:
            results = results.skip(offset)
        return list(results)

    def query_quant_by_ids(self, ids: List[int]):
        filter_ = {"_id": {"$in": ids}}
        quants = list(self.query_quants(filter=filter_, limit=len(ids)))
        return quants

    def query_quant_by_id(self, id: int):
        result = self.query_quant_by_ids(ids=[id])
        return result[0] if result else None

    def save_quant(self, quant_id, document):
        collection = self.get_db_collection()
        result = collection.update_one(
            {"_id": quant_id},
            {"$set": document},
            upsert=True
        )
        return result

    def to_standard_quant(self, quant: dict):
        # TODO: To Standard Quant Object
        raise NotImplementedError

    def delete_random_documents(self, **kwargs) -> Optional[int]:
        return super().delete_random_documents(
            database_name=self.db_name,
            collection_name=self.db_collection_name,
            **kwargs,
        )


class OdooOrderlineMongoDB(MongoDBDataManager):

    def __init__(self):
        super().__init__()
        self.db_name = "odoo_data"
        self.db_collection_name = "sale.order.line"

    def get_db_collection(self):
        return self.db_client[self.db_name][self.db_collection_name]

    def save_orderline(self, orderline_id, document):
        collection = self.get_db_collection()
        result = collection.update_one(
            {"_id": orderline_id},
            {"$set": document},
            upsert=True
        )
        return result

    def save_orderlines(self, orderline_ids, documents):
        collection = self.get_db_collection()
        operations = []

        for orderline_id, document in zip(orderline_ids, documents):
            operations.append(
                UpdateOne(
                    {"_id": orderline_id},
                    {"$set": document},
                    upsert=True
                )
            )

        if operations:
            result = collection.bulk_write(operations)
            return result
        else:
            return None

    def query_orderlines(self, offset: int = 0, limit=None, *args, **kwargs):
        collection = self.get_db_collection()
        results = collection.find(**kwargs)
        if limit is not None:
            results = results.limit(limit)
        if offset > 0:
            results = results.skip(offset)
        return list(results)

    def to_standard_orderline(self, orderline: dict):
        raise NotImplementedError

































