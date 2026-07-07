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

@keyframes glowPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.cyber-title {
    font-family: 'Orbitron', monospace !important;
    color: #00FF88 !important;
    text-shadow: 0 0 10px rgba(0,255,136,0.5),
                 0 0 20px rgba(0,255,136,0.3) !important;
}
</style>
"""

IST = pytz.timezone('Asia/Kolkata')

def get_ist_time():
    return datetime.now(IST)

def is_trading_session():
    hour = get_ist_time().hour
    return 12 <= hour <= 20 or 21 <= hour <= 24 or hour == 0

def get_current_session():
    hour = get_ist_time().hour
    if 12 <= hour <= 16:
        return "London"
    elif 17 <= hour <= 20:
        return "London + NY Overlap"
    elif 21 <= hour <= 24 or hour == 0:
        return "New York"
    elif 4 <= hour <= 11:
        return "Asia"
    return "Off Session"

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
            return False, "DB connection failed!"
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
            json={"content": message})
        return response.status_code == 204
    except Exception:
        return False

def send_discord_alert_with_image(message, image_bytes):
    try:
        webhook_url = st.secrets["DISCORD_WEBHOOK"]
        response = requests.post(webhook_url,
            data={"content": message},
            files={"file": ("chart.png",
                image_bytes, "image/png")})
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
            "symbol=" + TWELVE_MAP.get(symbol, symbol) +
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
        return float((100 - (100/(1+rs))).iloc[-1])
    except Exception:
        return 50

def calculate_atr(df, period=14):
    try:
        high = df['High']
        low = df['Low']
        close = df['Close'].shift(1)
        tr = pd.concat([
            high - low,
            (high - close).abs(),
            (low - close).abs()
        ], axis=1).max(axis=1)
        return float(tr.ewm(span=period, adjust=False).mean().iloc[-1])
    except Exception:
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        return float(np.mean(highs[-14:] - lows[-14:]))

def calculate_adx(df, period=14):
    try:
        high = df['High'].values.astype(float)
        low = df['Low'].values.astype(float)
        close = df['Close'].values.astype(float)
        plus_dm = []
        minus_dm = []
        for i in range(1, len(high)):
            up = high[i] - high[i-1]
            down = low[i-1] - low[i]
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
        atr_vals = pd.Series(tr_vals).ewm(
            span=period, adjust=False).mean().values
        plus_di = 100 * pd.Series(plus_dm).ewm(
            span=period, adjust=False).mean().values / (atr_vals + 1e-10)
        minus_di = 100 * pd.Series(minus_dm).ewm(
            span=period, adjust=False).mean().values / (atr_vals + 1e-10)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = pd.Series(dx).ewm(
            span=period, adjust=False).mean().values
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
            if all(highs[i] >= highs[i-j] for j in range(1, lookback+1)) and \
               all(highs[i] >= highs[i+j] for j in range(1, lookback+1)):
                swing_highs.append((i, highs[i]))
            if all(lows[i] <= lows[i-j] for j in range(1, lookback+1)) and \
               all(lows[i] <= lows[i+j] for j in range(1, lookback+1)):
                swing_lows.append((i, lows[i]))
        return swing_highs, swing_lows
    except Exception:
        return [], []

def detect_bos_advanced(df):
    try:
        swing_highs, swing_lows = detect_swing_highs_lows(df)
        if not swing_highs or not swing_lows:
            return False, False, 0, 0
        current_close = float(df['Close'].values[-1])
        last_swing_high = swing_highs[-1][1] if swing_highs else 0
        last_swing_low = swing_lows[-1][1] if swing_lows else 0
        bull_bos = current_close > last_swing_high
        bear_bos = current_close < last_swing_low
        return bull_bos, bear_bos, last_swing_high, last_swing_low
    except Exception:
        return False, False, 0, 0

def detect_fvg_advanced(df):
    try:
        bull_fvg = bear_fvg = False
        fvg_zones = []
        candles = df.tail(30)
        for i in range(2, len(candles)-1):
            c1_high = float(candles['High'].iloc[i-2])
            c1_low = float(candles['Low'].iloc[i-2])
            c2_open = float(candles['Open'].iloc[i-1])
            c2_close = float(candles['Close'].iloc[i-1])
            c3_high = float(candles['High'].iloc[i])
            c3_low = float(candles['Low'].iloc[i])
            if c3_low > c1_high:
                gap_size = c3_low - c1_high
                if gap_size > 0:
                    bull_fvg = True
                    fvg_zones.append({
                        'type':'bullish',
                        'top': c3_low,
                        'bottom': c1_high,
                        'mid': (c3_low + c1_high) / 2,
                        'index': len(df) - len(candles) + i,
                        'size': gap_size
                    })
            if c3_high < c1_low:
                gap_size = c1_low - c3_high
                if gap_size > 0:
                    bear_fvg = True
                    fvg_zones.append({
                        'type':'bearish',
                        'top': c1_low,
                        'bottom': c3_high,
                        'mid': (c1_low + c3_high) / 2,
                        'index': len(df) - len(candles) + i,
                        'size': gap_size
                    })
        fvg_zones.sort(key=lambda x: x['size'], reverse=True)
        return bull_fvg, bear_fvg, fvg_zones[:3]
    except Exception:
        return False, False, []

def detect_order_block_advanced(df, direction):
    try:
        ob_found = False
        ob_top = ob_bottom = ob_index = 0
        ob_strength = 0
        closes = df['Close'].values.astype(float)
        opens = df['Open'].values.astype(float)
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        for i in range(3, min(40, len(df)-2)):
            if direction == "BUY":
                is_bearish = closes[-i] < opens[-i]
                next_bullish = closes[-i+1] > opens[-i+1]
                strong_move = (closes[-i+1] - opens[-i+1]) > \
                    abs(closes[-i] - opens[-i]) * 0.5
                if is_bearish and next_bullish and strong_move:
                    strength = (closes[-i+1] - opens[-i+1]) / (opens[-i] + 1e-10) * 100
                    if strength > ob_strength:
                        ob_strength = strength
                        ob_top = opens[-i]
                        ob_bottom = lows[-i]
                        ob_index = len(df) - i
                        ob_found = True
            else:
                is_bullish = closes[-i] > opens[-i]
                next_bearish = closes[-i+1] < opens[-i+1]
                strong_move = abs(closes[-i+1] - opens[-i+1]) > \
                    (closes[-i] - opens[-i]) * 0.5
                if is_bullish and next_bearish and strong_move:
                    strength = abs(closes[-i+1] - opens[-i+1]) / (opens[-i] + 1e-10) * 100
                    if strength > ob_strength:
                        ob_strength = strength
                        ob_top = highs[-i]
                        ob_bottom = opens[-i]
                        ob_index = len(df) - i
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
        recent_high = swing_highs[-1][1] if swing_highs else max(highs[-20:])
        recent_low = swing_lows[-1][1] if swing_lows else min(lows[-20:])
        current_low = lows[-1]
        current_close = closes[-1]
        current_high = highs[-1]
        bullish_sweep = (current_low < recent_low and
                        current_close > recent_low and
                        current_close > (current_low + current_high) / 2)
        bearish_sweep = (current_high > recent_high and
                        current_close < recent_high and
                        current_close < (current_low + current_high) / 2)
        return bullish_sweep, bearish_sweep
    except Exception:
        return False, False

def detect_choch_advanced(df):
    try:
        swing_highs, swing_lows = detect_swing_highs_lows(df, lookback=5)
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return False, False
        last_hh = swing_highs[-1][1] > swing_highs[-2][1]
        last_ll = swing_lows[-1][1] < swing_lows[-2][1]
        last_lh = swing_highs[-1][1] < swing_highs[-2][1]
        last_hl = swing_lows[-1][1] > swing_lows[-2][1]
        bull_choch = last_lh and last_hl
        bear_choch = last_hh and last_ll
        return bull_choch, bear_choch
    except Exception:
        return False, False

def detect_candle_pattern(df):
    try:
        o = float(df['Open'].iloc[-1])
        h = float(df['High'].iloc[-1])
        l = float(df['Low'].iloc[-1])
        c = float(df['Close'].iloc[-1])
        body = abs(c - o)
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        total_range = h - l
        if total_range == 0:
            return "Doji", "NEUTRAL"
        if body / total_range < 0.1:
            return "Doji", "NEUTRAL"
        if c > o and lower_wick > body * 2:
            return "Hammer", "BULLISH"
        if c < o and upper_wick > body * 2:
            return "Shooting Star", "BEARISH"
        if c > o and body / total_range > 0.7:
            return "Bullish Marubozu", "BULLISH"
        if c < o and body / total_range > 0.7:
            return "Bearish Marubozu", "BEARISH"
        prev_o = float(df['Open'].iloc[-2])
        prev_c = float(df['Close'].iloc[-2])
        if prev_c < prev_o and c > prev_o and o < prev_c:
            return "Bullish Engulfing", "BULLISH"
        if prev_c > prev_o and c < prev_o and o > prev_c:
            return "Bearish Engulfing", "BEARISH"
        return "Normal", "NEUTRAL"
    except Exception:
        return "Unknown", "NEUTRAL"

def get_htf_bias_advanced(symbol):
    try:
        df_4h = get_data(symbol, interval="4h")
        df_1h = get_data(symbol, interval="1h")
        scores = {"BULLISH": 0, "BEARISH": 0}
        for df, weight in [(df_4h, 2), (df_1h, 1)]:
            if df is None or len(df) < 50:
                continue
            ema20 = float(calculate_ema(df, 20).iloc[-1])
            ema50 = float(calculate_ema(df, 50).iloc[-1])
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
        ema20 = float(calculate_ema(df, 20).iloc[-1])
        ema50 = float(calculate_ema(df, 50).iloc[-1])
        if adx > 25 and plus_di > minus_di:
            return "TRENDING UP", adx
        elif adx > 25 and minus_di > plus_di:
            return "TRENDING DOWN", adx
        elif adx < 20:
            return "RANGING", adx
        else:
            price_range = float(max(closes[-20:]) - min(closes[-20:]))
            if price_range > atr * 4:
                return "VOLATILE", adx
            return "NEUTRAL", adx
    except Exception:
        return "UNKNOWN", 0

def is_price_in_pd_zone(df, direction):
    try:
        swing_highs, swing_lows = detect_swing_highs_lows(df, lookback=10)
        if not swing_highs or not swing_lows:
            return True
        recent_high = swing_highs[-1][1] if swing_highs else float(max(df['High'].values[-50:]))
        recent_low = swing_lows[-1][1] if swing_lows else float(min(df['Low'].values[-50:]))
        current = float(df['Close'].iloc[-1])
        r = recent_high - recent_low
        if r == 0:
            return True
        pos = (current - recent_low) / r
        eq = (recent_high + recent_low) / 2
        if direction == "BUY":
            return pos < 0.45
        else:
            return pos > 0.55
    except Exception:
        return True

def calculate_structure_sl_advanced(df, direction, atr, swing_highs, swing_lows):
    try:
        close = float(df['Close'].iloc[-1])
        if direction == "BUY":
            if swing_lows:
                recent_lows = [sl[1] for sl in swing_lows[-3:]]
                structure_low = min(recent_lows)
                sl = structure_low - (atr * 0.3)
            else:
                sl = close - (atr * 2)
            if close - sl > atr * 3:
                sl = close - (atr * 2)
        else:
            if swing_highs:
                recent_highs = [sh[1] for sh in swing_highs[-3:]]
                structure_high = max(recent_highs)
                sl = structure_high + (atr * 0.3)
            else:
                sl = close + (atr * 2)
            if sl - close > atr * 3:
                sl = close + (atr * 2)
        return round(sl, 5)
    except Exception:
        close = float(df['Close'].iloc[-1])
        return round(close - atr*2 if direction=="BUY" else close + atr*2, 5)

def generate_professional_chart(df, signal, fvg_zones,
    ob_found, ob_top, ob_bottom, ob_index,
    bull_bos, bear_bos, swing_highs, swing_lows,
    bull_sweep, bear_sweep, candle_pattern):
    try:
        fig = plt.figure(figsize=(18, 12),
            facecolor='#0D1117')
        gs = fig.add_gridspec(4, 1, height_ratios=[3,1,1,1],
            hspace=0)
        ax_main = fig.add_subplot(gs[0])
        ax_vol = fig.add_subplot(gs[1], sharex=ax_main)
        ax_rsi = fig.add_subplot(gs[2], sharex=ax_main)
        ax_info = fig.add_subplot(gs[3])
        for ax in [ax_main, ax_vol, ax_rsi, ax_info]:
            ax.set_facecolor('#0D1117')

        display_df = df.tail(80).reset_index(drop=True)
        n = len(display_df)

        for i in range(n):
            o = float(display_df['Open'].iloc[i])
            h = float(display_df['High'].iloc[i])
            l = float(display_df['Low'].iloc[i])
            c = float(display_df['Close'].iloc[i])
            is_bull = c >= o
            color = '#26A69A' if is_bull else '#EF5350'
            border = '#2EBD8E' if is_bull else '#F23645'
            ax_main.plot([i,i],[l,h],
                color=border, linewidth=0.8, zorder=2)
            rect = patches.Rectangle(
                (i-0.4, min(o,c)), 0.8, max(abs(c-o), 0.0001),
                linewidth=0.5, edgecolor=border,
                facecolor=color, alpha=0.9, zorder=3)
            ax_main.add_patch(rect)

        for fvg in fvg_zones:
            try:
                fx = fvg.get('index', n-5) - (len(df)-n)
                if 0 <= fx < n:
                    is_bull_fvg = fvg['type'] == 'bullish'
                    fc = '#26A69A22' if is_bull_fvg else '#EF535022'
                    fb = '#26A69A' if is_bull_fvg else '#EF5350'
                    fvg_rect = patches.Rectangle(
                        (fx, fvg['bottom']),
                        n - fx,
                        fvg['top'] - fvg['bottom'],
                        linewidth=1, edgecolor=fb,
                        facecolor=fc, alpha=0.8, zorder=1)
                    ax_main.add_patch(fvg_rect)
                    ax_main.text(fx+0.5, fvg['mid'],
                        'FVG', color=fb, fontsize=7,
                        fontweight='bold', va='center',
                        bbox=dict(boxstyle='round,pad=0.2',
                            facecolor='#0D1117',
                            edgecolor=fb, alpha=0.8))
            except Exception:
                pass

        if ob_found:
            ox = ob_index - (len(df)-n)
            if 0 <= ox < n:
                oc = '#26A69A22' if signal['direction']=='BUY' else '#EF535022'
                ob_c = '#26A69A' if signal['direction']=='BUY' else '#EF5350'
                ob_rect = patches.Rectangle(
                    (ox, ob_bottom), n-ox, ob_top-ob_bottom,
                    linewidth=1.5, edgecolor=ob_c,
                    facecolor=oc, linestyle='--', zorder=1)
                ax_main.add_patch(ob_rect)
                ax_main.text(ox+0.5,
                    (ob_top+ob_bottom)/2,
                    'OB', color=ob_c, fontsize=8,
                    fontweight='bold', va='center',
                    bbox=dict(boxstyle='round,pad=0.2',
                        facecolor='#0D1117',
                        edgecolor=ob_c, alpha=0.9))

        visible_swing_highs = [(i, h) for i, h in swing_highs
            if i >= len(df)-n]
        visible_swing_lows = [(i, l) for i, l in swing_lows
            if i >= len(df)-n]
        for idx, h_val in visible_swing_highs[-5:]:
            plot_idx = idx - (len(df)-n)
            if 0 <= plot_idx < n:
                ax_main.plot(plot_idx, h_val,
                    '^', color='#FF6B6B',
                    markersize=6, zorder=4)
                ax_main.text(plot_idx, h_val + h_val*0.0002,
                    'SH', color='#FF6B6B',
                    fontsize=6, ha='center', va='bottom')
        for idx, l_val in visible_swing_lows[-5:]:
            plot_idx = idx - (len(df)-n)
            if 0 <= plot_idx < n:
                ax_main.plot(plot_idx, l_val,
                    'v', color='#4ECDC4',
                    markersize=6, zorder=4)
                ax_main.text(plot_idx, l_val - l_val*0.0002,
                    'SL', color='#4ECDC4',
                    fontsize=6, ha='center', va='top')

        entry = signal['entry']
        sl = signal['sl']
        tp = signal['tp']
        rr = signal['rr']
        is_buy = signal['direction'] == "BUY"

        tp_color = '#26A69A'
        sl_color = '#EF5350'
        entry_color = '#FFFFFF'

        if is_buy:
            tp_zone = patches.Rectangle(
                (0, entry), n, tp-entry,
                color='#26A69A', alpha=0.08, zorder=0)
            sl_zone = patches.Rectangle(
                (0, sl), n, entry-sl,
                color='#EF5350', alpha=0.08, zorder=0)
        else:
            tp_zone = patches.Rectangle(
                (0, tp), n, entry-tp,
                color='#26A69A', alpha=0.08, zorder=0)
            sl_zone = patches.Rectangle(
                (0, entry), n, sl-entry,
                color='#EF5350', alpha=0.08, zorder=0)
        ax_main.add_patch(tp_zone)
        ax_main.add_patch(sl_zone)

        ax_main.axhline(y=entry, color=entry_color,
            linewidth=1.5, linestyle='-',
            alpha=0.9, zorder=5)
        ax_main.axhline(y=sl, color=sl_color,
            linewidth=1.5, linestyle='--',
            alpha=0.9, zorder=5)
        ax_main.axhline(y=tp, color=tp_color,
            linewidth=1.5, linestyle='--',
            alpha=0.9, zorder=5)

        price_range = abs(tp - sl)
        offset = price_range * 0.02
        ax_main.text(n-1, entry+offset,
            f'ENTRY  {entry}',
            color=entry_color, fontsize=8,
            fontweight='bold', ha='right', va='bottom',
            bbox=dict(boxstyle='round,pad=0.3',
                facecolor='#1E2530',
                edgecolor=entry_color, alpha=0.9))
        ax_main.text(n-1, sl-offset,
            f'SL  {sl}',
            color=sl_color, fontsize=8,
            fontweight='bold', ha='right', va='top',
            bbox=dict(boxstyle='round,pad=0.3',
                facecolor='#1E2530',
                edgecolor=sl_color, alpha=0.9))
        ax_main.text(n-1, tp+offset,
            f'TP  {tp}',
            color=tp_color, fontsize=8,
            fontweight='bold', ha='right', va='bottom',
            bbox=dict(boxstyle='round,pad=0.3',
                facecolor='#1E2530',
                edgecolor=tp_color, alpha=0.9))

        rr_text = f'RR 1:{rr}'
        mid_y = (entry + tp) / 2
        ax_main.text(2, mid_y, rr_text,
            color='#FFD700', fontsize=9,
            fontweight='bold', va='center',
            bbox=dict(boxstyle='round,pad=0.3',
                facecolor='#1E2530',
                edgecolor='#FFD700', alpha=0.9))

        if bull_bos:
            try:
                bos_level = signal.get('swing_high_level', entry)
                ax_main.axhline(y=bos_level,
                    color='#26A69A', linewidth=1,
                    linestyle=':', alpha=0.6)
                ax_main.text(5, bos_level,
                    'BOS ↑', color='#26A69A',
                    fontsize=7, fontweight='bold')
            except Exception:
                pass
        if bear_bos:
            try:
                bos_level = signal.get('swing_low_level', entry)
                ax_main.axhline(y=bos_level,
                    color='#EF5350', linewidth=1,
                    linestyle=':', alpha=0.6)
                ax_main.text(5, bos_level,
                    'BOS ↓', color='#EF5350',
                    fontsize=7, fontweight='bold')
            except Exception:
                pass

        if bull_sweep or bear_sweep:
            sweep_color = '#26A69A' if bull_sweep else '#EF5350'
            sweep_label = 'LIQ SWEEP ↑' if bull_sweep else 'LIQ SWEEP ↓'
            ax_main.text(n//2, float(display_df['High'].iloc[-5]),
                sweep_label, color=sweep_color,
                fontsize=7, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2',
                    facecolor='#0D1117',
                    edgecolor=sweep_color, alpha=0.8))

        grade = ("A+" if signal['score']>=90 else
                 "A" if signal['score']>=80 else
                 "B" if signal['score']>=70 else "C")
        dir_color = '#26A69A' if is_buy else '#EF5350'
        dir_symbol = '▲ BUY' if is_buy else '▼ SELL'
        ax_main.set_title(
            f"{signal['pair']}  {dir_symbol}  |  "
            f"Confidence: {signal['score']}%  |  "
            f"Grade: {grade}  |  "
            f"Session: {signal['session']}  |  "
            f"HTF: {signal['htf_bias']}",
            color='#E0E0E0', fontsize=12,
            fontweight='bold', pad=10,
            fontfamily='monospace')
        ax_main.tick_params(
            colors='#555555', labelsize=8)
        ax_main.yaxis.tick_right()
        for spine in ax_main.spines.values():
            spine.set_color('#1E2530')
        ax_main.grid(axis='y', color='#1E2530',
            linewidth=0.3, alpha=0.5)
        ax_main.set_xlim(-1, n+2)
        plt.setp(ax_main.get_xticklabels(), visible=False)

        if 'Volume' in display_df.columns:
            try:
                for i in range(n):
                    o = float(display_df['Open'].iloc[i])
                    c = float(display_df['Close'].iloc[i])
                    v = float(display_df['Volume'].iloc[i]) if pd.notna(display_df['Volume'].iloc[i]) else 0
                    color = '#26A69A' if c >= o else '#EF5350'
                    ax_vol.bar(i, v, color=color,
                        alpha=0.6, width=0.8)
                ax_vol.set_ylabel('Vol', color='#555555',
                    fontsize=7)
            except Exception:
                pass
        ax_vol.tick_params(colors='#555555', labelsize=6)
        for spine in ax_vol.spines.values():
            spine.set_color('#1E2530')
        ax_vol.grid(axis='y', color='#1E2530',
            linewidth=0.3, alpha=0.3)
        plt.setp(ax_vol.get_xticklabels(), visible=False)

        try:
            close_series = display_df['Close']
            delta = close_series.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.ewm(span=14, adjust=False).mean()
            avg_loss = loss.ewm(span=14, adjust=False).mean()
            rs = avg_gain / avg_loss
            rsi_series = 100 - (100/(1+rs))
            rsi_vals = rsi_series.values
            ax_rsi.plot(range(n), rsi_vals,
                color='#BB86FC', linewidth=1.2)
            ax_rsi.axhline(y=70, color='#EF5350',
                linewidth=0.5, linestyle='--', alpha=0.5)
            ax_rsi.axhline(y=30, color='#26A69A',
                linewidth=0.5, linestyle='--', alpha=0.5)
            ax_rsi.fill_between(range(n), rsi_vals, 50,
                where=[v > 50 for v in rsi_vals],
                alpha=0.1, color='#26A69A')
            ax_rsi.fill_between(range(n), rsi_vals, 50,
                where=[v < 50 for v in rsi_vals],
                alpha=0.1, color='#EF5350')
            ax_rsi.set_ylim(0, 100)
            ax_rsi.set_ylabel('RSI', color='#555555',
                fontsize=7)
            current_rsi = rsi_vals[-1] if len(rsi_vals) > 0 else 50
            ax_rsi.text(n-1, current_rsi,
                f' {current_rsi:.1f}',
                color='#BB86FC', fontsize=7, va='center')
        except Exception:
            pass
        ax_rsi.tick_params(colors='#555555', labelsize=6)
        for spine in ax_rsi.spines.values():
            spine.set_color('#1E2530')
        ax_rsi.grid(axis='y', color='#1E2530',
            linewidth=0.3, alpha=0.3)
        plt.setp(ax_rsi.get_xticklabels(), visible=False)

        ax_info.set_facecolor('#0D1117')
        ax_info.axis('off')
        reasons_str = "  ✅  ".join(signal['reasons'][:5])
        neg_str = ""
        if signal.get('negative'):
            neg_str = "  ⚠️  ".join(signal['negative'][:3])
        info_line1 = (
            f"Entry: {signal['entry']}   "
            f"SL: {signal['sl']}   "
            f"TP: {signal['tp']}   "
            f"RR: 1:{signal['rr']}   "
            f"RSI: {signal['rsi']}   "
            f"Market: {signal['regime']}   "
            f"Pattern: {candle_pattern}")
        info_line2 = "✅  " + reasons_str
        ax_info.text(0.5, 0.7, info_line1,
            color='#AAAAAA', fontsize=8,
            ha='center', va='center',
            transform=ax_info.transAxes)
        ax_info.text(0.5, 0.3, info_line2,
            color='#26A69A', fontsize=8,
            ha='center', va='center',
            transform=ax_info.transAxes)
        if neg_str:
            ax_info.text(0.5, 0.05,
                "⚠️  " + neg_str,
                color='#EF5350', fontsize=7,
                ha='center', va='center',
                transform=ax_info.transAxes)

        time_str = signal['time']
        fig.text(0.99, 0.99,
            f"AI Trading Scanner  |  {time_str}",
            color='#333333', fontsize=7,
            ha='right', va='top')

        plt.tight_layout(pad=0.5)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150,
            bbox_inches='tight',
            facecolor='#0D1117',
            edgecolor='none')
        buf.seek(0)
        image_bytes = buf.read()
        plt.close(fig)
        return image_bytes
    except Exception:
        return None

def analyze_pair_advanced(symbol):
    try:
        if not is_trading_session():
            return None

        df_5m = get_data(symbol, interval="5m")
        df_15m = get_data(symbol, interval="15m")
        df_1h = get_data(symbol, interval="1h")

        if df_5m is None or len(df_5m) < 60:
            return None

        score = 0
        reasons = []
        neg = []
        confluences = 0

        htf_bias = get_htf_bias_advanced(symbol)
        regime, adx_val = detect_market_regime_advanced(
            df_1h if df_1h is not None else df_5m)
        session = get_current_session()

        rsi = calculate_rsi(df_5m)
        atr = calculate_atr(df_5m)
        adx, plus_di, minus_di = calculate_adx(df_5m)
        candle_pattern, candle_dir = detect_candle_pattern(df_5m)

        bull_bos, bear_bos, swing_high_level, swing_low_level = detect_bos_advanced(df_5m)
        bull_fvg, bear_fvg, fvg_zones = detect_fvg_advanced(df_5m)
        bull_sweep, bear_sweep = detect_liquidity_sweep_advanced(df_5m)
        bull_choch, bear_choch = detect_choch_advanced(df_5m)
        swing_highs, swing_lows = detect_swing_highs_lows(df_5m)

        ob_found, ob_top, ob_bottom, ob_index = detect_order_block_advanced(
            df_5m, "BUY")

        close = float(df_5m['Close'].iloc[-1])

        ema8 = float(calculate_ema(df_5m, 8).iloc[-1])
        ema21 = float(calculate_ema(df_5m, 21).iloc[-1])
        ema50 = float(calculate_ema(df_5m, 50).iloc[-1])

        is_bull = (bull_bos or bull_fvg or bull_sweep or bull_choch or
                   (candle_dir == "BULLISH"))
        is_bear = (bear_bos or bear_fvg or bear_sweep or bear_choch or
                   (candle_dir == "BEARISH"))

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

        ob_found, ob_top, ob_bottom, ob_index = detect_order_block_advanced(
            df_5m, direction)
        in_pd = is_price_in_pd_zone(df_5m, direction)

        if htf_bias == "BULLISH" and direction == "BUY":
            score += 20
            reasons.append("HTF Bullish Alignment")
            confluences += 1
        elif htf_bias == "BEARISH" and direction == "SELL":
            score += 20
            reasons.append("HTF Bearish Alignment")
            confluences += 1
        elif htf_bias == "NEUTRAL":
            score += 3
            neg.append("HTF Neutral")
        else:
            score -= 15
            neg.append("HTF Conflict")

        if adx > 25:
            if direction == "BUY" and plus_di > minus_di:
                score += 15
                reasons.append("Strong Uptrend (ADX " + str(round(adx,1)) + ")")
                confluences += 1
            elif direction == "SELL" and minus_di > plus_di:
                score += 15
                reasons.append("Strong Downtrend (ADX " + str(round(adx,1)) + ")")
                confluences += 1
        elif adx < 15:
            score -= 10
            neg.append("Weak Trend (ADX " + str(round(adx,1)) + ")")

        if regime == "VOLATILE":
            score -= 20
            neg.append("High Volatility")
        elif regime == "RANGING" and adx < 20:
            score -= 10
            neg.append("Ranging Market")
        elif regime in ["TRENDING UP","TRENDING DOWN"]:
            if (regime == "TRENDING UP" and direction == "BUY") or \
               (regime == "TRENDING DOWN" and direction == "SELL"):
                score += 10
                reasons.append("Trend Alignment")
                confluences += 1

        if bull_bos and direction == "BUY":
            score += 18
            reasons.append("Bullish BOS")
            confluences += 1
        if bear_bos and direction == "SELL":
            score += 18
            reasons.append("Bearish BOS")
            confluences += 1
        if bull_fvg and direction == "BUY":
            score += 15
            reasons.append("Bullish FVG")
            confluences += 1
        if bear_fvg and direction == "SELL":
            score += 15
            reasons.append("Bearish FVG")
            confluences += 1
        if bull_sweep and direction == "BUY":
            score += 18
            reasons.append("Bullish Liquidity Sweep")
            confluences += 1
        if bear_sweep and direction == "SELL":
            score += 18
            reasons.append("Bearish Liquidity Sweep")
            confluences += 1
        if bull_choch and direction == "BUY":
            score += 12
            reasons.append("Bullish CHOCH")
            confluences += 1
        if bear_choch and direction == "SELL":
            score += 12
            reasons.append("Bearish CHOCH")
            confluences += 1
        if ob_found:
            score += 12
            reasons.append("Order Block")
            confluences += 1
        if in_pd:
            score += 10
            reasons.append("Premium/Discount Zone")
            confluences += 1

        if direction == "BUY":
            if ema8 > ema21 > ema50:
                score += 8
                reasons.append("EMA Stack Bullish")
                confluences += 1
            elif ema8 < ema21:
                score -= 5
                neg.append("EMA Bearish Stack")
        else:
            if ema8 < ema21 < ema50:
                score += 8
                reasons.append("EMA Stack Bearish")
                confluences += 1
            elif ema8 > ema21:
                score -= 5
                neg.append("EMA Bullish Stack")

        if direction == "BUY":
            if 20 < rsi < 55:
                score += 8
                reasons.append("RSI Bullish Zone (" + str(round(rsi,1)) + ")")
            elif rsi >= 55 and rsi < 70:
                score += 3
            elif rsi >= 70:
                score -= 15
                neg.append("RSI Overbought (" + str(round(rsi,1)) + ")")
            elif rsi <= 20:
                score -= 5
                neg.append("RSI Extreme Oversold")
        else:
            if 45 < rsi < 80:
                score += 8
                reasons.append("RSI Bearish Zone (" + str(round(rsi,1)) + ")")
            elif rsi > 80:
                score += 3
            elif rsi <= 30:
                score -= 15
                neg.append("RSI Oversold (" + str(round(rsi,1)) + ")")

        if candle_dir == "BULLISH" and direction == "BUY":
            score += 8
            reasons.append(candle_pattern + " Pattern")
        elif candle_dir == "BEARISH" and direction == "SELL":
            score += 8
            reasons.append(candle_pattern + " Pattern")
        elif candle_dir != "NEUTRAL":
            if (candle_dir == "BEARISH" and direction == "BUY") or \
               (candle_dir == "BULLISH" and direction == "SELL"):
                score -= 10
                neg.append("Opposing Candle Pattern")

        if session in ["London","New York","London + NY Overlap"]:
            score += 5
            reasons.append(session + " Session")
        else:
            score -= 20
            neg.append("Off-Peak Session")

        news = st.session_state.get('cached_news', [])
        if [n for n in news if n['impact'] == 3]:
            score -= 20
            neg.append("High Impact News Active!")

        if confluences < 4:
            return None

        score = min(max(score, 0), 95)

        sl = calculate_structure_sl_advanced(
            df_5m, direction, atr, swing_highs, swing_lows)
        sl_dist = abs(close - sl)

        if sl_dist < atr * 0.5:
            sl = (close - atr*1.5 if direction=="BUY"
                else close + atr*1.5)
            sl_dist = abs(close - sl)

        if sl_dist > atr * 4:
            sl = (close - atr*2 if direction=="BUY"
                else close + atr*2)
            sl_dist = abs(close - sl)

        entry = close
        tp_multiplier = 2.0
        if adx > 30:
            tp_multiplier = 2.5
        if score >= 85:
            tp_multiplier = 2.0

        tp = round(entry + sl_dist*tp_multiplier if direction=="BUY"
            else entry - sl_dist*tp_multiplier, 5)
        rr = round(tp_multiplier, 1)

        return {
            "pair": symbol,
            "direction": direction,
            "score": score,
            "entry": round(entry, 5),
            "sl": round(sl, 5),
            "tp": round(tp, 5),
            "rr": rr,
            "rsi": round(rsi, 1),
            "adx": round(adx, 1),
            "htf_bias": htf_bias,
            "regime": regime,
            "session": session,
            "confluences": confluences,
            "reasons": reasons,
            "negative": neg,
            "candle_pattern": candle_pattern,
            "time": get_ist_time().strftime('%d %b %Y %H:%M IST'),
            "current_price": round(close, 5),
            "atr": round(atr, 5),
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
            "swing_high_level": swing_high_level,
            "swing_low_level": swing_low_level
        }
    except Exception:
        return None

def check_signal_outcomes():
    try:
        journal = st.session_state.trade_journal
        pending = [j for j in journal if j['result'] == "Pending"]
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
                current_high = float(df['High'].iloc[-1])
                current_low = float(df['Low'].iloc[-1])
                entry = trade['entry']
                sl = trade['sl']
                tp = trade['tp']
                direction = trade['direction']
                if direction == "BUY":
                    if current_high >= tp:
                        for j in st.session_state.trade_journal:
                            if j['id'] == trade['id']:
                                j['result'] = "TP Hit"
                                j['pnl'] = trade['rr']
                        send_discord_alert(
                            "✅ **TP HIT!**\n"
                            + trade['pair'] + " " + direction +
                            "\nEntry: " + str(entry) +
                            "\nTP: " + str(tp) +
                            "\nRR: 1:" + str(trade['rr']) +
                            "\nTime: " + get_ist_time().strftime('%H:%M IST'))
                    elif current_low <= sl:
                        for j in st.session_state.trade_journal:
                            if j['id'] == trade['id']:
                                j['result'] = "SL Hit"
                                j['pnl'] = -1
                        send_discord_alert(
                            "❌ **SL HIT!**\n"
                            + trade['pair'] + " " + direction +
                            "\nEntry: " + str(entry) +
                            "\nSL: " + str(sl) +
                            "\nTime: " + get_ist_time().strftime('%H:%M IST'))
                else:
                    if current_low <= tp:
                        for j in st.session_state.trade_journal:
                            if j['id'] == trade['id']:
                                j['result'] = "TP Hit"
                                j['pnl'] = trade['rr']
                        send_discord_alert(
                            "✅ **TP HIT!**\n"
                            + trade['pair'] + " " + direction +
                            "\nEntry: " + str(entry) +
                            "\nTP: " + str(tp) +
                            "\nRR: 1:" + str(trade['rr']) +
                            "\nTime: " + get_ist_time().strftime('%H:%M IST'))
                    elif current_high >= sl:
                        for j in st.session_state.trade_journal:
                            if j['id'] == trade['id']:
                                j['result'] = "SL Hit"
                                j['pnl'] = -1
                        send_discord_alert(
                            "❌ **SL HIT!**\n"
                            + trade['pair'] + " " + direction +
                            "\nEntry: " + str(entry) +
                            "\nSL: " + str(sl) +
                            "\nTime: " + get_ist_time().strftime('%H:%M IST'))
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
    instr = ("📍 **Enter BUY at or below: " + str(signal['entry']) + "**"
        if signal['direction']=="BUY"
        else "📍 **Enter SELL at or above: " + str(signal['entry']) + "**")
    msg = (
        "🚨 **HIGH CONFIDENCE SIGNAL** 🚨\n\n"
        "**" + emoji + " " + signal['pair'] + "**\n\n"
        "📊 Confidence: " + str(signal['score']) + "%\n"
        "🏆 Grade: " + grade + "\n"
        "🔗 Confluences: " + str(signal['confluences']) + "\n"
        "📐 Pattern: " + signal.get('candle_pattern','N/A') + "\n"
        "📉 ADX: " + str(signal.get('adx','N/A')) + "\n\n"
        + instr + "\n"
        "💰 Entry: " + str(signal['entry']) + "\n"
        "🛑 SL: " + str(signal['sl']) + "\n"
        "🎯 TP: " + str(signal['tp']) + "\n"
        "⚖️ RR: 1:" + str(signal['rr']) + "\n\n"
        "📈 HTF: " + signal['htf_bias'] + "\n"
        "🌍 Market: " + signal['regime'] + "\n"
        "🕐 Session: " + signal['session'] + "\n"
        "📉 RSI: " + str(signal['rsi']) + "\n\n"
        "⏰ Time: " + signal['time'] + "\n"
        "🟢 Status: FRESH — Auto tracking active!\n\n"
        "⚠️ Skip if price moved >" + str(signal['atr']) + " away!\n\n"
        "✅ **Reasons:**\n" + reasons_text + "\n")
    if signal['negative']:
        msg += "\n⚠️ **Caution:**\n" + neg_text + "\n"
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
    completed = [j for j in journal if j['result'] not in ["Pending","Expired"]]
    wins = [j for j in completed if j['result'] == "TP Hit"]
    losses = [j for j in completed if j['result'] == "SL Hit"]
    win_rate = len(wins)/len(completed)*100 if completed else 0
    pair_wins = {}
    for j in wins:
        pair_wins[j['pair']] = pair_wins.get(j['pair'],0) + 1
    session_wins = {}
    for j in wins:
        session_wins[j['session']] = session_wins.get(j['session'],0) + 1
    return {
        "total": len(journal),
        "wins": len(wins),
        "losses": len(losses),
        "pending": len([j for j in journal if j['result']=="Pending"]),
        "win_rate": round(win_rate, 1),
        "best_pair": max(pair_wins, key=pair_wins.get) if pair_wins else "N/A",
        "best_session": max(session_wins, key=session_wins.get) if session_wins else "N/A"
    }

for key, val in [
    ('scanner_running',False),('logged_in',False),
    ('user_email',None),('user_id',None),
    ('signals',[]),('alerts_sent',0),
    ('total_scans',0),('last_scan_time',None),
    ('next_scan_seconds',300),
    ('sent_signal_ids',set()),
    ('trade_journal',[]),('cached_news',[]),
    ('last_news_fetch',None),('show_reset',False),
    ('last_outcome_check',None)
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
    pairs = ["XAUUSD","USDJPY","AUDCAD","GBPJPY",
             "GBPUSD","EURUSD","EURJPY","US30","NAS100"]
    found = []
    new_high = []
    for pair in pairs:
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
        elapsed = int((now-st.session_state.last_scan_time).total_seconds())
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
            font-size:2.5em; font-weight:900; color:#00FF88;
            text-shadow:0 0 20px rgba(0,255,136,0.6),
                        0 0 40px rgba(0,255,136,0.3);
            letter-spacing:3px; margin-bottom:10px'>
        ⬡ AI TRADING SCANNER</div>
        <div style='font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.95em;
            letter-spacing:4px; margin-bottom:8px'>
        PROFESSIONAL FOREX & INDICES INTELLIGENCE</div>
        <div style='font-family:Exo 2,sans-serif;
            color:rgba(0,255,136,0.4); font-size:0.8em;
            letter-spacing:2px'>
        XAUUSD · EURUSD · GBPUSD · USDJPY · GBPJPY · EURJPY · AUDCAD · US30 · NAS100</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        if st.session_state.show_reset:
            st.markdown("<h3 style='color:#00FF88;font-family:Orbitron,monospace;text-align:center'>🔑 RESET PASSWORD</h3>",
                unsafe_allow_html=True)
            reset_email = st.text_input("Email", key="reset_email")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Send Reset Email",
                    use_container_width=True, type="primary"):
                    success, msg = reset_password(reset_email)
                    st.success(msg) if success else st.error(msg)
            with col_b:
                if st.button("← Back", use_container_width=True):
                    st.session_state.show_reset = False
                    st.rerun()
        else:
            tab1, tab2 = st.tabs(["🔑  LOGIN","📝  SIGN UP"])
            with tab1:
                st.markdown("<br>", unsafe_allow_html=True)
                email = st.text_input("Email", key="login_email",
                    placeholder="your@email.com")
                password = st.text_input("Password",
                    type="password", key="login_pass",
                    placeholder="••••••••")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⚡ ENTER SCANNER",
                    use_container_width=True, type="primary"):
                    if email and password:
                        success, msg = login_user(email, password)
                        if success:
                            st.success("✅ " + msg)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ " + msg)
                    else:
                        st.error("Please enter email and password!")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Forgot Password?",
                    use_container_width=True):
                    st.session_state.show_reset = True
                    st.rerun()
            with tab2:
                st.markdown("<br>", unsafe_allow_html=True)
                new_email = st.text_input("Email", key="signup_email",
                    placeholder="your@email.com")
                new_pass = st.text_input("Password",
                    type="password", key="signup_pass",
                    placeholder="Min 6 characters")
                confirm_pass = st.text_input("Confirm Password",
                    type="password", key="confirm_pass",
                    placeholder="Repeat password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🚀 CREATE ACCOUNT",
                    use_container_width=True, type="primary"):
                    if new_email and new_pass and confirm_pass:
                        if new_pass == confirm_pass:
                            if len(new_pass) < 6:
                                st.error("Password must be at least 6 characters!")
                            else:
                                success, msg = signup_user(new_email, new_pass)
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
            📊 Professional Charts</div>
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid rgba(0,255,136,0.2);
            border-radius:10px; padding:10px 15px;
            font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.82em'>
            🔔 Auto TP/SL Tracking</div>
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid rgba(0,255,136,0.2);
            border-radius:10px; padding:10px 15px;
            font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.82em'>
            📐 ADX + EMA Filters</div>
    </div>
    """, unsafe_allow_html=True)

def show_dashboard():
    session = get_current_session()
    news = st.session_state.get('cached_news', [])
    high_impact = [n for n in news if n['impact'] == 3]
    stats = calculate_stats()

    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding:15px 0'>
            <div style='font-family:Orbitron,monospace;
                font-size:1.05em; font-weight:700;
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
            <div style='color:#8899AA; font-size:0.7em'>👤 USER</div>
            <div style='color:#FFFFFF; font-size:0.78em;
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
            </div>
        </div>""", unsafe_allow_html=True)

        if session in ["London","New York","London + NY Overlap"]:
            st.success("🟢 " + session)
        else:
            st.warning("⚠️ " + session)

        if high_impact:
            st.error("🚨 HIGH IMPACT NEWS!")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Win Rate", str(stats['win_rate']) + "%")
        with col2:
            st.metric("Signals", stats['total'])

        pending_count = stats.get('pending', 0)
        if pending_count > 0:
            st.info("⏳ " + str(pending_count) + " tracking...")

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
        if st.button("🚪 Logout", use_container_width=True):
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

    session = get_current_session()
    news = st.session_state.get('cached_news', [])
    high_impact = [n for n in news if n['impact'] == 3]
    stats = calculate_stats()

    if high_impact:
        st.error("🚨 HIGH IMPACT NEWS ACTIVE — Signals paused!")
    if session not in ["London","New York","London + NY Overlap"]:
        st.warning("⚠️ " + session + " — Best during London (12PM-8PM IST) and NY (9PM-12AM IST)")

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
                use_container_width=True, type="primary"):
                st.session_state.scanner_running = True
                st.session_state.last_scan_time = None
                st.session_state.sent_signal_ids = set()
                send_discord_alert(
                    "🟢 **AI Trading Scanner ACTIVATED!**\n"
                    "Advanced SMC + ICT + ADX + EMA Analysis\n"
                    "Auto TP/SL tracking enabled!\n"
                    "Min 4 confluences required\n"
                    "User: " + str(st.session_state.user_email) +
                    "\nTime: " + get_ist_time().strftime('%d %b %Y %H:%M IST'))
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
        st.metric("Win Rate", str(stats['win_rate']) + "%")
    with col3:
        st.metric("Alerts Sent", st.session_state.alerts_sent)
    with col4:
        st.metric("Total Scans", st.session_state.total_scans)

    st.divider()

    if st.session_state.scanner_running:
        if st.session_state.last_scan_time:
            elapsed = int((get_ist_time() -
                st.session_state.last_scan_time).total_seconds())
            remaining = max(0,
                st.session_state.next_scan_seconds - elapsed)
            progress_val = min(1.0,
                elapsed/st.session_state.next_scan_seconds)
            st.info("⏱️ Last: " +
                st.session_state.last_scan_time.strftime('%H:%M:%S IST') +
                " | Next in: " + str(remaining) + "s | "
                "Auto TP/SL tracking: Active ✅")
            st.progress(progress_val)
        else:
            st.info("⚡ Initializing...")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚡ SCAN NOW",
                type="primary", use_container_width=True):
                with st.spinner("Advanced scanning..."):
                    run_scan()
                st.success("✅ Scan complete!")
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
        opacity:0.8'>📡 PAIRS UNDER SURVEILLANCE</div>
    """, unsafe_allow_html=True)

    pairs = ["XAUUSD","USDJPY","AUDCAD","GBPJPY",
             "GBPUSD","EURUSD","EURJPY","US30","NAS100"]
    cols = st.columns(3)
    for i, pair in enumerate(pairs):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='background:rgba(0,255,136,0.04);
                border:1px solid rgba(0,255,136,0.15);
                border-radius:10px; padding:10px;
                text-align:center; margin-bottom:8px;
                font-family:Orbitron,monospace;
                color:#00FF88; font-size:0.85em;
                letter-spacing:1px'>{pair}</div>
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
            st.success("✅ News refreshed!")
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
            imp_emoji + " " + event['time'] +
            " | " + event['event'] +
            " (" + event['currency'] + ")"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Impact", event['impact'])
            with col2:
                st.metric("Forecast", event['forecast'])
            with col3:
                st.metric("Previous", event['previous'])

    st.divider()
    st.subheader("📰 Live News")
    news = st.session_state.get('cached_news', [])
    if not news:
        st.info("Click Refresh News!")
        if st.button("📰 Load Now", use_container_width=True):
            with st.spinner("Loading..."):
                st.session_state.cached_news = fetch_forex_news()
                st.session_state.last_news_fetch = get_ist_time()
            st.rerun()
    else:
        for item in [n for n in news if n['impact']==3]:
            with st.expander("🔴 " + item['title'][:80]):
                st.write("📰 " + item['source'])
                if item['summary']:
                    st.write(item['summary'])
                st.markdown("[Read →](" + item['link'] + ")")
        for item in [n for n in news if n['impact']==2][:5]:
            with st.expander("🟡 " + item['title'][:80]):
                st.write("📰 " + item['source'])
                if item['summary']:
                    st.write(item['summary'])
                st.markdown("[Read →](" + item['link'] + ")")
        for item in [n for n in news if n['impact']==1][:5]:
            st.write("🟢 " + item['title'][:100] +
                " | " + item['source'])

def show_signals_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.8em;
        margin-bottom:15px'>📊 ACTIVE SIGNALS</div>
    """, unsafe_allow_html=True)

    news = st.session_state.get('cached_news', [])
    if [n for n in news if n['impact']==3]:
        st.error("🚨 HIGH IMPACT NEWS — Extra caution!")

    if not st.session_state.signals:
        st.markdown("""
        <div style='text-align:center; padding:50px 20px;
            font-family:Exo 2,sans-serif; color:#8899AA'>
            <div style='font-size:3em; margin-bottom:15px'>📡</div>
            <div>No signals yet. Activate scanner.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    high = [s for s in st.session_state.signals if s['score'] >= 80]
    medium = [s for s in st.session_state.signals if 60 <= s['score'] < 80]
    low = [s for s in st.session_state.signals if s['score'] < 60]

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
            with st.expander(
                "🟢 " + signal['pair'] + " " +
                signal['direction'] + "  |  " +
                str(signal['score']) + "%  |  " +
                str(signal['confluences']) + " conf  |  " +
                status + "  |  ADX: " +
                str(signal.get('adx','N/A'))):
                col1, col2, col3 = st.columns(3)
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
                        st.success("✅ Enter BUY at or below: " + str(signal['entry']))
                    else:
                        st.success("✅ Enter SELL at or above: " + str(signal['entry']))
                col1, col2 = st.columns(2)
                with col1:
                    st.write("⚖️ RR: 1:" + str(signal['rr']))
                    st.write("📈 HTF: " + signal['htf_bias'])
                    st.write("🌍 Market: " + signal['regime'])
                with col2:
                    st.write("🕐 Session: " + signal['session'])
                    st.write("📉 RSI: " + str(signal['rsi']))
                    st.write("📐 ADX: " + str(signal.get('adx','N/A')))
                st.write("📐 Pattern: " + signal.get('candle_pattern','N/A'))
                st.write("✅ " + ", ".join(signal['reasons']))
                if signal.get('negative'):
                    st.warning("⚠️ " + ", ".join(signal['negative']))

    if medium:
        st.markdown("""
        <div style='font-family:Orbitron,monospace;
            color:#FFAA00; font-size:0.85em;
            letter-spacing:2px; margin:12px 0 8px'>
        🟡 MEDIUM — 60-80%</div>
        """, unsafe_allow_html=True)
        for signal in medium:
            age = get_signal_age(signal['time'])
            with st.expander(
                "🟡 " + signal['pair'] + " " +
                signal['direction'] + "  |  " +
                str(signal['score']) + "%"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Entry", signal['entry'])
                with col2:
                    st.metric("SL", signal['sl'])
                with col3:
                    st.metric("TP", signal['tp'])
                st.write("Age: " + str(age) +
                    " min | " + ", ".join(signal['reasons']))

    if low:
        st.markdown("""
        <div style='font-family:Orbitron,monospace;
            color:#FF4444; font-size:0.85em;
            letter-spacing:2px; margin:12px 0 8px'>
        🔴 LOW — Below 60%</div>
        """, unsafe_allow_html=True)
        for signal in low:
            st.write("🔴 " + signal['pair'] +
                " | " + str(signal['score']) + "%")

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
        with st.spinner("Checking outcomes..."):
            check_signal_outcomes()
        st.success("✅ Outcomes updated!")
        st.rerun()

    pending = [j for j in journal if j['result'] == "Pending"]
    if pending:
        st.subheader("⏳ Pending — Auto tracking active")
        for trade in pending:
            with st.expander(
                "⏳ " + trade['pair'] + " " +
                trade['direction'] + "  |  " +
                str(trade['score']) + "%  |  " + trade['time']):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Entry", trade['entry'])
                with col2:
                    st.metric("SL", trade['sl'])
                with col3:
                    st.metric("TP", trade['tp'])
                st.info("Auto tracking enabled — will update automatically!")
                result = st.selectbox(
                    "Manual Override",
                    ["Pending","TP Hit","SL Hit","Expired","Partial Win"],
                    key="result_" + trade['id'])
                if st.button("✅ Override",
                    key="update_" + trade['id'],
                    use_container_width=True):
                    for j in st.session_state.trade_journal:
                        if j['id'] == trade['id']:
                            j['result'] = result
                            j['pnl'] = (trade['rr'] if result=="TP Hit"
                                else -1 if result=="SL Hit"
                                else 0.5 if result=="Partial Win" else 0)
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
        result_color = ("color:#00FF88" if trade['result']=="TP Hit" else
                        "color:#FF4444" if trade['result']=="SL Hit" else
                        "color:#8899AA")
        st.markdown(f"""
        <div style='background:rgba(255,255,255,0.02);
            border:1px solid rgba(255,255,255,0.06);
            border-radius:8px; padding:8px 12px;
            margin-bottom:4px; font-family:Exo 2,sans-serif'>
            {emoji} <b>{trade['pair']} {trade['direction']}</b>
            | {trade['score']}%
            | <span style='{result_color}'><b>{trade['result']}</b></span>
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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", stats['total'])
    with col2:
        st.metric("✅ Wins", stats['wins'])
    with col3:
        st.metric("❌ Losses", stats['losses'])
    with col4:
        st.metric("🏆 Win Rate", str(stats['win_rate']) + "%")

    st.divider()
    col1, col2 = st.columns(2)
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
            wr = round(data['wins']/data['total']*100, 1)
            bar = "█" * int(wr/5) + "░" * (20-int(wr/5))
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
            if data['total'] > 0 else 0)
        color = "🟢" if wr >= 50 else "🔴"
        with st.expander(
            color + " " + date + " | " +
            str(data['total']) + " trades | WR: " +
            str(wr) + "%"):
            for trade in data['trades']:
                emoji = ("✅" if trade['result']=="TP Hit"
                    else "❌" if trade['result']=="SL Hit"
                    else "⏳")
                st.write(emoji + " " + trade['pair'] +
                    " " + trade['direction'] + " | " +
                    str(trade['score']) + "% | " +
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
        margin-bottom:20px; font-family:Exo 2,sans-serif'>
        <div style='color:#8899AA; font-size:0.85em;
            margin-bottom:5px'>👤 AUTHENTICATED USER</div>
        <div style='color:#00FF88'>
    """ + str(st.session_state.user_email) + """
    </div></div>
    """, unsafe_allow_html=True)

    st.subheader("🔔 Discord")
    if st.button("🔔 Test Discord Alert",
        use_container_width=True):
        success = send_discord_alert(
            "✅ **System Test — AI Trading Scanner**\n"
            "Advanced analysis engine active!\n"
            "Auto TP/SL tracking enabled!\n"
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
    if st.button("💾 Save", use_container_width=True):
        st.session_state.next_scan_seconds = scan_interval * 60
        st.success("✅ Set to " + str(scan_interval) + " min!")

    st.divider()
    st.subheader("🗑️ Data Management")
    col1, col2 = st.columns(2)
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
    st.subheader("✅ Active System Upgrades")
    upgrades = [
        "Advanced BOS with Swing Points",
        "FVG with Size Filtering",
        "Smart Order Block Detection",
        "ADX Trend Strength Filter",
        "EMA Stack Confirmation",
        "Candle Pattern Recognition",
        "Multi-timeframe HTF (4H+1H)",
        "Structure-based Dynamic SL",
        "Auto TP/SL Outcome Tracking",
        "Min 4 confluences required",
        "Confidence capped at 95%",
        "Session filter London + NY",
        "News impact filter",
        "Max 2 best signals per scan",
        "Professional chart layout"
    ]
    cols = st.columns(2)
    for i, u in enumerate(upgrades):
        with cols[i % 2]:
            st.success("✅ " + u)

    st.divider()
    st.markdown("""
    <div style='background:rgba(0,150,255,0.05);
        border:1px solid rgba(0,150,255,0.2);
        border-radius:10px; padding:15px;
        font-family:Exo 2,sans-serif; color:#8899AA'>
        <div style='color:#0096FF; margin-bottom:8px'>
        🕐 TRADING HOURS (IST)</div>
        <div>🇬🇧 London: 12:00 PM — 8:00 PM</div>
        <div>🇺🇸 New York: 9:00 PM — 12:00 AM</div>
        <div style='margin-top:8px; color:#00FF88'>
        ⭐ Best: London+NY Overlap 5:30PM-8PM</div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
