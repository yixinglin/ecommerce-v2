import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
import requests
from requests.auth import HTTPBasicAuth
from utils import utilpdf
from utils import stringutils
import easygui



# 模拟批量处理订单

"""
步骤：
1. 把亚马逊的装箱单发送到服务器，保存在Redis中，返回键Key.
2. 调用批量处理订单的接口，传入key, 服务器解析装箱单，并把客户地址保存到MongoDB中，并且返回订单id
3. 客户调用批量发货接口，传入订单id，服务器生成运单后，把结果暂存在redis中。服务器返回批次号
4. 客户根据批次号查询结果，下载pdf，保存在本地。
"""

URL_MAP = {
    'dev': "http://192.168.8.70:5018",
    'stage': "http://192.168.8.10:5018",
    'prod': "http://192.168.8.95:5018"
}

BASE_URL = URL_MAP['dev']
username = ""
password = ""

root = ".temp"
api_key_index = 0     # Amazon API key index

def get_method(*args, **kwargs):
    return requests.get(auth=HTTPBasicAuth(username, password), *args, **kwargs)

def post_method(*args, **kwargs):
    return requests.post(auth=HTTPBasicAuth(username, password), *args, **kwargs)

def update_database():
    params = {"api_key_index": api_key_index, "up_to_date": True}
    get_method(f"{BASE_URL}/api/v1/amazon/orders/unshipped",
                 params=params)

def display_unshipped_orders():
    # 获取未发货订单号。
    params = {"api_key_index": api_key_index, "up_to_date": True}
    resp = get_method(f"{BASE_URL}/api/v1/amazon/orders/unshipped", params=params)
    orderIds = resp.json()['data']['orderNumbers']
    # 生成装箱单下载链接
    resp = get_method(f"{BASE_URL}/api/v1/amazon/orders/sc-urls")
    data = resp.json()['data']
    pack_slip_url = f"{data['packing-slip']}/?orderIds={';'.join(orderIds)}"
    print(f"装箱单下载链接: {pack_slip_url}\n")
    return orderIds

def sim_upload_amazon_pack_slips():
    # Simulate the upload of Amazon packing slips to the server
    input("Step 1:模拟从紫鸟浏览器下载装箱单，按任意键继续。。。")
    display_unshipped_orders()

    # Download a packing slip from the website
    url = "https://www.hamster25.buzz/amazon/amazon-delivery-de-07.html"
    response = get_method(url)
    text = response.text.encode('utf-8')
    msg = "装箱单下载成功，准备上传到服务器"
    print(msg)
    easygui.msgbox(msg, title="装箱单下载成功, 准备上传到服务器")
    endpoint = BASE_URL + "/api/v1/amazon/orders/packslip/cache"
    resp = post_method(endpoint, data=text)
    key = resp.json()['data']['key']
    msg = f"装箱单上传成功，Key = {key}"
    print(msg)
    easygui.msgbox(msg, title="装箱单上传成功")
    return key

def upload_amazon_pack_slips_via_file():
    input("Step 1: 读取本地装箱单文件，按任意键继续。。。")
    # 获取未发货订单号。
    display_unshipped_orders()
    msg = "请下载装箱单到本地，然后用文件浏览器选择它，按任意键继续。。。"
    # input("请下载装箱单到本地，然后用文件浏览器选择它，按任意键继续。。。")
    easygui.msgbox(msg, title="下载")

    fpath = easygui.fileopenbox()
    print(f"选择的文件路径: {fpath}\n")
    # 上传本地装箱单文件到服务器
    with open(fpath, 'r', encoding='utf-8') as f:
        html_content = f.read()
    endpoint = BASE_URL + "/api/v1/amazon/orders/packslip/cache"
    headers = {'Content-Type': 'text/html'}
    resp = post_method(endpoint, data=html_content.encode('utf-8'), headers=headers)
    print(resp.content)
    key = resp.json()['data']['key']
    print(f"装箱单上传成功，Key = {key}\n")
    return key


def test_amazon_packslip_parser(key):
    input(f"Step 2: 从服务器下载暂存的装箱单，按任意键继续。。。\nKey={key}")
    endpoint = BASE_URL + "/api/v1/amazon/orders/packslip/uncache"
    params = {"key": key}
    resp = get_method(endpoint, params=params)
    text = resp.text
    print("装箱单解析成功，数据如下：\n")
    print(text[1000:1200], "...\n")

    input(f"Step 2.1: 解析装箱单，按任意键继续。。。")
    endpoint = BASE_URL + "/api/v1/amazon/orders/packslip/parse"
    body = {
      "country": "DE",
      "formatIn": "html",
      "formatOut": "",
      "data": f"{text}"
    }

    # Send the request to the server to parse the packing slip
    resp = post_method(endpoint, json=body)
    print(resp.url)
    data = resp.json()['data']
    orderIds = [od.get('orderId') for od in data.get('orders')]
    # print("\n".join(orderIds))
    for i, oid in enumerate(orderIds):
        print(f"订单{i+1}: {oid}")
    print(data['message'], "\n")
    easygui.msgbox(data['message'], title="装箱单解析成功")
    return data.get('orders')

# Add function to create parcel labels for the orders
def test_create_parcel_labels(orderIds):
    input(f"Step 3: 批量生成运单，这个过程可能持续几分钟，请耐心等待。。。按任意键继续。。。")
    endpoint = BASE_URL + "/api/v1/pickpack/amazon/bulk-ship/gls"
    resp = post_method(endpoint, json=orderIds)
    print(resp.url)
    if resp.status_code != 200:
        print(resp.text)
        exit(1)
        return
    data = resp.json()['data']
    batchId = data['batchId']
    print(data['message'])
    msg = f"运单已生成，批次号为: {batchId}\n"
    print(msg)
    easygui.msgbox(msg, title="运单生成成功")
    return batchId

# Add function to create manifest for the orders
def test_get_manifest(batchId):
    print(f"Step 4: 保存文件到本地，批次号：【{batchId}】")
    msg = "请准备打印运单和装箱单，然后到卖家中心确认订单，明白后点确定。。。"
    easygui.msgbox(msg, title="打印运单和装箱单")
    folder = os.path.join(root, batchId.replace(':', '-'))
    os.makedirs(folder, exist_ok=True)
    print(f"文件夹创建成功: {folder}\n")

    resp = get_method(f"{BASE_URL}/api/v1/pickpack/common/batch-ship-event", params={'batchId': batchId})
    data = resp.json()['data']
    print(resp.url)
    orderIds = data['orderIds']
    shipmentIds = data['shipmentIds']

    parcelLabelB64 = data['parcelLabelB64']
    packSlipB64 = data['packSlipB64']
    pdf = utilpdf.str_to_pdf(parcelLabelB64)
    html = stringutils.base64_decode_str(packSlipB64)
    with open(f'{folder}/parcels-V1-redis.pdf', 'wb') as f:
        f.write(pdf)
    with open(f'{folder}/pack-slip.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # input("运单和装箱单已经保存到本地, 请打印。\n按任意键打开文件夹。。。\n")
    msg = "运单和装箱单已经保存到本地, 请打印。点击确定打开文件夹。。。"
    easygui.msgbox(msg, title="保存成功")
    os.startfile(folder)

    resp = get_method(f"{BASE_URL}/api/v1/amazon/orders/sc-urls")
    data = resp.json()['data']
    bulk_confirm_shipment_url = f"{data['bulk-confirm-shipment']}/{';'.join(orderIds)}"

    input("按任意键开始批量确认Amazon订单。。。\n")
    msg = "接下来会打开一个txt文件，里面包含订单号和运单号的对应关系，请把它粘贴到亚马逊" \
          "卖家中心进行批量确认。明白后点击确定。。。\n"
    easygui.msgbox(msg, title="批量确认")
    pair = list(zip(orderIds, shipmentIds))
    pair_file = f'{folder}/order-shipment-pair.txt'
    txt_content = "\n".join([f"{o}: {s}" for o, s in pair])
    txt_content = f"请打开以下连接\n{bulk_confirm_shipment_url}\n\n请复制以下内容({len(pair)}条): \n{txt_content}"
    with open(f'{folder}/order-shipment-pair.txt', 'w', encoding='utf-8') as f:
        f.write(txt_content)
    print(bulk_confirm_shipment_url)
    os.startfile(pair_file)

    input("按任意键开始下载拣货单和订单列表。。。\n")
    # Save pick slip as excel
    refs = ";".join(orderIds)
    resp = get_method(f"{BASE_URL}/api/v1/pickpack/amazon/batch-pick", params={'refs': refs})
    print(resp.url)
    with open(f'{folder}/pick-slip.xlsx', 'wb') as f:
        f.write(resp.content)

    # Save pack slip as excel
    resp = get_method(f"{BASE_URL}/api/v1/pickpack/amazon/batch-pack", params={'refs': refs})
    print(resp.url)
    with open(f'{folder}/pack-slip.xlsx', 'wb') as f:
        f.write(resp.content)

    # Save parcels as pdf
    resp = get_method(f"{BASE_URL}/api/v1/carriers/gls/shipments/bulk-labels", params={'refs': refs})
    print(resp.url)
    data: bytes = resp.content
    with open(f'{folder}/parcels-V2-mongo.pdf', 'wb') as f:
        f.write(data)

    msg = "拣货单和订单列表已经保存到本地，请打印。"
    easygui.msgbox(msg, title="保存成功")
    os.startfile(folder)


if __name__ == '__main__':
    # key = sim_upload_amazon_pack_slips()
    key = upload_amazon_pack_slips_via_file()
    print("=" * 20)
    print("开始执行订单批量处理脚本。。。")
    orders = test_amazon_packslip_parser(key)
    orderIds = [o['orderId'] for o in orders]
    batchId = test_create_parcel_labels(orderIds)
    test_get_manifest(batchId)
    update_database()
    input("恭喜你，完成了整个批量发货流程，按任意键结束任务。。。")