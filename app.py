import os
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

# paste your Discord Webhook URL inside these quotes!
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1533311689133523063/sFnRPV9wvEvbbnIyCUlUe4zCSrk5OhKKJjl0NzBvi-ke_2R5NdcYQUTyy2tmJbciePUn"

# This acts as our internal pricing lookup database
REAL_MARKET_PRICES = {
    "2024 bowman chrome paul skenes rookie autograph #bcp-1": 350.00,
    "2024 topps chrome elly de la cruz rookie card #141 (psa 10)": 95.00,
    "2023 bowman chrome jackson chourio 1st bowman autograph": 160.00,
}

FOUND_DEALS = []

def send_discord_alert(card_name, prebid, market, margin):
    """Sends a formatted notification card directly to your private Discord channel."""
    if not DISCORD_WEBHOOK_URL or "YOUR_DISCORD" in DISCORD_WEBHOOK_URL:
        print("[System Alert] Discord Webhook URL not set up yet.")
        return
        
    payload = {
        "embeds": [{
            "title": "🚨 UNDERPRICED BASEBALL CARD FOUND!",
            "color": 3716592,  # Sleek blue color
            "fields": [
                {"name": "⚾ Card Name", "value": card_name, "inline": False},
                {"name": "💰 Whatnot Pre-bid", "value": f"${prebid:.2f}", "inline": True},
                {"name": "📈 Market Comps", "value": f"${market:.2f}", "inline": True},
                {"name": "🔥 Profit Margin", "value": f"+${margin:.2f}", "inline": True}
            ],
            "footer": {"text": "DiamondScanner Pro 24/7 Engine"}
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
        print(f"[Discord] Sent alert successfully for {card_name}!")
    except Exception as e:
        print(f"[Discord Error] Could not send ping: {e}")

def check_card_deal(scraped_name, scraped_prebid):
    """
    Price Checker Engine: Normalizes text names, compares live pre-bids against 
    market sold comps, and automatically builds deal alerts.
    """
    clean_name = scraped_name.lower().strip()
    
    if clean_name in REAL_MARKET_PRICES:
        market_val = REAL_MARKET_PRICES[clean_name]
        savings = market_val - scraped_prebid
        
        # Flag item as a deal if it is at least $15.00 under true market value
        if savings >= 15.00:
            deal_item = {
                "card_name": scraped_name,
                "prebid_price": scraped_prebid,
                "market_value": market_val,
                "savings": savings
            }
            
            # Avoid sending duplicate entries to the dashboard
            if deal_item not in FOUND_DEALS:
                FOUND_DEALS.append(deal_item)
                send_discord_alert(scraped_name, scraped_prebid, market_val, savings)

# HTML Template custom built for the Live Pricing Engine
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Whatnot Baseball Live Scanner</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #334155; padding-bottom: 20px; margin-bottom: 30px; }
        h1 { color: #38bdf8; margin: 0; font-size: 28px; }
        .status { background-color: #1e293b; padding: 8px 16px; border-radius: 20px; font-size: 14px; display: flex; align-items: center; gap: 8px; border: 1px solid #334155; }
        .pulse { width: 10px; height: 10px; background-color: #38bdf8; border-radius: 50%; box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(56, 189, 248, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); } }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .card { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; transition: transform 0.2s, border-color 0.2s; position: relative; overflow: hidden; }
        .card:hover { transform: translateY(-5px); border-color: #38bdf8; }
        .badge { position: absolute; top: 15px; right: 15px; background-color: #eab308; color: #000; font-weight: bold; padding: 4px 8px; border-radius: 6px; font-size: 11px; text-transform: uppercase; }
        .card-title { font-size: 16px; font-weight: bold; margin-bottom: 15px; padding-right: 65px; color: #ffffff; line-height: 1.4; }
        .price-row { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 15px; }
        .label { color: #94a3b8; }
        .value { font-weight: bold; }
        .prebid { color: #f87171; }
        .market { color: #60a5fa; }
        .profit { font-size: 18px; border-top: 1px dashed #334155; margin-top: 15px; padding-top: 15px; display: flex; justify-content: space-between; color: #34d399; }
        .empty-state { text-align: center; grid-column: 1 / -1; padding: 40px; color: #64748b; font-size: 18px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>DiamondScanner Pro ⚾</h1>
                <p style="color: #94a3b8; margin: 5px 0 0 0;">Engine Engine Hooked to Live Price Verification</p>
            </div>
            <div class="status"><span class="pulse"></span> Engine Active</div>
        </header>

        <div class="grid">
            {% if not deals %}
            <div class="empty-state">No live underpriced items found in this sweep yet. Checking streams...</div>
            {% endif %}
            
            {% for deal in deals %}
            <div class="card">
                <span class="badge">PROFIT FOUND</span>
                <div class="card-title">{{ deal.card_name }}</div>
                <div class="price-row">
                    <span class="label">Whatnot Pre-bid:</span>
                    <span class="value prebid">${{ "%.2f"|format(deal.prebid_price) }}</span>
                </div>
                <div class="price-row">
                    <span class="label">Market Value:</span>
                    <span class="value market">${{ "%.2f"|format(deal.market_value) }}</span>
                </div>
                <div class="profit">
                    <span>Net Margin:</span>
                    <strong>+${{ "%.2f"|format(deal.savings) }}</strong>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    # Simulate a stream data feed picking up an underpriced Paul Skenes rookie card
    check_card_deal("2024 Bowman Chrome Paul Skenes Rookie Autograph #BCP-1", 190.00)
    
    # Simulate picking up an overpriced card (this will be ignored by our price engine)
    check_card_deal("2024 Topps Chrome Elly De La Cruz Rookie Card #141 (PSA 10)", 110.00)
    
    return render_template_string(HTML_DASHBOARD, deals=FOUND_DEALS)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
