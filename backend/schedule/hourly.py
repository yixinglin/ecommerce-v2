from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time

from core.log import logger
from rest.amazon.DataManager import AmazonOrderMongoDBManager, AmazonCatalogManager
from core.config import settings
from rest.kaufland.DataManager import KauflandOrderMongoDBManager

hourlyScheduler = AsyncIOScheduler()


# @hourlyScheduler.scheduled_job('interval', seconds=10)
def hourly_job():
    print('This job runs every hour')
    time.sleep(2)
    print('This job runs every hour')


def save_amazon_orders_job(key_index=0):
    """
    This job fetches data from external API every 2 hours
    :return:
    """
    if not settings.SCHEDULER_AMAZON_ORDERS_FETCH_ENABLED:
        logger.info("Scheduled job to save orders to MongoDB is disabled in config")
        return

    try:
        logger.info("Scheduled job to save orders every 2 hours to MongoDB")
        with AmazonOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT, key_index=key_index) as man:
            man.save_all_orders(days_ago=7, FulfillmentChannels=["MFN"])
    except Exception as e:
        logger.error(f"Error in scheduled job to save orders every 2 hours to MongoDB: {e}")
    finally:
        # wait for 1 minute before running the next job, to avoid rate limiting
        time.sleep(60)


def save_kaufland_orders_job():
    """
    This job fetches data from external API every 2 hours
    :return:
    """
    if not settings.SCHEDULER_KAUFLAND_ORDERS_FETCH_ENABLED:
        logger.info("Scheduled job to save orders to MongoDB is disabled in config")
        return
    try:
        logger.info("Scheduled job to save orders every 2 hours to MongoDB")
        with KauflandOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
            man.save_all_orders(days_ago=14)
    except Exception as e:
        logger.error(f"Error in scheduled job to save orders every 2 hours to MongoDB: {e}")
    finally:
        # wait for 1 minute before running the next job, to avoid rate limiting
        time.sleep(60)


def save_amazon_catalog_job(key_index=0):
    """
    This job fetches data from external API every 2 hours
    :return:
    """
    if not settings.SCHEDULER_AMAZON_PRODUCTS_FETCH_ENABLED:
        logger.info("Scheduled job to save catalog to MongoDB is disabled in config")
        return
    try:
        logger.info("Scheduled job to save catalog every 2 hours to MongoDB")
        with AmazonCatalogManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT, key_index=key_index) as man:
            man.save_all_catalogs()
    except Exception as e:
        logger.error(f"Error in scheduled job to save catalog to MongoDB: {e}")
    finally:
        # wait for 1 minute before running the next job, to avoid rate limiting
        time.sleep(60)


@hourlyScheduler.scheduled_job('interval', seconds=settings.SCHEDULER_INTERVAL_SECONDS)
def common_scheduler_2hrs():
    """
    To schedule jobs every 2 hours
    :return:
    """
    save_amazon_orders_job(key_index=0)
    save_amazon_catalog_job(key_index=0)
    save_kaufland_orders_job()
    logger.info("Successfully scheduled common scheduler job...")


# Run the code once when the script is loaded
next_run_time = datetime.now() + timedelta(seconds=240)
hourlyScheduler.add_job(common_scheduler_2hrs, 'date', run_date=next_run_time)
