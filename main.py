import logging
from services.sql_server_database import SQLServerDatabase
from services.seo_service import SEOService  # Added SEOService import
from services.llm_service import QService

# تنظیمات لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def setup_database_connection():
    """اتصال به دیتابیس"""
    SERVER = "45.149.76.141"
    DATABASE = "ContentGenerator"
    USERNAME = "admin"
    PASSWORD = "HTTTHFocBbW5CM"
    db = SQLServerDatabase(SERVER, DATABASE, USERNAME, PASSWORD)
    return db

def setup_services(db):
    """راه‌اندازی سرویس‌ها"""
    SESSION_HASH = "amir"
    q_service = QService(session_hash=SESSION_HASH)
    seo_service = SEOService(db=db, q_service=q_service)  # Now recognized as SEOService
    return seo_service

def test_table_existence(db):
    """چک کردن موجودیت جدول"""
    try:
        if not db.test_table_exists('TblPureContent'):
            logger.error("❌ جدول 'TblPureContent' پیدا نشد.")
            return False
        logger.info("✅ جدول 'TblPureContent' موجود است.")
        return True
    except Exception as e:
        logger.error(f"❌ خطا در چک کردن جدول: {e}")
        return False

def main():
    # راه‌اندازی و اتصال به دیتابیس
    db = setup_database_connection()
    
    try:
        logger.info("🔌 در حال اتصال به دیتابیس...")
        db.connect()
        logger.info("✅ اتصال برقرار شد.")
        
        # چک کردن موجودیت جدول
        if not test_table_existence(db):
            return

        # راه‌اندازی سرویس‌ها
        seo_service = setup_services(db)

        # شروع فرآیند بهینه‌سازی
        logger.info("🚀 شروع فرآیند بهینه‌سازی عناوین برای سئو...")
        seo_service.generate_title_for_all()

    except Exception as e:
        logger.exception(f"❌ خطای کلی در اجرای برنامه: {e}")

    finally:
        # قطع ارتباط با دیتابیس
        db.disconnect()
        logger.info("🔌 ارتباط با دیتابیس قطع شد.")

if __name__ == "__main__":
    main()
