import logging

# تنظیم لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # ✳️ واردات داخلی برای جلوگیری از circular import
    from services.sql_server_database import SQLServerDatabase
    from services.seo_service import SEOService
    from services.llm_service import QService

    # اطلاعات اتصال به دیتابیس
    SERVER = "45.149.76.141"
    DATABASE = "ContentGenerator"
    USERNAME = "admin"
    PASSWORD = "HTTTHFocBbW5CM"

    # مقدار session_hash واقعی را اینجا جایگزین کن
    SESSION_HASH = "amir"

    # اتصال به دیتابیس
    db = SQLServerDatabase(SERVER, DATABASE, USERNAME, PASSWORD)
    q_service = QService(session_hash=SESSION_HASH)

    try:
        db.connect()

        # استفاده از متدی که واقعاً در کلاس وجود دارد (test_table_exists)
        table_exists = db.test_table_exists('TblPureContent')
        if not table_exists:
            logger.error("❌ جدول 'TblPureContent' پیدا نشد.")
            return
        logger.info("✅ جدول 'TblPureContent' وجود دارد.")

        # سرویس سئو
        seo_service = SEOService(db=db, q_service=q_service)

        # گرفتن همه محتواها
        all_contents = db.get_all_purecontents()
        if not all_contents:
            logger.info("❌ هیچ محتوایی پیدا نشد.")
            return

        for content in all_contents:
            content_id = content[0]  # Id محتوا
            title = content[1]  # عنوان محتوا
            lang_id = content[4]  # زبان محتوا

            if not title or title.strip() == "":  # اگر عنوان وجود ندارد
                logger.info(f"ℹ️ محتوا {content_id} عنوان ندارد. تولید عنوان جدید...")
            else:  # اگر عنوان وجود دارد
                logger.info(f"ℹ️ محتوا {content_id} عنوان دارد. بهینه‌سازی عنوان...")

            # تولید عنوان جدید یا بهینه‌سازی
            generated_title = seo_service.generate_title(content_id, lang_id, current_title=title)
            logger.info(f"✅ عنوان نهایی برای ID {content_id}: {generated_title}")

            # ذخیره عنوان در دیتابیس
            db.update_pure_content(content_id, title=generated_title)

    except Exception as e:
        logger.exception(f"❌ خطا هنگام اجرای برنامه: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()
