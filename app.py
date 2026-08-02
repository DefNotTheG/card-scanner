import os
import time
import requests
from flask import Flask, render_template_string
from playwright.sync_api import sync_playwright

app = Flask(__name__)

# Paste your actual Discord Webhook URL inside these quotes
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"

# Target Whatnot Stream URL (Change this to any live baseball stream link)
TARGET_STREAM_URL = "https://whatnot.com"

# Internal target price sheet for checking card deals
REAL_MARKET_PRICES = {
    "2024 bowman chrome paul skenes rookie autograph #bcp-1": 350.00,
    "2024 topps chrome elly de la cruz rookie card #141 (psa 10)": 95.00,
    "2023 bowman chrome jackson chourio 1st bowman autograph": 160.00,
}

FOUND_DEALS = []

def send_discord_alert(card_name, prebid, market, margin):
    """Sends a notification card to your private Discord channel."""
    if not DISCORD_WEBHOOK_URL or "YOUR_DISCORD" in DISCORD_WEBHOOK_URL:
        return
    payload = {
        "embeds": [{
            "title": "🚨 UNDERPRICED BASEBALL CARD FOUND!",
            "color": 3716592,
            "fields": [
                {"name": "⚾ Card Name", "value": card_name, "inline": False},
                {"name": "💰 Whatnot Pre-bid", "value": f"${prebid:.2f}", "inline": True},
                {"name": "📈 Market Comps", "value": f"${market:.2f}", "inline": True},
                {"name": "🔥 Profit Margin", "value": f"+${margin:.2f}", "inline": True}
            ],
            "footer": {"text": "DiamondScanner Pro Live Feed"}
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception:
        pass

def check_card_deal(scraped_name, scraped_prebid):
    """Compares scraped card prices against market sold values."""
    clean_name = scraped_name.lower().strip()
    if clean_name in REAL_MARKET_PRICES:
        market_val = REAL_MARKET_PRICES[clean_name]
        savings = market_val - scraped_prebid
        
        # Save deal if it's at least $15 under market value
        if savings >= 15.00:
            deal_item = {
                "card_name": scraped_name,
                "prebid_price": scraped_prebid,
                "market_value": market_val,
                "savings": savings
            }
            if deal_item not in FOUND_DEALS:
                FOUND_DEALS.append(deal_item)
                send_discord_alert(scraped_name, scraped_prebid, market_val, savings)

def scrape_whatnot_live(url):
    """
    Connects to the real live stream page, opens the pre-bids tab, 
    and reads the raw card data out of the text elements.
    """
    print(f"[Scanner] Connecting to live stream room: {url}")
    try:
        with sync_playwright() as p:
            # Launch automated browser engine
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Go to the stream link
            page.goto(url, wait_until="networkidle")
            time.sleep(5)  # Allow live sockets to connect
            
            # Look for Whatnot's item custom layout containers
            items = page.query_selector_all("[class*='PrebidCard'] , [class*='ProductRow']")
            
            for item in items:
                try:
                    # Extract the raw title text and raw pre-bid text fields
                    title_el = item.query_selector("[class*='Title'] , [class*='Name']")
                    price_el = item.query_selector("[class*='Price'] , [class*='Bid']")
                    
                    if title_el and price_el:
                        card_name = title_el.inner_text()
                        # Clean pricing formatting ($150.00 -> 150.00)
                        price_text = price_el.inner_text().replace("$", "").replace(",", "").strip()
                        prebid_price = float(price_text)
                        
                        # Process item through verification calculation logic
                        check_card_deal(card_name, prebid_price)
                except Exception:
                    continue
                    
            browser.close()
    except Exception as e:
        print(f"[Scanner Error] Could not read elements: {e}")

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Whatnot Baseball Live Scanner</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #334155; padding-bottom: 20px; margin-bottom: 30px; }
        h1 { color: #38bdf8; margin: 0; }
        .status { background-color: #1e293b; padding: 8px 16px; border-radius: 20px; font-size: 14px; display: flex; align-items: center; gap: 8px; border: 1px solid #334155; }
        .pulse { width: 10px; height: 10px; background-color: #38bdf8; border-radius: 50%; box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(56, 189, 248, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); } }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .card { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; position: relative; }
        .badge { position: absolute; top: 15px; right: 15px; background-color: #eab308; color: #000; font-weight: bold; padding: 4px 8px; border-radius: 6px; font-size: 11px; }
        .card-title { font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #ffffff; }
        .price-row { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .prebid { color: #f87171; font-weight: bold; }
        .market { color: #60a5fa; font-weight: bold; }
        .profit { font-size: 18px; border-top: 1px dashed #334155; margin-top: 15px; padding-top: 15px; display: flex; justify-content: space-between; color: #34d399; }
        .empty-state { text-align: center; grid-column: 1 / -1; padding: 40px; color: #64748b; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>DiamondScanner Pro ⚾</h1>
                <p style="color: #94a3b8; margin: 5px 0 0 0;">Connected to Live Data Feeds</p>
            </div>
            <div class="status"><span class="pulse"></span> Live Stream Active</div>
        </header>
        <div class="grid">
            {% if not deals %}
            <div class="empty-state">No live underpriced items found in this sweep yet. Scanning pre-bids...</div>
            {% endif %}
            {% for deal in deals %}
            <div class="card">
                <span class="badge">PROFIT FOUND</span>
                <div class="card-title">{{ deal.card_name }}</div>
                <div class="price-row"><span>Whatnot Pre-bid:</span><span class="prebid">${{ "%.2f"|format(deal.prebid_price) }}</span></div>
                <div class="price-row"><span>Market Value:</span><span class="market">${{ "%.2f"|format(deal.market_value) }}</span></div>
                <div class="profit"><span>Net Margin:</span><strong>+${{ "%.2f"|format(deal.savings) }}</strong></div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    scrape_whatnot_live(TARGET_STREAM_URL)
    return render_template_string(HTML_DASHBOARD, deals=FOUND_DEALS)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
