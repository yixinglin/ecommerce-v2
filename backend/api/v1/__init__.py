from fastapi import APIRouter

from .routes.crm_geo import crm_geo
from .routes.user import user
from .routes.amazon import amz_order
from .routes.kaufland import kfld_order
from .routes.carriers import gls
from .routes.pickpack import pp_amazon, pp_common
from .routes.odoo import odoo_inventory, odoo_sales, odoo_contact
from .routes.lingxing import warehouse_router, listing_router, basic_router, fba_schipment_plans
from .routes.print_task import print_task_router
from .routes.barcode import barcode
from .routes.common import common_router


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

geo = APIRouter(prefix="/crm-geo", tags=["CRM-Geolocation"])
geo.include_router(crm_geo)

ptask = APIRouter(prefix="/print_task", tags=["Print Task"])
ptask.include_router(print_task_router)

common = APIRouter(prefix="/common", tags=["Common Services"])
common.include_router(common_router)

v1 = APIRouter(prefix='/v1')
v1.include_router(user)
v1.include_router(amz)
v1.include_router(kfld)
v1.include_router(carriers)
v1.include_router(pickpack)
v1.include_router(odoo)
v1.include_router(lx)
v1.include_router(bcs)
v1.include_router(geo)
v1.include_router(ptask)
v1.include_router(common)
