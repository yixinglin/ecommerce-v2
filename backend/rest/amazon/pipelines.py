#
#
# PL_DAILY_FBM_ORDERS_COUNT = [
#             {
#                 '$unwind': '$items.OrderItems'  # Unwind the items array to get each item
#             }, {
#                 '$project': {
#                     '_id': 0,
#                     'orderDate': {
#                         '$dateFromString': {
#                             'dateString': '$order.PurchaseDate'
#                         }
#                     },
#                     'asin': '$items.OrderItems.ASIN',
#                     'quantityOrdered': '$items.OrderItems.QuantityOrdered',
#                     'quantityShipped': '$items.OrderItems.QuantityShipped',
#                     'sellerSKU': '$items.OrderItems.SellerSKU',
#                     'title': '$items.OrderItems.Title',
#                     'fulfillmentChannel': '$order.FulfillmentChannel',
#                     'orderStatus': '$order.OrderStatus'
#                 }
#             }, {
#                 '$match': {  # Filter orders that are not MFN and not canceled, and within the specified time range.
#                     'orderStatus': {'$ne': 'Canceled'},
#                     'fulfillmentChannel': 'MFN',
#                     "orderDate": {"$gte": start_date},
#                 }
#             }, {
#                 '$group': {
#                     '_id': {
#                         'date': {
#                             '$dateToString': {
#                                 'format': '%Y-%m-%d',
#                                 'date': '$orderDate'
#                             }
#                         },
#                         'asin': '$asin'
#                     },
#                     'totalQuantityOrdered': {
#                         '$sum': '$quantityOrdered'
#                     },
#                     'totalQuantityShipped': {
#                         '$sum': '$quantityShipped'
#                     },
#                     'sellerSKU': {
#                         '$first': '$sellerSKU'
#                     },
#                     'title': {
#                         '$first': '$title'
#                     }
#                 }
#             },
#             {'$sort': {'sellerSKU': 1}},
#             {
#                 '$group': {
#                     '_id': '$_id.date',
#                     'purchaseDate': {'$first': '$_id.date'},
#                     'dailyOrdersItemsCount': {'$sum': '$totalQuantityOrdered'},
#                     'dailyShippedItemsCount': {'$sum': '$totalQuantityShipped'},
#                     'dailyShipments': {
#                         '$push': {
#                             'asin': '$_id.asin',
#                             'sellerSKU': '$sellerSKU',
#                             'totalQuantityShipped': '$totalQuantityShipped',
#                             'totalQuantityOrdered': '$totalQuantityOrdered',
#                             'title': '$title'
#                         }
#                     }
#                 }
#             }, {
#                 '$sort': {
#                     '_id': -1
#                 }
#             }
#         ]