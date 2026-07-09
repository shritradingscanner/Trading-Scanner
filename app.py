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
    page_title="AI Trading Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

CYBER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600&display=swap');

.stApp {
    background: #080B14 !important;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(0,255,136,0.03) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(0,150,255,0.03) 0%, transparent 60%) !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

section[data-testid="stSidebar"] {
    background: rgba(8,11,20,0.98) !important;
    border-right: 1px solid rgba(0,255,136,0.2) !important;
}

.main .block-container {
    background: transparent !important;
    padding: 1rem 2rem !important;
}

div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(0,255,136,0.15) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(10px) !important;
    margin-bottom: 8px !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stExpander"]:hover {
    border-color: rgba(0,255,136,0.4) !important;
    background: rgba(0,255,136,0.05) !important;
}

div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(0,255,136,0.15) !important;
    border-radius: 10px !important;
    padding: 12px !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stMetricValue"] {
    color: #00FF88 !important;
    font-family: 'Orbitron', monospace !important;
}

div[data-testid="stButton"] button {
    background: linear-gradient(135deg,
        rgba(0,255,136,0.1),
        rgba(0,200,100,0.2)) !important;
    border: 1px solid rgba(0,255,136,0.5) !important;
    color: #00FF88 !important;
    border-radius: 8px !important;
    font-family: 'Exo 2', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stButton"] button:hover {
    background: linear-gradient(135deg,
        rgba(0,255,136,0.3),
        rgba(0,200,100,0.4)) !important;
    border-color: #00FF88 !important;
    box-shadow: 0 0 20px rgba(0,255,136,0.4) !important;
    color: #FFFFFF !important;
}

div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg,
        rgba(0,255,136,0.3),
        rgba(0,180,90,0.5)) !important;
    border-color: #00FF88 !important;
    box-shadow: 0 0 15px rgba(0,255,136,0.3) !important;
    color: #FFFFFF !important;
}

div[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(0,255,136,0.2) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
}

div[data-testid="stTextInput"] input:focus {
    border-color: #00FF88 !important;
    box-shadow: 0 0 10px rgba(0,255,136,0.3) !important;
}

div[data-testid="stSelectbox"] > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(0,255,136,0.2) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
}

div[data-testid="stRadio"] label {
    color: #8899AA !important;
    font-family: 'Exo 2', sans-serif !important;
}

div[data-testid="stRadio"] label:hover {
    color: #00FF88 !important;
}

hr { border-color: rgba(0,255,136,0.15) !important; }

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #00FF88 !important;
    border-bottom: 2px solid #00FF88 !important;
}

div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #00FF88, #00CC66) !important;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb {
    background: rgba(0,255,136,0.3);
    border-radius: 10px;
}

.cyber-title {
    font-family: 'Orbitron', monospace !important;
    color: #00FF88 !important;
    text-shadow: 0 0 10px rgba(0,255,136,0.5),
                 0 0 20px rgba(0,255,136,0.3) !important;
}

.pair-on {
    background: rgba(0,255,136,0.1);
    border: 1px solid rgba(0,255,136,0.5);
    border-radius: 10px;
    padding: 8px;
    text-align: center;
    font-family: 'Orbitron', monospace;
    color: #00FF88;
    font-size: 0.85em;
    margin-bottom: 6px;
    cursor: pointer;
}

.pair-off {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 8px;
    text-align: center;
    font-family: 'Orbitron', monospace;
    color: #445566;
    font-size: 0.85em;
    margin-bottom: 6px;
}
</style>
"""

IST = pytz.timezone('Asia/Kolkata')

ALL_PAIRS = [
    "XAUUSD","USDJPY","AUDCAD",
    "GBPJPY","GBPUSD","EURUSD",
    "EURJPY","US30","NAS100"
]

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

def is_good_session():
    session = get_current_session()
    return session in [
        "Asia", "London",
        "London + NY Overlap", "New York"]

def get_session_quality():
    session = get_current_session()
    if session == "London + NY Overlap":
        return "BEST", session
    elif session in ["London", "New York"]:
        return "GOOD", session
    elif session == "Asia":
        return "MODERATE", session
    return "POOR", session

def check_internet():
    try:
        requests.get("https://8.8.8.8",
            timeout=3)
        return True
    except Exception:
        try:
            requests.get("https://www.google.com",
                timeout=3)
            return True
        except Exception:
            return False

def handle_startup_reconnect():
    was_running = st.session_state.get(
        'scanner_was_running_before_disconnect', False)
    disconnected = st.session_state.get(
        'was_disconnected', False)
    if was_running and disconnected:
        st.session_state.scanner_running = True
        st.session_state.scanner_was_running_before_disconnect = False
        st.session_state.was_disconnected = False
        st.session_state.last_scan_time = None
        send_discord_alert(
            "🟢 **NETWORK RECONNECTED!**\n"
            "AI Trading Scanner AUTO-RESUMED!\n"
            "Scanner was paused due to network loss.\n"
            "All systems back online!\n"
            "Time: " + get_ist_time().strftime(
                '%d %b %Y %H:%M IST'))

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
        {"url":"https://www.forexlive.com/feed/news",
         "source":"ForexLive"},
        {"url":"https://feeds.reuters.com/reuters/businessNews",
         "source":"Reuters"},
        {"url":"https://www.marketwatch.com/rss/topstories",
         "source":"MarketWatch"}
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
    high = ["nfp","non-farm payroll","fomc",
            "federal reserve","cpi","inflation",
            "interest rate","rate decision","gdp",
            "ecb","bank of england","boe","powell",
            "lagarde","recession","crisis"]
    medium = ["pmi","retail sales","trade balance",
              "housing","manufacturing","employment"]
    for k in high:
        if k in text_lower:
            return 3
    for k in medium:
        if k in text_lower:
            return 2
    return 1

def get_economic_calendar():
    return [
        {"time":"Today 6:00 PM IST",
         "event":"US Initial Jobless Claims",
         "impact":"Medium","currency":"USD",
         "forecast":"220K","previous":"215K"},
        {"time":"Today 8:30 PM IST",
         "event":"US Non-Farm Payrolls",
         "impact":"High","currency":"USD",
         "forecast":"185K","previous":"175K"},
        {"time":"Tomorrow 2:30 PM IST",
         "event":"ECB Interest Rate Decision",
         "impact":"High","currency":"EUR",
         "forecast":"4.25%","previous":"4.50%"},
        {"time":"Friday 6:00 PM IST",
         "event":"US CPI Monthly",
         "impact":"High","currency":"USD",
         "forecast":"0.3%","previous":"0.4%"}
    ]

TICKER_MAP = {
    "XAUUSD":"GC=F","USDJPY":"JPY=X",
    "AUDCAD":"AUDCAD=X","GBPJPY":"GBPJPY=X",
    "GBPUSD":"GBPUSD=X","EURUSD":"EURUSD=X",
    "EURJPY":"EURJPY=X","US30":"YM=F","NAS100":"NQ=F"
}

TWELVE_MAP = {
    "XAUUSD":"XAU/USD","USDJPY":"USD/JPY",
    "AUDCAD":"AUD/CAD","GBPJPY":"GBP/JPY",
    "GBPUSD":"GBP/USD","EURUSD":"EUR/USD",
    "EURJPY":"EUR/JPY","US30":"US30/USD","NAS100":"IXIC"
}

def get_data_twelvedata(symbol, interval="5min"):
    try:
        api_key = st.secrets["TWELVEDATA_KEY"]
        url = (
            "https://api.twelvedata.com/time_series?"
            "symbol=" + TWELVE_MAP.get(symbol,symbol) +
            "&interval=" + interval +
            "&outputsize=150&apikey=" + api_key)
        response = requests.get(url, timeout=10)
        data = response.json()
        if "values" not in data:
            return None
        df = pd.DataFrame(data["values"])
        df = df.rename(columns={
            "open":"Open","high":"High",
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
    interval_map = {"5m":"5min","15m":"15min",
                    "1h":"1h","4h":"4h"}
    df = get_data_twelvedata(symbol,
        interval_map.get(interval,"5min"))
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
        plus_dm = []
        minus_dm = []
        for i in range(1, len(high)):
            up = high[i]-high[i-1]
            down = low[i-1]-low[i]
            plus_dm.append(up if up > down and up > 0 else 0)
            minus_dm.append(down if down > up and down > 0 else 0)
        plus_dm = np.array(plus_dm)
        minus_dm = np.array(minus_dm)
        tr_vals = []
        for i in range(1, len(high)):
            tr = max(high[i]-low[i],
                abs(high[i]-close[i-1]),
                abs(low[i]-close[i-1]))
            tr_vals.append(tr)
        tr_vals = np.array(tr_vals)
        atr_s = pd.Series(tr_vals).ewm(
            span=period,adjust=False).mean().values
        plus_di = 100*pd.Series(plus_dm).ewm(
            span=period,adjust=False).mean().values/(atr_s+1e-10)
        minus_di = 100*pd.Series(minus_dm).ewm(
            span=period,adjust=False).mean().values/(atr_s+1e-10)
        dx = 100*np.abs(plus_di-minus_di)/(plus_di+minus_di+1e-10)
        adx = pd.Series(dx).ewm(
            span=period,adjust=False).mean().values
        return float(adx[-1]), float(plus_di[-1]), float(minus_di[-1])
    except Exception:
        return 25.0, 25.0, 25.0

def detect_swing_highs_lows(df, lookback=5):
    try:
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        swing_highs = []
        swing_lows = []
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
                    'top':c3l,'bottom':c1h,
                    'mid':(c3l+c1h)/2,
                    'index':len(df)-len(candles)+i,'size':gap})
            if c3h < c1l:
                gap = c1l-c3h
                bear_fvg = True
                fvg_zones.append({'type':'bearish',
                    'top':c1l,'bottom':c3h,
                    'mid':(c1l+c3h)/2,
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
        if adx > 25 and plus_di > minus_di:
            return "TRENDING UP", adx
        elif adx > 25 and minus_di > plus_di:
            return "TRENDING DOWN", adx
        elif adx < 20:
            return "RANGING", adx
        atr = calculate_atr(df)
        pr = float(max(closes[-20:])-min(closes[-20:]))
        if pr > atr*4:
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

def calculate_structure_sl_advanced(df, direction,
    atr, swing_highs, swing_lows):
    try:
        close = float(df['Close'].iloc[-1])
        if direction == "BUY":
            if swing_lows:
                sl_level = min([sl[1] for sl in swing_lows[-3:]])
                sl = sl_level - atr*0.3
            else:
                sl = close - atr*2
            if close-sl > atr*3:
                sl = close-atr*2
        else:
            if swing_highs:
                sl_level = max([sh[1] for sh in swing_highs[-3:]])
                sl = sl_level + atr*0.3
            else:
                sl = close+atr*2
            if sl-close > atr*3:
                sl = close+atr*2
        return round(sl, 5)
    except Exception:
        close = float(df['Close'].iloc[-1])
        return round(close-atr*2 if direction=="BUY"
            else close+atr*2, 5)

def generate_professional_chart(df, signal, fvg_zones,
    ob_found, ob_top, ob_bottom, ob_index,
    bull_bos, bear_bos, swing_highs, swing_lows,
    bull_sweep, bear_sweep, candle_pattern):
    try:
        BG = '#0D1117'
        BG2 = '#161B22'
        GREEN = '#26A69A'
        RED = '#EF5350'
        WHITE = '#E6EDF3'
        GRAY = '#8B949E'
        YELLOW = '#F0B429'
        PURPLE = '#BB86FC'
        BLUE = '#58A6FF'

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

        ax_main.plot(range(n), ema8,
            color=YELLOW, linewidth=0.8, alpha=0.7,
            label='EMA8')
        ax_main.plot(range(n), ema21,
            color=BLUE, linewidth=0.8, alpha=0.7,
            label='EMA21')
        ax_main.plot(range(n), ema50,
            color=PURPLE, linewidth=0.8, alpha=0.7,
            label='EMA50')

        for i in range(n):
            o = float(display_df['Open'].iloc[i])
            h = float(display_df['High'].iloc[i])
            l = float(display_df['Low'].iloc[i])
            c = float(display_df['Close'].iloc[i])
            is_bull = c >= o
            body_color = GREEN if is_bull else RED
            wick_color = '#2EBD8E' if is_bull else '#F23645'
            ax_main.plot([i,i],[l,h],
                color=wick_color, linewidth=0.7,
                alpha=0.9, zorder=3)
            rect = patches.FancyBboxPatch(
                (i-0.38, min(o,c)),
                0.76, max(abs(c-o), 0.0001),
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
                    fvg_rect = patches.Rectangle(
                        (fx,fvg['bottom']),
                        n-fx, fvg['top']-fvg['bottom'],
                        linewidth=1, edgecolor=fb,
                        facecolor=fc, alpha=1, zorder=1)
                    ax_main.add_patch(fvg_rect)
                    label = 'FVG+' if is_bull_fvg else 'FVG-'
                    ax_main.text(fx+0.5, fvg['mid'],
                        label, color=fb, fontsize=7,
                        fontweight='bold', va='center',
                        fontfamily='monospace',
                        bbox=dict(boxstyle='round,pad=0.15',
                            facecolor=BG2,
                            edgecolor=fb, alpha=0.9))
            except Exception:
                pass

        if ob_found:
            ox = ob_index-(len(df)-n)
            if 0 <= ox < n:
                is_buy = signal['direction']=='BUY'
                oc = '#26A69A18' if is_buy else '#EF535018'
                ob_color = GREEN if is_buy else RED
                ob_rect = patches.Rectangle(
                    (ox,ob_bottom), n-ox, ob_top-ob_bottom,
                    linewidth=1.5, edgecolor=ob_color,
                    facecolor=oc, linestyle='--', zorder=1)
                ax_main.add_patch(ob_rect)
                ax_main.text(ox+0.5, (ob_top+ob_bottom)/2,
                    'OB', color=ob_color, fontsize=8,
                    fontweight='bold', va='center',
                    fontfamily='monospace',
                    bbox=dict(boxstyle='round,pad=0.2',
                        facecolor=BG2,
                        edgecolor=ob_color, alpha=0.9))

        for idx, h_val in swing_highs[-8:]:
            plot_idx = idx-(len(df)-n)
            if 0 <= plot_idx < n:
                ax_main.plot(plot_idx, h_val,
                    'v', color='#F85149',
                    markersize=5, zorder=5)
                ax_main.text(plot_idx, h_val+h_val*0.001,
                    'SH', color='#F85149', fontsize=6,
                    ha='center', fontfamily='monospace',
                    fontweight='bold')

        for idx, l_val in swing_lows[-8:]:
            plot_idx = idx-(len(df)-n)
            if 0 <= plot_idx < n:
                ax_main.plot(plot_idx, l_val,
                    '^', color='#3FB950',
                    markersize=5, zorder=5)
                ax_main.text(plot_idx, l_val-l_val*0.001,
                    'SL', color='#3FB950', fontsize=6,
                    ha='center', fontfamily='monospace',
                    fontweight='bold')

        entry = signal['entry']
        sl = signal['sl']
        tp = signal['tp']
        is_buy = signal['direction'] == "BUY"
        price_range = abs(tp-sl)
        off = price_range*0.015

        if is_buy:
            ax_main.fill_between(range(n), entry, tp,
                alpha=0.08, color=GREEN, zorder=0)
            ax_main.fill_between(range(n), sl, entry,
                alpha=0.08, color=RED, zorder=0)
        else:
            ax_main.fill_between(range(n), tp, entry,
                alpha=0.08, color=GREEN, zorder=0)
            ax_main.fill_between(range(n), entry, sl,
                alpha=0.08, color=RED, zorder=0)

        for level, color, label, pos in [
            (entry, WHITE, f'ENTRY  {entry}', 'bottom'),
            (sl, RED, f'SL  {sl}', 'top'),
            (tp, GREEN, f'TP  {tp}', 'bottom')
        ]:
            ax_main.axhline(y=level, color=color,
                linewidth=1.5,
                linestyle='-' if level==entry else '--',
                alpha=0.9, zorder=5)
            ypos = level+off if pos=='bottom' else level-off
            ax_main.text(n*0.98, ypos,
                label, color=color,
                fontsize=8.5, fontweight='bold',
                ha='right', va=pos,
                fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.3',
                    facecolor=BG2,
                    edgecolor=color, alpha=0.92))

        mid_y = (entry+tp)/2
        ax_main.text(n*0.05, mid_y,
            f'⚖ RR  1:{signal["rr"]}',
            color=YELLOW, fontsize=10,
            fontweight='bold', va='center',
            fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=0.4',
                facecolor=BG2,
                edgecolor=YELLOW, alpha=0.9,
                linewidth=1.5))

        if bull_bos:
            sh_level = signal.get('swing_high_level', entry)
            ax_main.axhline(y=sh_level,
                color=GREEN, linewidth=0.8,
                linestyle=':', alpha=0.5)
            ax_main.text(5, sh_level, '▲ BOS',
                color=GREEN, fontsize=6.5,
                fontweight='bold', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.2',
                    facecolor=BG2,
                    edgecolor=GREEN, alpha=0.8))
        if bear_bos:
            sl_level = signal.get('swing_low_level', entry)
            ax_main.axhline(y=sl_level,
                color=RED, linewidth=0.8,
                linestyle=':', alpha=0.5)
            ax_main.text(5, sl_level, '▼ BOS',
                color=RED, fontsize=6.5,
                fontweight='bold', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.2',
                    facecolor=BG2,
                    edgecolor=RED, alpha=0.8))

        if bull_sweep:
            ax_main.text(n//3,
                float(display_df['Low'].iloc[-5]),
                '⚡ LIQ SWEEP ▲', color=GREEN,
                fontsize=7, fontweight='bold',
                fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.25',
                    facecolor=BG2,
                    edgecolor=GREEN, alpha=0.9))
        if bear_sweep:
            ax_main.text(n//3,
                float(display_df['High'].iloc[-5]),
                '⚡ LIQ SWEEP ▼', color=RED,
                fontsize=7, fontweight='bold',
                fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.25',
                    facecolor=BG2,
                    edgecolor=RED, alpha=0.9))

        grade = ("A+" if signal['score']>=90 else
                 "A" if signal['score']>=80 else
                 "B" if signal['score']>=70 else "C")
        dir_arrow = '▲ LONG' if is_buy else '▼ SHORT'
        session_quality = signal.get('session_quality','GOOD')
        sq_color = (GREEN if session_quality=="BEST" else
                    YELLOW if session_quality=="GOOD" else
                    GRAY)

        ax_main.set_title(
            f"{signal['pair']}  |  {dir_arrow}  |  "
            f"Score: {signal['score']}%  |  Grade: {grade}  |  "
            f"HTF: {signal['htf_bias']}  |  "
            f"ADX: {signal.get('adx','N/A')}  |  "
            f"Session: {signal['session']} [{session_quality}]",
            color=WHITE, fontsize=11,
            fontweight='bold', pad=12,
            fontfamily='monospace', loc='left')

        ax_main.legend(loc='upper left', fontsize=7,
            facecolor=BG2, edgecolor='#21262D',
            labelcolor=GRAY)
        ax_main.tick_params(colors=GRAY, labelsize=7)
        ax_main.yaxis.tick_right()
        ax_main.grid(axis='y', color='#21262D',
            linewidth=0.3, alpha=0.7)
        ax_main.grid(axis='x', color='#21262D',
            linewidth=0.2, alpha=0.3)
        ax_main.set_xlim(-1, n+3)
        plt.setp(ax_main.get_xticklabels(), visible=False)

        try:
            vol_colors = []
            vols = []
            for i in range(n):
                o = float(display_df['Open'].iloc[i])
                c_val = float(display_df['Close'].iloc[i])
                vol_colors.append(GREEN if c_val>=o else RED)
                try:
                    v = float(display_df['Volume'].iloc[i])
                    vols.append(v if not np.isnan(v) else 0)
                except Exception:
                    vols.append(0)
            if any(v > 0 for v in vols):
                ax_vol.bar(range(n), vols,
                    color=vol_colors, alpha=0.5, width=0.8)
                vol_ma = pd.Series(vols).rolling(20).mean()
                ax_vol.plot(range(n), vol_ma,
                    color=YELLOW, linewidth=0.8, alpha=0.7)
        except Exception:
            pass
        ax_vol.set_ylabel('VOL', color=GRAY,
            fontsize=7, fontfamily='monospace')
        ax_vol.tick_params(colors=GRAY, labelsize=6)
        ax_vol.grid(axis='y', color='#21262D',
            linewidth=0.2, alpha=0.5)
        plt.setp(ax_vol.get_xticklabels(), visible=False)

        try:
            close_s = display_df['Close']
            delta = close_s.diff()
            gain = delta.where(delta>0,0)
            loss = -delta.where(delta<0,0)
            rsi_s = 100-(100/(1+
                gain.ewm(span=14,adjust=False).mean()/
                loss.ewm(span=14,adjust=False).mean()))
            rsi_v = rsi_s.values
            ax_rsi.plot(range(n), rsi_v,
                color=PURPLE, linewidth=1.2, zorder=3)
            ax_rsi.fill_between(range(n), rsi_v, 50,
                where=[v>50 for v in rsi_v],
                alpha=0.1, color=GREEN)
            ax_rsi.fill_between(range(n), rsi_v, 50,
                where=[v<50 for v in rsi_v],
                alpha=0.1, color=RED)
            ax_rsi.axhline(y=70, color=RED,
                linewidth=0.5, linestyle='--', alpha=0.5)
            ax_rsi.axhline(y=50, color=GRAY,
                linewidth=0.4, linestyle='--', alpha=0.3)
            ax_rsi.axhline(y=30, color=GREEN,
                linewidth=0.5, linestyle='--', alpha=0.5)
            ax_rsi.set_ylim(0,100)
            ax_rsi.set_yticks([30,50,70])
            crsi = rsi_v[-1] if len(rsi_v)>0 else 50
            rc = RED if crsi>70 else GREEN if crsi<30 else PURPLE
            ax_rsi.text(n-1, crsi, f' {crsi:.0f}',
                color=rc, fontsize=8,
                fontweight='bold', va='center')
        except Exception:
            pass
        ax_rsi.set_ylabel('RSI', color=GRAY,
            fontsize=7, fontfamily='monospace')
        ax_rsi.tick_params(colors=GRAY, labelsize=6)
        ax_rsi.grid(axis='y', color='#21262D',
            linewidth=0.2, alpha=0.5)
        plt.setp(ax_rsi.get_xticklabels(), visible=False)

        try:
            close_s = display_df['Close']
            ema12 = close_s.ewm(span=12,adjust=False).mean()
            ema26 = close_s.ewm(span=26,adjust=False).mean()
            macd_line = ema12-ema26
            signal_line = macd_line.ewm(span=9,adjust=False).mean()
            hist = macd_line-signal_line
            hist_v = hist.values
            hist_colors = [GREEN if v>=0 else RED for v in hist_v]
            ax_macd.bar(range(n), hist_v,
                color=hist_colors, alpha=0.6, width=0.8)
            ax_macd.plot(range(n), macd_line.values,
                color=BLUE, linewidth=0.9, label='MACD')
            ax_macd.plot(range(n), signal_line.values,
                color=YELLOW, linewidth=0.9, label='Signal')
            ax_macd.axhline(y=0, color=GRAY,
                linewidth=0.4, alpha=0.3)
        except Exception:
            pass
        ax_macd.set_ylabel('MACD', color=GRAY,
            fontsize=7, fontfamily='monospace')
        ax_macd.tick_params(colors=GRAY, labelsize=6)
        ax_macd.grid(axis='y', color='#21262D',
            linewidth=0.2, alpha=0.5)
        plt.setp(ax_macd.get_xticklabels(), visible=False)

        ax_info.axis('off')
        reasons_str = "   ✅  ".join(signal['reasons'][:5])
        neg_str = ("   ⚠️  ".join(signal['negative'][:2])
            if signal.get('negative') else "")
        info1 = (
            f"  ENTRY: {signal['entry']}    "
            f"SL: {signal['sl']}    "
            f"TP: {signal['tp']}    "
            f"RR: 1:{signal['rr']}    "
            f"RSI: {signal['rsi']}    "
            f"ADX: {signal.get('adx','N/A')}    "
            f"Pattern: {candle_pattern}    "
            f"Market: {signal['regime']}  ")
        info2 = "  ✅  " + reasons_str + "  "
        ax_info.text(0, 0.75, info1,
            color=GRAY, fontsize=8,
            ha='left', va='center',
            fontfamily='monospace',
            transform=ax_info.transAxes,
            bbox=dict(boxstyle='round,pad=0.4',
                facecolor=BG2, edgecolor='#21262D',
                alpha=0.9))
        ax_info.text(0, 0.2, info2,
            color=GREEN, fontsize=8,
            ha='left', va='center',
            fontfamily='monospace',
            transform=ax_info.transAxes,
            bbox=dict(boxstyle='round,pad=0.4',
                facecolor='#0D2818',
                edgecolor=GREEN, alpha=0.9))
        if neg_str:
            ax_info.text(0.65, 0.2,
                "  ⚠️  "+neg_str+"  ",
                color=YELLOW, fontsize=7.5,
                ha='left', va='center',
                fontfamily='monospace',
                transform=ax_info.transAxes,
                bbox=dict(boxstyle='round,pad=0.3',
                    facecolor='#1A1500',
                    edgecolor=YELLOW, alpha=0.9))

        fig.text(0.99, 0.995,
            f"AI Trading Scanner  ·  {signal['time']}  ·  "
            f"Confluences: {signal['confluences']}",
            color='#333333', fontsize=7,
            ha='right', va='top',
            fontfamily='monospace')

        plt.subplots_adjust(
            left=0.02, right=0.97,
            top=0.96, bottom=0.01)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150,
            bbox_inches='tight', facecolor=BG,
            edgecolor='none')
        buf.seek(0)
        image_bytes = buf.read()
        plt.close(fig)
        return image_bytes
    except Exception:
        return None

def get_asia_session_pairs():
    return ["USDJPY","EURJPY","GBPJPY","AUDCAD","XAUUSD"]

def get_session_min_score():
    session_quality, session = get_session_quality()
    if session_quality == "BEST":
        return 80
    elif session_quality == "GOOD":
        return 80
    elif session_quality == "MODERATE":
        return 88
    return 95

def analyze_pair_advanced(symbol):
    try:
        session_quality, session_name = get_session_quality()

        if session_quality == "POOR":
            return None

        is_asia = session_quality == "MODERATE"
        if is_asia and symbol not in get_asia_session_pairs():
            return None

        df_5m = get_data(symbol, interval="5m")
        if df_5m is None or len(df_5m) < 60:
            return None

        score = 0
        reasons = []
        neg = []
        confluences = 0

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

        close = float(df_5m['Close'].iloc[-1])
        ema8 = float(calculate_ema(df_5m,8).iloc[-1])
        ema21 = float(calculate_ema(df_5m,21).iloc[-1])
        ema50 = float(calculate_ema(df_5m,50).iloc[-1])

        is_bull = bull_bos or bull_fvg or bull_sweep or bull_choch or candle_dir=="BULLISH"
        is_bear = bear_bos or bear_fvg or bear_sweep or bear_choch or candle_dir=="BEARISH"

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
            score += 20; reasons.append("HTF Bullish"); confluences += 1
        elif htf_bias == "BEARISH" and direction == "SELL":
            score += 20; reasons.append("HTF Bearish"); confluences += 1
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
            score -= 10; neg.append("Weak Trend")

        if regime == "VOLATILE":
            score -= 20; neg.append("High Volatility")
        elif regime == "RANGING" and adx < 20:
            score -= 10; neg.append("Ranging Market")
        elif (regime=="TRENDING UP" and direction=="BUY") or \
             (regime=="TRENDING DOWN" and direction=="SELL"):
            score += 10; reasons.append("Trend Alignment"); confluences += 1

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
                score += 8; reasons.append("EMA Stack Bull"); confluences += 1
            elif ema8 < ema21:
                score -= 5; neg.append("EMA Conflict")
        else:
            if ema8 < ema21 < ema50:
                score += 8; reasons.append("EMA Stack Bear"); confluences += 1
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
            score += 10
            reasons.append("Best Session - London+NY Overlap")
        elif session_quality == "GOOD":
            score += 5
            reasons.append(session_name+" Session")
        elif session_quality == "MODERATE":
            score += 0
            reasons.append("Asia Session")
            neg.append("Moderate Session")

        news = st.session_state.get('cached_news', [])
        if [n for n in news if n['impact']==3]:
            score -= 20; neg.append("High Impact News!")

        min_confluences = 5 if is_asia else 4
        if confluences < min_confluences:
            return None

        score = min(max(score,0), 95)

        min_score = get_session_min_score()
        if score < min_score and not is_asia:
            pass

        sl = calculate_structure_sl_advanced(
            df_5m, direction, atr, swing_highs, swing_lows)
        sl_dist = abs(close-sl)
        if sl_dist < atr*0.5:
            sl = close-atr*1.5 if direction=="BUY" else close+atr*1.5
            sl_dist = abs(close-sl)
        if sl_dist > atr*4:
            sl = close-atr*2 if direction=="BUY" else close+atr*2
            sl_dist = abs(close-sl)

        entry = close
        tp_mult = 2.5 if adx > 30 else 2.0
        tp = round(entry+sl_dist*tp_mult if direction=="BUY"
            else entry-sl_dist*tp_mult, 5)

        return {
            "pair": symbol,
            "direction": direction,
            "score": score,
            "entry": round(entry,5),
            "sl": round(sl,5),
            "tp": round(tp,5),
            "rr": round(tp_mult,1),
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
                            j['pnl'] = 0
                    continue
                df = get_data(trade['pair'], interval="5m")
                if df is None:
                    continue
                ch = float(df['High'].iloc[-1])
                cl = float(df['Low'].iloc[-1])
                entry = trade['entry']
                sl = trade['sl']
                tp = trade['tp']
                direction = trade['direction']
                if direction == "BUY":
                    if ch >= tp:
                        for j in st.session_state.trade_journal:
                            if j['id'] == trade['id']:
                                j['result'] = "TP Hit"
                                j['pnl'] = trade['rr']
                        send_discord_alert(
                            "✅ **TP HIT! TRADE WON!** 🎯\n\n"
                            "**" + trade['pair'] + " BUY**\n"
                            "Entry: " + str(entry) + "\n"
                            "TP: " + str(tp) + "\n"
                            "RR: 1:" + str(trade['rr']) + "\n"
                            "Time: " + get_ist_time().strftime('%H:%M IST'))
                    elif cl <= sl:
                        for j in st.session_state.trade_journal:
                            if j['id'] == trade['id']:
                                j['result'] = "SL Hit"
                                j['pnl'] = -1
                        send_discord_alert(
                            "❌ **SL HIT! TRADE LOST!**\n\n"
                            "**" + trade['pair'] + " BUY**\n"
                            "Entry: " + str(entry) + "\n"
                            "SL: " + str(sl) + "\n"
                            "Time: " + get_ist_time().strftime('%H:%M IST'))
                else:
                    if cl <= tp:
                        for j in st.session_state.trade_journal:
                            if j['id'] == trade['id']:
                                j['result'] = "TP Hit"
                                j['pnl'] = trade['rr']
                        send_discord_alert(
                            "✅ **TP HIT! TRADE WON!** 🎯\n\n"
                            "**" + trade['pair'] + " SELL**\n"
                            "Entry: " + str(entry) + "\n"
                            "TP: " + str(tp) + "\n"
                            "RR: 1:" + str(trade['rr']) + "\n"
                            "Time: " + get_ist_time().strftime('%H:%M IST'))
                    elif ch >= sl:
                        for j in st.session_state.trade_journal:
                            if j['id'] == trade['id']:
                                j['result'] = "SL Hit"
                                j['pnl'] = -1
                        send_discord_alert(
                            "❌ **SL HIT! TRADE LOST!**\n\n"
                            "**" + trade['pair'] + " SELL**\n"
                            "Entry: " + str(entry) + "\n"
                            "SL: " + str(sl) + "\n"
                            "Time: " + get_ist_time().strftime('%H:%M IST'))
            except Exception:
                pass
    except Exception:
        pass

def format_discord_message(signal):
    grade = ("A+" if signal['score']>=90 else
             "A" if signal['score']>=80 else
             "B" if signal['score']>=70 else "C")
    emoji = "🟢 BUY" if signal['direction']=="BUY" else "🔴 SELL"
    reasons_text = "\n".join(["✅ "+r for r in signal['reasons']])
    neg_text = "\n".join(["⚠️ "+n for n in signal['negative']])
    instr = ("📍 **Enter BUY at or below: "+str(signal['entry'])+"**"
        if signal['direction']=="BUY"
        else "📍 **Enter SELL at or above: "+str(signal['entry'])+"**")
    sq = signal.get('session_quality','GOOD')
    sq_emoji = "⭐⭐⭐" if sq=="BEST" else "⭐⭐" if sq=="GOOD" else "⭐"
    msg = (
        "🚨 **HIGH CONFIDENCE SIGNAL** 🚨\n\n"
        "**"+emoji+" "+signal['pair']+"**\n\n"
        "📊 Score: "+str(signal['score'])+"%\n"
        "🏆 Grade: "+grade+"\n"
        "🔗 Confluences: "+str(signal['confluences'])+"\n"
        "📐 Pattern: "+signal.get('candle_pattern','N/A')+"\n"
        "📉 ADX: "+str(signal.get('adx','N/A'))+"\n"
        "🕐 Session: "+signal['session']+" "+sq_emoji+"\n\n"
        +instr+"\n"
        "💰 Entry: "+str(signal['entry'])+"\n"
        "🛑 SL: "+str(signal['sl'])+"\n"
        "🎯 TP: "+str(signal['tp'])+"\n"
        "⚖️ RR: 1:"+str(signal['rr'])+"\n\n"
        "📈 HTF: "+signal['htf_bias']+"\n"
        "🌍 Market: "+signal['regime']+"\n"
        "📉 RSI: "+str(signal['rsi'])+"\n\n"
        "⏰ Time: "+signal['time']+"\n"
        "🤖 Auto TP/SL tracking active!\n\n"
        "⚠️ Skip if price moved >"+str(signal['atr'])+" away!\n\n"
        "✅ **Reasons:**\n"+reasons_text+"\n")
    if signal['negative']:
        msg += "\n⚠️ **Caution:**\n"+neg_text+"\n"
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━"
    return msg

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
        "rsi": signal['rsi'],
        "htf_bias": signal['htf_bias'],
        "regime": signal['regime'],
        "session": signal['session'],
        "confluences": signal['confluences'],
        "reasons": signal['reasons'],
        "candle_pattern": signal.get('candle_pattern',''),
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
        return {"total":0,"wins":0,"losses":0,
                "pending":0,"win_rate":0,
                "best_pair":"N/A","best_session":"N/A"}
    completed = [j for j in journal
        if j['result'] not in ["Pending","Expired"]]
    wins = [j for j in completed if j['result']=="TP Hit"]
    losses = [j for j in completed if j['result']=="SL Hit"]
    win_rate = len(wins)/len(completed)*100 if completed else 0
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
        "best_session": max(session_wins,key=session_wins.get) if session_wins else "N/A"
    }

def get_active_pairs():
    enabled = st.session_state.get('enabled_pairs', {})
    if not enabled:
        return ALL_PAIRS
    active = [p for p in ALL_PAIRS if enabled.get(p, True)]
    return active if active else ALL_PAIRS

for key, val in [
    ('scanner_running',False),
    ('logged_in',False),
    ('user_email',None),
    ('user_id',None),
    ('signals',[]),
    ('alerts_sent',0),
    ('total_scans',0),
    ('last_scan_time',None),
    ('next_scan_seconds',300),
    ('sent_signal_ids',set()),
    ('trade_journal',[]),
    ('cached_news',[]),
    ('last_news_fetch',None),
    ('show_reset',False),
    ('last_outcome_check',None),
    ('enabled_pairs',{p:True for p in ALL_PAIRS}),
    ('scanner_was_running_before_disconnect',False),
    ('was_disconnected',False),
    ('startup_check_done',False)
]:
    if key not in st.session_state:
        st.session_state[key] = val

def refresh_news():
    try:
        now = get_ist_time()
        if (st.session_state.last_news_fetch is None or
            int((now-st.session_state.last_news_fetch
                ).total_seconds()) >= 900):
            st.session_state.cached_news = fetch_forex_news()
            st.session_state.last_news_fetch = now
    except Exception:
        pass

def run_scan():
    refresh_news()
    check_signal_outcomes()
    active_pairs = get_active_pairs()
    session_quality, _ = get_session_quality()
    if session_quality == "MODERATE":
        asia_pairs = get_asia_session_pairs()
        active_pairs = [p for p in active_pairs
            if p in asia_pairs]
    found = []
    new_high = []
    for pair in active_pairs:
        result = analyze_pair_advanced(pair)
        if result:
            found.append(result)
            min_score = get_session_min_score()
            if result['score'] >= min_score:
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
         ['df','fvg_zones','ob_found','ob_top','ob_bottom',
          'ob_index','bull_bos','bear_bos',
          'swing_highs','swing_lows',
          'swing_high_level','swing_low_level',
          'bull_sweep','bear_sweep']}
        for s in found]
    st.session_state.total_scans += 1
    st.session_state.last_scan_time = get_ist_time()

def auto_scan():
    try:
        now = get_ist_time()
        if st.session_state.last_scan_time is None:
            run_scan()
            return
        elapsed = int((now-st.session_state.last_scan_time
            ).total_seconds())
        if elapsed >= st.session_state.next_scan_seconds:
            run_scan()
        last_check = st.session_state.last_outcome_check
        if (last_check is None or
            int((now-last_check).total_seconds()) >= 60):
            check_signal_outcomes()
            st.session_state.last_outcome_check = now
    except Exception:
        pass

def main():
    st.markdown(CYBER_CSS, unsafe_allow_html=True)

    if not st.session_state.startup_check_done:
        st.session_state.startup_check_done = True
        handle_startup_reconnect()

    if not st.session_state.logged_in:
        show_login_page()
    else:
        if st.session_state.scanner_running:
            auto_scan()
        show_dashboard()

def show_login_page():
    st.markdown("""
    <div style='text-align:center; padding:50px 20px 30px'>
        <div style='font-family:Orbitron,monospace;
            font-size:2.5em; font-weight:900;
            color:#00FF88;
            text-shadow:0 0 20px rgba(0,255,136,0.6),
                        0 0 40px rgba(0,255,136,0.3);
            letter-spacing:3px; margin-bottom:10px'>
        ⬡ AI TRADING SCANNER</div>
        <div style='font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.95em;
            letter-spacing:4px; margin-bottom:8px'>
        PROFESSIONAL FOREX & INDICES INTELLIGENCE</div>
        <div style='font-family:Exo 2,sans-serif;
            color:rgba(0,255,136,0.4);
            font-size:0.8em; letter-spacing:2px'>
        XAUUSD · EURUSD · GBPUSD · USDJPY · GBPJPY ·
        EURJPY · AUDCAD · US30 · NAS100</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        if st.session_state.show_reset:
            st.markdown(
                "<h3 style='color:#00FF88;font-family:"
                "Orbitron,monospace;text-align:center'>"
                "🔑 RESET PASSWORD</h3>",
                unsafe_allow_html=True)
            reset_email = st.text_input("Email",
                key="reset_email")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Send Reset Email",
                    use_container_width=True,
                    type="primary"):
                    success, msg = reset_password(reset_email)
                    st.success(msg) if success else st.error(msg)
            with col_b:
                if st.button("← Back",
                    use_container_width=True):
                    st.session_state.show_reset = False
                    st.rerun()
        else:
            tab1, tab2 = st.tabs(["🔑  LOGIN","📝  SIGN UP"])
            with tab1:
                st.markdown("<br>", unsafe_allow_html=True)
                email = st.text_input("Email",
                    key="login_email",
                    placeholder="your@email.com")
                password = st.text_input("Password",
                    type="password",
                    key="login_pass",
                    placeholder="••••••••")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⚡ ENTER SCANNER",
                    use_container_width=True,
                    type="primary"):
                    if email and password:
                        success, msg = login_user(email, password)
                        if success:
                            st.success("✅ "+msg)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ "+msg)
                    else:
                        st.error("Please enter email and password!")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Forgot Password?",
                    use_container_width=True):
                    st.session_state.show_reset = True
                    st.rerun()
            with tab2:
                st.markdown("<br>", unsafe_allow_html=True)
                new_email = st.text_input("Email",
                    key="signup_email",
                    placeholder="your@email.com")
                new_pass = st.text_input("Password",
                    type="password",
                    key="signup_pass",
                    placeholder="Min 6 characters")
                confirm_pass = st.text_input(
                    "Confirm Password",
                    type="password",
                    key="confirm_pass",
                    placeholder="Repeat password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🚀 CREATE ACCOUNT",
                    use_container_width=True,
                    type="primary"):
                    if new_email and new_pass and confirm_pass:
                        if new_pass == confirm_pass:
                            if len(new_pass) < 6:
                                st.error("Min 6 characters!")
                            else:
                                success, msg = signup_user(
                                    new_email, new_pass)
                                st.success("✅ "+msg) if success else st.error("❌ "+msg)
                        else:
                            st.error("Passwords do not match!")
                    else:
                        st.error("Please fill all fields!")

    st.markdown("""
    <div style='text-align:center; margin-top:30px;
        display:flex; justify-content:center;
        gap:12px; flex-wrap:wrap'>
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid rgba(0,255,136,0.2);
            border-radius:10px; padding:10px 15px;
            font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.82em'>
            🧠 Advanced SMC + ICT</div>
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid rgba(0,255,136,0.2);
            border-radius:10px; padding:10px 15px;
            font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.82em'>
            📊 5-Panel Charts</div>
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid rgba(0,255,136,0.2);
            border-radius:10px; padding:10px 15px;
            font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.82em'>
            🌏 Asia+London+NY Sessions</div>
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid rgba(0,255,136,0.2);
            border-radius:10px; padding:10px 15px;
            font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.82em'>
            🎯 Pair Selection Control</div>
    </div>
    """, unsafe_allow_html=True)

def show_dashboard():
    session_quality, session_name = get_session_quality()
    news = st.session_state.get('cached_news',[])
    high_impact = [n for n in news if n['impact']==3]
    stats = calculate_stats()
    active_pairs = get_active_pairs()

    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding:12px 0'>
            <div style='font-family:Orbitron,monospace;
                font-size:1em; font-weight:700;
                color:#00FF88;
                text-shadow:0 0 10px rgba(0,255,136,0.5);
                letter-spacing:2px'>⬡ AI SCANNER</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid rgba(0,255,136,0.15);
            border-radius:10px; padding:8px;
            margin:4px 0; font-family:Exo 2,sans-serif'>
            <div style='color:#8899AA;font-size:0.7em'>👤</div>
            <div style='color:#FFFFFF;font-size:0.78em;
                word-break:break-all'>
        """ + str(st.session_state.user_email) + """
        </div></div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style='background:rgba(0,150,255,0.05);
            border:1px solid rgba(0,150,255,0.15);
            border-radius:10px; padding:8px;
            margin:4px 0; font-family:Orbitron,monospace;
            text-align:center'>
            <div style='color:#0096FF; font-size:0.9em'>
        """ + get_ist_time().strftime('%H:%M:%S IST') + """
        </div></div>""", unsafe_allow_html=True)

        sq_color = ("#00FF88" if session_quality=="BEST"
            else "#FFAA00" if session_quality in ["GOOD","MODERATE"]
            else "#FF4444")
        sq_emoji = ("⭐⭐⭐" if session_quality=="BEST"
            else "⭐⭐" if session_quality=="GOOD"
            else "⭐" if session_quality=="MODERATE"
            else "⚠️")
        st.markdown(f"""
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid {sq_color}44;
            border-radius:8px; padding:6px;
            text-align:center; margin:4px 0;
            font-family:Exo 2,sans-serif;
            color:{sq_color}; font-size:0.82em'>
            {sq_emoji} {session_name}
        </div>
        """, unsafe_allow_html=True)

        if high_impact:
            st.error("🚨 HIGH IMPACT NEWS!")

        st.markdown(f"""
        <div style='background:rgba(0,255,136,0.03);
            border:1px solid rgba(0,255,136,0.1);
            border-radius:8px; padding:6px;
            text-align:center; margin:4px 0;
            font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.78em'>
            📡 Scanning {len(active_pairs)}/9 pairs
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
        page = st.radio("📍 Navigation", [
            "🏠 Dashboard",
            "📊 Active Signals",
            "📰 News & Calendar",
            "📓 Trade Journal",
            "📈 Performance",
            "📅 Calendar",
            "⚙️ Settings"
        ])
        st.divider()
        if st.button("🚪 Logout",
            use_container_width=True):
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
    <div class='cyber-title' style='font-size:1.8em;
        margin-bottom:15px'>🏠 DASHBOARD</div>
    """, unsafe_allow_html=True)

    session_quality, session_name = get_session_quality()
    news = st.session_state.get('cached_news',[])
    high_impact = [n for n in news if n['impact']==3]
    stats = calculate_stats()
    active_pairs = get_active_pairs()

    if st.session_state.get('was_disconnected', False) == False and \
       st.session_state.get('scanner_was_running_before_disconnect', False):
        st.success("🟢 Network reconnected! Scanner auto-resumed!")

    if high_impact:
        st.error("🚨 HIGH IMPACT NEWS — Signals paused!")

    if session_quality == "MODERATE":
        st.markdown("""
        <div style='background:rgba(255,170,0,0.08);
            border:1px solid rgba(255,170,0,0.3);
            border-radius:10px; padding:10px;
            margin-bottom:10px;
            font-family:Exo 2,sans-serif;
            color:#FFAA00; font-size:0.9em'>
            ⭐ Asia Session Active — Only JPY/XAU pairs
            scanning with stricter filters (88%+ required)
        </div>
        """, unsafe_allow_html=True)
    elif session_quality == "POOR":
        st.warning("⚠️ Off Session — Scanner paused, waiting for Asia/London/NY")

    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if not st.session_state.scanner_running:
            st.markdown("""
            <div style='text-align:center;
                background:rgba(255,68,68,0.05);
                border:1px solid rgba(255,68,68,0.2);
                border-radius:12px; padding:20px;
                margin-bottom:10px'>
                <div style='font-family:Orbitron,monospace;
                    color:#8899AA; font-size:0.8em;
                    letter-spacing:3px'>SCANNER STATUS</div>
                <div style='font-family:Orbitron,monospace;
                    color:#FF4444; font-size:1.4em;
                    font-weight:700; margin:8px 0'>
                ● OFFLINE</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("▶ ACTIVATE SCANNER",
                use_container_width=True,
                type="primary"):
                st.session_state.scanner_running = True
                st.session_state.last_scan_time = None
                st.session_state.sent_signal_ids = set()
                st.session_state.scanner_was_running_before_disconnect = False
                active = get_active_pairs()
                send_discord_alert(
                    "🟢 **AI Trading Scanner ACTIVATED!**\n"
                    "Advanced SMC+ICT+ADX+EMA Analysis\n"
                    "Session: " + session_name +
                    " [" + session_quality + "]\n"
                    "Scanning " + str(len(active)) + " pairs: " +
                    ", ".join(active) + "\n"
                    "Auto TP/SL tracking: Active!\n"
                    "⚠️ Network disconnect → Scanner auto-pauses\n"
                    "⚠️ Network reconnect → Scanner auto-resumes\n"
                    "User: " + str(st.session_state.user_email) +
                    "\nTime: " + get_ist_time().strftime(
                        '%d %b %Y %H:%M IST'))
                st.rerun()
        else:
            st.markdown("""
            <div style='text-align:center;
                background:rgba(0,255,136,0.08);
                border:1px solid rgba(0,255,136,0.4);
                border-radius:12px; padding:20px;
                margin-bottom:10px;
                box-shadow:0 0 20px rgba(0,255,136,0.1)'>
                <div style='font-family:Orbitron,monospace;
                    color:#8899AA; font-size:0.8em;
                    letter-spacing:3px'>SCANNER STATUS</div>
                <div style='font-family:Orbitron,monospace;
                    color:#00FF88; font-size:1.4em;
                    font-weight:700; margin:8px 0;
                    text-shadow:0 0 15px rgba(0,255,136,0.8)'>
                ● ACTIVE</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⏹ DEACTIVATE SCANNER",
                use_container_width=True):
                st.session_state.scanner_running = False
                st.session_state.scanner_was_running_before_disconnect = False
                send_discord_alert(
                    "🔴 **AI Trading Scanner DEACTIVATED!**\n"
                    "Scans: " + str(st.session_state.total_scans) +
                    "\nAlerts: " + str(st.session_state.alerts_sent))
                st.rerun()

    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Scanner",
            "🟢 ACTIVE" if st.session_state.scanner_running
            else "🔴 OFFLINE")
    with col2:
        st.metric("Win Rate", str(stats['win_rate'])+"%")
    with col3:
        st.metric("Alerts Sent", st.session_state.alerts_sent)
    with col4:
        st.metric("Total Scans", st.session_state.total_scans)

    st.divider()

    if st.session_state.scanner_running:
        if st.session_state.last_scan_time:
            elapsed = int((get_ist_time()-
                st.session_state.last_scan_time).total_seconds())
            remaining = max(0,
                st.session_state.next_scan_seconds-elapsed)
            progress_val = min(1.0,
                elapsed/st.session_state.next_scan_seconds)
            st.info("⏱️ Last: " +
                st.session_state.last_scan_time.strftime('%H:%M:%S IST') +
                " | Next in: " + str(remaining) + "s" +
                " | Session: " + session_name)
            st.progress(progress_val)
        else:
            st.info("⚡ Initializing first scan...")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚡ SCAN NOW",
                type="primary",
                use_container_width=True):
                with st.spinner("Advanced scanning..."):
                    run_scan()
                st.success("✅ Complete!")
                st.rerun()
        with col2:
            if st.button("🔃 REFRESH",
                use_container_width=True):
                st.rerun()

    st.divider()
    st.markdown("""
    <div style='font-family:Orbitron,monospace;
        color:#00FF88; font-size:0.85em;
        letter-spacing:2px; margin-bottom:12px;
        opacity:0.8'>📡 ACTIVE PAIRS</div>
    """, unsafe_allow_html=True)

    enabled = st.session_state.get(
        'enabled_pairs', {p:True for p in ALL_PAIRS})
    cols = st.columns(3)
    for i, pair in enumerate(ALL_PAIRS):
        with cols[i % 3]:
            is_on = enabled.get(pair, True)
            color = "#00FF88" if is_on else "#445566"
            bg = "rgba(0,255,136,0.08)" if is_on else "rgba(255,255,255,0.02)"
            border = "rgba(0,255,136,0.4)" if is_on else "rgba(255,255,255,0.08)"
            st.markdown(f"""
            <div style='background:{bg};
                border:1px solid {border};
                border-radius:10px; padding:10px;
                text-align:center; margin-bottom:8px;
                font-family:Orbitron,monospace;
                color:{color}; font-size:0.85em;
                letter-spacing:1px'>{pair}
                {"✅" if is_on else "❌"}
            </div>
            """, unsafe_allow_html=True)

    if st.session_state.scanner_running:
        time.sleep(1)
        st.rerun()

def show_news_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.8em;
        margin-bottom:15px'>📰 NEWS & CALENDAR</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh News",
            use_container_width=True, type="primary"):
            with st.spinner("Fetching..."):
                st.session_state.cached_news = fetch_forex_news()
                st.session_state.last_news_fetch = get_ist_time()
            st.success("✅ Refreshed!")
            st.rerun()
    with col2:
        if st.session_state.last_news_fetch:
            st.info("Updated: " +
                st.session_state.last_news_fetch.strftime('%H:%M:%S IST'))

    st.divider()
    st.subheader("📅 Economic Calendar")
    for event in get_economic_calendar():
        imp_emoji = ("🔴" if event['impact']=="High" else
                     "🟡" if event['impact']=="Medium" else "🟢")
        with st.expander(
            imp_emoji+" "+event['time']+
            " | "+event['event']+
            " ("+event['currency']+")"):
            col1,col2,col3 = st.columns(3)
            with col1:
                st.metric("Impact", event['impact'])
            with col2:
                st.metric("Forecast", event['forecast'])
            with col3:
                st.metric("Previous", event['previous'])

    st.divider()
    st.subheader("📰 Live News")
    news = st.session_state.get('cached_news',[])
    if not news:
        st.info("Click Refresh News!")
        if st.button("📰 Load Now",
            use_container_width=True):
            with st.spinner("Loading..."):
                st.session_state.cached_news = fetch_forex_news()
                st.session_state.last_news_fetch = get_ist_time()
            st.rerun()
    else:
        for item in [n for n in news if n['impact']==3]:
            with st.expander("🔴 "+item['title'][:80]):
                st.write("📰 "+item['source'])
                if item['summary']:
                    st.write(item['summary'])
                st.markdown("[Read →]("+item['link']+")")
        for item in [n for n in news if n['impact']==2][:5]:
            with st.expander("🟡 "+item['title'][:80]):
                st.write("📰 "+item['source'])
                if item['summary']:
                    st.write(item['summary'])
                st.markdown("[Read →]("+item['link']+")")
        for item in [n for n in news if n['impact']==1][:5]:
            st.write("🟢 "+item['title'][:100]+
                " | "+item['source'])

def show_signals_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.8em;
        margin-bottom:15px'>📊 ACTIVE SIGNALS</div>
    """, unsafe_allow_html=True)

    news = st.session_state.get('cached_news',[])
    if [n for n in news if n['impact']==3]:
        st.error("🚨 HIGH IMPACT NEWS — Extra caution!")

    if not st.session_state.signals:
        st.markdown("""
        <div style='text-align:center;
            padding:50px 20px;
            font-family:Exo 2,sans-serif;
            color:#8899AA'>
            <div style='font-size:3em;
                margin-bottom:15px'>📡</div>
            <div>No signals yet. Activate scanner.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    high = [s for s in st.session_state.signals if s['score']>=80]
    medium = [s for s in st.session_state.signals if 60<=s['score']<80]
    low = [s for s in st.session_state.signals if s['score']<60]

    if high:
        st.markdown("""
        <div style='font-family:Orbitron,monospace;
            color:#00FF88; font-size:0.85em;
            letter-spacing:2px; margin-bottom:10px'>
        🟢 HIGH CONFIDENCE — 80%+</div>
        """, unsafe_allow_html=True)
        for signal in high:
            age = get_signal_age(signal['time'])
            status = get_signal_status(age)
            sq = signal.get('session_quality','GOOD')
            sq_badge = ("⭐⭐⭐" if sq=="BEST" else
                        "⭐⭐" if sq=="GOOD" else "⭐")
            with st.expander(
                "🟢 "+signal['pair']+" "+
                signal['direction']+"  |  "+
                str(signal['score'])+"%  |  "+
                str(signal['confluences'])+" conf  |  "+
                sq_badge+"  |  "+status):
                col1,col2,col3 = st.columns(3)
                with col1:
                    st.metric("Entry", signal['entry'])
                with col2:
                    st.metric("Stop Loss", signal['sl'])
                with col3:
                    st.metric("Take Profit", signal['tp'])
                if age >= 30:
                    st.error("⛔ EXPIRED!")
                elif age >= 15:
                    st.warning("⚠️ Aging — verify price!")
                else:
                    if signal['direction'] == "BUY":
                        st.success("✅ Enter BUY at or below: "+str(signal['entry']))
                    else:
                        st.success("✅ Enter SELL at or above: "+str(signal['entry']))
                col1,col2 = st.columns(2)
                with col1:
                    st.write("⚖️ RR: 1:"+str(signal['rr']))
                    st.write("📈 HTF: "+signal['htf_bias'])
                    st.write("🌍 Market: "+signal['regime'])
                with col2:
                    st.write("🕐 Session: "+signal['session'])
                    st.write("📉 RSI: "+str(signal['rsi']))
                    st.write("📐 ADX: "+str(signal.get('adx','N/A')))
                st.write("📐 Pattern: "+signal.get('candle_pattern','N/A'))
                st.write("✅ "+" | ".join(signal['reasons']))
                if signal.get('negative'):
                    st.warning("⚠️ "+" | ".join(signal['negative']))

    if medium:
        st.markdown("""
        <div style='font-family:Orbitron,monospace;
            color:#FFAA00; font-size:0.85em;
            letter-spacing:2px; margin:12px 0 8px'>
        🟡 MEDIUM — 60-80%</div>
        """, unsafe_allow_html=True)
        for signal in medium:
            with st.expander(
                "🟡 "+signal['pair']+" "+
                signal['direction']+"  |  "+
                str(signal['score'])+"%"):
                col1,col2,col3 = st.columns(3)
                with col1:
                    st.metric("Entry", signal['entry'])
                with col2:
                    st.metric("SL", signal['sl'])
                with col3:
                    st.metric("TP", signal['tp'])

    if low:
        st.markdown("""
        <div style='font-family:Orbitron,monospace;
            color:#FF4444; font-size:0.85em;
            letter-spacing:2px; margin:12px 0 8px'>
        🔴 LOW — Below 60%</div>
        """, unsafe_allow_html=True)
        for signal in low:
            st.write("🔴 "+signal['pair']+
                " | "+str(signal['score'])+"%")

def show_journal_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.8em;
        margin-bottom:15px'>📓 TRADE JOURNAL</div>
    """, unsafe_allow_html=True)

    journal = st.session_state.trade_journal
    if not journal:
        st.info("No trades yet!")
        return

    if st.button("🔄 Check TP/SL Now",
        use_container_width=True, type="primary"):
        with st.spinner("Checking..."):
            check_signal_outcomes()
        st.success("✅ Updated!")
        st.rerun()

    pending = [j for j in journal if j['result']=="Pending"]
    if pending:
        st.subheader("⏳ Pending — Auto tracking active")
        for trade in pending:
            with st.expander(
                "⏳ "+trade['pair']+" "+
                trade['direction']+"  |  "+
                str(trade['score'])+"%  |  "+
                trade['time']):
                col1,col2,col3 = st.columns(3)
                with col1:
                    st.metric("Entry", trade['entry'])
                with col2:
                    st.metric("SL", trade['sl'])
                with col3:
                    st.metric("TP", trade['tp'])
                st.info("🤖 Auto tracking every 60s!")
                result = st.selectbox(
                    "Manual Override",
                    ["Pending","TP Hit","SL Hit",
                     "Expired","Partial Win"],
                    key="result_"+trade['id'])
                if st.button("✅ Override",
                    key="update_"+trade['id'],
                    use_container_width=True):
                    for j in st.session_state.trade_journal:
                        if j['id'] == trade['id']:
                            j['result'] = result
                            j['pnl'] = (trade['rr'] if result=="TP Hit"
                                else -1 if result=="SL Hit"
                                else 0.5 if result=="Partial Win"
                                else 0)
                    st.success("Updated!")
                    st.rerun()
    else:
        st.success("✅ All trades have results!")

    st.divider()
    st.subheader("📋 All Trades")
    for trade in reversed(journal):
        emoji = ("✅" if trade['result']=="TP Hit" else
                 "❌" if trade['result']=="SL Hit" else
                 "⚠️" if trade['result']=="Partial Win" else
                 "🔴" if trade['result']=="Expired" else "⏳")
        rc = ("color:#00FF88" if trade['result']=="TP Hit" else
              "color:#FF4444" if trade['result']=="SL Hit" else
              "color:#8899AA")
        st.markdown(f"""
        <div style='background:rgba(255,255,255,0.02);
            border:1px solid rgba(255,255,255,0.06);
            border-radius:8px; padding:8px 12px;
            margin-bottom:4px;
            font-family:Exo 2,sans-serif'>
            {emoji} <b>{trade['pair']} {trade['direction']}</b>
            | {trade['score']}%
            | <span style='{rc}'><b>{trade['result']}</b></span>
            | {trade['time']}
        </div>
        """, unsafe_allow_html=True)

def show_performance_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.8em;
        margin-bottom:15px'>📈 PERFORMANCE</div>
    """, unsafe_allow_html=True)

    stats = calculate_stats()
    if stats['total'] == 0:
        st.info("No completed trades yet!")
        return

    col1,col2,col3,col4 = st.columns(4)
    with col1:
        st.metric("Total", stats['total'])
    with col2:
        st.metric("✅ Wins", stats['wins'])
    with col3:
        st.metric("❌ Losses", stats['losses'])
    with col4:
        st.metric("🏆 Win Rate", str(stats['win_rate'])+"%")

    st.divider()
    col1,col2 = st.columns(2)
    with col1:
        st.metric("🥇 Best Pair", stats['best_pair'])
    with col2:
        st.metric("⭐ Best Session", stats['best_session'])

    journal = st.session_state.trade_journal
    completed = [j for j in journal
        if j['result'] not in ["Pending","Expired"]]
    if completed:
        st.divider()
        st.subheader("📊 Win Rate by Pair")
        pair_stats = {}
        for j in completed:
            if j['pair'] not in pair_stats:
                pair_stats[j['pair']] = {'wins':0,'total':0}
            pair_stats[j['pair']]['total'] += 1
            if j['result'] == "TP Hit":
                pair_stats[j['pair']]['wins'] += 1
        for pair, data in sorted(pair_stats.items(),
            key=lambda x: x[1]['wins']/x[1]['total'],
            reverse=True):
            wr = round(data['wins']/data['total']*100,1)
            bar = "█"*int(wr/5)+"░"*(20-int(wr/5))
            color = ("#00FF88" if wr>=60 else
                     "#FFAA00" if wr>=40 else "#FF4444")
            st.markdown(f"""
            <div style='font-family:Exo 2,sans-serif;
                margin-bottom:6px; padding:8px 12px;
                background:rgba(255,255,255,0.02);
                border-radius:8px'>
                <span style='color:#FFFFFF;
                    font-weight:600'>{pair}</span>
                <span style='color:{color};
                    font-family:monospace;
                    margin-left:10px'>{bar}</span>
                <span style='color:{color};
                    margin-left:10px'>{wr}%</span>
                <span style='color:#8899AA;
                    font-size:0.85em'>
                ({data['wins']}/{data['total']})</span>
            </div>
            """, unsafe_allow_html=True)

def show_calendar_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.8em;
        margin-bottom:15px'>📅 CALENDAR</div>
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
                date_stats[date_str] = {
                    'wins':0,'losses':0,'total':0,'trades':[]}
            date_stats[date_str]['total'] += 1
            date_stats[date_str]['trades'].append(trade)
            if trade['result'] == "TP Hit":
                date_stats[date_str]['wins'] += 1
            elif trade['result'] == "SL Hit":
                date_stats[date_str]['losses'] += 1
        except Exception:
            pass

    for date, data in sorted(date_stats.items(), reverse=True):
        wr = (round(data['wins']/data['total']*100,1)
            if data['total']>0 else 0)
        color = "🟢" if wr>=50 else "🔴"
        with st.expander(
            color+" "+date+" | "+
            str(data['total'])+" trades | WR: "+str(wr)+"%"):
            for trade in data['trades']:
                emoji = ("✅" if trade['result']=="TP Hit"
                    else "❌" if trade['result']=="SL Hit"
                    else "⏳")
                st.write(emoji+" "+trade['pair']+" "+
                    trade['direction']+" | "+
                    str(trade['score'])+"% | "+
                    trade['result'])

def show_settings_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.8em;
        margin-bottom:15px'>⚙️ SETTINGS</div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:rgba(0,255,136,0.05);
        border:1px solid rgba(0,255,136,0.2);
        border-radius:12px; padding:15px 20px;
        margin-bottom:20px;
        font-family:Exo 2,sans-serif'>
        <div style='color:#8899AA;
            font-size:0.85em; margin-bottom:5px'>
        👤 AUTHENTICATED USER</div>
        <div style='color:#00FF88'>
    """ + str(st.session_state.user_email) + """
    </div></div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:rgba(255,170,0,0.05);
        border:1px solid rgba(255,170,0,0.2);
        border-radius:12px; padding:15px;
        margin-bottom:15px;
        font-family:Exo 2,sans-serif'>
        <div style='color:#FFAA00; font-size:0.9em;
            font-weight:bold; margin-bottom:8px'>
        ⚠️ ABOUT NETWORK DISCONNECT</div>
        <div style='color:#8899AA; font-size:0.85em'>
        When internet disconnects, Streamlit app pauses
        completely — so it cannot send Discord alerts
        during disconnection. This is a platform limitation.<br><br>
        ✅ <b>What we do:</b> When you reconnect and
        app restarts, scanner auto-resumes and sends
        a reconnect alert to Discord automatically!
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📡 Pair Selection")
    st.write("Toggle pairs to include/exclude from scanning:")

    enabled = st.session_state.get(
        'enabled_pairs', {p:True for p in ALL_PAIRS})
    changed = False

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Enable All Pairs",
            use_container_width=True):
            for p in ALL_PAIRS:
                enabled[p] = True
            st.session_state.enabled_pairs = enabled
            st.rerun()
    with col2:
        if st.button("❌ Disable All Pairs",
            use_container_width=True):
            for p in ALL_PAIRS:
                enabled[p] = False
            st.session_state.enabled_pairs = enabled
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(3)
    for i, pair in enumerate(ALL_PAIRS):
        with cols[i % 3]:
            is_enabled = enabled.get(pair, True)
            new_val = st.toggle(
                pair,
                value=is_enabled,
                key="toggle_"+pair)
            if new_val != is_enabled:
                enabled[pair] = new_val
                changed = True

    if changed:
        st.session_state.enabled_pairs = enabled
        active = [p for p in ALL_PAIRS if enabled.get(p, True)]
        st.success("✅ Now scanning: " + ", ".join(active))
        st.rerun()

    active_count = len([p for p in ALL_PAIRS if enabled.get(p, True)])
    st.markdown(f"""
    <div style='background:rgba(0,255,136,0.05);
        border:1px solid rgba(0,255,136,0.15);
        border-radius:10px; padding:10px;
        font-family:Exo 2,sans-serif;
        color:#8899AA; font-size:0.85em;
        text-align:center; margin-top:10px'>
        📡 Currently scanning <b style='color:#00FF88'>
        {active_count}</b> out of 9 pairs
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.subheader("🔔 Discord")
    if st.button("🔔 Test Discord Alert",
        use_container_width=True):
        active = get_active_pairs()
        success = send_discord_alert(
            "✅ **System Test — AI Trading Scanner**\n"
            "All systems operational!\n"
            "Active pairs: " + ", ".join(active) + "\n"
            "Session: " + get_current_session() + "\n"
            "User: " + str(st.session_state.user_email) +
            "\nTime: " + get_ist_time().strftime(
                '%d %b %Y %H:%M IST'))
        if success:
            st.success("✅ Discord working!")
        else:
            st.error("❌ Discord failed!")

    st.divider()
    st.subheader("⏱️ Scan Interval")
    scan_interval = st.selectbox(
        "Minutes between scans",
        [1,2,3,5,10,15], index=3)
    if st.button("💾 Save",
        use_container_width=True):
        st.session_state.next_scan_seconds = scan_interval*60
        st.success("✅ Set to "+str(scan_interval)+" min!")

    st.divider()
    st.subheader("🗑️ Data Management")
    col1,col2 = st.columns(2)
    with col1:
        if st.button("Clear Alert History",
            use_container_width=True):
            st.session_state.sent_signal_ids = set()
            st.success("Cleared!")
    with col2:
        if st.button("Clear Trade Journal",
            use_container_width=True):
            st.session_state.trade_journal = []
            st.success("Cleared!")

    st.divider()
    st.subheader("🌏 Session Rules")
    st.markdown("""
    <div style='font-family:Exo 2,sans-serif;
        font-size:0.9em'>
        <div style='color:#FFD700; margin-bottom:8px'>
        ⭐⭐⭐ London+NY Overlap (5:30PM-8PM IST)
        → All pairs | Min score: 80%</div>
        <div style='color:#00FF88; margin-bottom:8px'>
        ⭐⭐ London (12PM-5PM IST)
        → All pairs | Min score: 80%</div>
        <div style='color:#00FF88; margin-bottom:8px'>
        ⭐⭐ New York (9PM-12AM IST)
        → All pairs | Min score: 80%</div>
        <div style='color:#FFAA00; margin-bottom:8px'>
        ⭐ Asia (4AM-11AM IST)
        → JPY+XAU pairs only | Min score: 88%
        | Min 5 confluences</div>
        <div style='color:#FF4444'>
        ❌ Off Session → Scanner paused</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.subheader("✅ Active Features")
    features = [
        "Advanced BOS with Swing Points",
        "FVG with Size Filtering",
        "Smart Order Block Detection",
        "ADX Trend Strength Filter",
        "EMA 8/21/50 Stack",
        "Candle Pattern Recognition",
        "Multi-TF HTF Bias 4H+1H",
        "Structure Dynamic SL",
        "Auto TP/SL Tracking",
        "Auto Resume After Reconnect",
        "Discord Reconnect Alerts",
        "5-Panel Professional Charts",
        "MACD + RSI + Volume Panels",
        "Pair Toggle Selection",
        "Asia Session Support",
        "Session Quality Scoring",
        "Min 4-5 confluences",
        "Max 2 signals per scan",
        "News Impact Filter",
        "Signal Expiry (30 mins)"
    ]
    cols = st.columns(2)
    for i, f in enumerate(features):
        with cols[i%2]:
            st.success("✅ "+f)

if __name__ == "__main__":
    main()
