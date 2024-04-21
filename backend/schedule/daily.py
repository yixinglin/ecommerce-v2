# https://blog.csdn.net/qq_51967017/article/details/131058627
from apscheduler.schedulers.asyncio import AsyncIOScheduler

dailyScheduler = AsyncIOScheduler()


@dailyScheduler.scheduled_job('cron', hour=3, minute=0)
async def backup_database():
    """
    Backup database every day at 3am
    :return:
    """
    print('Backup database at 3am every day')