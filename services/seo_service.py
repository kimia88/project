import json
import os
from datetime import datetime
import pyodbc
import logging

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SEOService:
    def __init__(self, db, q_service):
        # سازنده که db و q_service را دریافت می‌کند
        self.db = db
        self.q_service = q_service

    def generate_titles_for_all(self, contents):
        if not contents:
            logging.warning("⚠️ داده‌ها به درستی بارگذاری نشده‌اند.")
            return  # اگر داده‌ها خالی هستند، پردازش ادامه نمی‌یابد

        logging.info("⚠️ داده‌های بارگذاری شده: %s", contents)  # نمایش داده‌ها برای بررسی

        seo_results = []

        for content in contents:
            if isinstance(content, dict):
                content_id = content.get('id')
                title = content.get('title', "")  # اگر عنوان موجود نیست، به صورت پیش‌فرض ""
                description = content.get('description', "")  # اگر توضیحات موجود نیست، به صورت پیش‌فرض ""
            else:
                logging.warning("⚠️ داده‌ها به درستی بارگذاری نشده‌اند.")
                continue  # اگر داده به درستی نباشد، ادامه می‌دهیم تا از بقیه داده‌ها استفاده کنیم

            if not title:
                logging.warning(f"⚠️ [Content ID {content_id}] عنوان خالی است! تلاش برای ایجاد عنوان جدید.")
                title = "عنوان موقت"  # عنوان پیش‌فرض اگر عنوان اصلی خالی باشد

            try:
                # ساخت پرامپت برای مدل زبان جهت تولید عنوان سئو
                prompt = f"Generate a compelling and SEO-optimized title for the content. Max 60 characters. Focus on relevance, user intent, and engagement. Description: '{description}'"
                new_title = self.qwen_generate(prompt)

                if not new_title:
                    raise ValueError("No response from LLM.")

                # اگر عنوان بیش از 60 کاراکتر بود، آن را کوتاه می‌کنیم
                if len(new_title) > 60:
                    logging.warning(f"⚠️ [{content_id}] عنوان بیش از 60 کاراکتر است ({len(new_title)}). تلاش برای خلاصه کردن...")
                    new_title = self.smart_shorten_title(new_title)

                # چاپ اطلاعات برای دیباگ
                logging.info(f"\n=== Content ID: {content_id} ===")
                logging.info(f"Original Title: {title}")
                logging.info(f"SEO Optimized Title: {new_title}")
                logging.info("=" * 40)

                # افزودن نتایج به لیست برای ذخیره‌سازی در فایل JSON
                seo_results.append({
                    'content_id': content_id,
                    'original_title': title,
                    'seo_optimized_title': new_title
                })

            except Exception as e:
                logging.error(f"⚠️ خطا برای Content ID {content_id}: {e.__class__.__name__} - {e}")

        # ذخیره نتایج در قالب JSON
        self.save_results_to_json(seo_results)

    def fetch_contents(self):
        # فرض می‌کنیم که در اینجا باید داده‌ها را از پایگاه داده بگیریم
        query = "SELECT id, title, description FROM contents"  # این فقط یک مثال است
        try:
            contents = self.db.select(query)  # اجرای کوئری
            logging.info(f"✅ {len(contents)} محتوا از پایگاه داده بارگذاری شد.")
            return contents
        except Exception as e:
            logging.error(f"⚠️ خطا در بارگذاری داده‌ها: {e}")
            return []

    def qwen_generate(self, prompt):
        try:
            self.q_service.send_request(prompt)
            response = self.q_service.get_response()
            logging.info(f"✅ پاسخ از Qwen دریافت شد: {response}")
            return response.strip()
        except Exception as e:
            logging.error(f"⚠️ خطا در ارتباط با Qwen: {e}")
            return ""

    def smart_shorten_title(self, title):
        # اگر عنوان بیشتر از 60 کاراکتر باشد، آن را کوتاه می‌کند
        if len(title) <= 60:
            return title
        words = title.split()
        short_title = ""
        for word in words:
            if len(short_title) + len(word) + 1 <= 57:  # محدودیت طول عنوان به 60 کاراکتر
                short_title += word + " "
            else:
                break
        return short_title.strip() + "..."

    def save_results_to_json(self, seo_results):
        # ذخیره نتایج در فایل JSON
        output_dir = 'seo_output'
        os.makedirs(output_dir, exist_ok=True)
        filename = f"seo_titles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_output_file = os.path.join(output_dir, filename)

        try:
            with open(json_output_file, 'w', encoding='utf-8') as f:
                json.dump(seo_results, f, ensure_ascii=False, indent=4)
            logging.info(f"✅ نتایج SEO در فایل {json_output_file} ذخیره شد.")
        except Exception as e:
            logging.error(f"⚠️ خطا در ذخیره نتایج SEO: {e}")

    def connect_to_db(self):
        try:
            self.db.connect()  # اتصال به پایگاه داده
            logging.info("✅ اتصال به دیتابیس برقرار شد.")
        except Exception as e:
            logging.error(f"⚠️ خطا در اتصال به دیتابیس: {e}")


class SQLServerDatabase:
    def __init__(self, server, database, username, password):
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
        self.connection = None

    def connect(self):
        """اتصال به پایگاه داده"""
        try:
            self.connection = pyodbc.connect(self.connection_string)
            logging.info("✅ اتصال به دیتابیس برقرار شد.")
        except Exception as e:
            logging.error(f"⚠️ خطا در اتصال به دیتابیس: {e}")
            raise

    def disconnect(self):
        """قطع اتصال از پایگاه داده"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logging.info("✅ اتصال از دیتابیس قطع شد.")
        else:
            logging.warning("❗ اتصال به دیتابیس قبلاً قطع شده است.")

    def select(self, query, params=None):
        """اجرای کوئری SELECT و بازگشت نتایج"""
        if not self.connection or self.connection.closed:
            logging.error("❗ اتصال به پایگاه داده قطع است.")
            return []

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or [])
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            logging.error(f"⚠️ خطا در اجرای کوئری: {e}")
            return []
        finally:
            cursor.close()


class MockQService:
    def send_request(self, prompt):
        logging.info(f"Sending request: {prompt}")

    def get_response(self):
        return "SEO Optimized Title Example"


# استفاده از کلاس‌ها
db = SQLServerDatabase("server_name", "database_name", "username", "password")
q_service = MockQService()

# ساخت شیء SEOService
seo_service = SEOService(db, q_service)

# اتصال به دیتابیس
seo_service.connect_to_db()

# بارگذاری داده‌ها و پردازش عنوان‌ها
contents = seo_service.fetch_contents()
seo_service.generate_titles_for_all(contents)

# قطع اتصال از دیتابیس
db.disconnect()
