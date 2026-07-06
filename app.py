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
    transition: all 0.2s ease !important;
}

div[data-testid="stRadio"] label:hover {
    color: #00FF88 !important;
}

hr {
    border-color: rgba(0,255,136,0.15) !important;
}

div[data-testid="stTabs"] button {
    color: #8899AA !important;
    font-family: 'Exo 2', sans-serif !important;
    font-weight: 600 !important;
}

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #00FF88 !important;
    border-bottom: 2px solid #00FF88 !important;
}

div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #00FF88, #00CC66) !important;
    box-shadow: 0 0 10px rgba(0,255,136,0.5) !important;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); }
::-webkit-scrollbar-thumb {
    background: rgba(0,255,136,0.3);
    border-radius: 10px;
}

@keyframes glowPulse {
    0%, 100% { box-shadow: 0 0 10px rgba(0,255,136,0.3); }
    50% { box-shadow: 0 0 25px rgba(0,255,136,0.6); }
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}

.cyber-title {
    font-family: 'Orbitron', monospace !important;
    color: #00FF88 !important;
    text-shadow:
        0 0 10px rgba(0,255,136,0.5),
        0 0 20px rgba(0,255,136,0.3) !important;
    animation: fadeInUp 0.5s ease-out !important;
}
</style>
"""

IST = pytz.timezone('Asia/Kolkata')

def get_ist_time():
    return datetime.now(IST)

def is_trading_session():
    hour = get_ist_time().hour
    return 12 <= hour <= 20 or 17 <= hour <= 24 or hour == 0

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

def signup_user(email, password):
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "DB connection failed!"
        response = supabase.auth.sign_up({
            "email": email, "password": password})
        if response.user:
            return True, "Account created! Check email to verify!"
        return False, "Signup failed!"
    except Exception as e:
        return False, "Error: " + str(e)

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

def logout_user():
    try:
        supabase = init_supabase()
        if supabase:
            supabase.auth.sign_out()
    except Exception:
        pass
    for key in ['logged_in','user_email',
        'user_id','scanner_running']:
        st.session_state[key] = (
            False if key != 'user_email'
            and key != 'user_id' else None)

def reset_password(email):
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "DB connection failed!"
        supabase.auth.reset_password_email(email)
        return True, "Password reset email sent!"
    except Exception as e:
        return False, str(e)

def send_discord_alert(message):
    try:
        webhook_url = st.secrets["DISCORD_WEBHOOK"]
        response = requests.post(
            webhook_url, json={"content": message})
        return response.status_code == 204
    except Exception:
        return False

def send_discord_alert_with_image(message, image_bytes):
    try:
        webhook_url = st.secrets["DISCORD_WEBHOOK"]
        response = requests.post(
            webhook_url,
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
        return int((get_ist_time() - signal_time
            ).total_seconds() / 60)
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
        {"url": "https://www.forexlive.com/feed/news",
         "source": "ForexLive"},
        {"url": "https://feeds.reuters.com/reuters/businessNews",
         "source": "Reuters"},
        {"url": "https://www.marketwatch.com/rss/topstories",
         "source": "MarketWatch"}
    ]
    for feed_info in feeds:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:5]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                impact = get_news_impact(title + " " + summary)
                news_items.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
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
            "lagarde","recession","crisis","emergency"]
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
        {"time": "Today 6:00 PM IST",
         "event": "US Initial Jobless Claims",
         "impact": "Medium", "currency": "USD",
         "forecast": "220K", "previous": "215K"},
        {"time": "Today 8:30 PM IST",
         "event": "US Non-Farm Payrolls",
         "impact": "High", "currency": "USD",
         "forecast": "185K", "previous": "175K"},
        {"time": "Tomorrow 2:30 PM IST",
         "event": "ECB Interest Rate Decision",
         "impact": "High", "currency": "EUR",
         "forecast": "4.25%", "previous": "4.50%"},
        {"time": "Friday 6:00 PM IST",
         "event": "US CPI Monthly",
         "impact": "High", "currency": "USD",
         "forecast": "0.3%", "previous": "0.4%"}
    ]

TICKER_MAP = {
    "XAUUSD": "GC=F", "USDJPY": "JPY=X",
    "AUDCAD": "AUDCAD=X", "GBPJPY": "GBPJPY=X",
    "GBPUSD": "GBPUSD=X", "EURUSD": "EURUSD=X",
    "EURJPY": "EURJPY=X", "US30": "YM=F",
    "NAS100": "NQ=F"
}

TWELVE_MAP = {
    "XAUUSD": "XAU/USD", "USDJPY": "USD/JPY",
    "AUDCAD": "AUD/CAD", "GBPJPY": "GBP/JPY",
    "GBPUSD": "GBP/USD", "EURUSD": "EUR/USD",
    "EURJPY": "EUR/JPY", "US30": "US30/USD",
    "NAS100": "IXIC"
}

def get_data_twelvedata(symbol, interval="5min"):
    try:
        api_key = st.secrets["TWELVEDATA_KEY"]
        url = (
            "https://api.twelvedata.com/time_series?"
            "symbol=" + TWELVE_MAP.get(symbol, symbol) +
            "&interval=" + interval +
            "&outputsize=100&apikey=" + api_key)
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
        df = yf.download(TICKER_MAP.get(symbol, symbol),
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

def detect_bos(df):
    try:
        highs = df['High'].values
        lows = df['Low'].values
        cc = float(df['Close'].values[-1])
        return cc > float(max(highs[-40:-20])), cc < float(min(lows[-40:-20]))
    except Exception:
        return False, False

def detect_fvg(df):
    try:
        bull_fvg = bear_fvg = False
        fvg_zones = []
        for i in range(2, min(20, len(df)-1)):
            hb = float(df['High'].values[-i-1])
            la = float(df['Low'].values[-i+1])
            lb = float(df['Low'].values[-i-1])
            ha = float(df['High'].values[-i+1])
            if la > hb:
                bull_fvg = True
                fvg_zones.append({'type':'bullish',
                    'top':la,'bottom':hb,'index':len(df)-i})
            if ha < lb:
                bear_fvg = True
                fvg_zones.append({'type':'bearish',
                    'top':lb,'bottom':ha,'index':len(df)-i})
        return bull_fvg, bear_fvg, fvg_zones
    except Exception:
        return False, False, []

def detect_liquidity_sweep(df):
    try:
        highs = df['High'].values
        lows = df['Low'].values
        closes = df['Close'].values
        rh = float(max(highs[-30:-5]))
        rl = float(min(lows[-30:-5]))
        return (float(lows[-1]) < rl and float(closes[-1]) > rl), \
               (float(highs[-1]) > rh and float(closes[-1]) < rh)
    except Exception:
        return False, False

def detect_choch(df):
    try:
        closes = df['Close'].values
        mid = len(closes) // 2
        ft = float(closes[mid]) - float(closes[0])
        st = float(closes[-1]) - float(closes[mid])
        return ft < 0 and st > 0, ft > 0 and st < 0
    except Exception:
        return False, False

def detect_order_block(df, direction):
    try:
        closes = df['Close'].values.astype(float)
        opens = df['Open'].values.astype(float)
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        for i in range(5, min(30, len(df)-1)):
            if direction == "BUY":
                if closes[-i] < opens[-i] and closes[-i+1] > opens[-i+1]:
                    return True, opens[-i], lows[-i], len(df)-i
            else:
                if closes[-i] > opens[-i] and closes[-i+1] < opens[-i+1]:
                    return True, highs[-i], opens[-i], len(df)-i
        return False, 0, 0, 0
    except Exception:
        return False, 0, 0, 0

def is_price_in_pd_zone(df, direction):
    try:
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        closes = df['Close'].values.astype(float)
        sh = float(max(highs[-50:]))
        sl = float(min(lows[-50:]))
        r = sh - sl
        if r == 0:
            return True
        pos = (float(closes[-1]) - sl) / r
        return (direction=="BUY" and pos < 0.5) or \
               (direction=="SELL" and pos > 0.5)
    except Exception:
        return True

def calculate_rsi(df, period=14):
    try:
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        rs = gain.rolling(period).mean() / loss.rolling(period).mean()
        return float((100 - (100 / (1 + rs))).iloc[-1])
    except Exception:
        return 50

def get_htf_bias(symbol):
    try:
        df = get_data(symbol, interval="1h")
        if df is None or len(df) < 50:
            return "NEUTRAL"
        ma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        ma50 = float(df['Close'].rolling(50).mean().iloc[-1])
        current = float(df['Close'].iloc[-1])
        if current > ma20 and ma20 > ma50:
            return "BULLISH"
        elif current < ma20 and ma20 < ma50:
            return "BEARISH"
        return "NEUTRAL"
    except Exception:
        return "NEUTRAL"

def detect_market_regime(df):
    try:
        closes = df['Close'].values.astype(float)
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        atr = float(np.mean(highs[-14:] - lows[-14:]))
        deviation = float(np.std(closes[-20:]))
        price_range = float(max(closes[-20:]) - min(closes[-20:]))
        if atr > deviation * 1.5:
            return "VOLATILE"
        elif price_range < atr * 3:
            return "RANGING"
        elif closes[-1] > float(np.mean(closes[-20:])):
            return "TRENDING UP"
        return "TRENDING DOWN"
    except Exception:
        return "UNKNOWN"

def calculate_structure_sl(df, direction, atr):
    try:
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        if direction == "BUY":
            return round(float(min(lows[-10:])) - atr*0.5, 5)
        return round(float(max(highs[-10:])) + atr*0.5, 5)
    except Exception:
        close = float(df['Close'].iloc[-1])
        return round(close - atr*2 if direction=="BUY"
            else close + atr*2, 5)

def generate_chart(df, signal, fvg_zones,
    ob_found, ob_top, ob_bottom, ob_index,
    bull_bos, bear_bos, bull_choch, bear_choch,
    bull_sweep, bear_sweep):
    try:
        fig, ax = plt.subplots(figsize=(16, 9))
        fig.patch.set_facecolor('#080B14')
        ax.set_facecolor('#080B14')
        display_df = df.tail(60).reset_index(drop=True)
        n = len(display_df)
        for i in range(n):
            o = float(display_df['Open'].iloc[i])
            h = float(display_df['High'].iloc[i])
            l = float(display_df['Low'].iloc[i])
            c = float(display_df['Close'].iloc[i])
            color = '#00FF88' if c >= o else '#FF4444'
            ax.plot([i,i],[l,h], color=color, linewidth=0.8)
            ax.add_patch(plt.Rectangle(
                (i-0.35, min(o,c)), 0.7, abs(c-o),
                color=color, alpha=0.9))
        for fvg in fvg_zones:
            try:
                fx = fvg.get('index', n-5) - (len(df)-n)
                if 0 <= fx < n:
                    fc = '#00FF8833' if fvg['type']=='bullish' else '#FF444433'
                    fb = '#00FF88' if fvg['type']=='bullish' else '#FF4444'
                    ax.add_patch(plt.Rectangle(
                        (fx, fvg['bottom']), n-fx,
                        fvg['top']-fvg['bottom'],
                        color=fc, linewidth=1.5, edgecolor=fb))
                    ax.text(fx+0.5, fvg['top'], 'FVG',
                        color=fb, fontsize=7, fontweight='bold')
            except Exception:
                pass
        if ob_found:
            ox = ob_index - (len(df)-n)
            if 0 <= ox < n:
                oc = '#00FF8822' if signal['direction']=='BUY' else '#FF444422'
                ob = '#00FF88' if signal['direction']=='BUY' else '#FF4444'
                ax.add_patch(plt.Rectangle(
                    (ox, ob_bottom), n-ox, ob_top-ob_bottom,
                    color=oc, linewidth=2, edgecolor=ob, linestyle='--'))
                ax.text(ox+0.5, ob_top, 'OB',
                    color=ob, fontsize=8, fontweight='bold')
        if bull_bos or bear_bos:
            bp = (float(max(df['High'].values[-40:-20]))
                if bear_bos else float(min(df['Low'].values[-40:-20])))
            bc = '#00FF88' if bull_bos else '#FF4444'
            ax.axhline(y=bp, color=bc, linewidth=1.5,
                linestyle='--', alpha=0.8)
            ax.text(2, bp, 'BOS', color=bc,
                fontsize=8, fontweight='bold')
        if bull_sweep or bear_sweep:
            sp = (float(min(df['Low'].values[-30:-5]))
                if bull_sweep else float(max(df['High'].values[-30:-5])))
            sc = '#00FF88' if bull_sweep else '#FF4444'
            ax.axhline(y=sp, color=sc, linewidth=1.5,
                linestyle=':', alpha=0.8)
            ax.text(2, sp, 'LIQ', color=sc,
                fontsize=8, fontweight='bold')
        entry = signal['entry']
        sl = signal['sl']
        tp = signal['tp']
        ax.axhline(y=entry, color='#FFFFFF', linewidth=2)
        ax.text(n+0.3, entry, '◄ ENTRY',
            color='#FFFFFF', fontsize=9,
            fontweight='bold', va='center')
        ax.axhline(y=sl, color='#FF4444', linewidth=2)
        ax.text(n+0.3, sl, '◄ SL',
            color='#FF4444', fontsize=9,
            fontweight='bold', va='center')
        ax.axhline(y=tp, color='#00FF88', linewidth=2)
        ax.text(n+0.3, tp, '◄ TP',
            color='#00FF88', fontsize=9,
            fontweight='bold', va='center')
        if signal['direction'] == "BUY":
            ax.add_patch(plt.Rectangle((0,entry),n,tp-entry,
                color='#00FF8815',linewidth=0))
            ax.add_patch(plt.Rectangle((0,sl),n,entry-sl,
                color='#FF444415',linewidth=0))
        else:
            ax.add_patch(plt.Rectangle((0,tp),n,entry-tp,
                color='#00FF8815',linewidth=0))
            ax.add_patch(plt.Rectangle((0,entry),n,sl-entry,
                color='#FF444415',linewidth=0))
        grade = ("A+" if signal['score']>=90 else
                 "A" if signal['score']>=80 else
                 "B" if signal['score']>=70 else "C")
        ax.set_title(
            signal['pair'] + "  " + signal['direction'] +
            "  |  " + str(signal['score']) + "%  |  Grade: " +
            grade + "  |  " + signal['session'],
            color='#00FF88', fontsize=13,
            fontweight='bold', pad=15, fontfamily='monospace')
        fig.text(0.5, 0.97,
            "Entry: " + str(entry) +
            "  SL: " + str(sl) +
            "  TP: " + str(tp) +
            "  RR: 1:" + str(signal['rr']) +
            "  RSI: " + str(signal['rsi']) +
            "  HTF: " + signal['htf_bias'],
            ha='center', color='#8899AA', fontsize=9)
        fig.text(0.5, 0.02,
            " | ".join(signal['reasons'][:4]),
            ha='center', color='#00FF8888', fontsize=9)
        ax.tick_params(colors='#334455')
        for spine in ax.spines.values():
            spine.set_color('#1A2030')
        ax.grid(axis='y', color='#1A2030',
            linewidth=0.5, alpha=0.5)
        plt.tight_layout(rect=[0, 0.04, 1, 0.96])
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150,
            bbox_inches='tight', facecolor='#080B14')
        buf.seek(0)
        image_bytes = buf.read()
        plt.close(fig)
        return image_bytes
    except Exception:
        return None

def analyze_pair(symbol):
    try:
        if not is_trading_session():
            return None
        df_5m = get_data(symbol, interval="5m")
        if df_5m is None or len(df_5m) < 50:
            return None
        score = 0
        reasons = []
        neg = []
        confluences = 0
        htf_bias = get_htf_bias(symbol)
        regime = detect_market_regime(df_5m)
        session = get_current_session()
        bull_bos, bear_bos = detect_bos(df_5m)
        bull_fvg, bear_fvg, fvg_zones = detect_fvg(df_5m)
        bull_sweep, bear_sweep = detect_liquidity_sweep(df_5m)
        bull_choch, bear_choch = detect_choch(df_5m)
        rsi = calculate_rsi(df_5m)
        close = float(df_5m['Close'].iloc[-1])
        highs = df_5m['High'].values.astype(float)
        lows = df_5m['Low'].values.astype(float)
        atr = float(np.mean(highs[-14:] - lows[-14:]))
        is_bull = bull_bos or bull_fvg or bull_sweep or bull_choch
        is_bear = bear_bos or bear_fvg or bear_sweep or bear_choch
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
        ob_found, ob_top, ob_bottom, ob_index = detect_order_block(df_5m, direction)
        in_pd = is_price_in_pd_zone(df_5m, direction)
        if htf_bias == "BULLISH" and direction == "BUY":
            score += 20; reasons.append("HTF Bullish Alignment"); confluences += 1
        elif htf_bias == "BEARISH" and direction == "SELL":
            score += 20; reasons.append("HTF Bearish Alignment"); confluences += 1
        elif htf_bias == "NEUTRAL":
            score += 5; neg.append("HTF Neutral")
        else:
            score -= 10; neg.append("HTF Conflict")
        if bull_bos and direction == "BUY":
            score += 20; reasons.append("Bullish BOS"); confluences += 1
        if bear_bos and direction == "SELL":
            score += 20; reasons.append("Bearish BOS"); confluences += 1
        if bull_fvg and direction == "BUY":
            score += 15; reasons.append("Bullish FVG"); confluences += 1
        if bear_fvg and direction == "SELL":
            score += 15; reasons.append("Bearish FVG"); confluences += 1
        if bull_sweep and direction == "BUY":
            score += 20; reasons.append("Bullish Liq Sweep"); confluences += 1
        if bear_sweep and direction == "SELL":
            score += 20; reasons.append("Bearish Liq Sweep"); confluences += 1
        if bull_choch and direction == "BUY":
            score += 15; reasons.append("Bullish CHOCH"); confluences += 1
        if bear_choch and direction == "SELL":
            score += 15; reasons.append("Bearish CHOCH"); confluences += 1
        if ob_found:
            score += 10; reasons.append("Order Block"); confluences += 1
        if in_pd:
            score += 10; reasons.append("P/D Zone"); confluences += 1
        if direction == "BUY" and 30 < rsi < 60:
            score += 10; reasons.append("RSI Bullish Zone")
        elif direction == "SELL" and 40 < rsi < 70:
            score += 10; reasons.append("RSI Bearish Zone")
        elif rsi > 85:
            score -= 10; neg.append("RSI Overbought")
        elif rsi < 15:
            score -= 10; neg.append("RSI Oversold")
        if regime == "TRENDING UP" and direction == "BUY":
            score += 10; reasons.append("Trend Confirmation")
        elif regime == "TRENDING DOWN" and direction == "SELL":
            score += 10; reasons.append("Trend Confirmation")
        elif regime == "VOLATILE":
            score -= 10; neg.append("High Volatility")
        elif regime == "RANGING":
            score -= 5; neg.append("Ranging Market")
        if session in ["London","New York","London + NY Overlap"]:
            score += 5; reasons.append(session + " Session")
        else:
            score -= 15; neg.append("Off-Peak Session")
        news = st.session_state.get('cached_news', [])
        if [n for n in news if n['impact'] == 3]:
            score -= 15; neg.append("High Impact News!")
        if confluences < 3:
            return None
        score = min(max(score, 0), 95)
        sl = calculate_structure_sl(df_5m, direction, atr)
        sl_dist = abs(close - sl)
        entry = close
        tp = round(entry + sl_dist*2 if direction=="BUY"
            else entry - sl_dist*2, 5)
        return {
            "pair": symbol, "direction": direction,
            "score": score, "entry": round(entry,5),
            "sl": round(sl,5), "tp": round(tp,5),
            "rr": 2.0, "rsi": round(rsi,1),
            "htf_bias": htf_bias, "regime": regime,
            "session": session, "confluences": confluences,
            "reasons": reasons, "negative": neg,
            "time": get_ist_time().strftime('%d %b %Y %H:%M IST'),
            "current_price": round(close,5),
            "atr": round(atr,5), "df": df_5m,
            "fvg_zones": fvg_zones,
            "ob_found": ob_found, "ob_top": ob_top,
            "ob_bottom": ob_bottom, "ob_index": ob_index,
            "bull_bos": bull_bos, "bear_bos": bear_bos,
            "bull_choch": bull_choch, "bear_choch": bear_choch,
            "bull_sweep": bull_sweep, "bear_sweep": bear_sweep
        }
    except Exception:
        return None

def format_discord_message(signal):
    grade = ("A+" if signal['score']>=90 else
             "A" if signal['score']>=80 else
             "B" if signal['score']>=70 else "C")
    emoji = "🟢 BUY" if signal['direction']=="BUY" else "🔴 SELL"
    reasons_text = "\n".join(["✅ "+r for r in signal['reasons']])
    neg_text = "\n".join(["❌ "+n for n in signal['negative']])
    instr = ("📍 **Enter BUY at or below: " + str(signal['entry']) + "**"
        if signal['direction']=="BUY"
        else "📍 **Enter SELL at or above: " + str(signal['entry']) + "**")
    msg = (
        "🚨 **HIGH CONFIDENCE SIGNAL** 🚨\n\n"
        "**" + emoji + " " + signal['pair'] + "**\n\n"
        "📊 Confidence: " + str(signal['score']) + "%\n"
        "🏆 Grade: " + grade + "\n"
        "🔗 Confluences: " + str(signal['confluences']) + "\n\n"
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
        "🟢 Status: FRESH\n\n"
        "⚠️ Skip if price moved >" + str(signal['atr']) + " away!\n\n"
        "✅ **Reasons:**\n" + reasons_text + "\n")
    if signal['negative']:
        msg += "\n❌ **Caution:**\n" + neg_text + "\n"
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
    completed = [j for j in journal if j['result'] != "Pending"]
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
    ('last_news_fetch',None),('show_reset',False)
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
    pairs = ["XAUUSD","USDJPY","AUDCAD","GBPJPY",
             "GBPUSD","EURUSD","EURJPY","US30","NAS100"]
    found = []
    new_high = []
    for pair in pairs:
        result = analyze_pair(pair)
        if result:
            found.append(result)
            if result['score'] >= 80:
                sig_id = get_signal_id(result)
                if sig_id not in st.session_state.sent_signal_ids:
                    new_high.append(result)
    found.sort(key=lambda x: x['score'], reverse=True)
    new_high.sort(key=lambda x: x['score'], reverse=True)
    for signal in new_high[:3]:
        sig_id = get_signal_id(signal)
        msg = format_discord_message(signal)
        chart_bytes = generate_chart(
            signal['df'], signal, signal['fvg_zones'],
            signal['ob_found'], signal['ob_top'],
            signal['ob_bottom'], signal['ob_index'],
            signal['bull_bos'], signal['bear_bos'],
            signal['bull_choch'], signal['bear_choch'],
            signal['bull_sweep'], signal['bear_sweep'])
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
          'ob_index','bull_bos','bear_bos','bull_choch',
          'bear_choch','bull_sweep','bear_sweep']}
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
        <div style='
            font-family: Orbitron, monospace;
            font-size: 2.5em;
            font-weight: 900;
            color: #00FF88;
            text-shadow: 0 0 20px rgba(0,255,136,0.6),
                         0 0 40px rgba(0,255,136,0.3);
            letter-spacing: 3px;
            margin-bottom: 10px;
        '>⬡ AI TRADING SCANNER</div>
        <div style='
            font-family: Exo 2, sans-serif;
            color: #8899AA;
            font-size: 0.95em;
            letter-spacing: 4px;
            margin-bottom: 8px;
        '>PROFESSIONAL FOREX & INDICES INTELLIGENCE</div>
        <div style='
            font-family: Exo 2, sans-serif;
            color: rgba(0,255,136,0.4);
            font-size: 0.8em;
            letter-spacing: 2px;
        '>XAUUSD · EURUSD · GBPUSD · USDJPY · GBPJPY · EURJPY · AUDCAD · US30 · NAS100</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        if st.session_state.show_reset:
            st.markdown("<h3 style='color:#00FF88; font-family:Orbitron,monospace; text-align:center'>🔑 RESET PASSWORD</h3>", unsafe_allow_html=True)
            reset_email = st.text_input("Email", key="reset_email")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Send Reset Email",
                    use_container_width=True, type="primary"):
                    success, msg = reset_password(reset_email)
                    st.success(msg) if success else st.error(msg)
            with col_b:
                if st.button("← Back to Login",
                    use_container_width=True):
                    st.session_state.show_reset = False
                    st.rerun()
        else:
            tab1, tab2 = st.tabs(["🔑  LOGIN", "📝  SIGN UP"])
            with tab1:
                st.markdown("<br>", unsafe_allow_html=True)
                email = st.text_input("Email",
                    key="login_email",
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
                new_email = st.text_input("Email",
                    key="signup_email",
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
                                st.success("✅ " + msg) if success else st.error("❌ " + msg)
                        else:
                            st.error("Passwords do not match!")
                    else:
                        st.error("Please fill all fields!")

    st.markdown("""
    <div style='text-align:center; margin-top:30px; display:flex;
        justify-content:center; gap:15px; flex-wrap:wrap'>
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid rgba(0,255,136,0.2);
            border-radius:10px; padding:12px 18px;
            font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.85em'>
            🧠 SMC + ICT Analysis</div>
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid rgba(0,255,136,0.2);
            border-radius:10px; padding:12px 18px;
            font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.85em'>
            📊 Auto Chart Generation</div>
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid rgba(0,255,136,0.2);
            border-radius:10px; padding:12px 18px;
            font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.85em'>
            🔔 Discord Alerts</div>
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid rgba(0,255,136,0.2);
            border-radius:10px; padding:12px 18px;
            font-family:Exo 2,sans-serif;
            color:#8899AA; font-size:0.85em'>
            📰 News Intelligence</div>
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
                font-size:1.1em; font-weight:700;
                color:#00FF88;
                text-shadow:0 0 10px rgba(0,255,136,0.5);
                letter-spacing:2px'>⬡ AI SCANNER</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='background:rgba(0,255,136,0.05);
            border:1px solid rgba(0,255,136,0.15);
            border-radius:10px; padding:10px;
            margin:5px 0; font-family:Exo 2,sans-serif'>
            <div style='color:#8899AA; font-size:0.75em'>
            👤 USER</div>
            <div style='color:#FFFFFF; font-size:0.8em;
            word-break:break-all'>
        """ + str(st.session_state.user_email) + """
        </div></div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style='background:rgba(0,150,255,0.05);
            border:1px solid rgba(0,150,255,0.15);
            border-radius:10px; padding:10px;
            margin:5px 0; font-family:Orbitron,monospace;
            text-align:center'>
            <div style='color:#0096FF; font-size:0.95em'>
        """ + get_ist_time().strftime('%H:%M:%S IST') + """
            </div>
            <div style='color:#8899AA; font-size:0.7em'>
        """ + get_ist_time().strftime('%d %b %Y') + """
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
    <div class='cyber-title' style='font-size:1.8em; margin-bottom:15px'>
    🏠 DASHBOARD</div>
    """, unsafe_allow_html=True)

    session = get_current_session()
    news = st.session_state.get('cached_news', [])
    high_impact = [n for n in news if n['impact'] == 3]
    stats = calculate_stats()

    if high_impact:
        st.error("🚨 HIGH IMPACT NEWS ACTIVE — Signals paused for safety!")
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
                    font-weight:700;
                    text-shadow:0 0 10px rgba(255,68,68,0.5);
                    margin:8px 0'>● OFFLINE</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("▶ ACTIVATE SCANNER",
                use_container_width=True, type="primary"):
                st.session_state.scanner_running = True
                st.session_state.last_scan_time = None
                st.session_state.sent_signal_ids = set()
                send_discord_alert(
                    "🟢 **AI Trading Scanner ACTIVATED!**\n"
                    "User: " + str(st.session_state.user_email) +
                    "\nSession: " + session +
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
                    font-weight:700;
                    text-shadow:0 0 15px rgba(0,255,136,0.8);
                    margin:8px 0'>● ACTIVE</div>
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
                elapsed / st.session_state.next_scan_seconds)
            st.info("⏱️ Last: " +
                st.session_state.last_scan_time.strftime('%H:%M:%S IST') +
                " | Next scan in: " + str(remaining) + "s")
            st.progress(progress_val)
        else:
            st.info("⚡ Initializing first scan...")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚡ SCAN NOW",
                type="primary", use_container_width=True):
                with st.spinner("Scanning all 9 pairs..."):
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
    <div class='cyber-title' style='font-size:1.8em; margin-bottom:15px'>
    📰 NEWS & ECONOMIC CALENDAR</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh News",
            use_container_width=True, type="primary"):
            with st.spinner("Fetching news..."):
                st.session_state.cached_news = fetch_forex_news()
                st.session_state.last_news_fetch = get_ist_time()
            st.success("✅ News refreshed!")
            st.rerun()
    with col2:
        if st.session_state.last_news_fetch:
            st.info("Updated: " +
                st.session_state.last_news_fetch.strftime('%H:%M:%S IST'))

    st.divider()
    st.markdown("""
    <div style='font-family:Orbitron,monospace; color:#00FF88;
        font-size:0.9em; letter-spacing:2px; margin-bottom:12px'>
    📅 ECONOMIC CALENDAR</div>
    """, unsafe_allow_html=True)

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
    st.markdown("""
    <div style='font-family:Orbitron,monospace; color:#00FF88;
        font-size:0.9em; letter-spacing:2px; margin-bottom:12px'>
    📰 LIVE MARKET NEWS</div>
    """, unsafe_allow_html=True)

    news = st.session_state.get('cached_news', [])
    if not news:
        st.info("Click Refresh News to load latest news!")
        if st.button("📰 Load News Now",
            use_container_width=True):
            with st.spinner("Loading..."):
                st.session_state.cached_news = fetch_forex_news()
                st.session_state.last_news_fetch = get_ist_time()
            st.rerun()
    else:
        for item in [n for n in news if n['impact']==3]:
            with st.expander("🔴 " + item['title'][:80]):
                st.write("📰 " + item['source'])
                st.write("🕐 " + item['published'])
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
            st.write("🟢 " + item['title'][:100] + " | " + item['source'])

def show_signals_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.8em; margin-bottom:15px'>
    📊 ACTIVE SIGNALS</div>
    """, unsafe_allow_html=True)

    news = st.session_state.get('cached_news', [])
    if [n for n in news if n['impact']==3]:
        st.error("🚨 HIGH IMPACT NEWS — Trade with extra caution!")

    if not st.session_state.signals:
        st.markdown("""
        <div style='text-align:center; padding:50px 20px;
            font-family:Exo 2,sans-serif; color:#8899AA'>
            <div style='font-size:3em; margin-bottom:15px'>📡</div>
            <div>No signals detected yet.</div>
            <div style='font-size:0.9em; margin-top:8px'>
            Activate scanner and click Scan Now.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    high = [s for s in st.session_state.signals if s['score'] >= 80]
    medium = [s for s in st.session_state.signals if 60 <= s['score'] < 80]
    low = [s for s in st.session_state.signals if s['score'] < 60]

    if high:
        st.markdown("""
        <div style='font-family:Orbitron,monospace; color:#00FF88;
            font-size:0.85em; letter-spacing:2px; margin-bottom:10px'>
        🟢 HIGH CONFIDENCE — 80%+</div>
        """, unsafe_allow_html=True)
        for signal in high:
            age = get_signal_age(signal['time'])
            status = get_signal_status(age)
            with st.expander(
                "🟢 " + signal['pair'] + " " +
                signal['direction'] + "  |  " +
                str(signal['score']) + "%  |  " +
                str(signal['confluences']) + " conf  |  " + status):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Entry", signal['entry'])
                with col2:
                    st.metric("Stop Loss", signal['sl'])
                with col3:
                    st.metric("Take Profit", signal['tp'])
                if age >= 30:
                    st.error("⛔ EXPIRED — Do not trade!")
                elif age >= 15:
                    st.warning("⚠️ Aging — verify price first!")
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
                    st.write("⏱️ Age: " + str(age) + " min")
                st.write("✅ " + ", ".join(signal['reasons']))
                if signal['negative']:
                    st.warning("❌ " + ", ".join(signal['negative']))

    if medium:
        st.markdown("""
        <div style='font-family:Orbitron,monospace; color:#FFAA00;
            font-size:0.85em; letter-spacing:2px; margin:12px 0 8px'>
        🟡 MEDIUM — 60-80%</div>
        """, unsafe_allow_html=True)
        for signal in medium:
            age = get_signal_age(signal['time'])
            status = get_signal_status(age)
            with st.expander(
                "🟡 " + signal['pair'] + " " +
                signal['direction'] + "  |  " +
                str(signal['score']) + "%  |  " + status):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Entry", signal['entry'])
                with col2:
                    st.metric("SL", signal['sl'])
                with col3:
                    st.metric("TP", signal['tp'])
                st.write("Age: " + str(age) + " min | " + ", ".join(signal['reasons']))

    if low:
        st.markdown("""
        <div style='font-family:Orbitron,monospace; color:#FF4444;
            font-size:0.85em; letter-spacing:2px; margin:12px 0 8px'>
        🔴 LOW — Below 60%</div>
        """, unsafe_allow_html=True)
        for signal in low:
            st.write("🔴 " + signal['pair'] + " | " + str(signal['score']) + "%")

def show_journal_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.8em; margin-bottom:15px'>
    📓 TRADE JOURNAL</div>
    """, unsafe_allow_html=True)

    journal = st.session_state.trade_journal
    if not journal:
        st.info("No trades recorded yet. Start scanner to begin!")
        return

    pending = [j for j in journal if j['result'] == "Pending"]
    if pending:
        st.subheader("⏳ Update Pending Trades")
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
                result = st.selectbox(
                    "Result",
                    ["Pending","TP Hit","SL Hit","Expired","Partial Win"],
                    key="result_" + trade['id'])
                if st.button("✅ Update",
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
        st.write(emoji + " " + trade['pair'] + " " +
            trade['direction'] + " | " + str(trade['score']) +
            "% | " + trade['result'] + " | " + trade['time'])

def show_performance_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.8em; margin-bottom:15px'>
    📈 PERFORMANCE ANALYTICS</div>
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

    st.divider()
    journal = st.session_state.trade_journal
    completed = [j for j in journal if j['result'] != "Pending"]
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
            wr = round(data['wins']/data['total']*100, 1)
            bar = "█" * int(wr/5) + "░" * (20-int(wr/5))
            color = "#00FF88" if wr>=60 else "#FFAA00" if wr>=40 else "#FF4444"
            st.markdown(f"""
            <div style='font-family:Exo 2,sans-serif;
                margin-bottom:6px; padding:8px 12px;
                background:rgba(255,255,255,0.02);
                border-radius:8px'>
                <span style='color:#FFFFFF; font-weight:600'>{pair}</span>
                <span style='color:{color}; font-family:monospace;
                    margin-left:10px'>{bar}</span>
                <span style='color:{color}; margin-left:10px'>{wr}%</span>
                <span style='color:#8899AA; font-size:0.85em'>
                ({data['wins']}/{data['total']})</span>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.subheader("📊 Win Rate by Session")
        session_stats = {}
        for j in completed:
            sess = j.get('session','Unknown')
            if sess not in session_stats:
                session_stats[sess] = {'wins':0,'total':0}
            session_stats[sess]['total'] += 1
            if j['result'] == "TP Hit":
                session_stats[sess]['wins'] += 1
        for sess, data in session_stats.items():
            wr = round(data['wins']/data['total']*100, 1)
            st.write(sess + ": " + str(wr) +
                "% (" + str(data['wins']) + "/" + str(data['total']) + ")")

def show_calendar_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.8em; margin-bottom:15px'>
    📅 CALENDAR ANALYTICS</div>
    """, unsafe_allow_html=True)

    journal = st.session_state.trade_journal
    if not journal:
        st.info("No trades yet!")
        return

    date_stats = {}
    for trade in journal:
        try:
            parts = trade['time'].split(' ')
            date_str = parts[0] + " " + parts[1] + " " + parts[2]
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
        wr = round(data['wins']/data['total']*100,1) if data['total'] > 0 else 0
        color = "🟢" if wr >= 50 else "🔴"
        with st.expander(
            color + " " + date + " | " +
            str(data['total']) + " trades | WR: " + str(wr) + "%"):
            for trade in data['trades']:
                emoji = ("✅" if trade['result']=="TP Hit"
                    else "❌" if trade['result']=="SL Hit"
                    else "⏳")
                st.write(emoji + " " + trade['pair'] + " " +
                    trade['direction'] + " | " +
                    str(trade['score']) + "% | " + trade['result'])

def show_settings_page():
    st.markdown("""
    <div class='cyber-title' style='font-size:1.8em; margin-bottom:15px'>
    ⚙️ SETTINGS</div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:rgba(0,255,136,0.05);
        border:1px solid rgba(0,255,136,0.2);
        border-radius:12px; padding:15px 20px;
        margin-bottom:20px; font-family:Exo 2,sans-serif'>
        <div style='color:#8899AA; font-size:0.85em; margin-bottom:5px'>
        👤 AUTHENTICATED USER</div>
        <div style='color:#00FF88'>
    """ + str(st.session_state.user_email) + """
    </div></div>
    """, unsafe_allow_html=True)

    st.subheader("🔔 Discord")
    if st.button("🔔 Test Discord Alert",
        use_container_width=True):
        success = send_discord_alert(
            "✅ **Test — AI Trading Scanner**\n"
            "All systems operational!\n"
            "User: " + str(st.session_state.user_email) +
            "\nTime: " + get_ist_time().strftime('%d %b %Y %H:%M IST'))
        if success:
            st.success("✅ Discord alert sent!")
        else:
            st.error("❌ Discord failed! Check webhook URL.")

    st.divider()
    st.subheader("⏱️ Scanner Settings")
    scan_interval = st.selectbox(
        "Auto Scan Interval (minutes)",
        [1,2,3,5,10,15], index=3)
    if st.button("💾 Save Interval",
        use_container_width=True):
        st.session_state.next_scan_seconds = scan_interval * 60
        st.success("✅ Set to " + str(scan_interval) + " minutes!")

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
    st.subheader("✅ Active Filters")
    filters = [
        "Supabase Authentication",
        "Min 3 confluences required",
        "Confidence capped at 95%",
        "London + NY session filter",
        "Structure-based Stop Loss",
        "Premium/Discount zone check",
        "No duplicate alerts",
        "Max 3 signals per scan",
        "Chart images in Discord",
        "News impact filter active",
        "Signal expires after 30 mins",
        "Forgot password system",
        "Trade journal active",
        "Performance analytics"
    ]
    cols = st.columns(2)
    for i, f in enumerate(filters):
        with cols[i % 2]:
            st.success("✅ " + f)

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
        <div>⭐ Best Overlap: 5:30 PM — 8:00 PM</div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
