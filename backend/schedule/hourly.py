from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time

from apscheduler.triggers.cron import CronTrigger
from sp_api.base import Marketplaces
from core.log import logger
from services.amazon.AmazonService import AmazonOrderService, AmazonCatalogService, AmazonService
from core.config import settings
from services.gls.GlsShipmentService import GlsShipmentService
from services.kaufland.KauflandOrderService import KauflandOrderSerice
from external.kaufland.base import Storefront

hourlyScheduler = AsyncIOScheduler()


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
    if not settings.SCHEDULER_AMAZON_ORDERS_FETCH_ENABLED:
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


def save_tracking_info_job(key_index):
    """
    :param key_index:
    :return:
    """
    if settings.SCHEDULER_GLS_TRACKING_FETCH_ENABLED:
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
    if not settings.SCHEDULER_KAUFLAND_ORDERS_FETCH_ENABLED:
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
    if not settings.SCHEDULER_AMAZON_PRODUCTS_FETCH_ENABLED:
        logger.info("Scheduled job to save catalog to MongoDB is disabled in config")
        return
    try:
        logger.info("Scheduled job to save catalog every 2 hours to MongoDB")
        with AmazonService(key_index=key_index, marketplace=marketplace) as svc:
            svc.save_all_catalogs()
    except Exception as e:
        logger.error(f"Error in scheduled job to save catalog to MongoDB: {e}")
    finally:
        # wait for 15 seconds before running the next job, to avoid rate limiting
        time.sleep(15)


@hourlyScheduler.scheduled_job('interval', seconds=settings.SCHEDULER_INTERVAL_SECONDS)
def common_scheduler_2hrs():
    """
    To schedule jobs every 2 hours
    :return:
    """
    save_amazon_orders_job(key_index=0, marketplace=Marketplaces.DE)
    save_amazon_catalog_job(key_index=0, marketplace=Marketplaces.DE)
    save_kaufland_orders_job(key_index=0, storefront=Storefront.DE)
    logger.info("Successfully scheduled common scheduler job...")

@hourlyScheduler.scheduled_job('interval', seconds=4 * 3600)
def common_scheduler_4hrs():
    """
    To schedule jobs every 4 hours
    :return:
    """
    # save_tracking_info_job(key_index=settings.GLS_ACCESS_KEY_INDEX)
    # logger.info("Successfully scheduled common scheduler job...")
    pass

# 添加每天9:00-17:00每半小时执行一次的任务
@hourlyScheduler.scheduled_job(CronTrigger(minute='0,30', hour='7-14'))
def half_hour_task():
    print(f"Half-hourly task executed")

# 添加17:01到次日7:59每3小时执行一次的任务
@hourlyScheduler.scheduled_job(CronTrigger(minute='1', hour='17,20,2,5'))
def three_hourly_task():
    print(f"Three-hourly task executed")



# Run the code once when the script is loaded
next_run_time = datetime.now() + timedelta(seconds=600)
hourlyScheduler.add_job(common_scheduler_2hrs, 'date', run_date=next_run_time)
# next_run_time = datetime.now() + timedelta(seconds=480)
# hourlyScheduler.add_job(common_scheduler_4hrs, 'date', run_date=next_run_time)
