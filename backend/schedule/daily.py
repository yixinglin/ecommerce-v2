# https://blog.csdn.net/qq_51967017/article/details/131058627
from apscheduler.schedulers.asyncio import AsyncIOScheduler

daily_scheduler = AsyncIOScheduler()


@daily_scheduler.scheduled_job('cron', hour=3, minute=0)
def backup_database():
    """
    TODO Backup database every day at 3am
    :return:
    """
    print('Backup database at 3am every day')


@daily_scheduler.scheduled_job('cron', hour=1, minute=0)
def standardize_raw_data():
    """
    TODO Standardize raw data every day at 1am
    :return:
    """
    print('Standardize raw data')
    # TODO common.standardize
