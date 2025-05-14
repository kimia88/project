import re

class SEOTitleEvaluator:
    def __init__(self):
        self.question_words = ["how", "what", "why", "when", "where", "which", "guide", "tutorial"]
        self.special_characters = [":", "-", "?"]
        self.triggers_for_clickbait = ["secret", "revealed", "unveiled", "ultimate", "best", "free"]
        self.voice_search_keywords = ["how to", "what is", "why is", "where can", "who is"]
    
    def evaluate(self, optimized_title, focus_keyword):
        score = 0.0
        
        # بررسی اینکه کلمه کلیدی در ابتدای عنوان باشد
        if optimized_title.lower().startswith(focus_keyword.lower()):
            score += 1.5  # اضافه کردن امتیاز برای کلمه کلیدی در ابتدا

        # وجود کلمه کلیدی در عنوان
        if focus_keyword.lower() in optimized_title.lower():
            score += 4.0  # کاهش امتیاز از 5 به 4 برای کلمه کلیدی در عنوان

        # طول عنوان مناسب باشد (بیش از 30 کاراکتر و کمتر از 70 کاراکتر)
        title_length = len(optimized_title.strip())
        if title_length < 30:
            score -= 1.0  # کسر امتیاز برای عناوین خیلی کوتاه
        elif title_length <= 60:
            score += 3.0  # امتیاز برای عناوین با طول مناسب
        elif title_length > 60:
            score -= 1.5  # کسر امتیاز برای عناوین خیلی طولانی

        # اولین حرف بزرگ باشد
        if optimized_title and optimized_title[0].isupper():
            score += 1.0  # اضافه کردن امتیاز برای اولین حرف بزرگ

        # وجود کلمات پرسشی در عنوان
        if any(word in optimized_title.lower() for word in self.question_words):
            score += 2.0  # اضافه کردن امتیاز برای کلمات پرسشی

        # بررسی استفاده از علائم نگارشی
        if any(char in optimized_title for char in self.special_characters):
            score += 1.0  # اضافه کردن امتیاز برای علائم نگارشی

        # استفاده از کلمات جذاب و ترغیب‌کننده (Clickbait)
        if any(word in optimized_title.lower() for word in self.triggers_for_clickbait):
            score += 1.5  # اضافه کردن امتیاز برای کلمات جذاب و ترغیب‌کننده

        # مناسب بودن برای جستجوهای صوتی
        if any(phrase in optimized_title.lower() for phrase in self.voice_search_keywords):
            score += 2.0  # اضافه کردن امتیاز برای جستجوهای صوتی

        # جلوگیری از تکرار کلمه کلیدی بیش از حد
        if optimized_title.lower().count(focus_keyword.lower()) > 2:
            score -= 1.0  # کسر امتیاز برای تکرار زیاد کلمه کلیدی

        # محدود کردن امتیاز نهایی بین 0 تا 10
        return min(max(score, 0.0), 10.0)
