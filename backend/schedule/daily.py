# https://blog.csdn.net/qq_51967017/article/details/131058627
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.db import backup_mysql_db, clean_old_mysql_db_backups
from core.log import logger
from schedule.hourly import odoo_access_key_index
from services.odoo import OdooProductService, OdooContactService, OdooInventoryService

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

@daily_scheduler.scheduled_job('cron', hour="20,22,0,2", minute=50)
def random_delete_odoo_doc_in_mongodb():
    """
    目的：每天晚上20:47至22:47，随机删除MongoDB中Odoo相关的文档，以强制程序重新拉取数据。
    :return:
    """
    try:
        logger.info("Random delete Odoo Products in MongoDB...")
        with OdooProductService(key_index=odoo_access_key_index, login=False) as svc:
            svc.mdb_product.delete_random_documents(percentage=0.1)
            svc.mdb_product_templ.delete_random_documents(percentage=0.1)
    except Exception as e:
        logger.error(f"Error occurred when random delete documents in MongoDB: {e}")

    try:
        logger.info("Random delete Odoo Contacts in MongoDB...")
        with OdooContactService(key_index=odoo_access_key_index, login=False) as svc:
            svc.mdb_contact.delete_random_documents(percentage=0.1)
    except Exception as e:
        logger.error(f"Error occurred when random delete documents in MongoDB: {e}")

    try:
        logger.info("Random delete Odoo Inventory in MongoDB...")
        with OdooInventoryService(key_index=odoo_access_key_index, login=False) as svc:
            svc.mdb_quant.delete_random_documents(percentage=0.1)
            svc.mdb_location.delete_random_documents(percentage=0.1)
    except Exception as e:
        logger.error(f"Error occurred when random delete documents in MongoDB: {e}")



