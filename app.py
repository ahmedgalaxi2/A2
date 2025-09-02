from flask import Flask, request, render_template_string
import yfinance as yf
import time
import os

app = Flask(__name__)

CACHE = {}
CACHE_TTL = 300  # 5 دقائق

TEMPLATE = """
<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>📈 محلل الدعوم والمقاومات</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background-color: #0f172a; color: #e5e7eb; min-height: 100vh; display: flex; flex-direction: column; }
    .card { background-color: #111827; border: 1px solid #374151; }
    pre { white-space: pre-wrap; color: #fff; font-size: 1.1rem; }
    .copy-btn { margin-top: 10px; }
    footer { margin-top: auto; background-color: #0b1220; color: #9ca3af; text-align: center; padding: 10px; border-top: 1px solid #374151; }
  </style>
</head>
<body>
<div class="container py-5">
  <h2 class="mb-4 text-center">📊 محلل الدعوم والمقاومات</h2>
  <form method="post">
    <div class="row g-3 align-items-end">
      <div class="col-md-8">
        <input type="text" name="ticker" class="form-control" placeholder="مثال: 2222 أو AAPL" value="{{ ticker or '' }}">
      </div>
      <div class="col-md-4 d-grid">
        <button class="btn btn-primary">تحليل</button>
      </div>
    </div>
  </form>

  {% if error %}
    <div class="alert alert-danger mt-4">{{ error }}</div>
  {% endif %}

  {% if analysis %}
  <div class="card mt-4 p-3">
    <pre id="analysis-text">{{ analysis }}</pre>
    <button class="btn btn-success copy-btn" onclick="copyText()">نسخ النتيجة</button>
  </div>
  {% endif %}
</div>

<footer>
  <div>لا تنسى الصلاة على النبي ﷺ</div>
  <div>Made with ❤️ by AHMED GAMAL</div>
</footer>

<script>
function copyText() {
  const text = document.getElementById("analysis-text").innerText;
  navigator.clipboard.writeText(text).then(() => {
    alert("✅ تم نسخ النتيجة!");
  });
}
</script>
</body>
</html>
"""

def get_price(ticker: str):
    """جلب السعر فقط بدون اسم السهم"""
    if ticker.isdigit():
        ticker += ".SR"

    now = time.time()
    if ticker in CACHE:
        price, ts = CACHE[ticker]
        if now - ts < CACHE_TTL:
            return price

    try:
        t = yf.Ticker(ticker)
        data = t.history(period="5d")
        if not data.empty:
            price = float(data["Close"].dropna().iloc[-1])
            CACHE[ticker] = (price, now)
            return price
    except Exception:
        pass
    return None

def compute_levels(price: float):
    raw_levels = {
        "support1": int(price * 0.97),
        "support2": int(price * 0.95),
        "resistance1": int(price * 1.04),
        "resistance2": int(price * 1.06)
    }

    price_int = int(price)

    # ضمان أن الدعوم أقل من السعر
    if raw_levels["support1"] >= price_int:
        raw_levels["support1"] = price_int - 1
    if raw_levels["support2"] >= raw_levels["support1"]:
        raw_levels["support2"] = raw_levels["support1"] - 1

    # ضمان أن المقاومات أعلى من السعر
    if raw_levels["resistance1"] <= price_int:
        raw_levels["resistance1"] = price_int + 1
    if raw_levels["resistance2"] <= raw_levels["resistance1"]:
        raw_levels["resistance2"] = raw_levels["resistance1"] + 1

    # إزالة أي تكرار
    seen = set()
    for key in raw_levels:
        while raw_levels[key] in seen:
            raw_levels[key] += 1
        seen.add(raw_levels[key])

    return raw_levels

def build_analysis(levels):
    return (
        f"يتداول السهم في اتجاه عرضي\n"
        f"ويستند على دعم أول عند {levels['support1']}\n"
        f"ودعم ثانٍ عند {levels['support2']}\n"
        f"إيجابية بالثبات أعلى من مستوى الدعم\n"
        f"ليستهدف بالتداول أعلاها {levels['resistance1']} – {levels['resistance2']}"
    )

@app.route("/", methods=["GET", "POST"])
def index():
    ticker = ""
    analysis = None
    error = None
    if request.method == "POST":
        ticker = (request.form.get("ticker") or "").strip().upper()
        if ticker:
            price = get_price(ticker)
            if price:
                levels = compute_levels(price)
                analysis = build_analysis(levels)
            else:
                error = "تعذر جلب البيانات من Yahoo Finance. تحقق من الرمز أو جرب لاحقاً."
    return render_template_string(TEMPLATE, ticker=ticker, analysis=analysis, error=error)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
