import logging
from services.sql_server_database import SQLServerDatabase
from services.seo_service import SEOService
from services.llm_service import QService

# تنظیم لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    SERVER = "45.149.76.141"
    DATABASE = "ContentGenerator"
    USERNAME = "admin"
    PASSWORD = "HTTTHFocBbW5CM"
    SESSION_HASH = "amir"

    # اتصال به دیتابیس و راه‌اندازی سرویس‌ها
    db = SQLServerDatabase(SERVER, DATABASE, USERNAME, PASSWORD)
    q_service = QService(session_hash=SESSION_HASH)
    seo_service = SEOService(db=db, q_service=q_service)

    try:
        logger.info("🔌 در حال اتصال به دیتابیس...")
        db.connect()
        logger.info("✅ اتصال برقرار شد.")

        # چک کردن موجودیت جدول
        if not db.test_table_exists('TblPureContent'):
            logger.error("❌ جدول 'TblPureContent' پیدا نشد.")
            return
        logger.info("✅ جدول 'TblPureContent' موجود است.")

        # شروع فرآیند بهینه‌سازی
        logger.info("🚀 شروع فرآیند بهینه‌سازی عناوین برای سئو...")
        seo_service.generate_title_for_all()

    except Exception as e:
        logger.exception(f"❌ خطای کلی در اجرای برنامه: {e}")
    finally:
        db.disconnect()
        logger.info("🔌 ارتباط با دیتابیس قطع شد.")

if __name__ == "__main__":
    main()
