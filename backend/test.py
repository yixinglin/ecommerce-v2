
from rest import (AmazonOrderAPI,
                  AmazonOrderMongoDBManager, AmazonCatalogAPI,
                  AmazonCatalogManager)


def save_orders():
    with AmazonOrderMongoDBManager("192.168.8.10", 27017) as man:
        man.save_all_orders(days_ago=10, FulfillmentChannels=["MFN"])
        # man.save_order("306-7409173-7592316")

def fetch_orders():
    with AmazonOrderMongoDBManager("192.168.8.10", 27017) as man:
        orders = man.find_orders(filter={"order.OrderStatus": "Shipped"})
        for order in orders:
            print(order)

        daily = man.get_daily_mfn_sales(days_ago=10)
        print(daily)
    pass

def fetch_catalog():
    # key = AmazonSpAPIKey.from_json()
    # catelogAPI = AmazonCatalogAPI(key)
    # data = catelogAPI.get_catalog_item("B0CVX5FFTQ")
    # image = data['AttributeSets'][0]['SmallImage']['URL']
    with AmazonCatalogManager("192.168.8.10",
                              27017) as man:
        item = man.save_all_catalogs()


if __name__ == '__main__':
   # save_orders()
   # fetch_orders()
   fetch_catalog()
