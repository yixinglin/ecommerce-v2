import os
import urllib
from typing import List, Optional
from fastapi import HTTPException
from pydantic import BaseModel
import requests
import copy
from .wpapi import WPAPI_V2, WCAPI_V3, WooClient, ApiKey

"""
    以下代码是对 WordPress API的扩展
"""


class WP_Media_V2(WPAPI_V2):
    """WordPress Media API Client"""

    def upload_image(self, file_path):
        """上传媒体文件"""
        filename = os.path.basename(file_path)
        quoted_filename = urllib.parse.quote(filename)
        url = f"{self.site_url}/wp-json/{self.version}/media"
        headers = copy.deepcopy(self._headers())
        headers['Content-Disposition'] = f'attachment; filename="{quoted_filename}"'
        headers['Content-Type'] = 'image/jpeg'

        assert file_path.endswith(".jpg") or file_path.endswith(".jpeg"), "Only JPEG format is supported"

        with open(file_path, "rb") as f:
            response = requests.post(
                url,
                headers=headers,
                data=f,
                timeout=self.timeout)
        return response

    def delete_media(self, media_id, force=False):
        """删除媒体文件"""
        return self.delete(f"media/{media_id}", {"force": force})


"""
    以下代码是对 WooCommerce API的扩展
"""


class WooProductUpdate(BaseModel):
    """WooCommerce Product"""
    id: int
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    sku: Optional[str] = None
    regular_price: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None


class WC_Product_V3(WCAPI_V3):
    """WooCommerce Product API Client"""

    def __init__(self, url, username, password, **kwargs):
        super().__init__(url, username, password, **kwargs)

    def get_media_api(self):
        """获取媒体 API 客户端"""
        token = self.token
        return WP_Media_V2(
            url=self.site_url,
            username=self.username,
            password=self.password,
            token=token
        )

    def create_simple_product(self, sku, status):
        """创建简单商品"""
        payload = {
            "name": f"Simple Product - {sku}",
            "type": "simple",
            "status": status,
            "sku": sku,
        }
        response = self.post("products", payload)
        return response

    def create_variable_product(self, sku, status):
        """ 创建可变商品 """
        payload = {
            "name": f"Variable Product - {sku}",
            "type": "variable",
            "status": status,
            "sku": sku,
        }
        response = self.post("products", payload)
        return response

    def update_product_images(self, product_id: int, images: List[str], square=False):
        """
            更新商品图片。
            @param product_id: 商品ID
            @param images: 图片本地路径
            @param square: 是否将图片自适应为正方形
        """
        if not images:
            raise ValueError("No images provided")
        parent_path = os.path.dirname(images[0])

        # 图片预处理
        if square:
            target_images = [
                resize_to_square(img, parent_path, size=600)
                for img in images
            ]
        else:
            target_images = images

        # 上传图片到WP媒体库
        media_api = self.get_media_api()
        media_ids = []
        for image_path in target_images:
            response = media_api.upload_image(image_path)
            if response.status_code == 201:
                media_id = response.json().get("id")
                media_ids.append(media_id)
            else:
                raise Exception(f"Failed to upload image: {response.text}")

        # 获取商品信息
        response = self.get(f"products/{product_id}")
        response.raise_for_status()
        if response.status_code != 200:
            raise Exception(f"Failed to get product: {response.text}")

        woo_product = response.json()
        if woo_product['type'] not in ['variable', 'simple']:
            raise ValueError("Only simple or variable product is supported")

        old_image_ids = [image['id'] for image in woo_product['images']]
        new_image_ids = media_ids

        # 更新商品图片
        payload = {
            "images": [
                {"id": image_id} for image_id in new_image_ids
            ]
        }
        update_response = self.put(f"products/{product_id}", payload)
        if update_response.status_code != 200:
            raise Exception(f"Failed to update product: {update_response.text}")

        # 删除旧的WP媒体库图片
        for image_id in old_image_ids:
            response = media_api.delete_media(image_id, force=True)
            if response.status_code != 200:
                raise Exception(f"Failed to delete media: {response.text}")
        return update_response

    def update_product(self, payload: WooProductUpdate):
        id = payload.id
        pl = payload.model_dump(exclude_unset=True)
        response = self.put(f"products/{id}", pl)
        return response
class TrackInfoUpdate(BaseModel):
    order_id: int
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    carrier: Optional[str] = None

class OrderClient(WooClient):

    def __init__(self, key:ApiKey, **kwargs):
        super().__init__(key, **kwargs)

    def fetch_orders(self, params, **kwargs):
        """Fetch a list of orders"""
        response = self.get("orders", params=params)
        if response.status_code != 200:
            raise HTTPException(f"Failed to get orders: {response.text}")
        return {
            "data": response.json(),
            "total_pages": int(response.headers.get("X-WP-TotalPages")),
            "total": int(response.headers.get("X-WP-Total")),
        }

    def fetch_order(self, order_id):
        """Fetch a single order"""
        response = self.get(f"orders/{order_id}")
        if response.status_code != 200:
            raise HTTPException(f"Failed to get order: {response.text}")
        return response.json()

    def update_track_info(self, info: TrackInfoUpdate):
        """Update tracking information for an order and change status to complete"""
        tracking_payload = {
            "status": "completed",
            "meta_data": [
                {
                    "key": "tracking_number",
                    "value": info.tracking_number
                },
                {
                    "key": "tracking_url",
                    "value": info.tracking_url
                },
                {
                    "key": "carrier",
                    "value": info.carrier
                }
            ]
        }
        response = self.put(f"orders/{info.order_id}", tracking_payload)
        if response.status_code != 200:
            raise HTTPException(f"Failed to update tracking info: {response.text}")
        return response.json()


