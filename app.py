from flask import Flask, request, render_template_string
import yfinance as yf
import time

app = Flask(__name__)

# كاش: { "TICKER": (price, timestamp) }
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
    :root{
      --bg-dark1:#0f172a;
      --bg-dark2:#0b1220;
      --card-bg:#111827;
      --text-light:#e5e7eb;
      --muted:#9ca3af;
      --border:#374151;
      --support:#86efac;
      --resistance:#fda4af;
    }
    body{
      background: radial-gradient(circle at top left, rgba(79,70,229,.15), transparent 40%),
                  radial-gradient(circle at top right, rgba(34,211,238,.12), transparent 40%),
                  linear-gradient(180deg, var(--bg-dark1), var(--bg-dark2));
      min-height:100vh;
      color: var(--text-light);
      display:flex;
      flex-direction:column;
    }
    .card{background-color:var(--card-bg); border:1px solid var(--border);}
    footer{
      margin-top:auto; background-color:var(--bg-dark1);
      color:var(--muted); text-align:center; padding:10px; border-top:1px solid var(--border);
    }
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

  {% if result %}
  <div class="card mt-4">
    <div class="card-header">
      {{ result.ticker_display }} - آخر سعر: {{ "{:,.2f}".format(result.price) }}
    </div>
    <div class="card-body">
      <ul class="list-group">
        <li class="list-group-item d-flex justify-content-between">
          <span class="support">الدعم 1 (-4%)</span>
          <span class="support">{{ "{:,.2f}".format(result.support1) }}</span>
        </li>
        <li class="list-group-item d-flex justify-content-between">
          <span class="support">الدعم 2 (-7%)</span>
          <span class="support">{{ "{:,.2f}".format(result.support2) }}</span>
        </li>
        <li class="list-group-item d-flex justify-content-between">
          <span class="resistance">المقاومة 1 (+4%)</span>
          <span class="resistance">{{ "{:,.2f}".format(result.resistance1) }}</span>
        </li>
        <li class="list-group-item d-flex justify-content-between">
          <span class="resistance">المقاومة 2 (+7%)</span>
          <span class="resistance">{{ "{:,.2f}".format(result.resistance2) }}</span>
        </li>
      </ul>
    </div>
  </div>
  {% endif %}
</div>

<footer>
  <div>لا تنسى الصلاة على النبي ﷺ</div>
  <div>Made with ❤️ by AHMED GAMAL</div>
</footer>
</body>
</html>
"""

def get_price(ticker: str):
    """جلب السعر مع الكاش"""
    original_ticker = ticker
    if ticker.isdigit():  # سهم سعودي
        ticker += ".SR"

    now = time.time()
    if ticker in CACHE:
        price, ts = CACHE[ticker]
        if now - ts < CACHE_TTL:
            return price, ticker  # من الكاش

    try:
        data = yf.download(ticker, period="5d", progress=False)
        if not data.empty:
            price = float(data["Close"].dropna().iloc[-1])
            CACHE[ticker] = (price, now)
            return price, ticker
    except Exception:
        pass
    return None, ticker

def compute_levels(price: float):
    return {
        "support1": round(price * 0.96, 2),
        "support2": round(price * 0.93, 2),
        "resistance1": round(price * 1.04, 2),
        "resistance2": round(price * 1.07, 2)
    }

@app.route("/", methods=["GET", "POST"])
def index():
    ticker = ""
    result = None
    error = None
    if request.method == "POST":
        ticker = (request.form.get("ticker") or "").strip().upper()
        if ticker:
            price, display_symbol = get_price(ticker)
            if price:
                levels = compute_levels(price)
                result = {
                    "ticker_display": display_symbol,
                    "price": price,
                    **levels
                }
            else:
                error = "تعذر جلب البيانات من Yahoo Finance. تحقق من الرمز أو جرب لاحقاً."
    return render_template_string(TEMPLATE, ticker=ticker, result=result, error=error)

if __name__ == "__main__":
    app.run(debug=True)
