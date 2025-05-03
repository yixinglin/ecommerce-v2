from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_get_barcode_by_keyword():
    # 确保前面创建过 id=1 的产品
    response = client.get("/api/v1/scanner/product/pid/1261")
    print(response.json())
    assert response.status_code == 200
    assert response.json()["barcode"] == "4000602004945"
    assert response.json()["weight"] == 10.0
    assert response.json()["sku"] == 'DBE-1494000'






