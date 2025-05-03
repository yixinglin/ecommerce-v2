# https://blog.csdn.net/qq_51967017/article/details/131058627
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.db import backup_mysql_db, clean_old_mysql_db_backups
from core.log import logger

daily_scheduler = AsyncIOScheduler()


@daily_scheduler.scheduled_job('cron', hour="0,18", minute=1)
def backup_database():
    """
    Backup database every day at 00:01 and 18:01
    :return:
    """
    logger.info('Clean old backups...')
    clean_old_mysql_db_backups(retain_days=30)
    logger.info('Backup database...')
    backup_mysql_db()
    logger.info('Backup database done.')

@daily_scheduler.scheduled_job('cron', hour=2, minute=0)
def standardize_raw_data():
    """
    TODO Standardize raw data every day at 2am
    :return:
    """
    print('Standardize raw data')
    # TODO common.standardize
