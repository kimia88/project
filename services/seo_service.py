import json
import time
import logging
import os
import re
from datetime import datetime
from services.seo_title_evaluator import SEOTitleEvaluator
from services.llm_service import QService

class SEOService:
    def __init__(self, db, q_service, min_score=7.0, retries=5, delay=5):
        self.db = db
        self.q_service = q_service
        self.min_score = min_score
        self.retries = retries
        self.delay = delay
        self.evaluator = SEOTitleEvaluator()

    def extract_focus_keyword(self, title):
        """ استخراج هوشمند کلمه کلیدی از عنوان با حذف stopwords و تمرکز بر اسم‌ها """
        stopwords = {"the", "of", "and", "a", "an", "to", "in", "on", "for", "with", "at", "by"}
        words = [w.lower() for w in re.findall(r'\w+', title) if w.lower() not in stopwords]
        
        # اولویت با کلمات کلیدی معنایی‌تر
        if len(words) >= 2:
            return f"{words[0]} {words[1]}"
        elif words:
            return words[0]
        return title.strip().lower()

    def generate_title_for_all(self):
        """ تولید عنوان بهینه برای تمام محتواها """
        contents = self.db.get_all_purecontents()
        results = []

        for content_id, title, *_rest, lang_id in contents:
            if not title or not title.strip():
                continue

            keyword = self.extract_focus_keyword(title)
            best_title, best_score = title, 0.0

            for i in range(1, self.retries + 1):
                prompt = self._build_prompt(title, lang_id, last_score=best_score)
                response = self._ask_qwen(prompt)

                if not response:
                    logging.warning(f"⚠️ Attempt {i}: No response from Qwen. Retrying...")
                    time.sleep(self.delay)
                    continue

                try:
                    data = self._parse_response(response)
                    candidate = data.get("optimized_title", "").strip()

                    if not candidate:
                        logging.warning(f"⚠️ Attempt {i}: Empty optimized title in response. Retrying...")
                        time.sleep(self.delay)
                        continue

                    score = self.evaluator.evaluate(candidate, keyword)
                    logging.info(f"🔁 Attempt {i}: «{candidate}» (SEO Score: {score})")

                    if score > best_score:
                        best_title = candidate
                        best_score = score

                    if score >= self.min_score:
                        logging.info(f"✅ Attempt {i}: Score meets threshold. Final title found!")
                        break

                except Exception as ex:
                    logging.warning(f"⚠️ Attempt {i}: Invalid response format: {response} | Error: {ex}")

                time.sleep(self.delay)

            # Update the optimized title in the database
            self._update_title_in_database(content_id, best_title, best_score)

            results.append({
                "content_id": content_id,
                "original_title": title,
                "optimized_title": best_title,
                "seo_score": best_score
            })

            logging.info(f"✅ Final Title for {content_id}: {best_title} (SEO: {best_score})")

        # ذخیره‌سازی نتایج به عنوان JSON
        self._save_results(results)

    def _ask_qwen(self, prompt):
        """ ارسال درخواست به Qwen و دریافت پاسخ """
        try:
            self.q_service.send_request(prompt)
            return self.q_service.get_response()
        except Exception:
            logging.exception("❌ Error in Qwen request")
            return None

    def _parse_response(self, raw):
        """ پارس کردن پاسخ دریافتی از Qwen """
        json_start = raw.find('{')
        if json_start == -1:
            raise ValueError("No JSON found in response.")
        return json.loads(raw[json_start:])

    def _build_prompt(self, title, lang_id, last_score=0.0):
        """ ساخت داینامیک prompt برای Qwen بر اساس زبان و امتیاز قبلی """
        if lang_id == 1:  # فارسی
            base = (
                "لطفاً عنوان زیر را برای سئو بازنویسی کن. فقط JSON زیر را خروجی بده:\n"
                "{\n"
                "  \"original_title\": \"...\",\n"
                "  \"optimized_title\": \"...\",\n"
                "  \"score\": عددی بین 0 تا 10\n"
                "}\n\n"
                f"عنوان:\n{title}"
            )
            if last_score < self.min_score:
                base += "\n\n❗️توجه: نسخه قبلی امتیاز کمی داشت. لطفاً عنوانی خیلی متفاوت، جذاب و قابل جستجوی صوتی پیشنهاد بده."
            return base

        else:  # انگلیسی
            base = (
                "Please rewrite the following title to improve SEO. Return ONLY a JSON like:\n"
                "{\n"
                "  \"original_title\": \"...\",\n"
                "  \"optimized_title\": \"...\",\n"
                "  \"score\": number between 0 and 10\n"
                "}\n\n"
                f"Title:\n{title}"
            )
            if last_score < self.min_score:
                base += "\n\n❗ Previous version had low SEO score. Please suggest a significantly different and more engaging SEO title, potentially starting with a question or guide format."
            return base

    def _save_results(self, results):
        """ ذخیره نتایج در فایل JSON """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("seo_output", exist_ok=True)
        path = f"seo_output/seo_results_{ts}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        logging.info(f"📁 Saved: {path}")

    def _update_title_in_database(self, content_id, optimized_title, seo_score):
        """ به‌روزرسانی عنوان بهینه‌شده در دیتابیس """
        try:
            self.db.update_pure_content(content_id, optimized_title)
            logging.info(f"✅ Updated content_id {content_id} with optimized title: {optimized_title} (SEO Score: {seo_score})")
        except Exception as e:
            logging.error(f"❌ Error updating content_id {content_id}: {e}")
