from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import ContextTypes
from modules.community_collector.models import User, Contribution
from modules.community_collector.utils import get_session
import logging

logger = logging.getLogger(__name__)

async def send_weekly_reports(context: ContextTypes.DEFAULT_TYPE):
    session = get_session()
    users = session.query(User).all()
    for user in users:
        total_contributions = session.query(Contribution).filter_by(user_id=user.user_id).count()
        if total_contributions > 0:
            try:
                await context.bot.send_message(
                    chat_id=int(user.user_id),
                    text=f"Привіт, {user.username}! Ви завантажили {total_contributions} скріншотів. Продовжуйте в тому ж дусі!"
                )
            except Exception as e:
                logger.error(f"Не вдалося надіслати повідомлення користувачу {user.user_id}: {e}")
    session.close()

def start_scheduler(application):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_weekly_reports, 'interval', weeks=1, args=[application])
    scheduler.start()
