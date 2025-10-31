import io, base64
from barcode import get as get_barcode
from barcode.writer import ImageWriter
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime

template_dir = r"conf/template/hansagt"

env = Environment(loader=FileSystemLoader(template_dir))

def fmt_date(dt):
    """格式化日期（德式）"""
    return dt.strftime("%d.%m.%Y")

def fmt_euro_price(price: float):
    """格式化价格, comma 作为小数点，dot 作为千分位分隔符，例如 1.234,56 €"""
    formatted = f"{price:,.2f}"         # 生成 '1,234.56'
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"

def make_barcode_base64(code: str) -> str:
    """生成Base64条形码图片"""
    barcode_cls = get_barcode("code128", code, writer=ImageWriter())
    buf = io.BytesIO()
    barcode_cls.write(buf, options={"write_text": False})
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"

def fmt_date(dt):
    return dt.strftime("%d.%m.%Y")

def generate_delivery_note(context: dict) -> bytes:
    # 生成条码（base64）
    context["barcode_img"] = make_barcode_base64(context["order_number"])
    # 渲染 HTML 模板
    template = env.get_template("delivery_note.html")
    html_str = template.render(context)
    # 设置 base_url，确保 CSS / 图片可加载
    base_path = template_dir
    print(base_path)
    pdf_bytes = HTML(string=html_str, base_url=str(base_path)).write_pdf()
    return pdf_bytes



if __name__ == "__main__":
    context = {
        "name": "Herr Max Mustermann",
        "address1": "Beispielstraße 1",
        "address2": "",
        "postal_code": "20095",
        "city": "Hamburg",
        "country_name": "DE",
        "order_number": "20095",
        "created_at": fmt_date(datetime.now()),
        "items": [
            {"sku": "GG-1001", "quantity": 5,
             "name": "OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR IIR OP-Maske Typ IIR",
             "unit_price_excl_tax": "0,13 €"},
            {"sku": "GG-2003", "quantity": 2, "name": "Nitrilhandschuhe L", "unit_price_excl_tax": "1,52 €"},
            {"sku": "GG-3100232132", "quantity": 1, "name": "Desinfektionsmittel 5L", "unit_price_excl_tax": "14,90 €"},
            {"sku": "GG-1001", "quantity": 5,
             "name": "OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR IIR OP-Maske Typ IIR",
             "unit_price_excl_tax": "0,13 €"},
            {"sku": "GG-2003", "quantity": 2, "name": "Nitrilhandschuhe L", "unit_price_excl_tax": "1,52 €"},
            {"sku": "GG-3100", "quantity": 1, "name": "Desinfektionsmittel 5L", "unit_price_excl_tax": "14,90 €"},
            {"sku": "GG-1001", "quantity": 5,
             "name": "OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR IIR OP-Maske Typ IIR",
             "unit_price_excl_tax": "0,13 €"},
            {"sku": "GG-2003", "quantity": 2, "name": "Nitrilhandschuhe L", "unit_price_excl_tax": "1,52 €"},
            {"sku": "GG-3100", "quantity": 1, "name": "Desinfektionsmittel 5L", "unit_price_excl_tax": "14,90 €"},
            {"sku": "GG-1001", "quantity": 5,
             "name": "OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR IIR OP-Maske Typ IIR",
             "unit_price_excl_tax": "0,13 €"},
            {"sku": "GG-2003", "quantity": 2, "name": "Nitrilhandschuhe L", "unit_price_excl_tax": "1,52 €"},
            {"sku": "GG-3100", "quantity": 1, "name": "Desinfektionsmittel 5L", "unit_price_excl_tax": "14,90 €"},
            {"sku": "GG-1001", "quantity": 5,
             "name": "OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR OP-Maske Typ IIR IIR OP-Maske Typ IIR",
             "unit_price_excl_tax": "0,13 €"},
            {"sku": "GG-2003", "quantity": 2, "name": "Nitrilhandschuhe L", "unit_price_excl_tax": "1,52 €"},
            {"sku": "GG-3100", "quantity": 1, "name": "Desinfektionsmittel 5L", "unit_price_excl_tax": "14,90 €"},

        ],
    }

    pdf_bytes = generate_delivery_note(context)
    with open("delivery_note.pdf", "wb") as f:
        f.write(pdf_bytes)