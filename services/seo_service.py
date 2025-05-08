import logging
import requests

class SEOService:
    def __init__(self, db, q_service):
        self.db = db
        self.q_service = q_service

    def generate_title_only(self, content_id, lang_id):
        try:
            # گرفتن توضیح برای محتوای مورد نظر
            query = "SELECT Description FROM dbo.TblPureContent WHERE Id = ?"
            result = self.db.select(query, [content_id])
            if not result:
                raise ValueError(f"❌ توضیحی برای محتوا با ID {content_id} پیدا نشد.")
            
            description = result[0][0]
            prompt = f"Generate a compelling and SEO-optimized title for the following content (LangId={lang_id}):\n\n{description}"
            
            title = self.qwen_generate(prompt)
            return title or "عنوان پیش‌فرض"
        except Exception as e:
            logging.error(f"❌ خطا در generate_title_only برای content_id={content_id}: {e}")
            return "عنوان پیش‌فرض"

    def generate_title_for_all(self):
        try:
            all_content = self.db.get_all_purecontents()  # گرفتن تمام محتواها
            if not all_content:
                logging.info("✅ محتوایی برای تولید عنوان پیدا نشد.")
                return

            for content in all_content:
                content_id = content[0]  # Id محتوا
                lang_id = content[4]  # زبان محتوا
                current_title = content[1]  # عنوان موجود
                
                if current_title and current_title.strip():
                    logging.info(f"ℹ️ محتوا {content_id} عنوان دارد. بهینه‌سازی عنوان...")
                    generated_title = self.optimize_title_for_seo(current_title)
                else:
                    logging.info(f"ℹ️ محتوا {content_id} عنوان ندارد. تولید عنوان جدید...")
                    generated_title = self.generate_title_only(content_id, lang_id)
                
                logging.info(f"✅ عنوان نهایی برای ID {content_id}: {generated_title}")

                # ذخیره عنوان جدید در دیتابیس
                self.db.update_pure_content(content_id, generated_title)

        except Exception as e:
            logging.error(f"⚠️ خطا در generate_title_for_all: {e}")

    def optimize_title_for_seo(self, title):
        optimized_title = title.strip()
        if len(optimized_title) < 60:
            optimized_title += " | بهترین انتخاب برای SEO"
        return optimized_title

    def qwen_generate(self, prompt):
        try:
            response = self.q_service.send_request(prompt)

            if not response:
                raise ValueError("پاسخی از مدل دریافت نشد.")

            if isinstance(response, dict):
                new_title = response.get("result", "").strip()
                if not new_title:
                    raise ValueError("مدل عنوانی تولید نکرد.")
                return new_title
            else:
                raise ValueError("فرمت پاسخ مدل قابل استفاده نیست.")

        except ValueError as e:
            logging.error(f"⚠️ خطای مقداردهی: {e}")
        except requests.exceptions.Timeout:
            logging.error("⚠️ درخواست به Qwen تایم‌اوت شد.")
        except requests.exceptions.RequestException as e:
            logging.error(f"⚠️ خطای شبکه: {e}")
        except Exception as e:
            logging.error(f"⚠️ خطای کلی در qwen_generate: {e}")

        return ""
