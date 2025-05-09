import logging
import json
import re
from datetime import datetime
import time
import os

class SEOService:
    def __init__(self, db, q_service, min_seo_score=5, max_retries=3, retry_delay=5):
        self.db = db
        self.q_service = q_service
        self.min_seo_score = min_seo_score
        self.max_retries = max_retries
        self.retry_delay = retry_delay  # زمان تاخیر بین تلاش‌ها

    def generate_title_for_all(self):
        """Extracts all content and attempts to optimize titles based on SEO score."""
        try:
            contents = self.db.get_all_purecontents()
            if not contents:
                logging.info("✅ محتوایی برای پردازش وجود ندارد.")
                return

            output = []
            for content_id, title, *_rest, lang_id in contents:
                if not title or not title.strip():
                    logging.warning(f"⚠️ محتوا {content_id} عنوان ندارد.")
                    continue

                logging.info(f"ℹ️ بهینه‌سازی عنوان محتوا {content_id} شروع شد...")

                try:
                    new_title, score, raw = self.optimize_title_until_score_ok(title, lang_id)
                    output.append({
                        "content_id": content_id,
                        "old_title": title,
                        "new_title": new_title,
                        "seo_score": score,
                        "raw_response": raw
                    })
                    logging.info(f"✅ عنوان نهایی {content_id}: {new_title} (SEO: {score})")
                except Exception:
                    logging.exception(f"❌ خطا در پردازش {content_id}")

            self._save_output_file(output)

        except Exception:
            logging.exception("❌ خطای کلی در generate_title_for_all")

    def optimize_title_until_score_ok(self, title, lang_id):
        """Try optimizing the title up to max_retries until SEO score is sufficient using Qwen."""
        for attempt in range(1, self.max_retries + 1):
            raw, new_title, score = self.qwen_optimize_title_and_score(title, lang_id)
            logging.info(f"📝 تلاش {attempt}: {new_title} (SEO: {score})")

            if score >= self.min_seo_score:
                logging.info(f"✅ امتیاز سئو مطلوب بدست آمد: {score}")
                return new_title, score, raw
            else:
                logging.debug(f"⏳ امتیاز کافی نبود (SEO: {score}), ادامه تلاش...")

            # Delay between retries to avoid overwhelming the service
            time.sleep(self.retry_delay)  # استفاده از time.sleep

        logging.error(f"❌ به امتیاز سئو مطلوب نرسید. آخرین امتیاز: {score} برای عنوان: {new_title}")
        return new_title, score, raw

    def qwen_optimize_title_and_score(self, title, lang_id):
        """Send title to Qwen model and evaluate response."""
        prompt = f"{self._get_prompt_by_lang(lang_id)}\n\n{title}"
        try:
            response = self.qwen_generate(prompt)
            optimized = self.extract_clean_title(response) or title
            score = self.calculate_seo_score(optimized)
            return response, optimized, score
        except Exception:
            logging.exception("❌ خطا در qwen_optimize_title_and_score")
            return "", title, 0

    def qwen_generate(self, prompt):
        """Send request to Qwen and return response."""
        try:
            self.q_service.send_request(prompt)
            result = self.q_service.get_response()
            if not result or "متاسفانه" in result:
                raise ValueError("مدل پاسخ مناسبی نداد.")
            return result.strip()
        except Exception:
            logging.exception("⚠️ خطا در qwen_generate")
            return ""

    def extract_clean_title(self, response):
        """Try extracting a clean title line from the model's response."""
        for line in response.splitlines():
            cleaned = re.sub(r"[*#“”\"]", "", line).strip()
            if 10 < len(cleaned) < 120 and ":" not in cleaned:
                return cleaned
        return None

    def calculate_seo_score(self, title):
        """Evaluate the SEO score of a given title."""
        score, length, words = 0, len(title), title.split()
        wc = len(words)

        # بررسی طول عنوان
        if 60 <= length <= 80:
            score += 3
        elif 50 <= length <= 90:
            score += 2
        elif 30 <= length <= 100:
            score += 1
        else:
            score -= 2
            logging.debug(f"🔴 طول نامناسب: {length} کاراکتر.")

        # بررسی تعداد کلمات
        if 4 <= wc <= 9:
            score += 1
        elif wc < 3 or wc > 12:
            score -= 1
            logging.debug(f"🔴 تعداد کلمات نامناسب: {wc} کلمه.")

        # بررسی وجود عدد
        if re.search(r"\b\d+\b", title):
            score += 1

        # میانگین طول کلمات
        if wc and (sum(len(w) for w in words) / wc) < 6:
            score += 1

        # کلمات کلیدی
        keywords = ["SEO", "optimize", "rank", "guide", "boost", "traffic", "title", "headline"]
        if any(kw.lower() in title.lower() for kw in keywords):
            score += 2

        # عنوان سوالی
        if "?" in title or any(q in title.lower() for q in ["why", "how", "what"]):
            score += 2

        logging.debug(f"📊 SEO Score: {score} برای عنوان: {title}")
        return score

    def _get_prompt_by_lang(self, lang_id):
        """Return language-specific prompt.""" 
        return {
            1: "این عنوان را برای سئو بهینه کن. کوتاه، جذاب، حاوی عدد و قابل کلیک باشد:",
            2: "Please rewrite the following title to make it more SEO-friendly and engaging.\nGuidelines:\n- Length: 60–80 characters\n- Use a number if possible\n- Use strong power words\n- Be clear and click-worthy\n- Output only the optimized title.\n\nOriginal title:",
            3: "حسّن هذا العنوان لمحركات البحث مع الحفاظ على جاذبيته ووضوحه:",
            4: "Bu başlığı SEO için optimize edin. Kısa, dikkat çekici ve açık olsun:",
            5: "Optimisez ce titre pour le SEO. Soyez accrocheur, clair et concis :",
        }.get(lang_id, "")

    def _save_output_file(self, data):
        """Save results to timestamped JSON file."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "seo_output"
        os.makedirs(output_dir, exist_ok=True)
        path = f"{output_dir}/seo_titles_output_{ts}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logging.info(f"📁 فایل خروجی ذخیره شد: {path}")
        except Exception:
            logging.exception("❌ خطا در ذخیره فایل خروجی:")
