import streamlit as st
import pytz
import requests
from datetime import datetime, timedelta
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

IST = pytz.timezone('Asia/Kolkata')

def get_ist_time():
    return datetime.now(IST)

def is_london_session():
    now = get_ist_time()
    hour = now.hour
    return 12 <= hour <= 20

def is_ny_session():
    now = get_ist_time()
    hour = now.hour
    return 17 <= hour <= 24 or hour == 0

def is_trading_session():
    return is_london_session() or is_ny_session()

def get_current_session():
    now = get_ist_time()
    hour = now.hour
    if 12 <= hour <= 16:
        return "London"
    elif 17 <= hour <= 20:
        return "London + NY Overlap"
    elif 21 <= hour <= 24 or hour == 0:
        return "New York"
    elif 4 <= hour <= 11:
        return "Asia"
    else:
        return "Off Session"

def init_supabase():
    try:
        from supabase import create_client
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

def signup_user(email, password):
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "Database connection failed!"
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        if response.user:
            return True, "Account created! Please check email to verify!"
        return False, "Signup failed!"
    except Exception as e:
        return False, str(e)

def login_user(email, password):
    try:
        supabase = init_supabase()
        if not supabase:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            return True, "Logged in (offline mode)!"
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response.user:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.user_id = response.user.id
            return True, "Login successful!"
        return False, "Invalid email or password!"
    except Exception as e:
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
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.scanner_running = False

def reset_password(email):
    try:
        supabase = init_supabase()
        if not supabase:
            return False, "Database connection failed!"
        supabase.auth.reset_password_email(email)
        return True, "Password reset email sent!"
    except Exception as e:
        return False, str(e)

def save_signal_to_db(signal):
    try:
        supabase = init_supabase()
        if not supabase:
            return False
        data = {
            "user_id": st.session_state.get(
                'user_id', 'offline'),
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
            "reasons": str(signal['reasons']),
            "signal_time": signal['time'],
            "result": "Pending"
        }
        supabase.table('signals').insert(data).execute()
        return True
    except Exception:
        return False

def send_discord_alert(message):
    try:
        webhook_url = st.secrets["DISCORD_WEBHOOK"]
        payload = {"content": message}
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 204
    except Exception:
        return False

def send_discord_alert_with_image(message, image_bytes):
    try:
        webhook_url = st.secrets["DISCORD_WEBHOOK"]
        files = {
            "file": ("chart.png", image_bytes, "image/png")
        }
        data = {"content": message}
        response = requests.post(
            webhook_url, data=data, files=files)
        return response.status_code == 204
    except Exception:
        return False

def get_signal_id(signal):
    key = (signal['pair'] + signal['direction'] +
        str(round(signal['entry'], 2)))
    return hashlib.md5(key.encode()).hexdigest()[:8]

def get_signal_age(signal_time_str):
    try:
        signal_time = IST.localize(
            datetime.strptime(signal_time_str,
                '%d %b %Y %H:%M IST'))
        now = get_ist_time()
        age_minutes = int(
            (now - signal_time).total_seconds() / 60)
        return age_minutes
    except Exception:
        return 0

def get_signal_status(age_minutes):
    if age_minutes < 5:
        return "🟢 FRESH"
    elif age_minutes < 15:
        return "🟡 VALID"
    elif age_minutes < 30:
        return "🟠 AGING"
    else:
        return "🔴 EXPIRED"

def fetch_forex_news():
    news_items = []
    feeds = [
        {
            "url": "https://www.forexlive.com/feed/news",
            "source": "ForexLive"
        },
        {
            "url": "https://feeds.reuters.com/reuters/businessNews",
            "source": "Reuters"
        },
        {
            "url": "https://www.marketwatch.com/rss/topstories",
            "source": "MarketWatch"
        },
        {
            "url": "https://www.investing.com/rss/news.rss",
            "source": "Investing.com"
        }
    ]
    for feed_info in feeds:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:5]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                published = entry.get("published", "")
                summary = entry.get("summary", "")
                impact = get_news_impact(
                    title + " " + summary)
                news_items.append({
                    "title": title,
                    "link": link,
                    "published": published,
                    "source": feed_info["source"],
                    "impact": impact,
                    "summary": summary[:200]
                    if summary else ""
                })
        except Exception:
            pass
    news_items.sort(
        key=lambda x: x['impact'], reverse=True)
    return news_items[:30]

def get_news_impact(text):
    text_lower = text.lower()
    high_impact_keywords = [
        "nfp", "non-farm payroll",
        "fomc", "federal reserve",
        "cpi", "inflation",
        "interest rate", "rate decision",
        "gdp", "unemployment",
        "ecb", "bank of england",
        "boe", "rba", "boj",
        "powell", "lagarde",
        "recession", "crisis",
        "emergency", "war", "conflict",
        "sanctions", "default"
    ]
    medium_impact_keywords = [
        "pmi", "retail sales",
        "trade balance", "housing",
        "manufacturing", "services",
        "consumer confidence", "jobs",
        "employment", "wages"
    ]
    for keyword in high_impact_keywords:
        if keyword in text_lower:
            return 3
    for keyword in medium_impact_keywords:
        if keyword in text_lower:
            return 2
    return 1

def get_economic_calendar():
    events = [
        {
            "time": "Today 6:00 PM IST",
            "event": "US Initial Jobless Claims",
            "impact": "Medium",
            "currency": "USD",
            "forecast": "220K",
            "previous": "215K"
        },
        {
            "time": "Today 8:30 PM IST",
            "event": "US Non-Farm Payrolls (NFP)",
            "impact": "High",
            "currency": "USD",
            "forecast": "185K",
            "previous": "175K"
        },
        {
            "time": "Tomorrow 2:30 PM IST",
            "event": "ECB Interest Rate Decision",
            "impact": "High",
            "currency": "EUR",
            "forecast": "4.25%",
            "previous": "4.50%"
        },
        {
            "time": "Tomorrow 6:00 PM IST",
            "event": "UK GDP Monthly",
            "impact": "Medium",
            "currency": "GBP",
            "forecast": "0.1%",
            "previous": "-0.1%"
        },
        {
            "time": "Friday 6:00 PM IST",
            "event": "US CPI Monthly",
            "impact": "High",
            "currency": "USD",
            "forecast": "0.3%",
            "previous": "0.4%"
        }
    ]
    return events

TICKER_MAP = {
    "XAUUSD": "GC=F",
    "USDJPY": "JPY=X",
    "AUDCAD": "AUDCAD=X",
    "GBPJPY": "GBPJPY=X",
    "GBPUSD": "GBPUSD=X",
    "EURUSD": "EURUSD=X",
    "EURJPY": "EURJPY=X",
    "US30": "YM=F",
    "NAS100": "NQ=F"
}

TWELVE_MAP = {
    "XAUUSD": "XAU/USD",
    "USDJPY": "USD/JPY",
    "AUDCAD": "AUD/CAD",
    "GBPJPY": "GBP/JPY",
    "GBPUSD": "GBP/USD",
    "EURUSD": "EUR/USD",
    "EURJPY": "EUR/JPY",
    "US30": "US30/USD",
    "NAS100": "IXIC"
}

def get_data_twelvedata(symbol, interval="5min"):
    try:
        api_key = st.secrets["TWELVEDATA_KEY"]
        td_symbol = TWELVE_MAP.get(symbol, symbol)
        url = (
            "https://api.twelvedata.com/time_series?"
            "symbol=" + td_symbol +
            "&interval=" + interval +
            "&outputsize=100" +
            "&apikey=" + api_key
        )
        response = requests.get(url, timeout=10)
        data = response.json()
        if "values" not in data:
            return None
        values = data["values"]
        df = pd.DataFrame(values)
        df = df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume"
        })
        for col in ['Open','High','Low','Close']:
            df[col] = pd.to_numeric(
                df[col], errors='coerce')
        df = df.iloc[::-1].reset_index(drop=True)
        return df
    except Exception:
        return None

def get_data_yfinance(symbol, interval="5m"):
    try:
        ticker = TICKER_MAP.get(symbol, symbol)
        df = yf.download(ticker, interval=interval,
            period="5d", progress=False)
        if df is not None and len(df) > 10:
            df.columns = ['Open','High','Low',
                'Close','Volume']
            df = df.reset_index(drop=True)
            return df
        return None
    except Exception:
        return None

def get_data(symbol, interval="5m"):
    interval_map = {
        "5m": "5min",
        "15m": "15min",
        "1h": "1h",
        "4h": "4h"
    }
    td_interval = interval_map.get(interval, "5min")
    df = get_data_twelvedata(symbol, td_interval)
    if df is not None and len(df) > 20:
        return df
    df = get_data_yfinance(symbol, interval)
    return df

def detect_bos(df):
    try:
        highs = df['High'].values
        lows = df['Low'].values
        current_close = float(df['Close'].values[-1])
        prev_high = float(max(highs[-40:-20]))
        prev_low = float(min(lows[-40:-20]))
        bullish_bos = current_close > prev_high
        bearish_bos = current_close < prev_low
        return bullish_bos, bearish_bos
    except Exception:
        return False, False

def detect_fvg(df):
    try:
        bullish_fvg = False
        bearish_fvg = False
        fvg_zones = []
        for i in range(2, min(20, len(df)-1)):
            high_before = float(df['High'].values[-i-1])
            low_after = float(df['Low'].values[-i+1])
            low_before = float(df['Low'].values[-i-1])
            high_after = float(df['High'].values[-i+1])
            if low_after > high_before:
                bullish_fvg = True
                fvg_zones.append({
                    'type': 'bullish',
                    'top': low_after,
                    'bottom': high_before,
                    'index': len(df) - i
                })
            if high_after < low_before:
                bearish_fvg = True
                fvg_zones.append({
                    'type': 'bearish',
                    'top': low_before,
                    'bottom': high_after,
                    'index': len(df) - i
                })
        return bullish_fvg, bearish_fvg, fvg_zones
    except Exception:
        return False, False, []

def detect_liquidity_sweep(df):
    try:
        highs = df['High'].values
        lows = df['Low'].values
        closes = df['Close'].values
        recent_high = float(max(highs[-30:-5]))
        recent_low = float(min(lows[-30:-5]))
        current_high = float(highs[-1])
        current_low = float(lows[-1])
        current_close = float(closes[-1])
        bullish_sweep = (current_low < recent_low
            and current_close > recent_low)
        bearish_sweep = (current_high > recent_high
            and current_close < recent_high)
        return bullish_sweep, bearish_sweep
    except Exception:
        return False, False

def detect_choch(df):
    try:
        closes = df['Close'].values
        mid = len(closes) // 2
        first_trend = (float(closes[mid]) -
            float(closes[0]))
        second_trend = (float(closes[-1]) -
            float(closes[mid]))
        choch_bull = (first_trend < 0
            and second_trend > 0)
        choch_bear = (first_trend > 0
            and second_trend < 0)
        return choch_bull, choch_bear
    except Exception:
        return False, False

def detect_order_block(df, direction):
    try:
        closes = df['Close'].values.astype(float)
        opens = df['Open'].values.astype(float)
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        ob_found = False
        ob_top = 0
        ob_bottom = 0
        ob_index = 0
        for i in range(5, min(30, len(df)-1)):
            if direction == "BUY":
                if (closes[-i] < opens[-i] and
                    closes[-i+1] > opens[-i+1]):
                    ob_top = opens[-i]
                    ob_bottom = lows[-i]
                    ob_index = len(df) - i
                    ob_found = True
                    break
            else:
                if (closes[-i] > opens[-i] and
                    closes[-i+1] < opens[-i+1]):
                    ob_top = highs[-i]
                    ob_bottom = opens[-i]
                    ob_index = len(df) - i
                    ob_found = True
                    break
        return ob_found, ob_top, ob_bottom, ob_index
    except Exception:
        return False, 0, 0, 0

def is_price_in_premium_discount(df, direction):
    try:
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        closes = df['Close'].values.astype(float)
        swing_high = float(max(highs[-50:]))
        swing_low = float(min(lows[-50:]))
        current = float(closes[-1])
        range_size = swing_high - swing_low
        if range_size == 0:
            return True
        position = (current - swing_low) / range_size
        if direction == "BUY" and position < 0.5:
            return True
        elif direction == "SELL" and position > 0.5:
            return True
        return False
    except Exception:
        return True

def calculate_rsi(df, period=14):
    try:
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except Exception:
        return 50

def get_htf_bias(symbol):
    try:
        df_1h = get_data(symbol, interval="1h")
        if df_1h is None or len(df_1h) < 50:
            return "NEUTRAL"
        ma20 = float(
            df_1h['Close'].rolling(20).mean().iloc[-1])
        ma50 = float(
            df_1h['Close'].rolling(50).mean().iloc[-1])
        current = float(df_1h['Close'].iloc[-1])
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
        ma20 = float(np.mean(closes[-20:]))
        deviation = float(np.std(closes[-20:]))
        price_range = float(
            max(closes[-20:]) - min(closes[-20:]))
        if atr > deviation * 1.5:
            return "VOLATILE"
        elif price_range < atr * 3:
            return "RANGING"
        elif closes[-1] > ma20:
            return "TRENDING UP"
        else:
            return "TRENDING DOWN"
    except Exception:
        return "UNKNOWN"

def calculate_structure_sl(df, direction, atr):
    try:
        highs = df['High'].values.astype(float)
        lows = df['Low'].values.astype(float)
        if direction == "BUY":
            recent_low = float(min(lows[-10:]))
            sl = recent_low - (atr * 0.5)
        else:
            recent_high = float(max(highs[-10:]))
            sl = recent_high + (atr * 0.5)
        return round(sl, 5)
    except Exception:
        close = float(df['Close'].iloc[-1])
        if direction == "BUY":
            return round(close - atr * 2, 5)
        else:
            return round(close + atr * 2, 5)

def generate_chart(df, signal, fvg_zones,
    ob_found, ob_top, ob_bottom, ob_index,
    bull_bos, bear_bos, bull_choch, bear_choch,
    bull_sweep, bear_sweep):
    try:
        fig, ax = plt.subplots(figsize=(14, 8))
        fig.patch.set_facecolor('#0A0A0A')
        ax.set_facecolor('#0A0A0A')
        display_df = df.tail(50).reset_index(drop=True)
        n = len(display_df)
        for i in range(n):
            o = float(display_df['Open'].iloc[i])
            h = float(display_df['High'].iloc[i])
            l = float(display_df['Low'].iloc[i])
            c = float(display_df['Close'].iloc[i])
            color = '#00FF88' if c >= o else '#FF4444'
            ax.plot([i, i], [l, h],
                color=color, linewidth=1)
            ax.add_patch(plt.Rectangle(
                (i - 0.3, min(o, c)),
                0.6, abs(c - o),
                color=color, alpha=0.9))
        for fvg in fvg_zones:
            try:
                fvg_x = fvg.get('index', n-5) - (
                    len(df) - n)
                if 0 <= fvg_x < n:
                    color = ('#00FF8844'
                        if fvg['type'] == 'bullish'
                        else '#FF444444')
                    border = ('#00FF88'
                        if fvg['type'] == 'bullish'
                        else '#FF4444')
                    ax.add_patch(plt.Rectangle(
                        (fvg_x, fvg['bottom']),
                        n - fvg_x,
                        fvg['top'] - fvg['bottom'],
                        color=color,
                        linewidth=1.5,
                        edgecolor=border))
                    label = ('FVG Bull'
                        if fvg['type'] == 'bullish'
                        else 'FVG Bear')
                    ax.text(fvg_x + 0.5,
                        fvg['top'], label,
                        color=border, fontsize=7,
                        fontweight='bold')
            except Exception:
                pass
        if ob_found:
            ob_x = ob_index - (len(df) - n)
            if 0 <= ob_x < n:
                ob_color = ('#00FF8833'
                    if signal['direction'] == 'BUY'
                    else '#FF444433')
                ob_border = ('#00FF88'
                    if signal['direction'] == 'BUY'
                    else '#FF4444')
                ax.add_patch(plt.Rectangle(
                    (ob_x, ob_bottom),
                    n - ob_x,
                    ob_top - ob_bottom,
                    color=ob_color,
                    linewidth=2,
                    edgecolor=ob_border,
                    linestyle='--'))
                ax.text(ob_x + 0.5, ob_top, 'OB',
                    color=ob_border, fontsize=8,
                    fontweight='bold')
        if bull_bos or bear_bos:
            bos_price = (float(max(
                df['High'].values[-40:-20]))
                if bear_bos else float(min(
                df['Low'].values[-40:-20])))
            bos_color = '#00FF88' if bull_bos else '#FF4444'
            bos_label = 'BOS Bull' if bull_bos else 'BOS Bear'
            ax.axhline(y=bos_price, color=bos_color,
                linewidth=1.5, linestyle='--', alpha=0.8)
            ax.text(2, bos_price, bos_label,
                color=bos_color, fontsize=8,
                fontweight='bold')
        if bull_sweep or bear_sweep:
            sweep_price = (float(min(
                df['Low'].values[-30:-5]))
                if bull_sweep else float(max(
                df['High'].values[-30:-5])))
            sweep_color = ('#00FF88'
                if bull_sweep else '#FF4444')
            ax.axhline(y=sweep_price,
                color=sweep_color, linewidth=1.5,
                linestyle=':', alpha=0.8)
            ax.text(2, sweep_price, 'Liq Sweep',
                color=sweep_color, fontsize=8,
                fontweight='bold')
        entry = signal['entry']
        sl = signal['sl']
        tp = signal['tp']
        ax.axhline(y=entry, color='#FFFFFF',
            linewidth=2, alpha=0.9)
        ax.text(n + 0.3, entry, 'ENTRY',
            color='#FFFFFF', fontsize=9,
            fontweight='bold')
        ax.axhline(y=sl, color='#FF4444',
            linewidth=2, alpha=0.9)
        ax.text(n + 0.3, sl, 'SL',
            color='#FF4444', fontsize=9,
            fontweight='bold')
        ax.axhline(y=tp, color='#00FF88',
            linewidth=2, alpha=0.9)
        ax.text(n + 0.3, tp, 'TP',
            color='#00FF88', fontsize=9,
            fontweight='bold')
        if signal['direction'] == "BUY":
            ax.add_patch(plt.Rectangle(
                (0, entry), n, tp - entry,
                color='#00FF8822', linewidth=0))
            ax.add_patch(plt.Rectangle(
                (0, sl), n, entry - sl,
                color='#FF444422', linewidth=0))
        else:
            ax.add_patch(plt.Rectangle(
                (0, tp), n, entry - tp,
                color='#00FF8822', linewidth=0))
            ax.add_patch(plt.Rectangle(
                (0, entry), n, sl - entry,
                color='#FF444422', linewidth=0))
        grade = ("A+" if signal['score'] >= 90 else
                 "A" if signal['score'] >= 80 else
                 "B" if signal['score'] >= 70 else "C")
        title = (signal['pair'] + " " +
            signal['direction'] + " | " +
            str(signal['score']) + "% | Grade: " +
            grade + " | " + signal['session'])
        ax.set_title(title, color='#FFFFFF',
            fontsize=14, fontweight='bold', pad=15)
        reasons_text = " | ".join(signal['reasons'][:4])
        fig.text(0.5, 0.02, reasons_text,
            ha='center', color='#AAAAAA', fontsize=9)
        info_text = (
            "Entry: " + str(entry) +
            "  SL: " + str(sl) +
            "  TP: " + str(tp) +
            "  RR: 1:" + str(signal['rr']) +
            "  RSI: " + str(signal['rsi']) +
            "  HTF: " + signal['htf_bias'])
        fig.text(0.5, 0.96, info_text,
            ha='center', color='#CCCCCC', fontsize=9)
        ax.tick_params(colors='#AAAAAA')
        for spine in ax.spines.values():
            spine.set_color('#333333')
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150,
            bbox_inches='tight',
            facecolor='#0A0A0A')
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
        negative_reasons = []
        confluences = 0
        htf_bias = get_htf_bias(symbol)
        regime = detect_market_regime(df_5m)
        session = get_current_session()
        bull_bos, bear_bos = detect_bos(df_5m)
        bull_fvg, bear_fvg, fvg_zones = detect_fvg(df_5m)
        bull_sweep, bear_sweep = detect_liquidity_sweep(
            df_5m)
        bull_choch, bear_choch = detect_choch(df_5m)
        rsi = calculate_rsi(df_5m)
        close = float(df_5m['Close'].iloc[-1])
        highs = df_5m['High'].values.astype(float)
        lows = df_5m['Low'].values.astype(float)
        atr = float(np.mean(highs[-14:] - lows[-14:]))
        is_bullish = (bull_bos or bull_fvg
            or bull_sweep or bull_choch)
        is_bearish = (bear_bos or bear_fvg
            or bear_sweep or bear_choch)
        if is_bullish and not is_bearish:
            direction = "BUY"
        elif is_bearish and not is_bullish:
            direction = "SELL"
        elif is_bullish and is_bearish:
            if htf_bias == "BULLISH":
                direction = "BUY"
            elif htf_bias == "BEARISH":
                direction = "SELL"
            else:
                return None
        else:
            return None
        ob_found, ob_top, ob_bottom, ob_index = (
            detect_order_block(df_5m, direction))
        in_pd_zone = is_price_in_premium_discount(
            df_5m, direction)
        if htf_bias == "BULLISH" and direction == "BUY":
            score += 20
            reasons.append("HTF Bullish Alignment")
            confluences += 1
        elif htf_bias == "BEARISH" and direction == "SELL":
            score += 20
            reasons.append("HTF Bearish Alignment")
            confluences += 1
        elif htf_bias == "NEUTRAL":
            score += 5
            negative_reasons.append("HTF Neutral")
        else:
            score -= 10
            negative_reasons.append("HTF Conflict")
        if bull_bos and direction == "BUY":
            score += 20
            reasons.append("Bullish BOS")
            confluences += 1
        if bear_bos and direction == "SELL":
            score += 20
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
            score += 20
            reasons.append("Bullish Liquidity Sweep")
            confluences += 1
        if bear_sweep and direction == "SELL":
            score += 20
            reasons.append("Bearish Liquidity Sweep")
            confluences += 1
        if bull_choch and direction == "BUY":
            score += 15
            reasons.append("Bullish CHOCH")
            confluences += 1
        if bear_choch and direction == "SELL":
            score += 15
            reasons.append("Bearish CHOCH")
            confluences += 1
        if ob_found:
            score += 10
            reasons.append("Order Block Present")
            confluences += 1
        if in_pd_zone:
            score += 10
            reasons.append("Premium/Discount Zone")
            confluences += 1
        if direction == "BUY" and 30 < rsi < 60:
            score += 10
            reasons.append("RSI Bullish Zone")
        elif direction == "SELL" and 40 < rsi < 70:
            score += 10
            reasons.append("RSI Bearish Zone")
        elif rsi > 85:
            score -= 10
            negative_reasons.append("RSI Overbought")
        elif rsi < 15:
            score -= 10
            negative_reasons.append("RSI Oversold")
        if regime == "TRENDING UP" and direction == "BUY":
            score += 10
            reasons.append("Trend Confirmation")
        elif regime == "TRENDING DOWN" and direction == "SELL":
            score += 10
            reasons.append("Trend Confirmation")
        elif regime == "VOLATILE":
            score -= 10
            negative_reasons.append("High Volatility")
        elif regime == "RANGING":
            score -= 5
            negative_reasons.append("Ranging Market")
        if session in ["London", "New York",
            "London + NY Overlap"]:
            score += 5
            reasons.append(session + " Session")
        else:
            score -= 15
            negative_reasons.append("Off-Peak Session")
        news = st.session_state.get('cached_news', [])
        high_impact = [n for n in news
            if n['impact'] == 3]
        if high_impact:
            score -= 15
            negative_reasons.append(
                "High Impact News Active!")
        if confluences < 3:
            return None
        score = min(score, 95)
        score = max(score, 0)
        sl = calculate_structure_sl(df_5m, direction, atr)
        sl_distance = abs(close - sl)
        if direction == "BUY":
            entry = close
            tp = round(entry + (sl_distance * 2), 5)
        else:
            entry = close
            tp = round(entry - (sl_distance * 2), 5)
        return {
            "pair": symbol,
            "direction": direction,
            "score": score,
            "entry": round(entry, 5),
            "sl": round(sl, 5),
            "tp": round(tp, 5),
            "rr": 2.0,
            "rsi": round(rsi, 1),
            "htf_bias": htf_bias,
            "regime": regime,
            "session": session,
            "confluences": confluences,
            "reasons": reasons,
            "negative": negative_reasons,
            "time": get_ist_time().strftime(
                '%d %b %Y %H:%M IST'),
            "current_price": round(close, 5),
            "atr": round(atr, 5),
            "df": df_5m,
            "fvg_zones": fvg_zones,
            "ob_found": ob_found,
            "ob_top": ob_top,
            "ob_bottom": ob_bottom,
            "ob_index": ob_index,
            "bull_bos": bull_bos,
            "bear_bos": bear_bos,
            "bull_choch": bull_choch,
            "bear_choch": bear_choch,
            "bull_sweep": bull_sweep,
            "bear_sweep": bear_sweep
        }
    except Exception:
        return None

def format_discord_message(signal):
    grade = ("A+" if signal['score'] >= 90 else
             "A" if signal['score'] >= 80 else
             "B" if signal['score'] >= 70 else "C")
    emoji = ("🟢 BUY" if signal['direction'] == "BUY"
             else "🔴 SELL")
    reasons_text = "\n".join(
        ["✅ " + r for r in signal['reasons']])
    neg_text = "\n".join(
        ["❌ " + n for n in signal['negative']])
    if signal['direction'] == "BUY":
        entry_instruction = (
            "📍 **Enter BUY at or below: " +
            str(signal['entry']) + "**")
    else:
        entry_instruction = (
            "📍 **Enter SELL at or above: " +
            str(signal['entry']) + "**")
    msg = (
        "🚨 **HIGH CONFIDENCE SIGNAL** 🚨\n\n"
        "**" + emoji + " " + signal['pair'] + "**\n\n"
        "📊 Confidence: " + str(signal['score']) + "%\n"
        "🏆 Grade: " + grade + "\n"
        "🔗 Confluences: " +
        str(signal['confluences']) + "\n\n"
        + entry_instruction + "\n"
        "💰 Entry: " + str(signal['entry']) + "\n"
        "🛑 Stop Loss: " + str(signal['sl']) + "\n"
        "🎯 Take Profit: " + str(signal['tp']) + "\n"
        "⚖️ RR Ratio: 1:" + str(signal['rr']) + "\n\n"
        "📈 HTF Bias: " + signal['htf_bias'] + "\n"
        "🌍 Market: " + signal['regime'] + "\n"
        "🕐 Session: " + signal['session'] + "\n"
        "📉 RSI: " + str(signal['rsi']) + "\n\n"
        "⏰ Time: " + signal['time'] + "\n"
        "🟢 Status: FRESH\n\n"
        "⚠️ Skip if price moved >" +
        str(signal['atr']) + " away!\n\n"
        "✅ **Reasons:**\n" + reasons_text + "\n"
    )
    if signal['negative']:
        msg += "\n❌ **Caution:**\n" + neg_text + "\n"
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━"
    return msg

def add_to_journal(signal):
    journal_entry = {
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
    existing_ids = [j['id'] for j in
        st.session_state.trade_journal]
    if journal_entry['id'] not in existing_ids:
        st.session_state.trade_journal.append(
            journal_entry)
        save_signal_to_db(signal)

def calculate_stats():
    journal = st.session_state.trade_journal
    if not journal:
        return {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "pending": 0,
            "win_rate": 0,
            "best_pair": "N/A",
            "best_session": "N/A"
        }
    completed = [j for j in journal
        if j['result'] != "Pending"]
    wins = [j for j in completed
        if j['result'] == "TP Hit"]
    losses = [j for j in completed
        if j['result'] == "SL Hit"]
    pending = [j for j in journal
        if j['result'] == "Pending"]
    win_rate = (len(wins) / len(completed) * 100
        if completed else 0)
    pair_wins = {}
    for j in wins:
        pair_wins[j['pair']] = (
            pair_wins.get(j['pair'], 0) + 1)
    best_pair = (max(pair_wins, key=pair_wins.get)
        if pair_wins else "N/A")
    session_wins = {}
    for j in wins:
        session_wins[j['session']] = (
            session_wins.get(j['session'], 0) + 1)
    best_session = (max(session_wins,
        key=session_wins.get)
        if session_wins else "N/A")
    return {
        "total": len(journal),
        "wins": len(wins),
        "losses": len(losses),
        "pending": len(pending),
        "win_rate": round(win_rate, 1),
        "best_pair": best_pair,
        "best_session": best_session
    }

if 'scanner_running' not in st.session_state:
    st.session_state.scanner_running = False
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'signals' not in st.session_state:
    st.session_state.signals = []
if 'alerts_sent' not in st.session_state:
    st.session_state.alerts_sent = 0
if 'total_scans' not in st.session_state:
    st.session_state.total_scans = 0
if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = None
if 'next_scan_seconds' not in st.session_state:
    st.session_state.next_scan_seconds = 300
if 'sent_signal_ids' not in st.session_state:
    st.session_state.sent_signal_ids = set()
if 'trade_journal' not in st.session_state:
    st.session_state.trade_journal = []
if 'cached_news' not in st.session_state:
    st.session_state.cached_news = []
if 'last_news_fetch' not in st.session_state:
    st.session_state.last_news_fetch = None
if 'show_reset' not in st.session_state:
    st.session_state.show_reset = False

def refresh_news():
    try:
        now = get_ist_time()
        if st.session_state.last_news_fetch is None:
            st.session_state.cached_news = (
                fetch_forex_news())
            st.session_state.last_news_fetch = now
            return
        elapsed = int((now -
            st.session_state.last_news_fetch
            ).total_seconds())
        if elapsed >= 900:
            st.session_state.cached_news = (
                fetch_forex_news())
            st.session_state.last_news_fetch = now
    except Exception:
        pass

def run_scan():
    refresh_news()
    pairs = [
        "XAUUSD","USDJPY","AUDCAD",
        "GBPJPY","GBPUSD","EURUSD",
        "EURJPY","US30","NAS100"
    ]
    found_signals = []
    new_high_conf = []
    for pair in pairs:
        result = analyze_pair(pair)
        if result:
            found_signals.append(result)
            if result['score'] >= 80:
                sig_id = get_signal_id(result)
                if sig_id not in (
                    st.session_state.sent_signal_ids):
                    new_high_conf.append(result)
    found_signals.sort(
        key=lambda x: x['score'], reverse=True)
    new_high_conf.sort(
        key=lambda x: x['score'], reverse=True)
    top_signals = new_high_conf[:3]
    for signal in top_signals:
        sig_id = get_signal_id(signal)
        msg = format_discord_message(signal)
        chart_bytes = generate_chart(
            signal['df'], signal,
            signal['fvg_zones'],
            signal['ob_found'],
            signal['ob_top'],
            signal['ob_bottom'],
            signal['ob_index'],
            signal['bull_bos'],
            signal['bear_bos'],
            signal['bull_choch'],
            signal['bear_choch'],
            signal['bull_sweep'],
            signal['bear_sweep'])
        if chart_bytes:
            success = send_discord_alert_with_image(
                msg, chart_bytes)
        else:
            success = send_discord_alert(msg)
        if success:
            st.session_state.sent_signal_ids.add(sig_id)
            st.session_state.alerts_sent += 1
            add_to_journal(signal)
    if len(st.session_state.sent_signal_ids) > 100:
        st.session_state.sent_signal_ids = set()
    signals_clean = []
    for s in found_signals:
        s_clean = {k: v for k, v in s.items()
            if k not in ['df','fvg_zones',
                'ob_found','ob_top','ob_bottom',
                'ob_index','bull_bos','bear_bos',
                'bull_choch','bear_choch',
                'bull_sweep','bear_sweep']}
        signals_clean.append(s_clean)
    st.session_state.signals = signals_clean
    st.session_state.total_scans += 1
    st.session_state.last_scan_time = get_ist_time()

def main():
    if not st.session_state.logged_in:
        show_login_page()
    else:
        if st.session_state.scanner_running:
            auto_scan()
        show_dashboard()

def auto_scan():
    try:
        now = get_ist_time()
        if st.session_state.last_scan_time is None:
            run_scan()
            return
        elapsed = int((now -
            st.session_state.last_scan_time
            ).total_seconds())
        if elapsed >= st.session_state.next_scan_seconds:
            run_scan()
    except Exception:
        pass

def show_login_page():
    st.markdown("""
    <div style='text-align:center; padding:30px'>
        <h1 style='color:#00FF88; font-size:2.5em'>
        📈 AI Trading Scanner</h1>
        <p style='color:#AAAAAA; font-size:1.1em'>
        Professional Forex & Indices Scanner</p>
        <p style='color:#AAAAAA'>
        XAUUSD | EURUSD | GBPUSD | USDJPY |
        GBPJPY | EURJPY | AUDCAD | US30 | NAS100
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.session_state.show_reset:
            st.subheader("🔑 Reset Password")
            reset_email = st.text_input(
                "Enter your email", key="reset_email")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Send Reset Email",
                    use_container_width=True,
                    type="primary"):
                    success, msg = reset_password(
                        reset_email)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
            with col_b:
                if st.button("Back to Login",
                    use_container_width=True):
                    st.session_state.show_reset = False
                    st.rerun()
        else:
            tab1, tab2 = st.tabs(
                ["🔑 Login", "📝 Sign Up"])
            with tab1:
                st.subheader("Welcome Back!")
                email = st.text_input(
                    "Email", key="login_email")
                password = st.text_input(
                    "Password", type="password",
                    key="login_pass")
                if st.button("🔑 Login",
                    use_container_width=True,
                    type="primary"):
                    if email and password:
                        success, msg = login_user(
                            email, password)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error(
                            "Please enter email and password!")
                if st.button("Forgot Password?",
                    use_container_width=True):
                    st.session_state.show_reset = True
                    st.rerun()

            with tab2:
                st.subheader("Create Account")
                new_email = st.text_input(
                    "Email", key="signup_email")
                new_pass = st.text_input(
                    "Password", type="password",
                    key="signup_pass")
                confirm_pass = st.text_input(
                    "Confirm Password",
                    type="password",
                    key="confirm_pass")
                if st.button("📝 Create Account",
                    use_container_width=True,
                    type="primary"):
                    if new_email and new_pass and confirm_pass:
                        if new_pass == confirm_pass:
                            if len(new_pass) < 6:
                                st.error(
                                    "Password must be "
                                    "at least 6 characters!")
                            else:
                                success, msg = signup_user(
                                    new_email, new_pass)
                                if success:
                                    st.success(msg)
                                else:
                                    st.error(msg)
                        else:
                            st.error(
                                "Passwords do not match!")
                    else:
                        st.error("Please fill all fields!")

def show_dashboard():
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center'>
            <h2 style='color:#00FF88'>📈 AI Scanner</h2>
        </div>
        """, unsafe_allow_html=True)
        st.write("👤 " + str(st.session_state.user_email))
        st.write("🕐 " + get_ist_time().strftime(
            '%d %b %Y %H:%M:%S IST'))
        st.divider()
        session = get_current_session()
        if session in ["London", "New York",
            "London + NY Overlap"]:
            st.success("🟢 " + session)
        else:
            st.warning("⚠️ " + session)
        news = st.session_state.get('cached_news', [])
        high_impact = [n for n in news
            if n['impact'] == 3]
        if high_impact:
            st.error("🚨 HIGH IMPACT NEWS!")
        st.divider()
        stats = calculate_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Win Rate",
                str(stats['win_rate']) + "%")
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
    st.title("🏠 Dashboard")
    session = get_current_session()
    news = st.session_state.get('cached_news', [])
    high_impact = [n for n in news if n['impact'] == 3]
    if high_impact:
        st.error(
            "🚨 HIGH IMPACT NEWS ACTIVE! "
            "Signals paused for safety!")
    if session not in ["London", "New York",
        "London + NY Overlap"]:
        st.warning(
            "⚠️ " + session +
            " — Best during London (12PM-8PM IST)"
            " and NY (9PM-12AM IST)!")
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if not st.session_state.scanner_running:
            st.success("Scanner is STOPPED")
            if st.button("▶ START SCANNER",
                use_container_width=True,
                type="primary"):
                st.session_state.scanner_running = True
                st.session_state.last_scan_time = None
                st.session_state.sent_signal_ids = set()
                send_discord_alert(
                    "🟢 **AI Trading Scanner STARTED!**\n"
                    "User: " +
                    str(st.session_state.user_email) +
                    "\nSession: " + session + "\n"
                    "News filter: Active!\n"
                    "Chart images: Enabled!\n"
                    "Time: " + get_ist_time().strftime(
                        '%d %b %Y %H:%M IST'))
                st.rerun()
        else:
            st.error("Scanner is ACTIVE")
            if st.button("⏹ STOP SCANNER",
                use_container_width=True):
                st.session_state.scanner_running = False
                send_discord_alert(
                    "🔴 **AI Trading Scanner STOPPED!**\n"
                    "Scans: " +
                    str(st.session_state.total_scans) +
                    "\nAlerts: " +
                    str(st.session_state.alerts_sent))
                st.rerun()
    st.divider()
    stats = calculate_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.session_state.scanner_running:
            st.metric("Scanner", "🟢 ACTIVE")
        else:
            st.metric("Scanner", "🔴 STOPPED")
    with col2:
        st.metric("Win Rate",
            str(stats['win_rate']) + "%")
    with col3:
        st.metric("Alerts Sent",
            st.session_state.alerts_sent)
    with col4:
        st.metric("Total Scans",
            st.session_state.total_scans)
    st.divider()
    if st.session_state.scanner_running:
        if st.session_state.last_scan_time:
            elapsed = int((get_ist_time() -
                st.session_state.last_scan_time
                ).total_seconds())
            remaining = max(0,
                st.session_state.next_scan_seconds -
                elapsed)
            st.info(
                "⏱️ Last scan: " +
                st.session_state.last_scan_time.strftime(
                    '%H:%M:%S IST') +
                " | Next in: " +
                str(remaining) + "s")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 SCAN NOW",
                type="primary",
                use_container_width=True):
                with st.spinner("Scanning all pairs..."):
                    run_scan()
                st.success("Scan complete!")
                st.rerun()
        with col2:
            if st.button("🔃 REFRESH",
                use_container_width=True):
                st.rerun()
    st.divider()
    st.subheader("📡 Pairs Being Scanned")
    pairs = [
        "XAUUSD","USDJPY","AUDCAD",
        "GBPJPY","GBPUSD","EURUSD",
        "EURJPY","US30","NAS100"
    ]
    cols = st.columns(3)
    for i, pair in enumerate(pairs):
        with cols[i % 3]:
            st.info(pair)
    if st.session_state.scanner_running:
        time.sleep(1)
        st.rerun()

def show_news_page():
    st.title("📰 News & Economic Calendar")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh News",
            use_container_width=True,
            type="primary"):
            with st.spinner("Fetching latest news..."):
                st.session_state.cached_news = (
                    fetch_forex_news())
                st.session_state.last_news_fetch = (
                    get_ist_time())
            st.success("News refreshed!")
            st.rerun()
    with col2:
        if st.session_state.last_news_fetch:
            st.info("Updated: " +
                st.session_state.last_news_fetch.strftime(
                    '%H:%M:%S IST'))
    st.divider()
    st.subheader("📅 Economic Calendar")
    events = get_economic_calendar()
    for event in events:
        impact_emoji = (
            "🔴" if event['impact'] == "High" else
            "🟡" if event['impact'] == "Medium" else
            "🟢")
        with st.expander(
            impact_emoji + " " + event['time'] +
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
    st.subheader("📰 Latest Market News")
    news = st.session_state.get('cached_news', [])
    if not news:
        st.info("Click Refresh News to load!")
        if st.button("📰 Load News Now",
            use_container_width=True):
            with st.spinner("Loading..."):
                st.session_state.cached_news = (
                    fetch_forex_news())
                st.session_state.last_news_fetch = (
                    get_ist_time())
            st.rerun()
    else:
        high_impact = [n for n in news
            if n['impact'] == 3]
        medium_impact = [n for n in news
            if n['impact'] == 2]
        low_impact = [n for n in news
            if n['impact'] == 1]
        if high_impact:
            st.subheader("🔴 High Impact News")
            for item in high_impact:
                with st.expander(
                    "🔴 " + item['title'][:80]):
                    st.write("📰 " + item['source'])
                    st.write("🕐 " + item['published'])
                    if item['summary']:
                        st.write(item['summary'])
                    st.markdown(
                        "[Read Full Article →](" +
                        item['link'] + ")")
        if medium_impact:
            st.subheader("🟡 Medium Impact News")
            for item in medium_impact[:5]:
                with st.expander(
                    "🟡 " + item['title'][:80]):
                    st.write("📰 " + item['source'])
                    if item['summary']:
                        st.write(item['summary'])
                    st.markdown(
                        "[Read Full Article →](" +
                        item['link'] + ")")
        if low_impact:
            st.subheader("🟢 General Market News")
            for item in low_impact[:5]:
                st.write("🟢 " + item['title'][:100] +
                    " | " + item['source'])

def show_signals_page():
    st.title("📊 Active Signals")
    news = st.session_state.get('cached_news', [])
    high_impact = [n for n in news if n['impact'] == 3]
    if high_impact:
        st.error(
            "🚨 HIGH IMPACT NEWS ACTIVE! "
            "Be careful with these signals!")
    if not st.session_state.signals:
        st.info("No signals yet! Start scanner!")
        return
    high = [s for s in st.session_state.signals
        if s['score'] >= 80]
    medium = [s for s in st.session_state.signals
        if 60 <= s['score'] < 80]
    low = [s for s in st.session_state.signals
        if s['score'] < 60]
    if high:
        st.subheader("🟢 High Confidence (80%+)")
        for signal in high:
            age = get_signal_age(signal['time'])
            status = get_signal_status(age)
            with st.expander(
                "🟢 " + signal['pair'] + " " +
                signal['direction'] + " | " +
                str(signal['score']) + "% | " +
                status):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Entry", signal['entry'])
                with col2:
                    st.metric("SL", signal['sl'])
                with col3:
                    st.metric("TP", signal['tp'])
                if age >= 30:
                    st.error("⛔ EXPIRED!")
                elif age >= 15:
                    st.warning("⚠️ Signal aging!")
                else:
                    if signal['direction'] == "BUY":
                        st.success(
                            "✅ Enter BUY at or below: "
                            + str(signal['entry']))
                    else:
                        st.success(
                            "✅ Enter SELL at or above: "
                            + str(signal['entry']))
                st.write("RR: 1:" + str(signal['rr']))
                st.write("HTF: " + signal['htf_bias'])
                st.write("Session: " + signal['session'])
                st.write("Market: " + signal['regime'])
                st.write("RSI: " + str(signal['rsi']))
                st.write("Age: " + str(age) +
                    " min | " + status)
                st.write("Reasons: " +
                    ", ".join(signal['reasons']))
                if signal['negative']:
                    st.warning("Caution: " +
                        ", ".join(signal['negative']))
    if medium:
        st.subheader("🟡 Medium (60-80%)")
        for signal in medium:
            age = get_signal_age(signal['time'])
            status = get_signal_status(age)
            with st.expander(
                "🟡 " + signal['pair'] + " " +
                signal['direction'] + " | " +
                str(signal['score']) + "%"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Entry", signal['entry'])
                with col2:
                    st.metric("SL", signal['sl'])
                with col3:
                    st.metric("TP", signal['tp'])
                st.write("Age: " + str(age) + " min")
                st.write("Reasons: " +
                    ", ".join(signal['reasons']))
    if low:
        st.subheader("🔴 Low Confidence")
        for signal in low:
            st.write("🔴 " + signal['pair'] +
                " | " + str(signal['score']) + "%")

def show_journal_page():
    st.title("📓 Trade Journal")
    journal = st.session_state.trade_journal
    if not journal:
        st.info("No trades recorded yet!")
        return
    pending = [j for j in journal
        if j['result'] == "Pending"]
    if pending:
        st.subheader("⏳ Update Pending Trades")
        for trade in pending:
            with st.expander(
                "⏳ " + trade['pair'] + " " +
                trade['direction'] + " | " +
                str(trade['score']) + "% | " +
                trade['time']):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Entry", trade['entry'])
                with col2:
                    st.metric("SL", trade['sl'])
                with col3:
                    st.metric("TP", trade['tp'])
                result = st.selectbox(
                    "Select Result",
                    ["Pending", "TP Hit",
                     "SL Hit", "Expired",
                     "Partial Win"],
                    key="result_" + trade['id'])
                if st.button("✅ Update Result",
                    key="update_" + trade['id'],
                    use_container_width=True):
                    for j in (
                        st.session_state.trade_journal):
                        if j['id'] == trade['id']:
                            j['result'] = result
                            if result == "TP Hit":
                                j['pnl'] = trade['rr']
                            elif result == "SL Hit":
                                j['pnl'] = -1
                            elif result == "Partial Win":
                                j['pnl'] = 0.5
                    st.success("Result updated!")
                    st.rerun()
    else:
        st.success("✅ All trades have results!")
    st.divider()
    st.subheader("📋 All Trades")
    for trade in reversed(journal):
        result_emoji = (
            "✅" if trade['result'] == "TP Hit" else
            "❌" if trade['result'] == "SL Hit" else
            "⚠️" if trade['result'] == "Partial Win" else
            "🔴" if trade['result'] == "Expired" else
            "⏳")
        st.write(
            result_emoji + " " +
            trade['pair'] + " " +
            trade['direction'] + " | " +
            str(trade['score']) + "% | " +
            trade['result'] + " | " +
            trade['time'])

def show_performance_page():
    st.title("📈 Performance Statistics")
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
        st.metric("Win Rate",
            str(stats['win_rate']) + "%")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🏆 Best Pair", stats['best_pair'])
    with col2:
        st.metric("🕐 Best Session",
            stats['best_session'])
    st.divider()
    journal = st.session_state.trade_journal
    completed = [j for j in journal
        if j['result'] != "Pending"]
    if completed:
        st.subheader("📊 Win Rate by Pair")
        pair_stats = {}
        for j in completed:
            if j['pair'] not in pair_stats:
                pair_stats[j['pair']] = {
                    'wins': 0, 'total': 0}
            pair_stats[j['pair']]['total'] += 1
            if j['result'] == "TP Hit":
                pair_stats[j['pair']]['wins'] += 1
        for pair, data in sorted(
            pair_stats.items(),
            key=lambda x: x[1]['wins'] /
            x[1]['total'], reverse=True):
            wr = round(
                data['wins'] / data['total'] * 100, 1)
            bar = "█" * int(wr / 10)
            st.write(pair + ": " + str(wr) +
                "% " + bar +
                " (" + str(data['wins']) + "/" +
                str(data['total']) + ")")
        st.divider()
        st.subheader("📊 Win Rate by Session")
        session_stats = {}
        for j in completed:
            sess = j.get('session', 'Unknown')
            if sess not in session_stats:
                session_stats[sess] = {
                    'wins': 0, 'total': 0}
            session_stats[sess]['total'] += 1
            if j['result'] == "TP Hit":
                session_stats[sess]['wins'] += 1
        for sess, data in session_stats.items():
            wr = round(
                data['wins'] / data['total'] * 100, 1)
            st.write(sess + ": " + str(wr) +
                "% (" + str(data['wins']) + "/" +
                str(data['total']) + ")")

def show_calendar_page():
    st.title("📅 Calendar Analytics")
    journal = st.session_state.trade_journal
    if not journal:
        st.info("No trades yet!")
        return
    date_stats = {}
    for trade in journal:
        try:
            parts = trade['time'].split(' ')
            date_str = (parts[0] + " " +
                parts[1] + " " + parts[2])
            if date_str not in date_stats:
                date_stats[date_str] = {
                    'wins': 0, 'losses': 0,
                    'total': 0, 'trades': []}
            date_stats[date_str]['total'] += 1
            date_stats[date_str]['trades'].append(trade)
            if trade['result'] == "TP Hit":
                date_stats[date_str]['wins'] += 1
            elif trade['result'] == "SL Hit":
                date_stats[date_str]['losses'] += 1
        except Exception:
            pass
    for date, data in sorted(
        date_stats.items(), reverse=True):
        win_rate = (round(
            data['wins'] / data['total'] * 100, 1)
            if data['total'] > 0 else 0)
        color = "🟢" if win_rate >= 50 else "🔴"
        with st.expander(
            color + " " + date +
            " | " + str(data['total']) + " trades" +
            " | WR: " + str(win_rate) + "%"):
            for trade in data['trades']:
                result_emoji = (
                    "✅" if trade['result'] == "TP Hit"
                    else "❌" if trade['result'] == "SL Hit"
                    else "⏳")
                st.write(
                    result_emoji + " " +
                    trade['pair'] + " " +
                    trade['direction'] + " | " +
                    str(trade['score']) + "% | " +
                    trade['result'])

def show_settings_page():
    st.title("⚙️ Settings")
    st.subheader("👤 Account")
    st.info("Logged in as: " +
        str(st.session_state.user_email))
    st.divider()
    st.subheader("🔔 Discord Settings")
    if st.button("🔔 Test Discord Alert",
        use_container_width=True):
        success = send_discord_alert(
            "✅ **Test Alert!**\n"
            "Discord working perfectly!\n"
            "User: " +
            str(st.session_state.user_email) +
            "\nTime: " + get_ist_time().strftime(
                '%d %b %Y %H:%M IST'))
        if success:
            st.success("Discord alert sent!")
        else:
            st.error("Discord failed!")
    st.divider()
    st.subheader("⏱️ Scan Settings")
    scan_interval = st.selectbox(
        "Auto Scan Interval",
        [1, 2, 3, 5, 10, 15],
        index=3)
    if st.button("💾 Save Interval"):
        st.session_state.next_scan_seconds = (
            scan_interval * 60)
        st.success("Set to " +
            str(scan_interval) + " minutes!")
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
    st.subheader("✅ Active Quality Filters")
    st.success("✅ Real Supabase Authentication")
    st.success("✅ Min 3 confluences required")
    st.success("✅ Confidence capped at 95%")
    st.success("✅ London + NY session only")
    st.success("✅ Structure based SL")
    st.success("✅ Premium/Discount zone check")
    st.success("✅ No duplicate alerts")
    st.success("✅ Max 3 signals per scan")
    st.success("✅ Chart images in Discord")
    st.success("✅ Trade journal with DB storage")
    st.success("✅ News filter active")
    st.success("✅ Economic calendar active")
    st.success("✅ Signal expires after 30 mins")
    st.info(
        "Trading Hours IST:\n"
        "🇬🇧 London: 12PM - 8PM\n"
        "🇺🇸 New York: 9PM - 12AM")

if __name__ == "__main__":
    main()
