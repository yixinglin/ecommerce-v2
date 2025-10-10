import io
from typing import Optional

from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)
from reportlab.graphics.barcode import code128
from datetime import datetime


def euro(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

class ShipperInfo(BaseModel):
    name: str
    street: str
    city: str
    zip: str
    country: str
    website: str = None

class BuyerAddress(BaseModel):
    street: str
    city: str
    zip: str
    country: str

class Item(BaseModel):
    sku: str
    name: str
    qty: int
    price: float

class Order(BaseModel):
    order_id: str
    buyer_name: str
    buyer_address: BuyerAddress
    items: list[Item]
    shipper_info: Optional[ShipperInfo] = None
    created_at: datetime = datetime.now()

class Batch(BaseModel):
    batch_id: str
    items: list[Item]
    shipper_info: Optional[ShipperInfo] = None
    created_at: datetime = datetime.now()


class SlipBuilder:
    @staticmethod
    def generate_packing_slip(
        order: Order,
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=50 * mm,
            bottomMargin=25 * mm
        )
        address = order.buyer_address
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Normal-DE", fontName="Helvetica", fontSize=10, leading=12))
        styles.add(ParagraphStyle(name="Header", fontName="Helvetica-Bold", fontSize=16, leading=20, alignment=1))  # 居中
        styles.add(ParagraphStyle(name="SubHeader", fontName="Helvetica-Bold", fontSize=11, leading=14))

        styles.add(ParagraphStyle(
            name="ProductName",
            fontName="Helvetica",
            fontSize=9,
            leading=11,          # 行距
            wordWrap='CJK',      # 支持自动换行
            maxLineHeight=3*11,  # 视觉上最多三行（可选，不影响逻辑）
        ))

        elements = []
        items_per_page = 20
        total_pages = (len(order.items) + items_per_page - 1) // items_per_page

        # ============ 页眉 + 页脚 =============
        shipper_info = order.shipper_info
        def draw_page_frame(canvas, doc):
            # 页眉
            # --- 发货方信息 ---
            y = 285
            if shipper_info:
                canvas.setFont("Helvetica-Bold", 13)
                canvas.drawString(20 * mm, y * mm, shipper_info.name)
                canvas.setFont("Helvetica", 9)
                canvas.drawString(20 * mm, (y - 5) * mm,
                                  f"{shipper_info.street}, {shipper_info.zip} {shipper_info.city}, {shipper_info.country}")

            # --- 标题 ---
            canvas.setFont("Helvetica-Bold", 16)
            canvas.drawString(20 * mm, 265 * mm, f"Bestellnummer: {order.order_id}")

            # --- 条形码 ---
            barcode = code128.Code128(order.order_id, barHeight=12 * mm, barWidth=0.9)
            barcode.drawOn(canvas, 130 * mm, 268 * mm)

            # --- 收货方信息 ---
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(20 * mm, 257 * mm, f"Lieferanschrift:")
            canvas.setFont("Helvetica", 9)
            canvas.drawString(20 * mm, 250 * mm, f"{order.buyer_name}")
            canvas.drawString(20 * mm, 245 * mm, f"{address.street}")
            canvas.drawString(20 * mm, 240 * mm, f"{address.zip} {address.city}, {address.country}")

            created_date_str = order.created_at.strftime("%d.%m.%Y")
            canvas.drawRightString(190 * mm, 255 * mm, f"Erstellt am: {created_date_str}")

            # 页脚
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(190 * mm, 15 * mm, f"Seite {doc.page} / {total_pages}")

            if shipper_info:
                canvas.drawString(20 * mm, 15 * mm, f"{shipper_info.website or ''}")


        # ============ 表格内容 =============
        items = order.items
        for i in range(0, len(items), items_per_page):
            page_items = items[i:i + items_per_page]
            data = [["Pos.", "Artikelnummer", "Menge", "Bezeichnung", "Einzelpreis (€)", "Gesamt (€)"]]
            for idx, item in enumerate(page_items, start=i + 1):
                qty = item.qty
                price = float(item.price)
                total = qty * price
                name_text = item.name
                # 粗略限制字符长度（约 135 个字符对应三行）
                if len(name_text) > 135:
                    name_text = name_text[:132] + "..."
                name_paragraph = Paragraph(name_text, styles["ProductName"])

                data.append([
                    f"{str(idx)}.",
                    item.sku,
                    str(qty),
                    name_paragraph,
                    euro(price),  # 用德式格式化函数
                    euro(total),  # 用德式格式化函数
                ])

            available_width = A4[0] - doc.leftMargin - doc.rightMargin
            table = Table(
                data,
                colWidths=[
                    available_width * 0.08,  # Pos.
                    available_width * 0.17,  # Artikelnummer
                    available_width * 0.10,  # Menge
                    available_width * 0.38,  # Bezeichnung
                    available_width * 0.13,  # Einzelpreis
                    available_width * 0.14,  # Gesamt
                ],
            )
            table.hAlign = "LEFT"
            table.setStyle(TableStyle([
                ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
            ]))
            if i > 0:
                elements.append(PageBreak())
            elements.append(Spacer(1, 30))
            elements.append(table)

        doc.build(elements, onFirstPage=draw_page_frame, onLaterPages=draw_page_frame)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes


    @staticmethod
    def generate_picking_slip(
        batch: Batch,
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=50 * mm,
            bottomMargin=25 * mm
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Normal-DE", fontName="Helvetica", fontSize=10, leading=12))
        styles.add(ParagraphStyle(name="Header", fontName="Helvetica-Bold", fontSize=16, leading=20, alignment=1))
        styles.add(ParagraphStyle(name="SubHeader", fontName="Helvetica-Bold", fontSize=11, leading=14))
        styles.add(ParagraphStyle(
            name="ProductName",
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            wordWrap='CJK',
        ))

        elements = []
        items_per_page = 25
        total_pages = (len(batch.items) + items_per_page - 1) // items_per_page

        shipper_info = batch.shipper_info

        def draw_page_frame(canvas, doc):
            # 页眉
            y = 285
            if shipper_info:
                canvas.setFont("Helvetica-Bold", 13)
                canvas.drawString(20 * mm, y * mm, shipper_info.name)
                canvas.setFont("Helvetica", 9)
                canvas.drawString(20 * mm, (y - 5) * mm,
                                  f"{shipper_info.street}, {shipper_info.zip} {shipper_info.city}, {shipper_info.country}")

            # 标题
            canvas.setFont("Helvetica-Bold", 16)
            canvas.drawString(20 * mm, 258 * mm, f"Pickliste # {batch.batch_id}")

            # 条形码
            barcode = code128.Code128(batch.batch_id, barHeight=12 * mm, barWidth=0.5)
            barcode.drawOn(canvas, 120 * mm, 268 * mm)

            # 创建日期
            created_date_str = batch.created_at.strftime("%d.%m.%Y")
            canvas.setFont("Helvetica", 9)
            canvas.drawRightString(190 * mm, 255 * mm, f"Erstellt am: {created_date_str}")

            # 页脚
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(190 * mm, 15 * mm, f"Seite {doc.page} / {total_pages}")
            if shipper_info:
                canvas.drawString(20 * mm, 15 * mm, f"{shipper_info.website or ''}")

        # ========== 表格内容 ==========
        items = batch.items
        total_qty = 0  # 汇总数量

        for i in range(0, len(items), items_per_page):
            page_items = items[i:i + items_per_page]
            data = [["Pos.", "Artikelnummer", "Bezeichnung", "Menge", "Einzelpreis (€)", "Notiz"]]
            for idx, item in enumerate(page_items, start=i + 1):
                total_qty += item.qty
                name_text = item.name
                if len(name_text) > 135:
                    name_text = name_text[:132] + "..."
                name_paragraph = Paragraph(name_text, styles["ProductName"])

                data.append([
                    f"{idx}.",
                    item.sku,
                    name_paragraph,
                    str(item.qty),
                    euro(item.price),
                    "",  # 备注或签名
                ])

            available_width = A4[0] - doc.leftMargin - doc.rightMargin
            table = Table(
                data,
                colWidths=[
                    available_width * 0.07,  # Pos.
                    available_width * 0.16,  # Artikelnummer
                    available_width * 0.40,  # Bezeichnung
                    available_width * 0.10,  # Menge
                    available_width * 0.13,  # Preis
                    available_width * 0.14,  # Notiz
                ],
            )
            table.hAlign = "LEFT"
            table.setStyle(TableStyle([
                ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (3, 1), (4, -1), "RIGHT"),
            ]))
            if i > 0:
                elements.append(PageBreak())
            elements.append(Spacer(1, 30))
            elements.append(table)

        # ========== 底部统计 & 签名区域 ==========
        elements.append(Spacer(1, 20))
        total_line = Table(
            [[
                "",
                "",
                Paragraph("<b>Gesamtmenge:</b>", styles["Normal-DE"]),
                Paragraph(f"<b>{total_qty}</b>", styles["Normal-DE"]),
                "",
                ""
            ]],
            colWidths=[
                available_width * 0.07,
                available_width * 0.16,
                available_width * 0.40,
                available_width * 0.10,
                available_width * 0.12,
                available_width * 0.15,
            ],
            style=[
                ("ALIGN", (3, 0), (3, 0), "RIGHT"),
                ("FONT", (0, 0), (-1, -1), "Helvetica-Bold", 10),
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.black),
            ]
        )
        elements.append(total_line)

        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Unterschrift des Kommissionierers / Picker's Signature:", styles["Normal-DE"]))
        elements.append(Spacer(1, 10))
        elements.append(Table(
            [[""]],
            colWidths=[160 * mm],
            rowHeights=[10 * mm],
            style=[("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.black)]
        ))

        # 构建 PDF
        doc.build(elements, onFirstPage=draw_page_frame, onLaterPages=draw_page_frame)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes


# ====== 示例运行 ======
if __name__ == "__main__":
    order_id = "DE20251004-98765"
    batch_id = "BATCH_WOOCOMMERCE_20251011_001"
    buyer_name = "Max Mustermann, ABC-GmbH"
    address = {"street": "Musterstraße 12", "city": "Berlin", "zip": "10115", "country": "Deutschland"}
    items = [
        {"sku": f"SKU-{i:03}", "name": f"Produkt {i} Beispielartikel BeispielartikelBeispielartikel", "qty": (i % 5) + 1, "price": 12.99}
        for i in range(1, 114)
    ]

    shipper_info = {
        "name": "Good Logistics GmbH",
        "street": "Gewerbestraße 22",
        "city": "Hamburg",
        "zip": "21035",
        "country": "Deutschland",
        "website": "https://www.goodlogistics.de",
    }

    order = Order(
        order_id=order_id,
        buyer_name=buyer_name,
        buyer_address=BuyerAddress(**address),
        items=[Item(**item) for item in items],
        shipper_info=ShipperInfo(**shipper_info),
    )
    pdf_bytes = SlipBuilder.generate_packing_slip(order)
    with open(f"lieferschein-{order_id}.pdf", "wb") as f:
        f.write(pdf_bytes)

    batch = Batch(
        batch_id=batch_id,
        items=[Item(**item) for item in items[:100]],
        shipper_info=ShipperInfo(**shipper_info),
    )
    pdf_bytes = SlipBuilder.generate_picking_slip(batch)
    with open(f"picking-slip-{batch.batch_id}.pdf", "wb") as f:
        f.write(pdf_bytes)