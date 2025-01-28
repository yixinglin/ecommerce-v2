from fastapi import APIRouter
from .routes.user import user
from .routes.amazon import amz_order
from .routes.kaufland import kfld_order
from .routes.carriers import gls
from .routes.pickpack import pp_amazon, pp_common
from .routes.odoo import odoo_inventory, odoo_sales, odoo_contact
from .routes.lingxing import warehouse_router, listing_router, basic_router, fba_schipment_plans
from .routes.barcode import barcode

amz = APIRouter(prefix="/amazon")
amz.include_router(amz_order)

kfld = APIRouter(prefix="/kaufland", tags=['Kaufland Services'])
kfld.include_router(kfld_order)

carriers = APIRouter(prefix="/carriers", tags=["GLS Services"],)
carriers.include_router(gls)

pickpack = APIRouter(prefix="/pickpack")
pickpack.include_router(pp_amazon)
pickpack.include_router(pp_common)

odoo = APIRouter(prefix="/odoo", tags=["Odoo Services"])
odoo.include_router(odoo_inventory)
odoo.include_router(odoo_sales)
odoo.include_router(odoo_contact)

lx = APIRouter(prefix="/lingxing", tags=["LingXing Services"])
lx.include_router(warehouse_router)
lx.include_router(listing_router)
lx.include_router(basic_router)
lx.include_router(fba_schipment_plans)

bcs = APIRouter(prefix="/scanner", tags=["Barcode Scanner"])
bcs.include_router(barcode)


v1 = APIRouter(prefix='/v1')
v1.include_router(user)
v1.include_router(amz)
v1.include_router(kfld)
v1.include_router(carriers)
v1.include_router(pickpack)
v1.include_router(odoo)
v1.include_router(lx)
v1.include_router(bcs)
