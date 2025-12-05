
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
import random
import csv


# --- Optional: OpenAI (only used if OPENAI_API_KEY is set) ---
USE_OPENAI = False
client = None


try:
   from openai import OpenAI
   api_key = os.getenv("OPENAI_API_KEY")
   print("OPENAI_API_KEY:", api_key)
   if api_key:
       client = OpenAI(api_key=api_key)
       USE_OPENAI = True
   else:
       USE_OPENAI = False
except Exception as e:
   print("OpenAI import failed:", e)
   USE_OPENAI = False


print("USE_OPENAI:", USE_OPENAI)
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))


app = Flask(__name__)


# Load 48-pattern trait database
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


def openai_message(category, concern, month, blood,facets):
   prompt = f"""
あなたはポジティブ占い師です。ユーザーの悩みに寄り添い、前向きなメッセージを日本語で220〜280字で返してください。
条件:
- トーンは優しく非判断的、根拠のない断定は避けるが、希望の比喩を使って励ます
- カテゴリ: {category} / 悩み: {concern}
- 誕生月: {month}月 / 血液型: {blood}型 の長所も1つだけ触れる
- タロットの焦点: {facets} にも自然に触れてメッセージに組み込む
- 今日のポジティブ指数がその数値になった理由を、1〜2文で優しく説明する（比喩的OK）
- 最後に「今日のポジティブ指数: XX%」の形式で数値をつける（XXは60〜95）
"""
   if not USE_OPENAI:
       return None
   try:
       resp = client.chat.completions.create(
           model="gpt-4o-mini",
           messages=[{"role":"user", "content": prompt}],
           temperature=0.8,
           max_tokens=300
       )
       text = resp.choices[0].message.content.strip()
       import re
       m = re.search(r"(\d{2})\s*%", text)
       positive_index = int(m.group(1)) if m else random.randint(60,95)
       return text, positive_index, random.choice(TAROT_FACETS)
   except Exception:
       return None


@app.route("/", methods=["GET"])
def index():
   return render_template("index.html", facets=TAROT_FACETS)


@app.route("/result", methods=["POST"])
def result():
   username = request.form.get("username", "")
   category = request.form.get("category", "work")
   concern = request.form.get("concern", "").strip()
   month = request.form.get("month", "1")
   blood = request.form.get("blood", "A")
   facets = request.form.get("facets","love")



   ai = openai_message(category, concern, month, blood,facets)
   if ai:
       message, positive_index, facet = ai
   else:
       message, positive_index, facet = rule_based_message(category, concern, month, blood)


   return render_template("result.html",
                          username=username, category=category, concern=concern,
                          month=month, blood=blood,
                          message=message, positive_index=positive_index,
                          facet=facet)


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
       import csv
       writer = csv.writer(f)
       writer.writerow([datetime.utcnow().isoformat(), category, month, blood, positive_index, sukkiri, satisfaction, condition])
   return jsonify({"ok": True})


if __name__ == "__main__":
   app.run(debug=True, host="0.0.0.0", port=8000)








