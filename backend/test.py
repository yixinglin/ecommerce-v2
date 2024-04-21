
from rest import AmazonOrderAPI, AmazonOrderMongoDBManager


def save_orders():
    with AmazonOrderMongoDBManager("192.168.8.10", 27017) as man:
        man.save_all_orders(days_ago=2, FulfillmentChannels=["MFN"])
        # man.save_order("306-7409173-7592316")

def fetch_orders():
    with AmazonOrderMongoDBManager("192.168.8.10", 27017) as man:
        orders = man.find_orders(filter={"order.OrderStatus": "Shipped"})
        for order in orders:
            print(order)

        daily = man.get_daily_mfn_sales(days_ago=10)
        print(daily)
    pass


if __name__ == '__main__':
   #  save_orders()
   fetch_orders()
