from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time

from core.log import logger
from rest.amazon.DataManager import AmazonOrderMongoDBManager
from core.config import settings

hourlyScheduler = AsyncIOScheduler()


# @hourlyScheduler.scheduled_job('interval', seconds=10)
async def hourly_job():
    print('This job runs every hour')
    time.sleep(2)
    print('This job runs every hour')


async def save_orders_job():
    """
    This job fetches data from external API every 2 hours
    :return:
    """
    if not settings.SCHEDULER_AMAZON_ORDERS_FETCH_ENABLED:
        logger.info("Scheduled job to save orders to MongoDB is disabled in config")
        return

    try:
        logger.info("Scheduled job to save orders every 2 hours to MongoDB")
        with AmazonOrderMongoDBManager(settings.DB_MONGO_URI, settings.DB_MONGO_PORT) as man:
            man.save_all_orders(days_ago=7, FulfillmentChannels=["MFN"])
    except Exception as e:
        logger.error(f"Error in scheduled job to save orders every 2 hours to MongoDB: {e}")
    finally:
        # wait for 1 minute before running the next job, to avoid rate limiting
        time.sleep(60)


@hourlyScheduler.scheduled_job('interval', seconds=settings.SCHEDULER_INTERVAL_SECONDS)
async def common_scheduler_2hrs():
    """
    To schedule jobs every 2 hours
    :return:
    """
    await save_orders_job()



# Run the code once when the script is loaded
next_run_time = datetime.now() + timedelta(seconds=10)
hourlyScheduler.add_job(save_orders_job, 'date', run_date=next_run_time)
