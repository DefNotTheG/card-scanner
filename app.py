import os
import time
import requests
import urllib.parse
import threading
import xml.etree.ElementTree as ET
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# System Configurations
DISCORD_WEBHOOK_URL = "https://discord.com"
NOTIFICATIONS_ENABLED = True

# Global Application Filter Settings (Blank = Scan All)
APP_FILTERS = {
    "target_keyword": "",
    "min_profit_margin": 15.00,
    "max_starting_price": 500.00
}

FOUND_DEALS = []

def calculate_ebay_arbitrage(listed_price):
    """Calculates custom eBay fee deductions and sets profit margins."""
    estimated_market_value = listed_price * 1.50
    ebay_fees = (estimated_market_value * 0.1325) + 0.30
    net_profit = estimated_market_value - listed_price - ebay_fees
    return estimated_market_value, net_profit

def send_discord_deal_alert(title, price, market, profit, link, image_url=None):
    """Dispatches a formatted arbitrage ticket with an image attachment to Discord."""
    global NOTIFICATIONS_ENABLED
    if not NOTIFICATIONS_ENABLED:
        return
        
    payload = {
        "embeds": [{
            "title": "🔥 EBAY UNDERPRICED FLIP ALIGNED!",
            "url": link,
            "color": 16738048, # eBay Orange
            "fields": [
                {"name": "📦 Item Description", "value": title, "inline": False},
                {"name": "💰 Listed Buy It Now Price", "value": f"${price:.2f}", "inline": True},
                {"name": "📈 Estimated Market Value", "value": f"${market:.2f}", "inline": True},
                {"name": "💵 Projected Net Profit", "value": f"+${profit:.2f}", "inline": True}
            ],
            "footer": {"text": "DiamondScanner Pro | eBay Arbitrage pipeline"}
        }]
    }
    
    # If eBay provides a thumbnail image, inject it directly into the Discord preview panel
    if image_url:
        payload["embeds"][0]["image"] = {"url": image_url}
        
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception:
        pass

def send_system_startup_ping():
    """Fires a verification alert immediately on launch so you know your webhook is active."""
    payload = {
        "embeds": [{
            "title": "🔌 SCANNER CONNECTION LIVE",
            "description": "Your eBay Arbitrage Cloud Scanner is online and monitoring newly listed feeds 24/7.",
            "color": 2263842
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        print("[System] Verification launch ping dispatched successfully.")
    except Exception:
        pass

def run_ebay_feed_sweep():
    """Parses eBay RSS text nodes for prices and listing thumbnail locations."""
    global FOUND_DEALS
    print("[eBay Engine] Scanning global live listings feed indices...")
    
    search_term = APP_FILTERS["target_keyword"] if APP_FILTERS["target_keyword"] else "baseball cards lot"
    safe_keyword = urllib.parse.quote(search_term)
    feed_url = f"https://ebay.com{safe_keyword}&_rss=1&rt=nc&LH_BIN=1"
    
    try:
        response = requests.get(feed_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if response.status_code != 200:
            return
            
        root = ET.fromstring(response.content)
        
        # Define XML namespaces that eBay uses to hide listing images
        namespaces = {'media': 'http://yahoo.com'}
        
        for item in root.findall(".//item"):
            title = item.find("title").text if item.find("title") is not None else "Unknown Item"
            link = item.find("link").text if item.find("link") is not None else "https://ebay.com"
            description = item.find("description").text if item.find("description") is not None else ""
            
            # Scrape out eBay's media content asset url to pull listing pictures
            media_content = item.find("media:content", namespaces)
            image_url = media_content.get("url") if media_content is not None else None
            
            price = 25.00
            if "Price:" in description:
                try:
                    price_str = description.split("Price:")[1].split()[0].replace("$", "").replace(",", "").strip()
                    price = float(price_str)
                except Exception:
                    continue
            
            if price > APP_FILTERS["max_starting_price"]:
                continue
                
            market_val, net_profit = calculate_ebay_arbitrage(price)
            
            if net_profit < APP_FILTERS["min_profit_margin"]:
                continue
                
            deal_entry = {
                "title": title,
                "price": price,
                "market": market_val,
                "profit": net_profit,
                "link": link,
                "image": image_url
            }
            if not any(d['title'] == title for d in FOUND_DEALS):
                FOUND_DEALS.append(deal_entry)
                send_discord_deal_alert(title, price, market_val, net_profit, link, image_url)
                
    except Exception as e:
        print(f"[eBay Error] Sweep sequence trace halt: {e}")

def continuous_automation_scheduler():
    """Loops background checks every 5 minutes."""
    print("[Automation Thread] eBay 5-Minute Arbitrage Runner Engaged!")
    # Run a test verification ping instantly on server launch
    send_system_startup_ping()
    
    while True:
        try:
            run_ebay_feed_sweep()
        except Exception as e:
            print(f"[Loop Alert] {e}")
        time.sleep(300)

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DiamondScanner eBay Edition</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b0f19; color: #f1f5f9; margin: 0; padding: 25px; }
        .container { max-width: 1100px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #1e293b; padding-bottom: 20px; margin-bottom: 25px; }
        h1 { color: #f59e0b; margin: 0; }
        .control-panel { background-color: #111827; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 30px; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .filter-group { display: flex; flex-direction: column; gap: 5px; }
        label { font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase; }
        input { background-color: #0b0f19; border: 1px solid #1e293b; padding: 10px; border-radius: 6px; color: white; font-size: 14px; }
        .btn { background-color: #f59e0b; color: black; font-weight: bold; border: none; padding: 12px; border-radius: 6px; cursor: pointer; text-align: center; text-decoration: none; }
        
        .btn-toggle-on { background-color: #10b981; color: white; padding: 12px 20px; border-radius: 6px; border: none; font-weight: bold; cursor: pointer; }
        .btn-toggle-off { background-color: #ef4444; color: white; padding: 12px 20px; border-radius: 6px; border: none; font-weight: bold; cursor: pointer; }

        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
        .card { background-color: #111827; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; position: relative; display: flex; flex-direction: column; justify-content: space-between; }
        .badge { position: absolute; top: 15px; right: 15px; background-color: #ef4444; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
        .card-title { font-size: 15px; font-weight: bold; margin-bottom: 15px; color: #ffffff; padding-right: 75px; line-height: 1.4; }
        .price-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }
        .profit-row { font-size: 16px; border-top: 1px dashed #1e293b; margin-top: 12px; padding-top: 12px; display: flex; justify-content: space-between; color: #10b981; }
        .empty { text-align: center; grid-column: 1/-1; color: #4b5563; padding: 40px; font-size: 16px; }
        .card-img { width: 100%; height: 160px; object-fit: cover; border-radius: 6px; margin-bottom: 15px; background-color: #0b0f19; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>DiamondScanner Pro: eBay Edition 🛒</h1>
                <p style="color: #64748b; margin: 5px 0 0 0;">Sweeping Live eBay Feeds for High Margin Misprices</p>
            </div>
            <form action="/toggle-notifs" method="POST">
                {% if notifs %}
                    <button type="submit" class="btn btn-toggle-on">🟢 Alerts: ON</button>
                {% else %}
                    <button type="submit" class="btn btn-toggle-off">🔴 Alerts: OFF</button>
                {% endif %}
            </form>
        </header>

        <form class="control-panel" action="/set-filters" method="POST">
            <div class="filter-group">
                <label>Ebay Search Term</label>
                <input type="text" name="keyword" placeholder="e.g. baseball cards lot" value="{{ filters.target_keyword }}">
            </div>
            <div class="filter-group">
                <label>Target Profit Margin Limit ($)</label>
                <input type="number" step="0.01" name="margin" placeholder="15.00" value="{{ filters.min_profit_margin }}">
            </div>
            <div class="filter-group">
                <label>Max Buy It Now Price Budget ($)</label>
            <div class="filter-group" style="justify-content: flex-end;">
                <button type="submit" class="btn">Lock Search Filters</button>
            </div>
        </form>

        <div class="grid">
            {% if not deals %}
            <div class="empty">Scanning eBay indices for fresh mispriced items matching your target profit. Standby...</div>
            {% endif %}
            {% for deal in deals %}
            <div class="card">
                <div>
                    {% if deal.image %}
                        <img src="{{ deal.image }}" class="card-img" alt="Product Image">
                    {% endif %}
                    <span class="badge">EBAY BIN</span>
                    <div class="card-title">{{ deal.title }}</div>
                    <div class="price-row"><span>Listed Price:</span><span style="color:#f87171; font-weight:bold;">${{ "%.2f"|format(deal.price) }}</span></div>
                    <div class="price-row"><span>Est. Comp Value:</span><span style="color:#60a5fa; font-weight:bold;">${{ "%.2f"|format(deal.market) }}</span></div>
                </div>
                <div>
                    <div class="profit-row"><span>Net Resale Profit:</span><strong>+${{ "%.2f"|format(deal.profit) }}</strong></div>
                    <a href="{{ deal.link }}" target="_blank" class="btn" style="display:block; margin-top:15px; font-size:13px; padding:8px;">View Item on eBay</a>
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
    return render_template_string(HTML_DASHBOARD, deals=FOUND_DEALS, filters=APP_FILTERS, notifs=NOTIFICATIONS_ENABLED)

@app.route('/set-filters', methods=['POST'])
def set_filters():
    global APP_FILTERS, FOUND_DEALS
    APP_FILTERS["target_keyword"] = request.form.get("keyword", "").strip()
    APP_FILTERS["min_profit_margin"] = float(request.form.get("margin") or 0.0)
    APP_FILTERS["max_starting_price"] = float(request.form.get("budget") or 99999.0)
    FOUND_DEALS = []
    return redirect(url_for('dashboard'))

@app.route('/toggle-notifs', methods=['POST'])
def toggle_notifs():
    global NOTIFICATIONS_ENABLED
    NOTIFICATIONS_ENABLED = not NOTIFICATIONS_ENABLED
    return redirect(url_for('dashboard'))

threading.Thread(target=continuous_automation_scheduler, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
