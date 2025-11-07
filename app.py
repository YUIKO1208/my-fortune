import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
import random
import csv
import requests  # ← 追加：GASに送信するため
import json

# --- Optional: OpenAI (only used if OPENAI_API_KEY is set) ---
USE_OPENAI = False
client = None

try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
        USE_OPENAI = True
    else:
       USE_OPENAI = False
  
except Exception as e:
    USE_OPENAI = False

print("USE_OPENAI:", USE_OPENAI)
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))


app = Flask(__name__)

# Google Apps Script のURL（あなたの実際のURL）
GAS_URL = "https://script.google.com/macros/s/AKfycbz-7j8Dyw9IfrOrGyKld8Q46V9-JEAvzAa5Z-MYj6FMYSGCUnzUejtSnT7lfLoZMhej/exec"

# Load trait data
with open(os.path.join(os.path.dirname(__file__), "data", "traits.json"), "r", encoding="utf-8") as f:
    TRAITS = json.load(f)

TAROT_FACETS = [
    {"id": "love", "label": "愛情面", "hint": "自分を大切にしつつ素直に気持ちを伝えると吉。"},
    {"id": "work", "label": "仕事面", "hint": "小さな改善を積み重ねると大きな信頼に。"},
    {"id": "mind", "label": "精神面", "hint": "休息は前進の準備。呼吸を整えて一歩ずつ。"}
]

SURVEY_CSV = os.path.join(os.path.dirname(__file__), "outputs", "survey.csv")
os.makedirs(os.path.join(os.path.dirname(__file__), "outputs"), exist_ok=True)
if not os.path.exists(SURVEY_CSV):
    with open(SURVEY_CSV, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp","category","month","blood","positive_index","sukkiri","satisfaction","condition"])

def month_blood_key(month, blood):
    return f"{int(month)}_{blood.upper()}"

def rule_based_message(category, concern, month, blood):
    key = month_blood_key(month, blood)
    trait = TRAITS.get(key, {})
    month_trait = trait.get("month_trait","")
    blood_trait = trait.get("blood_trait","")
    strength = trait.get("strength","")
    base = 60 + (int(month) % 5) * 4
    positive_index = min(99, max(0, base + random.randint(-25, 25)))
    facet = random.choice(TAROT_FACETS)
    lines = []
    lines.append(f"今は少し曇り空でも、来月には晴れ間がのぞく兆し。{facet['label']}では「{facet['hint']}」の運気。")
    if concern:
        lines.append(f"あなたの悩み「{concern}」を受け止めたよ。")
    lines.append(f"{int(month)}月生まれのあなたは「{month_trait}」タイプ、{blood}型の長所は「{blood_trait}」。")
    if strength:
        lines.append(f"とくに「{strength}」が今週の切り札。")
    lines.append("大丈夫。あなたの丁寧さと優しさはちゃんと伝わっている。")
    lines.append("小さな一歩が、思っている以上の追い風になるよ。")
    return " ".join(lines), positive_index, facet

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", facets=TAROT_FACETS)

@app.route("/result", methods=["POST"])
def result():
    # --- ユーザー識別ID（cookieに保存） ---
    user_id = request.cookies.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())

    username = request.form.get("username", "")
    category = request.form.get("category", "work")
    concern = request.form.get("concern", "").strip()
    month = request.form.get("month", "1")
    blood = request.form.get("blood", "A")

    # --- 占いメッセージ生成 ---
    message, positive_index, facet = rule_based_message(category, concern, month, blood)

    # --- Googleスプレッドシートへ送信 ---
    data = {
        "user_id": user_id,
        "category": category,
        "positivity": positive_index
    }
    try:
        requests.post(GAS_URL, data=json.dumps(data), headers={"Content-Type": "application/json"}, timeout=3)
    except Exception as e:
        print("Failed to send to GAS:", e)

    # --- 結果ページを返す（cookieにIDを保存） ---
    resp = make_response(render_template("result.html",
                           username=username, category=category, concern=concern,
                           month=month, blood=blood,
                           message=message, positive_index=positive_index,
                           facet=facet))
    resp.set_cookie("user_id", user_id, max_age=60*60*24*365)  # 1年間保持
    return resp

@app.route("/survey", methods=["POST"])
def survey():
    sukkiri = request.form.get("sukkiri")
    satisfaction = request.form.get("satisfaction") 
    category = request.form.get("category")
    month = request.form.get("month")
    blood = request.form.get("blood")
    positive_index = request.form.get("positive_index")
    condition = request.form.get("condition","LM")  
    
    with open(SURVEY_CSV, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.utcnow().isoformat(), category, month, blood, positive_index, sukkiri, satisfaction, condition])
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)








