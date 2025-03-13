import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sp_api.base import Marketplaces
from core.log import logger
from services.amazon.AmazonService import AmazonOrderService, AmazonCatalogService, AmazonService
from core.config2 import settings
from services.gls.GlsShipmentService import GlsShipmentService
from services.kaufland.KauflandOrderService import KauflandOrderSerice
from external.kaufland.base import Storefront
from services.odoo import OdooProductService, OdooInventoryService, OdooContactService
from services.odoo.OdooOrderService import OdooProductPackagingService

hourly_scheduler = BackgroundScheduler()

odoo_access_key_index = settings.api_keys.odoo_access_key_index
interval_seconds = settings.scheduler.interval_seconds

# @hourlyScheduler.scheduled_job('interval', seconds=10)
def hourly_job():
    print('This job runs every hour')
    time.sleep(2)
    print('This job runs every hour')


def save_amazon_orders_job(key_index, marketplace):
    """
    This job fetches data from external API every 2 hours
    :return:
    """
    if not settings.scheduler.amazon_orders_fetch_enabled:
        logger.info("Scheduled job to save orders to MongoDB is disabled in config")
        return

    try:
        logger.info("Scheduled job to save orders every 2 hours to MongoDB")
        with AmazonOrderService(key_index=key_index, marketplace=marketplace) as man:
            man.save_all_orders(days_ago=7, FulfillmentChannels=["MFN"])
    except Exception as e:
        logger.error(f"Error in scheduled job to save orders every 2 hours to MongoDB: {e}")
    finally:
        # wait for 15 seconds before running the next job, to avoid rate limiting
        time.sleep(15)
    logger.info("Successfully scheduled Amazon orders scheduler job...")


def save_tracking_info_job(key_index):
    """
    :param key_index:
    :return:
    """
    if settings.scheduler.gls_tracking_fetch_enabled:
        with GlsShipmentService(key_index=key_index) as man:
            shipments = man.get_incomplete_shipments(days_ago=7)
            ids = [';'.join(s.references) for s in shipments]
            logger.info(f"Fetching tracking info for {len(ids)} shipments: {';'.join(ids)}")
            man.save_tracking_info(ids=ids)


def save_kaufland_orders_job(key_index, storefront):
    """
    This job fetches data from external API every 2 hours
    :return:
    """
    if not settings.scheduler.kaufland_orders_fetch_enabled:
        logger.info("Scheduled job to save orders to MongoDB is disabled in config")
        return
    try:
        logger.info("Scheduled job to save orders every 2 hours to MongoDB")
        with KauflandOrderSerice(key_index=key_index, storefront=storefront) as svc:
            svc.save_all_orders(days_ago=14)
    except Exception as e:
        logger.error(f"Error in scheduled job to save orders every 2 hours to MongoDB: {e}")
    finally:
        # wait for 15 seconds before running the next job, to avoid rate limiting
        time.sleep(15)


def save_amazon_catalog_job(key_index, marketplace):
    """
    This job fetches data from external API every 2 hours
    :return:
    """
    if not settings.scheduler.amazon_products_fetch_enabled:
        logger.info("Scheduled job to save catalog to MongoDB is disabled in config")
        return
    try:
        logger.info("Scheduled job to save catalog every 2 hours to MongoDB")
        with AmazonService(key_index=key_index, marketplace=marketplace) as svc:
            svc.save_all_catalogs_from_orders()
            # svc.clear_expired_catalogs()
            # svc.save_all_catalogs_from_db(force_fetch=True)
    except Exception as e:
        logger.error(f"Error in scheduled job to save catalog to MongoDB: {e}")
    finally:
        # wait for 15 seconds before running the next job, to avoid rate limiting
        time.sleep(15)
    logger.info("Successfully scheduled Amazon catalog scheduler job...")


def save_odoo_data_jobs():
    try:
        logger.info("Scheduled job to save product data to Odoo")
        with OdooProductService(key_index=odoo_access_key_index, login=True) as svc:
            svc.save_all_product_templates()
            svc.save_all_products()
    except Exception as e:
        logger.error(f"Error in scheduled job to save product data to Odoo: {e}")
    finally:
        # wait for 15 seconds before running the next job, to avoid rate limiting
        time.sleep(15)

    try:
        logger.info("Scheduled job to save contact data to Odoo")
        with OdooContactService(key_index=odoo_access_key_index, login=True) as svc:
            svc.save_all_contacts()
    except Exception as e:
        logger.error(f"Error in scheduled job to save contact data to Odoo: {e}")
    finally:
        # wait for 15 seconds before running the next job, to avoid rate limiting
        time.sleep(15)

    try:
        logger.info("Scheduled job to save inventory data to Odoo")
        with OdooInventoryService(key_index=odoo_access_key_index, login=True) as svc:
            svc.save_all_quants()
            svc.save_all_putaway_rules()
            svc.save_all_internal_locations()
    except Exception as e:
        logger.error(f"Error in scheduled job to save inventory data to Odoo: {e}")
    finally:
        # wait for 15 seconds before running the next job, to avoid rate limiting
        time.sleep(15)


    try:
        logger.info("Scheduled job to save packaging data to Odoo")
        with OdooProductPackagingService(key_index=odoo_access_key_index, login=True) as svc:
            svc.save_all_product_packaging()
    except Exception as e:
        logger.error(f"Error in scheduled job to save packaging data to Odoo: {e}")
    finally:
        # wait for 15 seconds before running the next job, to avoid rate limiting
        time.sleep(15)

    logger.info("Successfully scheduled Odoo data scheduler job...")

@hourly_scheduler.scheduled_job('interval', seconds=interval_seconds)
def common_scheduler_2hrs():
    """
    To schedule jobs every 2 hours
    :return:
    """
    save_odoo_data_jobs()
    save_amazon_orders_job(key_index=0, marketplace=Marketplaces.DE)
    save_amazon_catalog_job(key_index=0, marketplace=Marketplaces.DE)
    save_kaufland_orders_job(key_index=0, storefront=Storefront.DE)
    logger.info("Successfully scheduled common scheduler job...")

@hourly_scheduler.scheduled_job('interval', seconds=4 * 3600)
def common_scheduler_4hrs():
    """
    To schedule jobs every 4 hours
    :return:
    """
    # save_tracking_info_job(key_index=settings.GLS_ACCESS_KEY_INDEX)
    # logger.info("Successfully scheduled common scheduler job...")
    pass

# 添加每天9:00-17:00每半小时执行一次的任务
@hourly_scheduler.scheduled_job(CronTrigger(minute='0,30', hour='7-14'))
def half_hour_task():
    print(f"Half-hourly task executed")

# 添加17:01到次日7:59每3小时执行一次的任务
@hourly_scheduler.scheduled_job(CronTrigger(minute='1', hour='17,20,2,5'))
def three_hourly_task():
    print(f"Three-hourly task executed")


"""
AsyncIOScheduler

"""


from services.lingxing import (ListingService, BasicDataService,
                               WarehouseService, FbaShipmentPlanService)

async_hourly_scheduler = AsyncIOScheduler()

@async_hourly_scheduler.scheduled_job('interval', seconds=interval_seconds)
async def save_lingxing_job():
    enabled = settings.scheduler.lingxing_fetch_enabled
    if not enabled:
        logger.info("Scheduled job to save LingXing data is disabled in config")
        return

    key_index = settings.api_keys.lingxing_access_key_index
    proxy_index = settings.http_proxy.index

    try:
        async with BasicDataService(key_index, proxy_index) as svc_basic:
            async with ListingService(key_index, proxy_index) as svc_listing:
                await svc_basic.save_all_basic_data()
                await svc_listing.save_all_listings()
    except Exception as e:
        logger.error(f"Error in scheduled job to save LingXing data: {e}")
    finally:
        await asyncio.sleep(15)

    try:
        async with WarehouseService(key_index, proxy_index) as svc_inventory:
            await svc_inventory.save_all_inventories()
            await svc_inventory.save_all_inventory_bins()
    except Exception as e:
        logger.error(f"Error in scheduled job to save LingXing inventory data: {e}")
    finally:
        await asyncio.sleep(15)

    try:
        async with FbaShipmentPlanService(key_index, proxy_index) as svc_fba_shipment_plan:
            await svc_fba_shipment_plan.save_fba_shipment_plans_latest(100)
    except Exception as e:
        logger.error(f"Error in scheduled job to save LingXing FBA shipment plan data: {e}")
    finally:
        await asyncio.sleep(15)

    logger.info("Successfully scheduled LingXing scheduler job...")


# Run the code once when the script is loaded
next_run_time = datetime.now() + timedelta(seconds=240)
hourly_scheduler.add_job(common_scheduler_2hrs, 'date', run_date=next_run_time)

# Run the code once when the script is loaded
next_run_time = datetime.now() + timedelta(seconds=480)
async_hourly_scheduler.add_job(save_lingxing_job, 'date', run_date=next_run_time)