from typing import Any, Dict, Optional

from ..models import AddressModel

MAX_NAME_LEN = 40


def build_gls_delivery_from_address(address: AddressModel) -> Dict[str, Any]:
    """
    将 AddressModel 映射为 GLS delivery 请求体。
    规则：
    - name1 必填；name2、name3 选填，填充顺序：company → name → address2
    - street1 ← address1
    - country 优先使用 country_code（ISO，如 DE），否则回退到 country
    - zipCode ← postal_code，city ← city，email ← email，mobile ← mobile
    - 自动去除多余空白、去重，保证 name1 不为空
    - 对德国地址（country_code == 'DE'）尽量保证信息完整（name1、street1、zipCode、city）
    """

    def norm(s: Optional[str]) -> str:
        if not s:
            return ""
        # 折叠多空格并去掉首尾空白
        return " ".join(str(s).strip().split())

    # 取字段并标准化
    company = norm(getattr(address, "company", None))
    name = norm(getattr(address, "name", None))
    address2 = norm(getattr(address, "address2", None))
    street1 = norm(getattr(address, "address1", None))
    city = norm(getattr(address, "city", None))
    zip_code = norm(getattr(address, "postal_code", None))
    email = norm(getattr(address, "email", None))
    mobile = norm(getattr(address, "mobile", None))
    country = norm(getattr(address, "country", None))
    country_code = norm(getattr(address, "country_code", None)).upper()

    # 组装 name1/2/3，顺序：company → name → address2，并去重、去空
    name_candidates = []
    for part in (company, name, address2):
        if part and part not in name_candidates:
            name_candidates.append(part)

    # 至少要有一个用于 name1；若都为空，尝试用 (city or country) 兜底，否则抛错
    if not name_candidates:
        fallback = norm(" / ".join(x for x in (city, country or country_code) if x))
        if fallback:
            name_candidates.append(fallback)
        else:
            raise ValueError("GLS delivery.name1 is required but both company/name/address2 are empty.")

    name1 = name_candidates[0]
    name2 = name_candidates[1] if len(name_candidates) > 1 else ""
    name3 = name_candidates[2] if len(name_candidates) > 2 else ""

    # 校验 street1（必填）
    if not street1:
        raise ValueError("GLS delivery.street1 is required (mapped from address1).")

    # 选择 country 字段：优先 ISO 码
    gls_country = country_code or country
    if not gls_country:
        raise ValueError("GLS delivery.country is required (country_code or country).")

    # 德国地址尽量完整：zipCode/city 不能为空（不给死卡，给出提示式校验）
    if gls_country == "DE":
        if not zip_code or not city:
            raise ValueError("For DE addresses, zipCode and city should be provided for a complete address.")

    delivery = {
        "name1": name1,
        "name2": name2,
        "name3": name3,
        "street1": street1,  # ← address1
        "country": gls_country,  # 优先 country_code（如 DE）
        "zipCode": zip_code,
        "city": city,
        "email": email,
        "mobile": mobile,
    }

    return delivery


def build_gls_single_parcel(weight: float = 1.0, comment: str = "") -> Dict[str, Any]:
    return {
        "weight": weight,
        "comment": comment,
        "services": [{"name": "flexdeliveryservice"}]
    }


if __name__ == "__main__":
    address = {
        "name": "John Doe John Doe John DoeJohn DoeJohn Doe",
        "company": "Acme Corp GmBH GmBHGmBHGmBHGmBHGmBH",
        "email": "john.doe@example.com",
        "mobile": "123-456-7890",
        "address1": "Grosse Strasse 123",
        # "address2": "OG2",
        "city": "Hamburg",
        "postal_code": "22113",
        "country_code": "DE",
        "country": "Germany"
    }
    address_model = AddressModel(**address)
    payload = build_gls_delivery_from_address(address_model)
    for k, v in payload.items():
        print(f"{k}: {v}")
