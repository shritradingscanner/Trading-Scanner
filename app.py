import streamlit as st
import pytz
import requests
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
import time
import hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
import io
import feedparser

st.set_page_config(
    page_title="AI Trading Scanner Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

KEEP_ALIVE_JS = """
<script>
(function() {
    var pingCount = 0;
    function keepAlive() {
        pingCount++;
        try {
            var xhr = new XMLHttpRequest();
            xhr.open('HEAD', window.location.href, true);
            xhr.send();
        } catch(e) {}
    }
    setInterval(keepAlive, 25000);

    try {
        if ('wakeLock' in navigator) {
            navigator.wakeLock.request('screen').catch(function(){});
        }
    } catch(e) {}

    window.addEventListener('online', function() {
        setTimeout(function() { window.location.reload(); }, 2000);
    });
})();
</script>
"""

CYBER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500&display=swap');

* { box-sizing: border-box; }

.stApp {
    background: #060912 !important;
    background-image:
        radial-gradient(ellipse at 15% 50%, rgba(0,255,136,0.04) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 20%, rgba(88,166,255,0.04) 0%, transparent 55%),
        radial-gradient(ellipse at 50% 90%, rgba(187,134,252,0.02) 0%, transparent 50%) !important;
    font-family: 'Exo 2', sans-serif !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,
        rgba(6,9,18,0.99) 0%,
        rgba(8,12,22,0.98) 100%) !important;
    border-right: 1px solid rgba(0,255,136,0.12) !important;
}

.main .block-container {
    background: transparent !important;
    padding: 1.2rem 2rem !important;
    max-width: 100% !important;
}

/* Expanders */
div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(0,255,136,0.12) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(12px) !important;
    margin-bottom: 10px !important;
    transition: all 0.25s ease !important;
    overflow: hidden !important;
}

div[data-testid="stExpander"]:hover {
    border-color: rgba(0,255,136,0.35) !important;
    background: rgba(0,255,136,0.04) !important;
    box-shadow: 0 4px 20px rgba(0,255,136,0.08) !important;
}

/* Metrics - smoother look */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg,
        rgba(255,255,255,0.04) 0%,
        rgba(255,255,255,0.02) 100%) !important;
    border: 1px solid rgba(0,255,136,0.12) !important;
    border-radius: 14px !important;
    padding: 16px !important;
    transition: all 0.25s ease !important;
    backdrop-filter: blur(8px) !important;
}

div[data-testid="stMetric"]:hover {
    border-color: rgba(0,255,136,0.3) !important;
    box-shadow: 0 4px 16px rgba(0,255,136,0.1) !important;
    transform: translateY(-1px) !important;
}

div[data-testid="stMetricValue"] {
    color: #00FF88 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500 !important;
    font-size: 1.6em !important;
    letter-spacing: 0.5px !important;
}

div[data-testid="stMetricLabel"] {
    color: #6B7A8D !important;
    font-family: 'Exo 2', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.8em !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}

div[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82em !important;
}

/* Buttons */
div[data-testid="stButton"] button {
    background: linear-gradient(135deg,
        rgba(0,255,136,0.08) 0%,
        rgba(0,200,100,0.12) 100%) !important;
    border: 1px solid rgba(0,255,136,0.35) !important;
    color: #00FF88 !important;
    border-radius: 10px !important;
    font-family: 'Exo 2', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88em !important;
    letter-spacing: 0.5px !important;
    transition: all 0.2s ease !important;
    backdrop-filter: blur(8px) !important;
}

div[data-testid="stButton"] button:hover {
    background: linear-gradient(135deg,
        rgba(0,255,136,0.2) 0%,
        rgba(0,200,100,0.28) 100%) !important;
    border-color: #00FF88 !important;
    box-shadow:
        0 0 16px rgba(0,255,136,0.3),
        0 4px 12px rgba(0,0,0,0.3) !important;
    transform: translateY(-1px) !important;
    color: #FFFFFF !important;
}

div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg,
        rgba(0,255,136,0.22) 0%,
        rgba(0,180,90,0.35) 100%) !important;
    border-color: rgba(0,255,136,0.7) !important;
    box-shadow: 0 0 12px rgba(0,255,136,0.2) !important;
    color: #FFFFFF !important;
}

div[data-testid="stButton"] button[kind="primary"]:hover {
    box-shadow:
        0 0 24px rgba(0,255,136,0.45),
        0 6px 20px rgba(0,0,0,0.4) !important;
}

/* Inputs */
div[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(0,255,136,0.18) !important;
    border-radius: 10px !important;
    color: #E6EDF3 !important;
    font-family: 'Exo 2', sans-serif !important;
    font-size: 0.9em !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stTextInput"] input:focus {
    border-color: rgba(0,255,136,0.6) !important;
    box-shadow: 0 0 0 2px rgba(0,255,136,0.12) !important;
}

/* Number input */
div[data-testid="stNumberInput"] input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(0,255,136,0.18) !important;
    border-radius: 10px !important;
    color: #E6EDF3 !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Selectbox */
div[data-testid="stSelectbox"] > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(0,255,136,0.18) !important;
    border-radius: 10px !important;
    color: #E6EDF3 !important;
}

/* Radio */
div[data-testid="stRadio"] label {
    color: #6B7A8D !important;
    font-family: 'Exo 2', sans-serif !important;
    font-size: 0.88em !important;
    transition: color 0.15s ease !important;
}

div[data-testid="stRadio"] label:hover {
    color: #00FF88 !important;
}

/* Divider */
hr { border-color: rgba(0,255,136,0.1) !important; }

/* Tabs */
div[data-testid="stTabs"] button {
    color: #6B7A8D !important;
    font-family: 'Exo 2', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88em !important;
    letter-spacing: 0.3px !important;
}

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #00FF88 !important;
    border-bottom: 2px solid #00FF88 !important;
}

/* Progress */
div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg,
        #00CC66, #00FF88) !important;
    border-radius: 10px !important;
    box-shadow: 0 0 8px rgba(0,255,136,0.4) !important;
}

div[data-testid="stProgress"] > div {
    background: rgba(255,255,255,0.06) !important;
    border-radius: 10px !important;
}

/* Toggle */
div[data-testid="stToggle"] label {
    color: #8B949E !important;
    font-family: 'Exo 2', sans-serif !important;
    font-size: 0.9em !important;
}

/* Alerts */
div[data-testid="stAlert"] {
    border-radius: 12px !important;
    backdrop-filter: blur(8px) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,0.15); }
::-webkit-scrollbar-thumb {
    background: rgba(0,255,136,0.25);
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(0,255,136,0.45);
}

/* Typography */
h1, h2, h3 {
    font-family: 'Orbitron', monospace !important;
    letter-spacing: 1px !important;
}

p, span, div {
    font-family: 'Exo 2', sans-serif !important;
}

code, pre {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Cyber title */
.cyber-title {
    font-family: 'Orbitron', monospace !important;
    color: #00FF88 !important;
    font-weight: 700 !important;
    text-shadow:
        0 0 8px rgba(0,255,136,0.4),
        0 0 16px rgba(0,255,136,0.2) !important;
    letter-spacing: 1.5px !important;
}

/* Smooth number display */
.metric-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.4em;
    font-weight: 500;
    color: #00FF88;
    letter-spacing: 0.5px;
}

.stat-card {
    background: linear-gradient(135deg,
        rgba(0,255,136,0.06) 0%,
        rgba(0,255,136,0.02) 100%);
    border: 1px solid rgba(0,255,136,0.15);
    border-radius: 14px;
    padding: 16px 20px;
    backdrop-filter: blur(10px);
    transition: all 0.25s ease;
}

.stat-card:hover {
    border-color: rgba(0,255,136,0.35);
    box-shadow: 0 4px 20px rgba(0,255,136,0.1);
}

.signal-card-high {
    background: linear-gradient(135deg,
        rgba(0,255,136,0.06) 0%,
        rgba(0,200,100,0.03) 100%);
    border-left: 3px solid #00FF88;
    border-radius: 0 12px 12px 0;
    padding: 12px 16px;
    margin-bottom: 8px;
    animation: slideIn 0.3s ease;
}

.signal-card-medium {
    background: linear-gradient(135deg,
        rgba(240,180,41,0.06) 0%,
        rgba(240,180,41,0.02) 100%);
    border-left: 3px solid #F0B429;
    border-radius: 0 12px 12px 0;
    padding: 12px 16px;
    margin-bottom: 8px;
}

.warning-box {
    background: linear-gradient(135deg,
        rgba(255,170,0,0.08) 0%,
        rgba(255,170,0,0.04) 100%);
    border: 1px solid rgba(255,170,0,0.25);
    border-radius: 12px;
    padding: 14px 18px;
    font-family: 'Exo 2', sans-serif;
    color: #C8960A;
    font-size: 0.88em;
    line-height: 1.6;
}

.info-box {
    background: linear-gradient(135deg,
        rgba(88,166,255,0.08) 0%,
        rgba(88,166,255,0.04) 100%);
    border: 1px solid rgba(88,166,255,0.2);
    border-radius: 12px;
    padding: 14px 18px;
    font-family: 'Exo 2', sans-serif;
    color: #58A6FF;
    font-size: 0.88em;
    line-height: 1.6;
}

.success-box {
    background: linear-gradient(135deg,
        rgba(0,255,136,0.08) 0%,
        rgba(0,200,100,0.04) 100%);
    border: 1px solid rgba(0,255,136,0.2);
    border-radius: 12px;
    padding: 14px 18px;
    font-family: 'Exo 2', sans-serif;
    color: #00C070;
    font-size: 0.88em;
    line-height: 1.6;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-10px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.active-pulse {
    animation: pulse 2s ease-in-out infinite;
}
</style>
"""

IST = pytz.timezone('Asia/Kolkata')

ALL_PAIRS = [
    "XAUUSD","USDJPY","AUDCAD",
    "GBPJPY","GBPUSD","EURUSD",
    "EURJPY","US30","NAS100"
]

PAIR_SETTINGS = {
    "XAUUSD": {"sl_pips": 15, "tp_mult": 2.0, "atr_mult": 0.8, "min_score": 82},
    "USDJPY": {"sl_pips": 8,  "tp_mult": 2.0, "atr_mult": 0.6, "min_score": 80},
    "AUDCAD": {"sl_pips": 8,  "tp_mult": 2.0, "atr_mult": 0.6, "min_score": 80},
    "GBPJPY": {"sl_pips": 12, "tp_mult": 2.0, "atr_mult": 0.7, "min_score": 80},
    "GBPUSD": {"sl_pips": 8,  "tp_mult": 2.0, "atr_mult": 0.6, "min_score": 80},
    "EURUSD": {"sl_pips": 7,  "tp_mult": 2.0, "atr_mult": 0.6, "min_score": 80},
    "EURJPY": {"sl_pips": 10, "tp_mult": 2.0, "atr_mult": 0.7, "min_score": 80},
    "US30":   {"sl_pips": 30, "tp_mult": 2.0, "atr_mult": 1.0, "min_score": 83},
    "NAS100": {"sl_pips": 25, "tp_mult": 2.0, "atr_mult": 1.0, "min_score": 83},
}

LOT_RISK_PERCENT = 0.01

def calculate_lot_size(account_size, symbol, sl_pips):
    try:
        risk_amount = account_size * LOT_RISK_PERCENT
        if symbol == "XAUUSD":
            pip_value_per_lot = 10.0
            max_lots = 0.02
        elif symbol in ["US30", "NAS100"]:
            pip_value_per_lot = 1.0
            max_lots = 0.05
        elif "JPY" in symbol:
            pip_value_per_lot = 1000.0
            max_lots = 1.0
        else:
            pip_value_per_lot = 10.0
            max_lots = 1.0
        lot_size = risk_amount / (sl_pips * pip_value_per_lot)
        lot_size = round(min(lot_size, max_lots), 2)
        lot_size = max(lot_size, 0.01)
        return lot_size
    except Exception:
        return 0.01

def get_pip_value(symbol):
    if symbol == "XAUUSD":
        return 0.1
    elif symbol in ["US30","NAS100"]:
        return 1.0
    elif "JPY" in symbol:
        return 0.01
    return 0.0001

def get_ist_time():
    return datetime.now(IST)

def get_current_session():
    hour = get_ist_time().hour
    if 4 <= hour <= 11:
        return "Asia"
    elif 12 <= hour <= 16:
        return "London"
    elif 17 <= hour <= 20:
        return "London + NY Overlap"
    elif 21 <= hour <= 24 or hour == 0:
        return "New York"
    return "Off Session"

def get_session_quality():
    session = get_current_session()
    if session == "London + NY Overlap":
        return "BEST", session
    elif session in ["London","New York"]:
        return "GOOD", session
    elif session == "Asia":
        return "MODERATE", session
    return "POOR", session

def is_good_session():
    quality, _ = get_session_quality()
    return quality != "POOR"

def init_supabase():
    try:
        from supabase import create_client
        return create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"])
    except Exception:
        return None

def login_user(email, password):
    try:
        supabase = init_supabase()
        if not supabase:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            return True, "Logged in!"
        response = supabase.auth.sign_in_with_password({
            "email": email, "password": password})
        if response.user:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.user_id = response.user.id
            return True, "Login successful!"
        return False, "Invalid email or password!"
    except Exception:
        st.session_state.logged_in = True
        st.session_state.user_email = email
        return True, "Logged in!"

def signup_user(email, password):
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "DB failed!"
        response = supabase.auth.sign_up({
            "email": email, "password": password})
        if response.user:
            return True, "Account created! Check email!"
        return False, "Signup failed!"
    except Exception as e:
        return False, str(e)

def logout_user():
    try:
        supabase = init_supabase()
        if supabase:
            supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.scanner_running = False

def reset_password(email):
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "DB failed!"
        supabase.auth.reset_password_email(email)
        return True, "Reset email sent!"
    except Exception as e:
        return False, str(e)

def send_discord_alert(message):
    try:
        webhook_url = st.secrets["DISCORD_WEBHOOK"]
        response = requests.post(webhook_url,
            json={"content": message}, timeout=10)
        return response.status_code == 204
    except Exception:
        return False

def send_discord_alert_with_image(message, image_bytes):
    try:
        webhook_url = st.secrets["DISCORD_WEBHOOK"]
        response = requests.post(webhook_url,
            data={"content": message},
            files={"file": ("chart.png",
                image_bytes, "image/png")},
            timeout=15)
        return response.status_code == 204
    except Exception:
        return False

def get_signal_id(signal):
    key = (signal['pair'] + signal['direction'] +
        str(round(signal['entry'], 2)))
    return hashlib.md5(key.encode()).hexdigest()[:8]

def get_signal_age(signal_time_str):
    try:
        signal_time = IST.localize(datetime.strptime(
            signal_time_str, '%d %b %Y %H:%M IST'))
        return int((get_ist_time() -
            signal_time).total_seconds() / 60)
    except Exception:
        return 0

def get_signal_status(age_minutes):
    if age_minutes < 5:
        return "🟢 FRESH"
    elif age_minutes < 15:
        return "🟡 VALID"
    elif age_minutes < 30:
        return "🟠 AGING"
    return "🔴 EXPIRED"

def fetch_forex_news():
    news_items = []
    feeds = [
        {"url":"https://www.forexlive.com/feed/news","source":"ForexLive"},
        {"url":"https://feeds.reuters.com/reuters/businessNews","source":"Reuters"},
        {"url":"https://www.marketwatch.com/rss/topstories","source":"MarketWatch"}
    ]
    for feed_info in feeds:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:5]:
                title = entry.get("title","")
                summary = entry.get("summary","")
                impact = get_news_impact(title+" "+summary)
                news_items.append({
                    "title": title,
                    "link": entry.get("link",""),
                    "published": entry.get("published",""),
                    "source": feed_info["source"],
                    "impact": impact,
                    "summary": summary[:200]
                })
        except Exception:
            pass
    news_items.sort(key=lambda x: x['impact'], reverse=True)
    return news_items[:30]

def get_news_impact(text):
    text_lower = text.lower()
    high = ["nfp","non-farm payroll","fomc","federal reserve",
            "cpi","inflation","interest rate","rate decision",
            "gdp","ecb","bank of england","boe","powell",
            "lagarde","recession","crisis","emergency"]
    medium = ["pmi","retail sales","trade balance",
              "housing","manufacturing","employment","wages"]
    for k in high:
        if k in text_lower:
            return 3
    for k in medium:
        if k in text_lower:
            return 2
    return 1

def get_economic_calendar():
    return [
        {"time":"Today 6:00 PM IST","event":"US Initial Jobless Claims",
         "impact":"Medium","currency":"USD","forecast":"220K","previous":"215K"},
        {"time":"Today 8:30 PM IST","event":"US Non-Farm Payrolls",
         "impact":"High","currency":"USD","forecast":"185K","previous":"175K"},
        {"time":"Tomorrow 2:30 PM IST","event":"ECB Interest Rate Decision",
         "impact":"High","currency":"EUR","forecast":"4.25%","previous":"4.50%"},
        {"time":"Friday 6:00 PM IST","event":"US CPI Monthly",
         "impact":"High","currency":"USD","forecast":"0.3%","previous":"0.4%"}
    ]

TICKER_MAP = {
    "XAUUSD":"GC=F","USDJPY":"JPY=X","AUDCAD":"AUDCAD=X",
    "GBPJPY":"GBPJPY=X","GBPUSD":"GBPUSD=X","EURUSD":"EURUSD=X",
    "EURJPY":"EURJPY=X","US30":"YM=F","NAS100":"NQ=F"
}
TWELVE_MAP = {
    "XAUUSD":"XAU/USD","USDJPY":"USD/JPY","AUDCAD":"AUD/CAD",
    "GBPJPY":"GBP/JPY","GBPUSD":"GBP/USD","EURUSD":"EUR/USD",
    "EURJPY":"EUR/JPY","US30":"US30/USD","NAS100":"IXIC"
}

def get_data_twelvedata(symbol, interval="5min"):
    try:
        api_key = st.secrets["TWELVEDATA_KEY"]
        url = (
            "https://api.twelvedata.com/time_series?"
            "symbol="+TWELVE_MAP.get(symbol,symbol)+
            "&interval="+interval+
            "&outputsize=200&apikey="+api_key)
        response = requests.get(url, timeout=10)
        data = response.json()
        if "values" not in data:
            return None
        df = pd.DataFrame(data["values"])
        df = df.rename(columns={"open":"Open","high":"High",
            "low":"Low","close":"Close","volume":"Volume"})
        for col in ['Open','High','Low','Close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.iloc[::-1].reset_index(drop=True)
    except Exception:
        return None

def get_data_yfinance(symbol, interval="5m"):
    try:
        df = yf.download(TICKER_MAP.get(symbol,symbol),
            interval=interval, period="5d", progress=False)
        if df is not None and len(df) > 10:
            df.columns = ['Open','High','Low','Close','Volume']
            return df.reset_index(drop=True)
        return None
    except Exception:
        return None

def get_data(symbol, interval="5m"):
    interval_map = {"5m":"5min","15m":"15min","1h":"1h","4h":"4h"}
    df = get_data_twelvedata(symbol, interval_map.get(interval,"5min"))
    if df is not None and len(df) > 20:
        return df
    return get_data_yfinance(symbol, interval)

def calculate_ema(df, period):
    return df['Close'].ewm(span=period, adjust=False).mean()

def calculate_rsi(df, period=14):
    try:
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()
        rs = avg_gain / avg_loss
        return float((100-(100/(1+rs))).iloc[-1])
    except Exception:
        return 50

def calculate_atr(df, period=14):
    try:
        high = df['High']
        low = df['Low']
        close = df['Close'].shift(1)
        tr = pd.concat([
            high-low,
            (high-close).abs(),
            (low-close).abs()
        ], axis=1).max(axis=1)
        return float(tr.ewm(span=period,adjust=False).mean().iloc[-1])
    except Exception:
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        return float(np.mean(highs[-14:]-lows[-14:]))

def calculate_adx(df, period=14):
    try:
        high = df['High'].values.astype(float)
        low = df['Low'].values.astype(float)
        close = df['Close'].values.astype(float)
        plus_dm, minus_dm, tr_vals = [], [], []
        for i in range(1, len(high)):
            up = high[i]-high[i-1]
            down = low[i-1]-low[i]
            plus_dm.append(up if up > down and up > 0 else 0)
            minus_dm.append(down if down > up and down > 0 else 0)
            tr_vals.append(max(high[i]-low[i],
                abs(high[i]-close[i-1]),
                abs(low[i]-close[i-1])))
        plus_dm = np.array(plus_dm)
        minus_dm = np.array(minus_dm)
        tr_vals = np.array(tr_vals)
        atr_s = pd.Series(tr_vals).ewm(span=period,adjust=False).mean().values
        plus_di = 100*pd.Series(plus_dm).ewm(span=period,adjust=False).mean().values/(atr_s+1e-10)
        minus_di = 100*pd.Series(minus_dm).ewm(span=period,adjust=False).mean().values/(atr_s+1e-10)
        dx = 100*np.abs(plus_di-minus_di)/(plus_di+minus_di+1e-10)
        adx = pd.Series(dx).ewm(span=period,adjust=False).mean().values
        return float(adx[-1]), float(plus_di[-1]), float(minus_di[-1])
    except Exception:
        return 25.0, 25.0, 25.0

def detect_swing_highs_lows(df, lookback=5):
    try:
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        swing_highs, swing_lows = [], []
        for i in range(lookback, len(highs)-lookback):
            if all(highs[i]>=highs[i-j] for j in range(1,lookback+1)) and \
               all(highs[i]>=highs[i+j] for j in range(1,lookback+1)):
                swing_highs.append((i, highs[i]))
            if all(lows[i]<=lows[i-j] for j in range(1,lookback+1)) and \
               all(lows[i]<=lows[i+j] for j in range(1,lookback+1)):
                swing_lows.append((i, lows[i]))
        return swing_highs, swing_lows
    except Exception:
        return [], []

def detect_amd_phase(df):
    """
    AMD = Accumulation, Manipulation, Distribution
    ICT concept:
    1. Accumulation: Price consolidates in a range (smart money loads positions)
    2. Manipulation: Price fakes out (stop hunt) one direction
    3. Distribution: Price moves strongly opposite direction (real move)
    We detect: range -> false breakout -> reversal entry
    """
    try:
        closes = df['Close'].values.astype(float)
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)

        recent_highs = highs[-30:]
        recent_lows = lows[-30:]
        range_high = float(np.max(recent_highs[-20:-5]))
        range_low = float(np.min(recent_lows[-20:-5]))
        range_size = range_high - range_low

        if range_size == 0:
            return None, None, 0

        recent_close = float(closes[-1])
        recent_high = float(highs[-1])
        recent_low = float(lows[-1])
        prev_close = float(closes[-2])
        prev_high = float(highs[-2])
        prev_low = float(lows[-2])

        atr = float(np.mean(highs[-14:]-lows[-14:]))
        range_atr_ratio = range_size / (atr + 1e-10)

        if range_atr_ratio < 2.0:
            return None, None, 0

        range_threshold = range_size * 0.15

        bullish_manipulation = (
            prev_low < range_low - range_threshold and
            recent_close > range_low and
            recent_close > prev_close
        )

        bearish_manipulation = (
            prev_high > range_high + range_threshold and
            recent_close < range_high and
            recent_close < prev_close
        )

        if bullish_manipulation:
            manipulation_strength = (range_low - prev_low) / range_size
            return "BULLISH", "BUY", round(min(manipulation_strength * 100, 30), 1)
        elif bearish_manipulation:
            manipulation_strength = (prev_high - range_high) / range_size
            return "BEARISH", "SELL", round(min(manipulation_strength * 100, 30), 1)

        return None, None, 0
    except Exception:
        return None, None, 0

def detect_bos_advanced(df):
    try:
        swing_highs, swing_lows = detect_swing_highs_lows(df)
        if not swing_highs or not swing_lows:
            return False, False, 0, 0
        cc = float(df['Close'].values[-1])
        lsh = swing_highs[-1][1]
        lsl = swing_lows[-1][1]
        return cc > lsh, cc < lsl, lsh, lsl
    except Exception:
        return False, False, 0, 0

def detect_fvg_advanced(df):
    try:
        bull_fvg = bear_fvg = False
        fvg_zones = []
        candles = df.tail(30)
        for i in range(2, len(candles)-1):
            c1h = float(candles['High'].iloc[i-2])
            c1l = float(candles['Low'].iloc[i-2])
            c3h = float(candles['High'].iloc[i])
            c3l = float(candles['Low'].iloc[i])
            if c3l > c1h:
                gap = c3l-c1h
                bull_fvg = True
                fvg_zones.append({'type':'bullish',
                    'top':c3l,'bottom':c1h,'mid':(c3l+c1h)/2,
                    'index':len(df)-len(candles)+i,'size':gap})
            if c3h < c1l:
                gap = c1l-c3h
                bear_fvg = True
                fvg_zones.append({'type':'bearish',
                    'top':c1l,'bottom':c3h,'mid':(c1l+c3h)/2,
                    'index':len(df)-len(candles)+i,'size':gap})
        fvg_zones.sort(key=lambda x: x['size'], reverse=True)
        return bull_fvg, bear_fvg, fvg_zones[:3]
    except Exception:
        return False, False, []

def detect_order_block_advanced(df, direction):
    try:
        closes = df['Close'].values.astype(float)
        opens = df['Open'].values.astype(float)
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        ob_found = False
        ob_top = ob_bottom = ob_index = 0
        ob_strength = 0
        for i in range(3, min(40, len(df)-2)):
            if direction == "BUY":
                is_bear = closes[-i] < opens[-i]
                next_bull = closes[-i+1] > opens[-i+1]
                strong = (closes[-i+1]-opens[-i+1]) > abs(closes[-i]-opens[-i])*0.5
                if is_bear and next_bull and strong:
                    s = (closes[-i+1]-opens[-i+1])/(opens[-i]+1e-10)*100
                    if s > ob_strength:
                        ob_strength = s
                        ob_top = opens[-i]
                        ob_bottom = lows[-i]
                        ob_index = len(df)-i
                        ob_found = True
            else:
                is_bull = closes[-i] > opens[-i]
                next_bear = closes[-i+1] < opens[-i+1]
                strong = abs(closes[-i+1]-opens[-i+1]) > (closes[-i]-opens[-i])*0.5
                if is_bull and next_bear and strong:
                    s = abs(closes[-i+1]-opens[-i+1])/(opens[-i]+1e-10)*100
                    if s > ob_strength:
                        ob_strength = s
                        ob_top = highs[-i]
                        ob_bottom = opens[-i]
                        ob_index = len(df)-i
                        ob_found = True
        return ob_found, ob_top, ob_bottom, ob_index
    except Exception:
        return False, 0, 0, 0

def detect_liquidity_sweep_advanced(df):
    try:
        swing_highs, swing_lows = detect_swing_highs_lows(df, lookback=3)
        if not swing_highs or not swing_lows:
            return False, False
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        closes = df['Close'].values.astype(float)
        rh = swing_highs[-1][1]
        rl = swing_lows[-1][1]
        bull_sweep = (lows[-1]<rl and closes[-1]>rl and
            closes[-1]>(lows[-1]+highs[-1])/2)
        bear_sweep = (highs[-1]>rh and closes[-1]<rh and
            closes[-1]<(lows[-1]+highs[-1])/2)
        return bull_sweep, bear_sweep
    except Exception:
        return False, False

def detect_choch_advanced(df):
    try:
        swing_highs, swing_lows = detect_swing_highs_lows(df, lookback=5)
        if len(swing_highs)<2 or len(swing_lows)<2:
            return False, False
        bull_choch = (swing_highs[-1][1]<swing_highs[-2][1] and
                     swing_lows[-1][1]>swing_lows[-2][1])
        bear_choch = (swing_highs[-1][1]>swing_highs[-2][1] and
                     swing_lows[-1][1]<swing_lows[-2][1])
        return bull_choch, bear_choch
    except Exception:
        return False, False

def detect_candle_pattern(df):
    try:
        o = float(df['Open'].iloc[-1])
        h = float(df['High'].iloc[-1])
        l = float(df['Low'].iloc[-1])
        c = float(df['Close'].iloc[-1])
        body = abs(c-o)
        upper = h-max(o,c)
        lower = min(o,c)-l
        total = h-l
        if total == 0:
            return "Doji","NEUTRAL"
        if body/total < 0.1:
            return "Doji","NEUTRAL"
        if c > o and lower > body*2:
            return "Hammer","BULLISH"
        if c < o and upper > body*2:
            return "Shooting Star","BEARISH"
        if c > o and body/total > 0.7:
            return "Bullish Marubozu","BULLISH"
        if c < o and body/total > 0.7:
            return "Bearish Marubozu","BEARISH"
        prev_o = float(df['Open'].iloc[-2])
        prev_c = float(df['Close'].iloc[-2])
        if prev_c < prev_o and c > prev_o and o < prev_c:
            return "Bullish Engulfing","BULLISH"
        if prev_c > prev_o and c < prev_o and o > prev_c:
            return "Bearish Engulfing","BEARISH"
        return "Normal","NEUTRAL"
    except Exception:
        return "Unknown","NEUTRAL"

def get_htf_bias_advanced(symbol):
    try:
        df_4h = get_data(symbol, interval="4h")
        df_1h = get_data(symbol, interval="1h")
        scores = {"BULLISH":0,"BEARISH":0}
        for df, weight in [(df_4h,2),(df_1h,1)]:
            if df is None or len(df)<50:
                continue
            ema20 = float(calculate_ema(df,20).iloc[-1])
            ema50 = float(calculate_ema(df,50).iloc[-1])
            current = float(df['Close'].iloc[-1])
            if current > ema20 and ema20 > ema50:
                scores["BULLISH"] += weight
            elif current < ema20 and ema20 < ema50:
                scores["BEARISH"] += weight
        if scores["BULLISH"] > scores["BEARISH"]:
            return "BULLISH"
        elif scores["BEARISH"] > scores["BULLISH"]:
            return "BEARISH"
        return "NEUTRAL"
    except Exception:
        return "NEUTRAL"

def detect_market_regime_advanced(df):
    try:
        closes = df['Close'].values.astype(float)
        adx, plus_di, minus_di = calculate_adx(df)
        atr = calculate_atr(df)
        pr = float(max(closes[-20:])-min(closes[-20:]))
        if adx > 25 and plus_di > minus_di:
            return "TRENDING UP", adx
        elif adx > 25 and minus_di > plus_di:
            return "TRENDING DOWN", adx
        elif adx < 20:
            return "RANGING", adx
        elif pr > atr*4:
            return "VOLATILE", adx
        return "NEUTRAL", adx
    except Exception:
        return "UNKNOWN", 0

def is_price_in_pd_zone(df, direction):
    try:
        swing_highs, swing_lows = detect_swing_highs_lows(df, lookback=10)
        if not swing_highs or not swing_lows:
            return True
        rh = swing_highs[-1][1]
        rl = swing_lows[-1][1]
        current = float(df['Close'].iloc[-1])
        r = rh-rl
        if r == 0:
            return True
        pos = (current-rl)/r
        return (direction=="BUY" and pos < 0.45) or \
               (direction=="SELL" and pos > 0.55)
    except Exception:
        return True

def calculate_scalping_sl_tp(symbol, direction, close, atr, swing_highs, swing_lows):
    settings = PAIR_SETTINGS.get(symbol, {"sl_pips":10,"tp_mult":2.0,"atr_mult":0.7})
    pip_value = get_pip_value(symbol)
    max_sl_price = settings['sl_pips'] * pip_value
    atr_sl = atr * settings['atr_mult']
    sl_distance = min(atr_sl, max_sl_price)
    sl_distance = max(sl_distance, max_sl_price * 0.5)
    if direction == "BUY":
        if swing_lows:
            recent_low = min([sl[1] for sl in swing_lows[-2:]])
            structure_sl = recent_low - (pip_value * 2)
            sl = structure_sl if close - structure_sl <= max_sl_price * 1.5 else close - sl_distance
        else:
            sl = close - sl_distance
        tp = close + (abs(close-sl) * settings['tp_mult'])
    else:
        if swing_highs:
            recent_high = max([sh[1] for sh in swing_highs[-2:]])
            structure_sl = recent_high + (pip_value * 2)
            sl = structure_sl if structure_sl - close <= max_sl_price * 1.5 else close + sl_distance
        else:
            sl = close + sl_distance
        tp = close - (abs(sl-close) * settings['tp_mult'])
    sl_pips = round(abs(close-sl) / pip_value, 1)
    tp_pips = round(abs(tp-close) / pip_value, 1)
    return round(sl,5), round(tp,5), sl_pips, tp_pips

def analyze_pair_advanced(symbol):
    try:
        if not is_good_session():
            return None
        df_5m = get_data(symbol, interval="5m")
        if df_5m is None or len(df_5m) < 60:
            return None

        score = 0
        reasons = []
        neg = []
        confluences = 0

        session_quality, session_name = get_session_quality()
        htf_bias = get_htf_bias_advanced(symbol)
        regime, adx_val = detect_market_regime_advanced(df_5m)
        rsi = calculate_rsi(df_5m)
        atr = calculate_atr(df_5m)
        adx, plus_di, minus_di = calculate_adx(df_5m)
        candle_pattern, candle_dir = detect_candle_pattern(df_5m)

        bull_bos, bear_bos, sh_level, sl_level = detect_bos_advanced(df_5m)
        bull_fvg, bear_fvg, fvg_zones = detect_fvg_advanced(df_5m)
        bull_sweep, bear_sweep = detect_liquidity_sweep_advanced(df_5m)
        bull_choch, bear_choch = detect_choch_advanced(df_5m)
        swing_highs, swing_lows = detect_swing_highs_lows(df_5m)

        amd_phase, amd_direction, amd_score = detect_amd_phase(df_5m)

        close = float(df_5m['Close'].iloc[-1])
        ema8 = float(calculate_ema(df_5m,8).iloc[-1])
        ema21 = float(calculate_ema(df_5m,21).iloc[-1])
        ema50 = float(calculate_ema(df_5m,50).iloc[-1])

        is_bull = bull_bos or bull_fvg or bull_sweep or bull_choch or candle_dir=="BULLISH"
        is_bear = bear_bos or bear_fvg or bear_sweep or bear_choch or candle_dir=="BEARISH"

        if amd_direction == "BUY":
            is_bull = True
        elif amd_direction == "SELL":
            is_bear = True

        if is_bull and not is_bear:
            direction = "BUY"
        elif is_bear and not is_bull:
            direction = "SELL"
        elif is_bull and is_bear:
            if htf_bias == "BULLISH":
                direction = "BUY"
            elif htf_bias == "BEARISH":
                direction = "SELL"
            else:
                return None
        else:
            return None

        ob_found, ob_top, ob_bottom, ob_index = detect_order_block_advanced(df_5m, direction)
        in_pd = is_price_in_pd_zone(df_5m, direction)

        if htf_bias == "BULLISH" and direction == "BUY":
            score += 20; reasons.append("HTF Bullish Bias"); confluences += 1
        elif htf_bias == "BEARISH" and direction == "SELL":
            score += 20; reasons.append("HTF Bearish Bias"); confluences += 1
        elif htf_bias == "NEUTRAL":
            score += 3; neg.append("HTF Neutral")
        else:
            score -= 15; neg.append("HTF Conflict")

        if adx > 25:
            if direction=="BUY" and plus_di>minus_di:
                score += 15
                reasons.append("Strong Uptrend ADX:"+str(round(adx,1)))
                confluences += 1
            elif direction=="SELL" and minus_di>plus_di:
                score += 15
                reasons.append("Strong Downtrend ADX:"+str(round(adx,1)))
                confluences += 1
        elif adx < 15:
            score -= 10; neg.append("Weak Trend ADX<15")

        if regime == "VOLATILE":
            score -= 20; neg.append("High Volatility — SKIP!")
        elif regime == "RANGING" and adx < 20:
            score -= 10; neg.append("Ranging Market")
        elif (regime=="TRENDING UP" and direction=="BUY") or \
             (regime=="TRENDING DOWN" and direction=="SELL"):
            score += 10; reasons.append("Trend Alignment"); confluences += 1

        if amd_direction and amd_direction == direction:
            score += amd_score
            reasons.append("AMD Manipulation Detected ⚡")
            confluences += 1
        elif amd_direction and amd_direction != direction:
            score -= 15
            neg.append("AMD Conflict")

        if bull_bos and direction=="BUY":
            score += 18; reasons.append("Bullish BOS"); confluences += 1
        if bear_bos and direction=="SELL":
            score += 18; reasons.append("Bearish BOS"); confluences += 1
        if bull_fvg and direction=="BUY":
            score += 15; reasons.append("Bullish FVG"); confluences += 1
        if bear_fvg and direction=="SELL":
            score += 15; reasons.append("Bearish FVG"); confluences += 1
        if bull_sweep and direction=="BUY":
            score += 18; reasons.append("Bullish Liq Sweep"); confluences += 1
        if bear_sweep and direction=="SELL":
            score += 18; reasons.append("Bearish Liq Sweep"); confluences += 1
        if bull_choch and direction=="BUY":
            score += 12; reasons.append("Bullish CHOCH"); confluences += 1
        if bear_choch and direction=="SELL":
            score += 12; reasons.append("Bearish CHOCH"); confluences += 1
        if ob_found:
            score += 12; reasons.append("Order Block"); confluences += 1
        if in_pd:
            score += 10; reasons.append("P/D Zone"); confluences += 1

        if direction=="BUY":
            if ema8 > ema21 > ema50:
                score += 8; reasons.append("EMA Stack Bullish"); confluences += 1
            elif ema8 < ema21:
                score -= 5; neg.append("EMA Conflict")
        else:
            if ema8 < ema21 < ema50:
                score += 8; reasons.append("EMA Stack Bearish"); confluences += 1
            elif ema8 > ema21:
                score -= 5; neg.append("EMA Conflict")

        if direction=="BUY":
            if 20 < rsi < 55:
                score += 8; reasons.append("RSI Bullish Zone")
            elif rsi >= 70:
                score -= 15; neg.append("RSI Overbought")
        else:
            if 45 < rsi < 80:
                score += 8; reasons.append("RSI Bearish Zone")
            elif rsi <= 30:
                score -= 15; neg.append("RSI Oversold")

        if (candle_dir=="BULLISH" and direction=="BUY") or \
           (candle_dir=="BEARISH" and direction=="SELL"):
            score += 8; reasons.append(candle_pattern)
        elif candle_dir != "NEUTRAL":
            if (candle_dir=="BEARISH" and direction=="BUY") or \
               (candle_dir=="BULLISH" and direction=="SELL"):
                score -= 10; neg.append("Opposing Pattern")

        if session_quality == "BEST":
            score += 10; reasons.append("Best Session ⭐⭐⭐")
        elif session_quality == "GOOD":
            score += 5; reasons.append(session_name)
        elif session_quality == "MODERATE":
            neg.append("Asia Session")

        news = st.session_state.get('cached_news', [])
        if [n for n in news if n['impact']==3]:
            score -= 25; neg.append("⚠️ HIGH IMPACT NEWS!")

        if confluences < 4:
            return None

        score = min(max(score,0), 95)

        min_score = PAIR_SETTINGS.get(symbol,{}).get('min_score', 80)
        if score < min_score:
            return None

        sl, tp, sl_pips, tp_pips = calculate_scalping_sl_tp(
            symbol, direction, close, atr, swing_highs, swing_lows)

        rr = round(tp_pips / sl_pips, 1) if sl_pips > 0 else 2.0

        account_size = st.session_state.get('account_size', 10000)
        suggested_lots = calculate_lot_size(account_size, symbol, sl_pips)

        return {
            "pair": symbol,
            "direction": direction,
            "score": score,
            "entry": round(close,5),
            "sl": sl, "tp": tp,
            "rr": rr,
            "sl_pips": sl_pips,
            "tp_pips": tp_pips,
            "rsi": round(rsi,1),
            "adx": round(adx,1),
            "htf_bias": htf_bias,
            "regime": regime,
            "session": session_name,
            "session_quality": session_quality,
            "confluences": confluences,
            "reasons": reasons,
            "negative": neg,
            "candle_pattern": candle_pattern,
            "suggested_lots": suggested_lots,
            "account_size": account_size,
            "amd_phase": amd_phase,
            "time": get_ist_time().strftime('%d %b %Y %H:%M IST'),
            "current_price": round(close,5),
            "atr": round(atr,5),
            "result": "Pending",
            "df": df_5m,
            "fvg_zones": fvg_zones,
            "ob_found": ob_found,
            "ob_top": ob_top,
            "ob_bottom": ob_bottom,
            "ob_index": ob_index,
            "bull_bos": bull_bos,
            "bear_bos": bear_bos,
            "bull_sweep": bull_sweep,
            "bear_sweep": bear_sweep,
            "swing_highs": swing_highs,
            "swing_lows": swing_lows,
            "swing_high_level": sh_level,
            "swing_low_level": sl_level
        }
    except Exception:
        return None

def check_signal_outcomes():
    try:
        journal = st.session_state.trade_journal
        pending = [j for j in journal if j['result']=="Pending"]
        if not pending:
            return
        for trade in pending:
            try:
                age = get_signal_age(trade['time'])
                if age > 120:
                    for j in st.session_state.trade_journal:
                        if j['id'] == trade['id']:
                            j['result'] = "Expired"
                    continue
                df = get_data(trade['pair'], interval="5m")
                if df is None:
                    continue
                ch = float(df['High'].iloc[-1])
                cl = float(df['Low'].iloc[-1])
                if trade['direction'] == "BUY":
                    if ch >= trade['tp']:
                        for j in st.session_state.trade_journal:
                            if j['id'] == trade['id']:
                                j['result'] = "TP Hit"; j['pnl'] = trade['rr']
                        send_discord_alert(
                            "✅ **TP HIT — TRADE WON!** 🎯\n\n"
                            "**"+trade['pair']+" BUY**\n"
                            "Entry: "+str(trade['entry'])+" → TP: "+str(trade['tp'])+"\n"
                            "SL: "+str(trade.get('sl_pips','?'))+"p | "
                            "TP: "+str(trade.get('tp_pips','?'))+"p | "
                            "RR: 1:"+str(trade['rr'])+"\n"
                            "Lots: "+str(trade.get('suggested_lots','?'))+"\n"
                            "⏰ "+get_ist_time().strftime('%H:%M IST'))
                    elif cl <= trade['sl']:
                        for j in st.session_state.trade_journal:
                            if j['id'] == trade['id']:
                                j['result'] = "SL Hit"; j['pnl'] = -1
                        send_discord_alert(
                            "❌ **SL HIT — TRADE LOST**\n\n"
                            "**"+trade['pair']+" BUY**\n"
                            "Entry: "+str(trade['entry'])+" → SL: "+str(trade['sl'])+"\n"
                            "Loss: "+str(trade.get('sl_pips','?'))+" pips\n"
                            "⏰ "+get_ist_time().strftime('%H:%M IST'))
                else:
                    if cl <= trade['tp']:
                        for j in st.session_state.trade_journal:
                            if j['id'] == trade['id']:
                                j['result'] = "TP Hit"; j['pnl'] = trade['rr']
                        send_discord_alert(
                            "✅ **TP HIT — TRADE WON!** 🎯\n\n"
                            "**"+trade['pair']+" SELL**\n"
                            "Entry: "+str(trade['entry'])+" → TP: "+str(trade['tp'])+"\n"
                            "RR: 1:"+str(trade['rr'])+"\n"
                            "⏰ "+get_ist_time().strftime('%H:%M IST'))
                    elif ch >= trade['sl']:
                        for j in st.session_state.trade_journal:
                            if j['id'] == trade['id']:
                                j['result'] = "SL Hit"; j['pnl'] = -1
                        send_discord_alert(
                            "❌ **SL HIT — TRADE LOST**\n\n"
                            "**"+trade['pair']+" SELL**\n"
                            "Entry: "+str(trade['entry'])+" → SL: "+str(trade['sl'])+"\n"
                            "⏰ "+get_ist_time().strftime('%H:%M IST'))
            except Exception:
                pass
    except Exception:
        pass

def format_discord_message(signal):
    grade = ("A+" if signal['score']>=90 else
             "A" if signal['score']>=85 else
             "B+" if signal['score']>=80 else "B")
    emoji = "🟢 BUY" if signal['direction']=="BUY" else "🔴 SELL"
    reasons_text = "\n".join(["✅ "+r for r in signal['reasons']])
    neg_text = "\n".join(["⚠️ "+n for n in signal['negative']]) if signal['negative'] else ""
    sq = signal.get('session_quality','GOOD')
    sq_s = "⭐⭐⭐" if sq=="BEST" else "⭐⭐" if sq=="GOOD" else "⭐"
    sl_pips = signal.get('sl_pips','?')
    tp_pips = signal.get('tp_pips','?')
    lots = signal.get('suggested_lots','0.01')
    acc = signal.get('account_size',10000)
    amd = signal.get('amd_phase')
    amd_line = f"\n⚡ AMD: {amd} Phase Manipulation Detected!" if amd else ""

    msg = (
        "🚨 **HIGH CONFIDENCE SCALP SIGNAL** 🚨\n\n"
        "**"+emoji+" "+signal['pair']+"**"+amd_line+"\n\n"
        "📊 Score: **"+str(signal['score'])+"%** | Grade: **"+grade+"**\n"
        "🔗 Confluences: "+str(signal['confluences'])+"\n"
        "📐 Pattern: "+signal.get('candle_pattern','N/A')+"\n"
        "📉 ADX: "+str(signal.get('adx','N/A'))+" | RSI: "+str(signal['rsi'])+"\n"
        "🕐 Session: "+signal['session']+" "+sq_s+"\n\n"
        "━━━ TRADE SETUP ━━━\n"
        "💰 Entry: **"+str(signal['entry'])+"**\n"
        "🛑 Stop Loss: **"+str(signal['sl'])+"** ("+str(sl_pips)+" pips)\n"
        "🎯 Take Profit: **"+str(signal['tp'])+"** ("+str(tp_pips)+" pips)\n"
        "⚖️ Risk/Reward: **1:"+str(signal['rr'])+"**\n\n"
        "💼 Account: $"+str(f"{acc:,.0f}")+"\n"
        "📦 Suggested Lots: **"+str(lots)+"** (1% risk)\n"
        "📈 HTF Bias: "+signal['htf_bias']+"\n"
        "🌍 Market: "+signal['regime']+"\n\n"
        "⏰ Signal Time: "+signal['time']+"\n"
        "🤖 Auto TP/SL tracking: ACTIVE\n\n"
        "⚠️ Skip if price moved >"+str(signal['atr'])+" from entry!\n"
        "⚠️ Check news BEFORE entering!\n\n"
        "✅ **Confluences:**\n"+reasons_text+"\n")
    if neg_text:
        msg += "\n⚠️ **Caution:**\n"+neg_text+"\n"
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━"
    return msg

def generate_professional_chart(df, signal, fvg_zones,
    ob_found, ob_top, ob_bottom, ob_index,
    bull_bos, bear_bos, swing_highs, swing_lows,
    bull_sweep, bear_sweep, candle_pattern):
    try:
        BG = '#0D1117'; BG2 = '#161B22'
        GREEN = '#26A69A'; RED = '#EF5350'
        WHITE = '#E6EDF3'; GRAY = '#8B949E'
        YELLOW = '#F0B429'; PURPLE = '#BB86FC'; BLUE = '#58A6FF'

        fig = plt.figure(figsize=(20, 14), facecolor=BG)
        gs = gridspec.GridSpec(5, 1,
            height_ratios=[4, 0.8, 1, 1, 0.6],
            hspace=0.02, figure=fig)

        ax_main = fig.add_subplot(gs[0])
        ax_vol = fig.add_subplot(gs[1], sharex=ax_main)
        ax_rsi = fig.add_subplot(gs[2], sharex=ax_main)
        ax_macd = fig.add_subplot(gs[3], sharex=ax_main)
        ax_info = fig.add_subplot(gs[4])

        for ax in [ax_main,ax_vol,ax_rsi,ax_macd,ax_info]:
            ax.set_facecolor(BG)
            for spine in ax.spines.values():
                spine.set_color('#21262D')

        display_df = df.tail(80).reset_index(drop=True)
        n = len(display_df)

        ema8 = display_df['Close'].ewm(span=8,adjust=False).mean()
        ema21 = display_df['Close'].ewm(span=21,adjust=False).mean()
        ema50 = display_df['Close'].ewm(span=50,adjust=False).mean()

        ax_main.plot(range(n), ema8, color=YELLOW, linewidth=0.8, alpha=0.7, label='EMA8')
        ax_main.plot(range(n), ema21, color=BLUE, linewidth=0.8, alpha=0.7, label='EMA21')
        ax_main.plot(range(n), ema50, color=PURPLE, linewidth=0.8, alpha=0.7, label='EMA50')

        for i in range(n):
            o = float(display_df['Open'].iloc[i])
            h = float(display_df['High'].iloc[i])
            l = float(display_df['Low'].iloc[i])
            c = float(display_df['Close'].iloc[i])
            is_bull = c >= o
            body_color = GREEN if is_bull else RED
            wick_color = '#2EBD8E' if is_bull else '#F23645'
            ax_main.plot([i,i],[l,h], color=wick_color, linewidth=0.7, alpha=0.9, zorder=3)
            rect = patches.FancyBboxPatch(
                (i-0.38, min(o,c)), 0.76, max(abs(c-o), 0.0001),
                boxstyle="round,pad=0.0001",
                linewidth=0.3, edgecolor=wick_color,
                facecolor=body_color, alpha=0.92, zorder=4)
            ax_main.add_patch(rect)

        for fvg in fvg_zones:
            try:
                fx = fvg.get('index',n-5)-(len(df)-n)
                if 0 <= fx < n:
                    is_bull_fvg = fvg['type']=='bullish'
                    fc = '#26A69A18' if is_bull_fvg else '#EF535018'
                    fb = GREEN if is_bull_fvg else RED
                    ax_main.add_patch(patches.Rectangle(
                        (fx,fvg['bottom']), n-fx, fvg['top']-fvg['bottom'],
                        linewidth=1, edgecolor=fb, facecolor=fc, alpha=1, zorder=1))
                    ax_main.text(fx+0.5, fvg['mid'],
                        'FVG+' if is_bull_fvg else 'FVG-',
                        color=fb, fontsize=7, fontweight='bold', va='center',
                        fontfamily='monospace',
                        bbox=dict(boxstyle='round,pad=0.15', facecolor=BG2, edgecolor=fb, alpha=0.9))
            except Exception:
                pass

        if ob_found:
            ox = ob_index-(len(df)-n)
            if 0 <= ox < n:
                is_buy = signal['direction']=='BUY'
                ob_color = GREEN if is_buy else RED
                ax_main.add_patch(patches.Rectangle(
                    (ox,ob_bottom), n-ox, ob_top-ob_bottom,
                    linewidth=1.5, edgecolor=ob_color,
                    facecolor=('#26A69A18' if is_buy else '#EF535018'),
                    linestyle='--', zorder=1))
                ax_main.text(ox+0.5, (ob_top+ob_bottom)/2, 'OB',
                    color=ob_color, fontsize=8, fontweight='bold', va='center',
                    fontfamily='monospace',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor=BG2, edgecolor=ob_color, alpha=0.9))

        for idx, h_val in swing_highs[-8:]:
            plot_idx = idx-(len(df)-n)
            if 0 <= plot_idx < n:
                ax_main.plot(plot_idx, h_val, 'v', color='#F85149', markersize=5, zorder=5)
                ax_main.text(plot_idx, h_val+h_val*0.001, 'SH',
                    color='#F85149', fontsize=6, ha='center', fontfamily='monospace', fontweight='bold')

        for idx, l_val in swing_lows[-8:]:
            plot_idx = idx-(len(df)-n)
            if 0 <= plot_idx < n:
                ax_main.plot(plot_idx, l_val, '^', color='#3FB950', markersize=5, zorder=5)
                ax_main.text(plot_idx, l_val-l_val*0.001, 'SL',
                    color='#3FB950', fontsize=6, ha='center', fontfamily='monospace', fontweight='bold')

        if bull_bos:
            sh_level = signal.get('swing_high_level', signal['entry'])
            ax_main.axhline(y=sh_level, color=GREEN, linewidth=0.8, linestyle=':', alpha=0.5)
            ax_main.text(5, sh_level, '▲ BOS', color=GREEN, fontsize=6.5, fontweight='bold',
                fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.2', facecolor=BG2, edgecolor=GREEN, alpha=0.8))
        if bear_bos:
            sl_level = signal.get('swing_low_level', signal['entry'])
            ax_main.axhline(y=sl_level, color=RED, linewidth=0.8, linestyle=':', alpha=0.5)
            ax_main.text(5, sl_level, '▼ BOS', color=RED, fontsize=6.5, fontweight='bold',
                fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.2', facecolor=BG2, edgecolor=RED, alpha=0.8))

        if bull_sweep:
            ax_main.text(n//3, float(display_df['Low'].iloc[-5]),
                '⚡ LIQ SWEEP ▲', color=GREEN, fontsize=7, fontweight='bold',
                fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.25', facecolor=BG2, edgecolor=GREEN, alpha=0.9))
        if bear_sweep:
            ax_main.text(n//3, float(display_df['High'].iloc[-5]),
                '⚡ LIQ SWEEP ▼', color=RED, fontsize=7, fontweight='bold',
                fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.25', facecolor=BG2, edgecolor=RED, alpha=0.9))

        entry = signal['entry']
        sl = signal['sl']
        tp = signal['tp']
        is_buy = signal['direction'] == "BUY"
        price_range = abs(tp-sl)
        off = price_range*0.015
        sl_pips = signal.get('sl_pips','?')
        tp_pips = signal.get('tp_pips','?')
        lots = signal.get('suggested_lots','?')

        if is_buy:
            ax_main.fill_between(range(n), entry, tp, alpha=0.08, color=GREEN, zorder=0)
            ax_main.fill_between(range(n), sl, entry, alpha=0.08, color=RED, zorder=0)
        else:
            ax_main.fill_between(range(n), tp, entry, alpha=0.08, color=GREEN, zorder=0)
            ax_main.fill_between(range(n), entry, sl, alpha=0.08, color=RED, zorder=0)

        for level, color, label, pos in [
            (entry, WHITE, f'ENTRY  {entry}', 'bottom'),
            (sl, RED, f'SL  {sl}  ({sl_pips}p)', 'top'),
            (tp, GREEN, f'TP  {tp}  ({tp_pips}p)', 'bottom')
        ]:
            ax_main.axhline(y=level, color=color, linewidth=1.5,
                linestyle='-' if level==entry else '--', alpha=0.9, zorder=5)
            ypos = level+off if pos=='bottom' else level-off
            ax_main.text(n*0.98, ypos, label, color=color,
                fontsize=8.5, fontweight='bold', ha='right', va=pos,
                fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=BG2, edgecolor=color, alpha=0.92))

        ax_main.text(n*0.05, (entry+tp)/2,
            f'⚖ RR  1:{signal["rr"]}',
            color=YELLOW, fontsize=10, fontweight='bold', va='center',
            fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=BG2, edgecolor=YELLOW, alpha=0.9, linewidth=1.5))

        grade = ("A+" if signal['score']>=90 else "A" if signal['score']>=85 else "B+" if signal['score']>=80 else "B")
        dir_arrow = '▲ LONG' if is_buy else '▼ SHORT'
        sq_s = "⭐⭐⭐" if signal.get('session_quality')=="BEST" else "⭐⭐" if signal.get('session_quality')=="GOOD" else "⭐"
        amd_str = f" | AMD:{signal.get('amd_phase','N/A')}" if signal.get('amd_phase') else ""

        ax_main.set_title(
            f"{signal['pair']}  |  {dir_arrow}  |  Score: {signal['score']}%  |  Grade: {grade}"
            f"  |  HTF: {signal['htf_bias']}  |  ADX: {signal.get('adx','?')}"
            f"  |  Session: {signal['session']} {sq_s}{amd_str}"
            f"  |  Lots: {lots}",
            color=WHITE, fontsize=10, fontweight='bold', pad=12,
            fontfamily='monospace', loc='left')

        ax_main.legend(loc='upper left', fontsize=7, facecolor=BG2, edgecolor='#21262D', labelcolor=GRAY)
        ax_main.tick_params(colors=GRAY, labelsize=7)
        ax_main.yaxis.tick_right()
        ax_main.grid(axis='y', color='#21262D', linewidth=0.3, alpha=0.7)
        ax_main.grid(axis='x', color='#21262D', linewidth=0.2, alpha=0.3)
        ax_main.set_xlim(-1, n+3)
        plt.setp(ax_main.get_xticklabels(), visible=False)

        try:
            vol_colors, vols = [], []
            for i in range(n):
                o_v = float(display_df['Open'].iloc[i])
                c_v = float(display_df['Close'].iloc[i])
                vol_colors.append(GREEN if c_v>=o_v else RED)
                try:
                    v = float(display_df['Volume'].iloc[i])
                    vols.append(v if not np.isnan(v) else 0)
                except Exception:
                    vols.append(0)
            if any(v > 0 for v in vols):
                ax_vol.bar(range(n), vols, color=vol_colors, alpha=0.5, width=0.8)
                ax_vol.plot(range(n), pd.Series(vols).rolling(20).mean(),
                    color=YELLOW, linewidth=0.8, alpha=0.7)
        except Exception:
            pass
        ax_vol.set_ylabel('VOL', color=GRAY, fontsize=7, fontfamily='monospace')
        ax_vol.tick_params(colors=GRAY, labelsize=6)
        ax_vol.grid(axis='y', color='#21262D', linewidth=0.2, alpha=0.5)
        plt.setp(ax_vol.get_xticklabels(), visible=False)

        try:
            close_s = display_df['Close']
            delta = close_s.diff()
            gain = delta.where(delta>0,0)
            loss = -delta.where(delta<0,0)
            rsi_s = 100-(100/(1+gain.ewm(span=14,adjust=False).mean()/loss.ewm(span=14,adjust=False).mean()))
            rsi_v = rsi_s.values
            ax_rsi.plot(range(n), rsi_v, color=PURPLE, linewidth=1.2, zorder=3)
            ax_rsi.fill_between(range(n), rsi_v, 50, where=[v>50 for v in rsi_v], alpha=0.1, color=GREEN)
            ax_rsi.fill_between(range(n), rsi_v, 50, where=[v<50 for v in rsi_v], alpha=0.1, color=RED)
            ax_rsi.axhline(y=70, color=RED, linewidth=0.5, linestyle='--', alpha=0.5)
            ax_rsi.axhline(y=50, color=GRAY, linewidth=0.4, linestyle='--', alpha=0.3)
            ax_rsi.axhline(y=30, color=GREEN, linewidth=0.5, linestyle='--', alpha=0.5)
            ax_rsi.set_ylim(0,100)
            ax_rsi.set_yticks([30,50,70])
            crsi = rsi_v[-1] if len(rsi_v)>0 else 50
            rc = RED if crsi>70 else GREEN if crsi<30 else PURPLE
            ax_rsi.text(n-1, crsi, f' {crsi:.0f}', color=rc, fontsize=8, fontweight='bold', va='center')
        except Exception:
            pass
        ax_rsi.set_ylabel('RSI', color=GRAY, fontsize=7, fontfamily='monospace')
        ax_rsi.tick_params(colors=GRAY, labelsize=6)
        ax_rsi.grid(axis='y', color='#21262D', linewidth=0.2, alpha=0.5)
        plt.setp(ax_rsi.get_xticklabels(), visible=False)

        try:
            close_s = display_df['Close']
            ema12 = close_s.ewm(span=12,adjust=False).mean()
            ema26 = close_s.ewm(span=26,adjust=False).mean()
            macd_line = ema12-ema26
            signal_line = macd_line.ewm(span=9,adjust=False).mean()
            hist = macd_line-signal_line
            hist_v = hist.values
            ax_macd.bar(range(n), hist_v,
                color=[GREEN if v>=0 else RED for v in hist_v], alpha=0.6, width=0.8)
            ax_macd.plot(range(n), macd_line.values, color=BLUE, linewidth=0.9)
            ax_macd.plot(range(n), signal_line.values, color=YELLOW, linewidth=0.9)
            ax_macd.axhline(y=0, color=GRAY, linewidth=0.4, alpha=0.3)
        except Exception:
            pass
        ax_macd.set_ylabel('MACD', color=GRAY, fontsize=7, fontfamily='monospace')
        ax_macd.tick_params(colors=GRAY, labelsize=6)
        ax_macd.grid(axis='y', color='#21262D', linewidth=0.2, alpha=0.5)
        plt.setp(ax_macd.get_xticklabels(), visible=False)

        ax_info.axis('off')
        info1 = (f"  ENTRY: {signal['entry']}    SL: {signal['sl']} ({sl_pips}p)    "
                 f"TP: {signal['tp']} ({tp_pips}p)    RR: 1:{signal['rr']}    "
                 f"RSI: {signal['rsi']}    ADX: {signal.get('adx','?')}    "
                 f"Pattern: {candle_pattern}    Lots: {lots}  ")
        info2 = "  ✅  " + "   ✅  ".join(signal['reasons'][:5]) + "  "

        ax_info.text(0, 0.75, info1, color=GRAY, fontsize=8, ha='left', va='center',
            fontfamily='monospace', transform=ax_info.transAxes,
            bbox=dict(boxstyle='round,pad=0.4', facecolor=BG2, edgecolor='#21262D', alpha=0.9))
        ax_info.text(0, 0.2, info2, color=GREEN, fontsize=8, ha='left', va='center',
            fontfamily='monospace', transform=ax_info.transAxes,
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#0D2818', edgecolor=GREEN, alpha=0.9))

        neg_str = ("   ⚠️  ".join(signal['negative'][:2]) if signal.get('negative') else "")
        if neg_str:
            ax_info.text(0.65, 0.2, "  ⚠️  "+neg_str+"  ", color=YELLOW, fontsize=7.5,
                ha='left', va='center', fontfamily='monospace', transform=ax_info.transAxes,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#1A1500', edgecolor=YELLOW, alpha=0.9))

        fig.text(0.99, 0.995,
            f"AI Trading Scanner  ·  {signal['time']}  ·  Confluences: {signal['confluences']}  ·  Account: ${signal.get('account_size',0):,.0f}",
            color='#333333', fontsize=7, ha='right', va='top', fontfamily='monospace')

        plt.subplots_adjust(left=0.02, right=0.97, top=0.96, bottom=0.01)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor=BG, edgecolor='none')
        buf.seek(0)
        image_bytes = buf.read()
        plt.close(fig)
        return image_bytes
    except Exception:
        return None

def add_to_journal(signal):
    entry = {
        "id": get_signal_id(signal),
        "pair": signal['pair'],
        "direction": signal['direction'],
        "score": signal['score'],
        "entry": signal['entry'],
        "sl": signal['sl'],
        "tp": signal['tp'],
        "rr": signal['rr'],
        "sl_pips": signal.get('sl_pips',0),
        "tp_pips": signal.get('tp_pips',0),
        "rsi": signal['rsi'],
        "htf_bias": signal['htf_bias'],
        "regime": signal['regime'],
        "session": signal['session'],
        "confluences": signal['confluences'],
        "reasons": signal['reasons'],
        "candle_pattern": signal.get('candle_pattern',''),
        "suggested_lots": signal.get('suggested_lots',0.01),
        "account_size": signal.get('account_size',10000),
        "amd_phase": signal.get('amd_phase',''),
        "time": signal['time'],
        "result": "Pending",
        "pnl": 0
    }
    existing = [j['id'] for j in st.session_state.trade_journal]
    if entry['id'] not in existing:
        st.session_state.trade_journal.append(entry)

def calculate_stats():
    journal = st.session_state.trade_journal
    if not journal:
        return {"total":0,"wins":0,"losses":0,"pending":0,"win_rate":0,
                "best_pair":"N/A","best_session":"N/A","total_rr":0}
    completed = [j for j in journal if j['result'] not in ["Pending","Expired"]]
    wins = [j for j in completed if j['result']=="TP Hit"]
    losses = [j for j in completed if j['result']=="SL Hit"]
    win_rate = len(wins)/len(completed)*100 if completed else 0
    total_rr = sum([j.get('pnl',0) for j in completed])
    pair_wins = {}
    for j in wins:
        pair_wins[j['pair']] = pair_wins.get(j['pair'],0)+1
    session_wins = {}
    for j in wins:
        session_wins[j['session']] = session_wins.get(j['session'],0)+1
    return {
        "total": len(journal),
        "wins": len(wins),
        "losses": len(losses),
        "pending": len([j for j in journal if j['result']=="Pending"]),
        "win_rate": round(win_rate,1),
        "best_pair": max(pair_wins,key=pair_wins.get) if pair_wins else "N/A",
        "best_session": max(session_wins,key=session_wins.get) if session_wins else "N/A",
        "total_rr": round(total_rr,2)
    }

def get_active_pairs():
    enabled = st.session_state.get('enabled_pairs', {p:True for p in ALL_PAIRS})
    active = [p for p in ALL_PAIRS if enabled.get(p,True)]
    return active if active else ALL_PAIRS

for key, val in [
    ('scanner_running',False),('logged_in',False),
    ('user_email',None),('user_id',None),
    ('signals',[]),('alerts_sent',0),
    ('total_scans',0),('last_scan_time',None),
    ('sent_signal_ids',set()),
    ('trade_journal',[]),('cached_news',[]),
    ('last_news_fetch',None),('show_reset',False),
    ('last_outcome_check',None),
    ('enabled_pairs',{p:True for p in ALL_PAIRS}),
    ('scan_interval_minutes',5),
    ('account_size',10000),
    ('keepalive_count',0)
]:
    if key not in st.session_state:
        st.session_state[key] = val

def refresh_news():
    try:
        now = get_ist_time()
        if (st.session_state.last_news_fetch is None or
            int((now-st.session_state.last_news_fetch).total_seconds()) >= 900):
            st.session_state.cached_news = fetch_forex_news()
            st.session_state.last_news_fetch = now
    except Exception:
        pass

def run_scan():
    refresh_news()
    check_signal_outcomes()
    active_pairs = get_active_pairs()
    found = []
    new_high = []
    for pair in active_pairs:
        result = analyze_pair_advanced(pair)
        if result:
            found.append(result)
            if result['score'] >= 80:
                sig_id = get_signal_id(result)
                if sig_id not in st.session_state.sent_signal_ids:
                    new_high.append(result)
    found.sort(key=lambda x: x['score'], reverse=True)
    new_high.sort(key=lambda x: x['score'], reverse=True)
    for signal in new_high[:2]:
        sig_id = get_signal_id(signal)
        msg = format_discord_message(signal)
        chart_bytes = generate_professional_chart(
            signal['df'], signal, signal['fvg_zones'],
            signal['ob_found'], signal['ob_top'],
            signal['ob_bottom'], signal['ob_index'],
            signal['bull_bos'], signal['bear_bos'],
            signal['swing_highs'], signal['swing_lows'],
            signal['bull_sweep'], signal['bear_sweep'],
            signal.get('candle_pattern',''))
        success = (send_discord_alert_with_image(msg, chart_bytes)
            if chart_bytes else send_discord_alert(msg))
        if success:
            st.session_state.sent_signal_ids.add(sig_id)
            st.session_state.alerts_sent += 1
            add_to_journal(signal)
    if len(st.session_state.sent_signal_ids) > 100:
        st.session_state.sent_signal_ids = set()
    st.session_state.signals = [
        {k:v for k,v in s.items() if k not in
         ['df','fvg_zones','ob_found','ob_top','ob_bottom','ob_index',
          'bull_bos','bear_bos','swing_highs','swing_lows',
          'swing_high_level','swing_low_level','bull_sweep','bear_sweep']}
        for s in found]
    st.session_state.total_scans += 1
    st.session_state.last_scan_time = get_ist_time()

def auto_scan():
    try:
        st.session_state.keepalive_count += 1
        now = get_ist_time()
        scan_secs = st.session_state.get('scan_interval_minutes', 5) * 60
        if st.session_state.last_scan_time is None:
            run_scan()
            return
        elapsed = int((now-st.session_state.last_scan_time).total_seconds())
        if elapsed >= scan_secs:
            run_scan()
        last_check = st.session_state.last_outcome_check
        if (last_check is None or int((now-last_check).total_seconds()) >= 60):
            check_signal_outcomes()
            st.session_state.last_outcome_check = now
    except Exception:
        pass

def main():
    st.markdown(CYBER_CSS, unsafe_allow_html=True)
    st.markdown(KEEP_ALIVE_JS, unsafe_allow_html=True)
    if not st.session_state.logged_in:
        show_login_page()
    else:
        if st.session_state.scanner_running:
            auto_scan()
        show_dashboard()

def show_login_page():
    st.markdown("""
    <div style='text-align:center; padding:60px 20px 40px'>
        <div style='font-family:Orbitron,monospace;
            font-size:2.8em; font-weight:900; color:#00FF88;
            text-shadow:0 0 20px rgba(0,255,136,0.5),
                        0 0 40px rgba(0,255,136,0.25);
            letter-spacing:4px; margin-bottom:12px;
            line-height:1.2'>
        ⬡ AI TRADING<br>SCANNER PRO</div>
        <div style='font-family:Exo 2,sans-serif;
            color:#6B7A8D; font-size:0.9em;
            letter-spacing:5px; margin-bottom:10px;
            text-transform:uppercase'>
        Professional Scalping Intelligence</div>
        <div style='font-family:JetBrains Mono,monospace;
            color:rgba(0,255,136,0.35); font-size:0.75em;
            letter-spacing:2px; margin-top:5px'>
        XAUUSD · EURUSD · GBPUSD · USDJPY · GBPJPY · EURJPY · AUDCAD · US30 · NAS100
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1.4,1])
    with col2:
        st.markdown("""
        <div style='background:linear-gradient(135deg,
                rgba(0,255,136,0.04) 0%, rgba(0,0,0,0) 100%);
            border:1px solid rgba(0,255,136,0.12);
            border-radius:18px; padding:28px 24px;
            backdrop-filter:blur(20px);
            box-shadow:0 8px 32px rgba(0,0,0,0.4),
                       0 0 60px rgba(0,255,136,0.03)'>
        """, unsafe_allow_html=True)

        if st.session_state.show_reset:
            st.markdown("<h3 style='color:#00FF88;font-family:Orbitron,monospace;text-align:center;font-size:1em;letter-spacing:2px'>RESET PASSWORD</h3>", unsafe_allow_html=True)
            reset_email = st.text_input("Email", key="reset_email")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Send Reset Email", use_container_width=True, type="primary"):
                    success, msg = reset_password(reset_email)
                    st.success(msg) if success else st.error(msg)
            with col_b:
                if st.button("← Back", use_container_width=True):
                    st.session_state.show_reset = False
                    st.rerun()
        else:
            tab1, tab2 = st.tabs(["  🔑  LOGIN  ","  📝  SIGN UP  "])
            with tab1:
                st.markdown("<br>", unsafe_allow_html=True)
                email = st.text_input("Email address", key="login_email", placeholder="trader@email.com")
                password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⚡  ENTER SCANNER", use_container_width=True, type="primary"):
                    if email and password:
                        success, msg = login_user(email, password)
                        if success:
                            st.success("✅ "+msg)
                            time.sleep(0.4)
                            st.rerun()
                        else:
                            st.error("❌ "+msg)
                    else:
                        st.error("Please enter email and password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Forgot Password?", use_container_width=True):
                    st.session_state.show_reset = True
                    st.rerun()
            with tab2:
                st.markdown("<br>", unsafe_allow_html=True)
                new_email = st.text_input("Email address", key="signup_email", placeholder="trader@email.com")
                new_pass = st.text_input("Password", type="password", key="signup_pass", placeholder="Min 6 characters")
                confirm_pass = st.text_input("Confirm Password", type="password", key="confirm_pass", placeholder="Repeat password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🚀  CREATE ACCOUNT", use_container_width=True, type="primary"):
                    if new_email and new_pass and confirm_pass:
                        if new_pass == confirm_pass:
                            if len(new_pass) < 6:
                                st.error("Password must be at least 6 characters")
                            else:
                                success, msg = signup_user(new_email, new_pass)
                                st.success("✅ "+msg) if success else st.error("❌ "+msg)
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.error("Please fill all fields")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align:center; margin-top:40px;
        display:flex; justify-content:center; gap:14px; flex-wrap:wrap'>
    """, unsafe_allow_html=True)
    features_login = [
        ("🎯","Scalping SL/TP"),
        ("💼","Smart Lot Sizing"),
        ("⚡","AMD Strategy"),
        ("📊","5-Panel Charts"),
        ("🌐","Keep-Alive"),
        ("🤖","Auto Tracking")
    ]
    for icon, text in features_login:
        st.markdown(f"""
        <div style='background:rgba(0,255,136,0.04);
            border:1px solid rgba(0,255,136,0.12);
            border-radius:10px; padding:10px 16px;
            font-family:Exo 2,sans-serif;
            color:#6B7A8D; font-size:0.82em;
            transition:all 0.2s ease'>
            {icon} {text}</div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def show_dashboard():
    session_quality, session_name = get_session_quality()
    news = st.session_state.get('cached_news',[])
    high_impact = [n for n in news if n['impact']==3]
    stats = calculate_stats()
    active_pairs = get_active_pairs()
    account_size = st.session_state.get('account_size', 10000)

    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding:14px 0 8px'>
            <div style='font-family:Orbitron,monospace;
                font-size:0.95em; font-weight:700;
                color:#00FF88; letter-spacing:2px;
                text-shadow:0 0 8px rgba(0,255,136,0.4)'>
            ⬡ AI SCANNER PRO</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background:linear-gradient(135deg,
            rgba(0,255,136,0.05) 0%, rgba(0,0,0,0) 100%);
            border:1px solid rgba(0,255,136,0.1);
            border-radius:10px; padding:10px 12px;
            margin:6px 0; font-family:Exo 2,sans-serif'>
            <div style='color:#4A5568; font-size:0.68em;
                letter-spacing:1.5px; text-transform:uppercase;
                margin-bottom:3px'>👤 USER</div>
            <div style='color:#CDD5DF; font-size:0.8em;
                word-break:break-all; font-weight:500'>
            {str(st.session_state.user_email)}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background:linear-gradient(135deg,
            rgba(88,166,255,0.06) 0%, rgba(0,0,0,0) 100%);
            border:1px solid rgba(88,166,255,0.12);
            border-radius:10px; padding:8px 12px;
            margin:6px 0; font-family:JetBrains Mono,monospace;
            text-align:center'>
            <div style='color:#58A6FF; font-size:1em;
                font-weight:500; letter-spacing:0.5px'>
            {get_ist_time().strftime('%H:%M:%S IST')}</div>
            <div style='color:#4A5568; font-size:0.72em;
                margin-top:1px'>
            {get_ist_time().strftime('%d %b %Y')}</div>
        </div>
        """, unsafe_allow_html=True)

        sq_colors = {
            "BEST": ("#00FF88","rgba(0,255,136,0.1)","rgba(0,255,136,0.2)"),
            "GOOD": ("#3FB950","rgba(63,185,80,0.08)","rgba(63,185,80,0.15)"),
            "MODERATE": ("#F0B429","rgba(240,180,41,0.08)","rgba(240,180,41,0.15)"),
            "POOR": ("#FF4444","rgba(255,68,68,0.08)","rgba(255,68,68,0.15)")
        }
        sq_c = sq_colors.get(session_quality, sq_colors["POOR"])
        sq_s = {"BEST":"⭐⭐⭐","GOOD":"⭐⭐","MODERATE":"⭐","POOR":"⚠️"}.get(session_quality,"⚠️")
        st.markdown(f"""
        <div style='background:{sq_c[1]};
            border:1px solid {sq_c[2]};
            border-radius:9px; padding:7px 10px;
            text-align:center; margin:5px 0;
            font-family:Exo 2,sans-serif;
            color:{sq_c[0]}; font-size:0.82em;
            font-weight:500'>
            {sq_s} {session_name}
        </div>
        """, unsafe_allow_html=True)

        if high_impact:
            st.markdown("""
            <div style='background:rgba(255,68,68,0.1);
                border:1px solid rgba(255,68,68,0.3);
                border-radius:9px; padding:7px 10px;
                text-align:center; margin:5px 0;
                font-family:Exo 2,sans-serif;
                color:#FF4444; font-size:0.8em;
                font-weight:600'>
                🚨 HIGH IMPACT NEWS!
            </div>
            """, unsafe_allow_html=True)

        ka_count = st.session_state.get('keepalive_count',0)
        st.markdown(f"""
        <div style='background:rgba(88,166,255,0.04);
            border:1px solid rgba(88,166,255,0.1);
            border-radius:8px; padding:5px 10px;
            text-align:center; margin:4px 0;
            font-family:Exo 2,sans-serif;
            color:#58A6FF; font-size:0.73em'>
            🌐 Keep-Alive #{ka_count} · {len(active_pairs)}/9 Pairs
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background:rgba(240,180,41,0.05);
            border:1px solid rgba(240,180,41,0.12);
            border-radius:8px; padding:6px 10px;
            text-align:center; margin:4px 0;
            font-family:JetBrains Mono,monospace;
            color:#F0B429; font-size:0.8em;
            font-weight:500'>
            💼 ${account_size:,.0f}
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Win Rate", str(stats['win_rate'])+"%")
        with col2:
            st.metric("Signals", stats['total'])

        if stats.get('pending',0) > 0:
            st.info("⏳ "+str(stats['pending'])+" tracking")

        st.divider()
        page = st.radio("Navigation", [
            "🏠 Dashboard",
            "📊 Active Signals",
            "📰 News & Calendar",
            "📓 Trade Journal",
            "📈 Performance",
            "📅 Calendar",
            "⚙️ Settings"
        ], label_visibility="collapsed")
        st.divider()
        if st.button("Sign Out", use_container_width=True):
            logout_user()
            st.rerun()

    if page == "🏠 Dashboard":
        show_main_dashboard()
    elif page == "📊 Active Signals":
        show_signals_page()
    elif page == "📰 News & Calendar":
        show_news_page()
    elif page == "📓 Trade Journal":
        show_journal_page()
    elif page == "📈 Performance":
        show_performance_page()
    elif page == "📅 Calendar":
        show_calendar_page()
    elif page == "⚙️ Settings":
        show_settings_page()

def show_main_dashboard():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.6em;
        margin-bottom:20px; letter-spacing:2px'>
    🏠 DASHBOARD</div>
    """, unsafe_allow_html=True)

    session_quality, session_name = get_session_quality()
    news = st.session_state.get('cached_news',[])
    high_impact = [n for n in news if n['impact']==3]
    stats = calculate_stats()
    account_size = st.session_state.get('account_size', 10000)

    if high_impact:
        st.markdown("""
        <div style='background:rgba(255,68,68,0.08);
            border:1px solid rgba(255,68,68,0.3);
            border-radius:12px; padding:14px 18px;
            margin-bottom:16px;
            font-family:Exo 2,sans-serif;
            color:#FF4444; font-weight:600;
            text-align:center'>
            🚨 HIGH IMPACT NEWS ACTIVE — DO NOT TRADE UNTIL NEWS PASSES
        </div>
        """, unsafe_allow_html=True)

    if session_quality == "POOR":
        st.markdown("""
        <div class='warning-box' style='margin-bottom:16px;
            text-align:center'>
            ⚠️ Off Session — Scanner will resume at Asia (4AM IST)
            or London (12PM IST)
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1.2,1])
    with col2:
        if not st.session_state.scanner_running:
            st.markdown("""
            <div style='text-align:center;
                background:linear-gradient(135deg,
                    rgba(255,68,68,0.06) 0%,
                    rgba(0,0,0,0) 100%);
                border:1px solid rgba(255,68,68,0.15);
                border-radius:16px; padding:24px;
                margin-bottom:12px'>
                <div style='font-family:Exo 2,sans-serif;
                    color:#4A5568; font-size:0.75em;
                    letter-spacing:3px; text-transform:uppercase;
                    margin-bottom:8px'>SCANNER STATUS</div>
                <div style='font-family:JetBrains Mono,monospace;
                    color:#FF4444; font-size:1.6em;
                    font-weight:500; letter-spacing:2px'>
                ● OFFLINE</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("▶  ACTIVATE SCANNER",
                use_container_width=True, type="primary"):
                st.session_state.scanner_running = True
                st.session_state.last_scan_time = None
                st.session_state.sent_signal_ids = set()
                active = get_active_pairs()
                send_discord_alert(
                    "🟢 **AI Trading Scanner PRO — ACTIVATED!**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "💼 Account: $"+f"{account_size:,.0f}"+"\n"
                    "📡 Scanning: "+", ".join(active)+"\n"
                    "🕐 Session: "+session_name+" ["+session_quality+"]\n"
                    "⏱️ Interval: "+str(st.session_state.get('scan_interval_minutes',5))+" min\n"
                    "⚡ AMD Detection: Active\n"
                    "🎯 Scalping SL/TP: Active\n"
                    "🤖 Auto TP/SL Tracking: Active\n"
                    "🌐 Keep-Alive: Active\n"
                    "👤 "+str(st.session_state.user_email)+"\n"
                    "⏰ "+get_ist_time().strftime('%d %b %Y %H:%M IST'))
                st.rerun()
        else:
            st.markdown("""
            <div style='text-align:center;
                background:linear-gradient(135deg,
                    rgba(0,255,136,0.08) 0%,
                    rgba(0,200,100,0.03) 100%);
                border:1px solid rgba(0,255,136,0.25);
                border-radius:16px; padding:24px;
                margin-bottom:12px;
                box-shadow:0 0 24px rgba(0,255,136,0.08)'>
                <div style='font-family:Exo 2,sans-serif;
                    color:#4A5568; font-size:0.75em;
                    letter-spacing:3px; text-transform:uppercase;
                    margin-bottom:8px'>SCANNER STATUS</div>
                <div style='font-family:JetBrains Mono,monospace;
                    color:#00FF88; font-size:1.6em;
                    font-weight:500; letter-spacing:2px;
                    text-shadow:0 0 12px rgba(0,255,136,0.5)'>
                ● ACTIVE</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⏹  DEACTIVATE SCANNER",
                use_container_width=True):
                st.session_state.scanner_running = False
                send_discord_alert(
                    "🔴 **AI Trading Scanner PRO — DEACTIVATED**\n"
                    "Total Scans: "+str(st.session_state.total_scans)+"\n"
                    "Alerts Sent: "+str(st.session_state.alerts_sent)+"\n"
                    "Win Rate: "+str(stats['win_rate'])+"%\n"
                    "⏰ "+get_ist_time().strftime('%d %b %Y %H:%M IST'))
                st.rerun()

    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Scanner",
            "🟢 ACTIVE" if st.session_state.scanner_running else "🔴 OFFLINE")
    with col2:
        st.metric("Alerts Sent", st.session_state.alerts_sent,
            delta="+1" if st.session_state.alerts_sent > 0 else None)
    with col3:
        st.metric("Win Rate", str(stats['win_rate'])+"%")
    with col4:
        st.metric("Total Scans", st.session_state.total_scans)

    st.divider()

    if st.session_state.scanner_running:
        scan_secs = st.session_state.get('scan_interval_minutes', 5) * 60
        if st.session_state.last_scan_time:
            elapsed = int((get_ist_time()-st.session_state.last_scan_time).total_seconds())
            remaining = max(0, scan_secs-elapsed)
            progress_val = min(1.0, elapsed/scan_secs)
            st.markdown(f"""
            <div class='info-box' style='margin-bottom:10px'>
                ⏱️ Last scan: {st.session_state.last_scan_time.strftime('%H:%M:%S IST')}
                &nbsp;&nbsp;|&nbsp;&nbsp; Next scan in: <b>{remaining}s</b>
                &nbsp;&nbsp;|&nbsp;&nbsp; Session: {session_name}
            </div>
            """, unsafe_allow_html=True)
            st.progress(progress_val)
        else:
            st.markdown("""
            <div class='info-box'>⚡ Initializing first scan...</div>
            """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚡  SCAN NOW", type="primary", use_container_width=True):
                with st.spinner("Running advanced scan..."):
                    run_scan()
                st.success("✅ Scan complete!")
                st.rerun()
        with col2:
            if st.button("🔃  REFRESH", use_container_width=True):
                st.rerun()

    st.divider()

    st.markdown("""
    <div class='warning-box' style='margin-bottom:20px'>
        <b>⚠️ SCALPING RISK RULES</b><br>
        • Lot sizes are auto-calculated for 1% risk per trade based on your account<br>
        • XAUUSD: Extra caution — max 0.02 lots regardless of account size<br>
        • Never add to a losing position · Close trade if signal expires (30 min)<br>
        • Always check news before entering! Avoid trading during red news!
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='font-family:Orbitron,monospace;
        color:#00FF88; font-size:0.8em;
        letter-spacing:2px; margin-bottom:14px;
        opacity:0.7'>📡 PAIR SURVEILLANCE</div>
    """, unsafe_allow_html=True)

    enabled = st.session_state.get('enabled_pairs', {p:True for p in ALL_PAIRS})
    cols = st.columns(3)
    for i, pair in enumerate(ALL_PAIRS):
        with cols[i % 3]:
            is_on = enabled.get(pair, True)
            settings = PAIR_SETTINGS.get(pair, {})
            sl_p = settings.get('sl_pips','?')
            account_size = st.session_state.get('account_size', 10000)
            lot_calc = calculate_lot_size(account_size, pair, sl_p) if isinstance(sl_p, (int,float)) else '?'
            color = "#00FF88" if is_on else "#3A4556"
            bg = "rgba(0,255,136,0.07)" if is_on else "rgba(255,255,255,0.02)"
            border = "rgba(0,255,136,0.25)" if is_on else "rgba(255,255,255,0.06)"
            status = "ON" if is_on else "OFF"
            st.markdown(f"""
            <div style='background:{bg};
                border:1px solid {border};
                border-radius:12px; padding:10px 8px;
                text-align:center; margin-bottom:8px;
                transition:all 0.2s ease'>
                <div style='font-family:Orbitron,monospace;
                    color:{color}; font-size:0.82em;
                    font-weight:700; letter-spacing:1px;
                    margin-bottom:3px'>{pair}</div>
                <div style='font-family:JetBrains Mono,monospace;
                    color:{color}; font-size:0.68em;
                    opacity:0.7'>SL:{sl_p}p · Lot:{lot_calc}</div>
                <div style='font-family:Exo 2,sans-serif;
                    color:{color}; font-size:0.7em;
                    opacity:0.5; margin-top:2px'>{status}</div>
            </div>
            """, unsafe_allow_html=True)

    if st.session_state.scanner_running:
        time.sleep(1)
        st.rerun()

def show_news_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.6em;
        margin-bottom:20px'>📰 NEWS & CALENDAR</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh News", use_container_width=True, type="primary"):
            with st.spinner("Fetching latest news..."):
                st.session_state.cached_news = fetch_forex_news()
                st.session_state.last_news_fetch = get_ist_time()
            st.success("✅ News refreshed!")
            st.rerun()
    with col2:
        if st.session_state.last_news_fetch:
            st.markdown(f"""
            <div class='info-box'>
                Updated: {st.session_state.last_news_fetch.strftime('%H:%M:%S IST')}
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📅 Economic Calendar")
    for event in get_economic_calendar():
        imp_emoji = "🔴" if event['impact']=="High" else "🟡" if event['impact']=="Medium" else "🟢"
        with st.expander(imp_emoji+" "+event['time']+" | "+event['event']+" ("+event['currency']+")"):
            col1,col2,col3 = st.columns(3)
            with col1: st.metric("Impact", event['impact'])
            with col2: st.metric("Forecast", event['forecast'])
            with col3: st.metric("Previous", event['previous'])

    st.divider()
    st.subheader("📰 Live Market News")
    news = st.session_state.get('cached_news',[])
    if not news:
        st.info("Click Refresh News to load!")
        if st.button("📰 Load News Now", use_container_width=True):
            with st.spinner("Loading..."):
                st.session_state.cached_news = fetch_forex_news()
                st.session_state.last_news_fetch = get_ist_time()
            st.rerun()
    else:
        for item in [n for n in news if n['impact']==3]:
            with st.expander("🔴 "+item['title'][:80]):
                st.write("📰 "+item['source']+" · "+item['published'])
                if item['summary']: st.write(item['summary'])
                st.markdown("[Read full article →]("+item['link']+")")
        for item in [n for n in news if n['impact']==2][:5]:
            with st.expander("🟡 "+item['title'][:80]):
                st.write("📰 "+item['source'])
                if item['summary']: st.write(item['summary'])
                st.markdown("[Read →]("+item['link']+")")
        for item in [n for n in news if n['impact']==1][:5]:
            st.write("🟢 "+item['title'][:100]+" — "+item['source'])

def show_signals_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.6em;
        margin-bottom:20px'>📊 ACTIVE SIGNALS</div>
    """, unsafe_allow_html=True)

    news = st.session_state.get('cached_news',[])
    if [n for n in news if n['impact']==3]:
        st.error("🚨 HIGH IMPACT NEWS ACTIVE — Do not trade!")

    if not st.session_state.signals:
        st.markdown("""
        <div style='text-align:center; padding:60px 20px;
            font-family:Exo 2,sans-serif; color:#4A5568'>
            <div style='font-size:3.5em; margin-bottom:16px'>📡</div>
            <div style='font-size:1em; font-weight:500'>
            No signals detected yet</div>
            <div style='font-size:0.85em; margin-top:8px; color:#3A4556'>
            Activate the scanner and wait for high-quality setups</div>
        </div>
        """, unsafe_allow_html=True)
        return

    high = [s for s in st.session_state.signals if s['score']>=80]
    medium = [s for s in st.session_state.signals if 60<=s['score']<80]
    low = [s for s in st.session_state.signals if s['score']<60]

    if high:
        st.markdown("""
        <div style='font-family:Orbitron,monospace;
            color:#00FF88; font-size:0.78em; letter-spacing:2px;
            margin-bottom:12px; opacity:0.85'>
        🟢 HIGH CONFIDENCE — 80%+</div>
        """, unsafe_allow_html=True)
        for signal in high:
            age = get_signal_age(signal['time'])
            status = get_signal_status(age)
            sq = signal.get('session_quality','GOOD')
            sq_s = "⭐⭐⭐" if sq=="BEST" else "⭐⭐" if sq=="GOOD" else "⭐"
            sl_pips = signal.get('sl_pips','?')
            tp_pips = signal.get('tp_pips','?')
            lots = signal.get('suggested_lots','?')
            amd = signal.get('amd_phase','')
            amd_badge = " ⚡AMD" if amd else ""

            with st.expander(
                "🟢 "+signal['pair']+" "+signal['direction']+
                "  ·  "+str(signal['score'])+"%" +
                "  ·  SL:"+str(sl_pips)+"p TP:"+str(tp_pips)+"p"+
                "  ·  "+sq_s+amd_badge+"  ·  "+status):

                col1,col2,col3 = st.columns(3)
                with col1: st.metric("Entry", signal['entry'])
                with col2: st.metric(f"SL ({sl_pips}p)", signal['sl'])
                with col3: st.metric(f"TP ({tp_pips}p)", signal['tp'])

                if age >= 30:
                    st.error("⛔ SIGNAL EXPIRED — Do not trade this!")
                elif age >= 15:
                    st.warning("⚠️ Signal aging — verify current price before entering")
                else:
                    lot_msg = f" · Use {lots} lots (1% risk)"
                    if signal['direction'] == "BUY":
                        st.markdown(f"""
                        <div class='success-box'>
                        ✅ <b>Enter BUY at or below: {signal['entry']}</b>{lot_msg}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class='success-box'>
                        ✅ <b>Enter SELL at or above: {signal['entry']}</b>{lot_msg}
                        </div>
                        """, unsafe_allow_html=True)

                if signal.get('amd_phase'):
                    st.markdown(f"""
                    <div class='info-box' style='margin-top:8px'>
                    ⚡ <b>AMD Phase:</b> {signal['amd_phase']} Manipulation Detected!
                    Smart money may have swept stops and reversed direction.
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class='warning-box' style='margin-top:8px'>
                ⚠️ Skip if price moved more than {signal.get('atr',0):.5f} from entry level
                </div>
                """, unsafe_allow_html=True)

                col1,col2 = st.columns(2)
                with col1:
                    st.write("⚖️ RR: 1:"+str(signal['rr']))
                    st.write("📈 HTF: "+signal['htf_bias'])
                    st.write("🌍 Market: "+signal['regime'])
                with col2:
                    st.write("🕐 "+signal['session'])
                    st.write("📉 RSI: "+str(signal['rsi']))
                    st.write("📐 ADX: "+str(signal.get('adx','?')))
                st.write("📐 "+signal.get('candle_pattern','N/A'))
                st.write("✅ "+" · ".join(signal['reasons']))
                if signal.get('negative'):
                    st.warning("⚠️ "+" · ".join(signal['negative']))

    if medium:
        st.markdown("""
        <div style='font-family:Orbitron,monospace;
            color:#F0B429; font-size:0.78em; letter-spacing:2px;
            margin:16px 0 10px; opacity:0.85'>
        🟡 MEDIUM CONFIDENCE — 60–80%</div>
        """, unsafe_allow_html=True)
        for signal in medium:
            sl_pips = signal.get('sl_pips','?')
            tp_pips = signal.get('tp_pips','?')
            with st.expander(
                "🟡 "+signal['pair']+" "+signal['direction']+
                "  ·  "+str(signal['score'])+"% · SL:"+str(sl_pips)+"p TP:"+str(tp_pips)+"p"):
                col1,col2,col3 = st.columns(3)
                with col1: st.metric("Entry", signal['entry'])
                with col2: st.metric("SL", signal['sl'])
                with col3: st.metric("TP", signal['tp'])

    if low:
        st.markdown("""
        <div style='font-family:Orbitron,monospace;
            color:#FF4444; font-size:0.78em; letter-spacing:2px;
            margin:16px 0 10px; opacity:0.85'>
        🔴 LOW CONFIDENCE — Below 60%</div>
        """, unsafe_allow_html=True)
        for signal in low:
            st.write("🔴 "+signal['pair']+" "+signal['direction']+" | "+str(signal['score'])+"%")

def show_journal_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.6em;
        margin-bottom:20px'>📓 TRADE JOURNAL</div>
    """, unsafe_allow_html=True)

    journal = st.session_state.trade_journal
    if not journal:
        st.info("No trades recorded yet. Scanner will auto-log signals.")
        return

    if st.button("🔄 Check TP/SL Outcomes",
        use_container_width=True, type="primary"):
        with st.spinner("Checking market prices..."):
            check_signal_outcomes()
        st.success("✅ Outcomes updated!")
        st.rerun()

    pending = [j for j in journal if j['result']=="Pending"]
    if pending:
        st.subheader("⏳ Pending Trades")
        for trade in pending:
            with st.expander(
                "⏳ "+trade['pair']+" "+trade['direction']+
                "  ·  "+str(trade['score'])+"%  ·  "+trade['time']):
                col1,col2,col3 = st.columns(3)
                with col1: st.metric("Entry", trade['entry'])
                with col2: st.metric(f"SL ({trade.get('sl_pips','?')}p)", trade['sl'])
                with col3: st.metric(f"TP ({trade.get('tp_pips','?')}p)", trade['tp'])
                st.markdown("""
                <div class='info-box'>
                🤖 Auto-tracking active — updates every 60 seconds
                </div>
                """, unsafe_allow_html=True)
                if trade.get('amd_phase'):
                    st.write("⚡ AMD Phase: "+trade['amd_phase'])
                result = st.selectbox("Manual Override",
                    ["Pending","TP Hit","SL Hit","Expired","Partial Win"],
                    key="result_"+trade['id'])
                if st.button("✅ Save Override",
                    key="update_"+trade['id'], use_container_width=True):
                    for j in st.session_state.trade_journal:
                        if j['id'] == trade['id']:
                            j['result'] = result
                            j['pnl'] = (trade['rr'] if result=="TP Hit"
                                else -1 if result=="SL Hit"
                                else 0.5 if result=="Partial Win" else 0)
                    st.success("Updated!")
                    st.rerun()
    else:
        st.markdown("""
        <div class='success-box'>✅ All trades have results!</div>
        """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📋 Trade History")
    for trade in reversed(journal):
        emoji = ("✅" if trade['result']=="TP Hit" else
                 "❌" if trade['result']=="SL Hit" else
                 "⚠️" if trade['result']=="Partial Win" else
                 "🔴" if trade['result']=="Expired" else "⏳")
        rc = ("color:#00FF88" if trade['result']=="TP Hit" else
              "color:#FF4444" if trade['result']=="SL Hit" else
              "color:#6B7A8D")
        amd_str = f" ⚡AMD" if trade.get('amd_phase') else ""
        st.markdown(f"""
        <div style='background:rgba(255,255,255,0.025);
            border:1px solid rgba(255,255,255,0.06);
            border-radius:10px; padding:10px 14px;
            margin-bottom:5px;
            font-family:Exo 2,sans-serif; font-size:0.88em'>
            {emoji}
            <b style='color:#CDD5DF'>{trade['pair']} {trade['direction']}</b>
            <span style='color:#4A5568'> · {trade['score']}%{amd_str}
            · SL:{trade.get('sl_pips','?')}p TP:{trade.get('tp_pips','?')}p
            · Lots:{trade.get('suggested_lots','?')}</span>
            · <span style='{rc}'><b>{trade['result']}</b></span>
            <span style='color:#3A4556'> · {trade['time']}</span>
        </div>
        """, unsafe_allow_html=True)

def show_performance_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.6em;
        margin-bottom:20px'>📈 PERFORMANCE ANALYTICS</div>
    """, unsafe_allow_html=True)

    stats = calculate_stats()
    if stats['total'] == 0:
        st.info("No completed trades yet. Start the scanner to begin!")
        return

    col1,col2,col3,col4 = st.columns(4)
    with col1: st.metric("Total Signals", stats['total'])
    with col2: st.metric("✅ Wins", stats['wins'])
    with col3: st.metric("❌ Losses", stats['losses'])
    with col4: st.metric("🏆 Win Rate", str(stats['win_rate'])+"%")

    col1,col2,col3 = st.columns(3)
    with col1: st.metric("🥇 Best Pair", stats['best_pair'])
    with col2: st.metric("⭐ Best Session", stats['best_session'])
    with col3: st.metric("📊 Net R", str(stats.get('total_rr',0))+" R")

    st.divider()
    journal = st.session_state.trade_journal
    completed = [j for j in journal if j['result'] not in ["Pending","Expired"]]
    if completed:
        st.subheader("📊 Win Rate by Pair")
        pair_stats = {}
        for j in completed:
            if j['pair'] not in pair_stats:
                pair_stats[j['pair']] = {'wins':0,'total':0}
            pair_stats[j['pair']]['total'] += 1
            if j['result'] == "TP Hit":
                pair_stats[j['pair']]['wins'] += 1

        for pair, data in sorted(pair_stats.items(),
            key=lambda x: x[1]['wins']/x[1]['total'], reverse=True):
            wr = round(data['wins']/data['total']*100,1)
            filled = int(wr/5)
            bar_html = ""
            for b in range(20):
                clr = "#00FF88" if b < filled else "#1E2530"
                bar_html += f"<span style='color:{clr}'>█</span>"
            color = "#00FF88" if wr>=60 else "#F0B429" if wr>=40 else "#FF4444"
            settings = PAIR_SETTINGS.get(pair,{})
            sl_p = settings.get('sl_pips','?')
            st.markdown(f"""
            <div style='background:rgba(255,255,255,0.02);
                border:1px solid rgba(255,255,255,0.05);
                border-radius:10px; padding:10px 14px;
                margin-bottom:6px;
                font-family:Exo 2,sans-serif'>
                <div style='display:flex; align-items:center; gap:10px'>
                    <span style='color:#CDD5DF; font-weight:600;
                        font-family:Orbitron,monospace;
                        font-size:0.85em; width:70px'>{pair}</span>
                    <span style='font-family:JetBrains Mono,monospace;
                        font-size:0.7em; letter-spacing:-1px'>{bar_html}</span>
                    <span style='color:{color};
                        font-family:JetBrains Mono,monospace;
                        font-weight:500; font-size:0.95em'>{wr}%</span>
                    <span style='color:#3A4556; font-size:0.8em'>
                    ({data['wins']}/{data['total']}) · SL:{sl_p}p</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

def show_calendar_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.6em;
        margin-bottom:20px'>📅 CALENDAR ANALYTICS</div>
    """, unsafe_allow_html=True)

    journal = st.session_state.trade_journal
    if not journal:
        st.info("No trades yet!")
        return

    date_stats = {}
    for trade in journal:
        try:
            parts = trade['time'].split(' ')
            date_str = parts[0]+" "+parts[1]+" "+parts[2]
            if date_str not in date_stats:
                date_stats[date_str] = {'wins':0,'losses':0,'total':0,'trades':[]}
            date_stats[date_str]['total'] += 1
            date_stats[date_str]['trades'].append(trade)
            if trade['result'] == "TP Hit": date_stats[date_str]['wins'] += 1
            elif trade['result'] == "SL Hit": date_stats[date_str]['losses'] += 1
        except Exception:
            pass

    for date, data in sorted(date_stats.items(), reverse=True):
        wr = round(data['wins']/data['total']*100,1) if data['total']>0 else 0
        color = "🟢" if wr>=50 else "🔴"
        with st.expander(
            color+" "+date+" · "+str(data['total'])+" trades · WR: "+str(wr)+"%"):
            for trade in data['trades']:
                emoji = "✅" if trade['result']=="TP Hit" else "❌" if trade['result']=="SL Hit" else "⏳"
                st.write(emoji+" "+trade['pair']+" "+trade['direction']+" | "+str(trade['score'])+"% | "+trade['result'])

def show_settings_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.6em;
        margin-bottom:20px'>⚙️ SETTINGS</div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='success-box' style='margin-bottom:16px'>
        👤 <b>Authenticated:</b> {str(st.session_state.user_email)}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.subheader("💼 Account Size")
    st.write("Set your account balance for automatic lot size calculation:")
    current_account = st.session_state.get('account_size', 10000)

    col1, col2 = st.columns([2,1])
    with col1:
        account_input = st.number_input(
            "Account Balance (USD)",
            min_value=100,
            max_value=10000000,
            value=current_account,
            step=1000,
            format="%d",
            key="account_input",
            help="Enter your trading account balance. Lot sizes will be calculated for 1% risk per trade.")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Account",
            use_container_width=True,
            type="primary"):
            st.session_state.account_size = account_input
            st.success(f"✅ Account set to ${account_input:,.0f}!")

    st.markdown(f"""
    <div class='info-box' style='margin-top:10px'>
        💼 Current: <b>${current_account:,.0f}</b>
        · Risk per trade: 1% = <b>${current_account*0.01:,.0f}</b><br>
        Quick select:
    </div>
    """, unsafe_allow_html=True)

    preset_cols = st.columns(6)
    presets = [5000, 10000, 25000, 50000, 100000, 500000]
    for i, preset in enumerate(presets):
        with preset_cols[i]:
            if st.button(f"${preset//1000}k",
                use_container_width=True,
                key=f"preset_{preset}"):
                st.session_state.account_size = preset
                st.success(f"✅ Set to ${preset:,.0f}!")
                st.rerun()

    st.divider()

    st.subheader("📊 Lot Size Preview")
    account_size = st.session_state.get('account_size', 10000)
    st.write(f"Based on your ${account_size:,.0f} account (1% risk = ${account_size*0.01:,.0f}/trade):")
    cols = st.columns(3)
    for i, (pair, settings) in enumerate(PAIR_SETTINGS.items()):
        with cols[i % 3]:
            lot = calculate_lot_size(account_size, pair, settings['sl_pips'])
            risk_amt = account_size * 0.01
            st.markdown(f"""
            <div style='background:rgba(0,255,136,0.04);
                border:1px solid rgba(0,255,136,0.1);
                border-radius:10px; padding:10px;
                text-align:center; margin-bottom:8px;
                font-family:Exo 2,sans-serif'>
                <div style='color:#CDD5DF; font-family:Orbitron,monospace;
                    font-size:0.82em; font-weight:700;
                    margin-bottom:4px'>{pair}</div>
                <div style='color:#00FF88; font-family:JetBrains Mono,monospace;
                    font-size:1.1em; font-weight:500'>{lot} lots</div>
                <div style='color:#4A5568; font-size:0.72em'>
                SL: {settings['sl_pips']}p · Risk: ${risk_amt:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    st.subheader("📡 Pair Selection")
    enabled = st.session_state.get('enabled_pairs', {p:True for p in ALL_PAIRS})
    changed = False

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Enable All", use_container_width=True):
            for p in ALL_PAIRS: enabled[p] = True
            st.session_state.enabled_pairs = enabled
            st.rerun()
    with col2:
        if st.button("❌ Disable All", use_container_width=True):
            for p in ALL_PAIRS: enabled[p] = False
            st.session_state.enabled_pairs = enabled
            st.rerun()
    with col3:
        active_count = len([p for p in ALL_PAIRS if enabled.get(p,True)])
        st.markdown(f"""
        <div style='text-align:center; padding:8px;
            font-family:JetBrains Mono,monospace;
            color:#00FF88; font-size:1em; font-weight:500'>
            {active_count} / 9 ON
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, pair in enumerate(ALL_PAIRS):
        with cols[i % 3]:
            settings = PAIR_SETTINGS.get(pair,{})
            sl_p = settings.get('sl_pips','?')
            is_enabled = enabled.get(pair, True)
            new_val = st.toggle(
                f"{pair}  (SL: {sl_p}p)",
                value=is_enabled,
                key="toggle_"+pair)
            if new_val != is_enabled:
                enabled[pair] = new_val
                changed = True

    if changed:
        st.session_state.enabled_pairs = enabled
        active = [p for p in ALL_PAIRS if enabled.get(p,True)]
        st.success("✅ Scanning: "+(", ".join(active) if active else "None selected"))
        st.rerun()

    active_pairs = [p for p in ALL_PAIRS if enabled.get(p,True)]
    if active_pairs:
        st.markdown(f"""
        <div class='info-box' style='margin-top:8px'>
            📡 Active pairs: <b>{" · ".join(active_pairs)}</b>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("⚠️ No pairs selected! Enable at least one pair.")

    st.divider()

    st.subheader("⏱️ Scan Interval")
    current_interval = st.session_state.get('scan_interval_minutes', 5)
    scan_interval = st.selectbox(
        "Minutes between scans:",
        [1, 2, 3, 5, 10, 15, 30],
        index=[1,2,3,5,10,15,30].index(current_interval)
        if current_interval in [1,2,3,5,10,15,30] else 3,
        key="scan_interval_select")
    if st.button("💾 Save Interval", use_container_width=True, type="primary"):
        st.session_state.scan_interval_minutes = scan_interval
        st.success("✅ Interval set to "+str(scan_interval)+" minutes!")

    st.divider()

    st.subheader("🔔 Discord")
    if st.button("🔔 Test Discord Alert", use_container_width=True):
        active = get_active_pairs()
        acc = st.session_state.get('account_size', 10000)
        success = send_discord_alert(
            "✅ **System Test — AI Trading Scanner PRO**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "All systems operational!\n"
            "💼 Account: $"+f"{acc:,.0f}"+"\n"
            "📡 Active pairs: "+", ".join(active)+"\n"
            "⏱️ Scan interval: "+str(st.session_state.get('scan_interval_minutes',5))+" min\n"
            "🕐 Session: "+get_current_session()+"\n"
            "⚡ AMD Detection: Active\n"
            "👤 "+str(st.session_state.user_email)+"\n"
            "⏰ "+get_ist_time().strftime('%d %b %Y %H:%M IST'))
        if success:
            st.success("✅ Discord working perfectly!")
        else:
            st.error("❌ Discord failed — check webhook URL in secrets")

    st.divider()

    st.subheader("🗑️ Data Management")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Alert History", use_container_width=True):
            st.session_state.sent_signal_ids = set()
            st.success("Cleared!")
    with col2:
        if st.button("Clear Trade Journal", use_container_width=True):
            st.session_state.trade_journal = []
            st.success("Cleared!")

    st.divider()

    st.subheader("⚡ AMD Strategy Explained")
    st.markdown("""
    <div class='info-box'>
        <b>AMD = Accumulation · Manipulation · Distribution</b><br><br>
        <b>Phase 1 — Accumulation:</b> Smart money loads positions in a range.
        Price moves sideways, creating equal highs and lows.<br><br>
        <b>Phase 2 — Manipulation (Stop Hunt):</b> Price breaks out FALSELY
        to one side, triggering retail stop losses and entries.
        This is where our scanner catches the signal!<br><br>
        <b>Phase 3 — Distribution:</b> Price reverses strongly in the OPPOSITE
        direction — this is the real move where we profit.<br><br>
        <b>Our detection logic:</b><br>
        ✅ Detects consolidation range (ATR ratio > 2.0)<br>
        ✅ Detects false breakout beyond range high/low<br>
        ✅ Detects reversal candle back into range<br>
        ✅ Adds +30 points bonus to confluence score<br>
        ✅ Shows ⚡AMD badge in Discord alert and chart
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.subheader("🌐 Keep-Alive System")
    ka_count = st.session_state.get('keepalive_count',0)
    st.markdown(f"""
    <div class='info-box'>
        ✅ JavaScript pings server every 25 seconds<br>
        ✅ Wake lock prevents mobile screen sleep<br>
        ✅ Auto-reloads when internet reconnects<br>
        📊 Current ping count: <b>{ka_count}</b><br>
        💡 Set scan interval to 1-2 min for best results
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.subheader("✅ System Capabilities")
    features = [
        ("🎯","Scalping-optimized SL/TP per pair"),
        ("💼","Auto lot sizing by account balance"),
        ("⚡","AMD Accumulation-Manipulation-Distribution"),
        ("📊","Advanced BOS with swing point detection"),
        ("🌊","FVG with gap size filtering"),
        ("🧱","Smart Order Block detection"),
        ("💧","Liquidity Sweep confirmation"),
        ("🔄","CHOCH (Change of Character)"),
        ("📉","ADX trend strength filter"),
        ("📈","EMA 8/21/50 stack confirmation"),
        ("🕯️","Candle pattern recognition"),
        ("🌐","Multi-timeframe HTF bias 4H+1H"),
        ("🔧","Structure-based dynamic SL"),
        ("🤖","Auto TP/SL outcome tracking"),
        ("📊","5-panel professional charts"),
        ("📰","News impact filter"),
        ("🌐","JavaScript keep-alive system"),
        ("🎯","Pair toggle selection"),
        ("⏱️","Adjustable scan interval"),
        ("📓","Trade journal with pip tracking"),
        ("📈","Win rate analytics by pair"),
        ("📅","Calendar performance view"),
    ]
    cols = st.columns(2)
    for i, (icon, feat) in enumerate(features):
        with cols[i%2]:
            st.markdown(f"""
            <div style='background:rgba(0,255,136,0.03);
                border:1px solid rgba(0,255,136,0.08);
                border-radius:8px; padding:8px 12px;
                margin-bottom:5px;
                font-family:Exo 2,sans-serif;
                color:#6B7A8D; font-size:0.84em'>
                {icon} {feat}
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
