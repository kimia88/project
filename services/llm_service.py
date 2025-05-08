import requests
import json
import re

class QService:
    BASE_URL = "https://qwen-qwen2-5-1m-demo.hf.space"
    #BASE_URL = "https://qwen-qwq-32b-preview.hf.space"
    def __init__(self, session_hash):
        self.session_hash = session_hash

    def predict(self, text):
        url = f"{self.BASE_URL}/run/predict?__theme=system"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Origin": self.BASE_URL,
            "Referer": f"{self.BASE_URL}/?__theme=system"
        }
        data = {
            "data": [{"files": [], "text": text}, [[{"id": None, "elem_id": None, "elem_classes": None, "name": None, "text": text, "flushing": None, "avatar": "", "files": []}, [{"id": None, "elem_id": None, "elem_classes": None, "name": None, "text": "", "flushing": None, "avatar": "", "files": []}, None, None]]], None],
            "event_data": None,
            "fn_index": 1,
            "trigger_id": 5,
            "session_hash": self.session_hash
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error in prediction request: {e}")
            if response:
                print(f"⚠️ Response status code: {response.status_code}")
                print(f"⚠️ Response text: {response.text}")
            return {"error": "خطا در ارسال درخواست به مدل"}

    def send_request(self, text):
        predict_response = self.predict(text)
        if "error" in predict_response:
            return predict_response

        url = f"{self.BASE_URL}/queue/join?__theme=system"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Origin": self.BASE_URL,
            "Referer": f"{self.BASE_URL}/?__theme=system"
        }
        
        data = {
            "data": [[[{"id": None, "elem_id": None, "elem_classes": None, "name": None, "text": text, "flushing": None, "avatar": "", "files": []}, None]], None, 0],
            "event_data": None,
            "fn_index": 2,
            "trigger_id": 5,
            "session_hash": self.session_hash
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error in sending request: {e}")
            if response:
                print(f"⚠️ Response status code: {response.status_code}")
                print(f"⚠️ Response text: {response.text}")
            return {"error": "خطا در ارسال درخواست به مدل"}

    def get_response(self):
        url = f"{self.BASE_URL}/queue/data?session_hash={self.session_hash}"
        headers = {
            "Accept": "text/event-stream",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Referer": f"{self.BASE_URL}/?__theme=system"
        }
    
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            for line in response.iter_lines():
                if line and line.startswith(b"data: "):
                    try:
                        data = json.loads(line[6:])
                        if data.get("msg") == "process_completed":
                            output_data = data.get("output", {}).get("data", [])
                            if output_data and isinstance(output_data[0], list) and len(output_data[0]) > 0:
                                last_text = output_data[0][0][1][0]["text"]
                                cleaned_text = re.sub(r'<summary>.*?</summary>', '', last_text)
                                return cleaned_text
                    except json.JSONDecodeError:
                        continue
            return "متاسفانه الان نمیتونم جواب بدم"
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error while getting response: {e}")
            return "خطا در دریافت پاسخ از مدل"

    def extract_last_text(self, response_text):
        messages = response_text.strip().split("\n")
        last_text = None
        
        for message in messages:
            if message.startswith("data: "):
                try:
                    data = json.loads(message[6:])
                    if data.get("msg") == "process_completed":
                        output_data = data.get("output", {}).get("data", [])
                        if output_data and isinstance(output_data[0], list) and len(output_data[0]) > 0:
                            last_text = output_data[0][0][1][0]["text"]
                except json.JSONDecodeError:
                    continue
        if last_text is None:
            return "متاسفانه الان نمیتونم جواب بدم"
        cleaned_text = re.sub(r'<summary>.*?</summary>', '', last_text)
        return cleaned_text
