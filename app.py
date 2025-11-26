import streamlit as st
import pandas as pd
import os
import random
import sqlite3
from datetime import datetime, timedelta, date, time
import matplotlib.pyplot as plt

# ---------- CONFIG ----------
st.set_page_config(page_title="WaterBuddy — SipSmart", page_icon="💧", layout="centered")

# ---------- STYLE ----------
page_bg = """
<style>
.stApp {
    background: linear-gradient(135deg, #89CFF0 0%, #4682B4 50%, #1E90FF 100%);
    color: white;
    font-family: 'Poppins', sans-serif;
}
h1, h2, h3, h4 {
    color: #ffffff !important;
    text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
}
div.stButton > button:first-child {
    background: linear-gradient(90deg, #1E90FF, #00BFFF);
    color: white;
    border-radius: 12px;
    border: none;
    padding: 0.6em 1.5em;
    font-weight: 600;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
}
div.stButton > button:first-child:hover {
    background: linear-gradient(90deg, #00BFFF, #1E90FF);
    transform: scale(1.05);
}
input, textarea, select {
    border-radius: 10px !important;
    border: 1px solid #87CEFA !important;
}
.stProgress > div > div > div > div {
    background-color: #00BFFF;
}
[data-testid="stMetricValue"] {
    color: #ffffff !important;
}
.water-bottle {
    width: 150px;
    height: 300px;
    border: 3px solid #ffffff;
    border-radius: 20px 20px 40px 40px;
    position: relative;
    background: linear-gradient(180deg, transparent 0%, #00BFFF 0%);
    margin: 20px auto;
    box-shadow: 0 8px 16px rgba(0,0,0,0.3);
}
.badge-box {
    background: linear-gradient(135deg, #FFD700, #FFA500);
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.comparison-box {
    background: rgba(255, 255, 255, 0.2);
    padding: 20px;
    border-radius: 15px;
    margin: 15px 0;
    backdrop-filter: blur(10px);
}
.log-entry {
    background: rgba(255, 255, 255, 0.1);
    padding: 10px 15px;
    margin: 5px 0;
    border-radius: 10px;
    border-left: 4px solid #00BFFF;
}
.reminder-popup {
    background: rgba(0,0,0,0.25);
    padding: 15px;
    border-radius: 10px;
    color: white;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# ---------- DATABASE (SQLite) ----------
DB_FILE = "waterbuddy.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

conn = get_conn()

def init_db():
    cur = conn.cursor()
    # users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        age INTEGER,
        weight REAL,
        daily_goal_ml INTEGER DEFAULT 2000,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # water logs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS water_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount_ml INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    # badges
    cur.execute("""
    CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, name),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    # challenges
    cur.execute("""
    CREATE TABLE IF NOT EXISTS challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT,
        days INTEGER,
        goal REAL,
        start TEXT,
        done INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    # settings
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        user_id INTEGER PRIMARY KEY,
        reminder_enabled INTEGER DEFAULT 0,
        reminder_minutes INTEGER DEFAULT 120,
        reminder_start_time TEXT DEFAULT '09:00',
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    conn.commit()

init_db()

# ---------- UTILITY ----------
def today_str():
    return date.today().isoformat()

# ---------- INIT SESSION STATE ----------
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "user" not in st.session_state:
    st.session_state.user = None  # username
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "age" not in st.session_state:
    st.session_state.age = 25
if "last_reminder_time" not in st.session_state:
    st.session_state.last_reminder_time = None
if "reminder_dismissed" not in st.session_state:
    st.session_state.reminder_dismissed = False

# ---------- AGE-BASED GOAL CALCULATOR ----------
def calculate_daily_goal(age, weight=None, activity_level="moderate"):
    if age < 4:
        return 1.3
    elif age < 9:
        return 1.7
    elif age < 14:
        return 2.4 if age >= 9 else 2.1
    elif age < 19:
        return 2.8
    elif age < 51:
        return 3.0
    elif age < 71:
        return 2.8
    else:
        return 2.5

# ---------- MOTIVATION & MASCOTS ----------
def get_motivational_message(percentage):
    if percentage <= 0:
        return "🌵 Time to start hydrating! Your body needs water!"
    elif percentage < 20:
        return "💧 Great first step! Keep the momentum going!"
    elif percentage < 40:
        return "😊 Good progress! You're building a healthy habit!"
    elif percentage < 60:
        return "💪 Halfway there! You're doing amazing!"
    elif percentage < 80:
        return "🌟 Excellent work! Almost at your goal!"
    elif percentage < 100:
        return "🔥 So close! Just a bit more to reach your target!"
    else:
        return "🎉 GOAL ACHIEVED! You're a hydration champion! 🏆"

def get_mascot_image(percentage):
    if percentage < 20:
        return "image/hardrated 1.webp"
    elif percentage < 50:
        return "image/happy-cute hydration 2.gif"
    elif percentage < 100:
        return "image/hydrated 3.webp"
    else:
        return "image/strong 4.webp"

reminder_messages = [
    "Take a small sip now — your future self will thank you!",
    "Hydration check! Drink some water and stretch your legs.",
    "A quick glass of water can boost your focus — try it now!"
]

FUN = [
    "💧 Drinking water boosts your brain power!",
    "🌊 Staying hydrated keeps your skin glowing and fresh!",
    "🚀 Small sips throughout the day keep your energy steady!",
    "🥤 Your body is nearly 60% water—keep it filled!",
    "⚡ Water helps your body maintain the perfect temperature!",
    "🔥 Even slight dehydration can reduce your focus!",
    "🧠 Your brain is 75% water — drink up for sharper thinking!",
    "💙 Drinking water improves your mood instantly!",
    "🏃‍♂️ Muscles work better when they are hydrated!",
    "👀 Water keeps your eyes from feeling dry and tired!",
    "💦 Drinking a glass of water in the morning boosts metabolism!",
    "🫀 Staying hydrated helps your heart pump blood smoothly!",
    "🌱 Plants need water to grow — and so do you!",
    "🎯 Hydration improves concentration and memory!",
    "🥗 Sometimes thirst feels like hunger — water helps fix it!",
    "💤 Drinking enough water improves your sleep quality!",
    "🌤️ Hot weather increases your water needs—sip often!",
    "🍋 Adding lemon to water boosts Vitamin C intake!",
    "📚 Hydrated students perform better in studies!",
    "🙂 Drinking water reduces stress and anxiety levels!"
]

# ---------- DATABASE HELPERS ----------
def create_user(username, password, age=None, weight=None, daily_goal_ml=2000):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, age, weight, daily_goal_ml) VALUES (?, ?, ?, ?, ?)",
            (username, password, age, weight, daily_goal_ml)
        )
        conn.commit()
        user_id = cur.lastrowid
        # ensure default settings row
        cur.execute("INSERT OR IGNORE INTO settings (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None

def get_user_by_username(username):
    cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    return row

def update_user_profile(user_id, age=None, weight=None, daily_goal_ml=None):
    cur = conn.cursor()
    if age is not None:
        cur.execute("UPDATE users SET age = ? WHERE id = ?", (age, user_id))
    if weight is not None:
        cur.execute("UPDATE users SET weight = ? WHERE id = ?", (weight, user_id))
    if daily_goal_ml is not None:
        cur.execute("UPDATE users SET daily_goal_ml = ? WHERE id = ?", (daily_goal_ml, user_id))
    conn.commit()

def check_login(username, password):
    cur = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return cur.fetchone()

def log_water(user_id, amount_ml, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO water_logs (user_id, amount_ml, timestamp) VALUES (?, ?, ?)",
        (user_id, int(amount_ml), timestamp)
    )
    conn.commit()
    # after logging, try awarding badges if needed
    award_badges_for_user(user_id)

def get_logs_for_date(user_id, date_iso):
    start = f"{date_iso} 00:00:00"
    end = f"{date_iso} 23:59:59"
    cur = conn.execute(
        "SELECT amount_ml, timestamp FROM water_logs WHERE user_id = ? AND timestamp BETWEEN ? AND ? ORDER BY timestamp DESC",
        (user_id, start, end)
    )
    rows = cur.fetchall()
    return rows

def get_today_total(user_id):
    today = today_str()
    cur = conn.execute(
        "SELECT SUM(amount_ml) as total FROM water_logs WHERE user_id = ? AND timestamp LIKE ?",
        (user_id, f"{today}%")
    )
    r = cur.fetchone()
    return r["total"] or 0

def get_7day_history(user_id):
    history = {}
    for d in range(6, -1, -1):
        dd = date.today() - timedelta(days=d)
        iso = dd.isoformat()
        cur = conn.execute(
            "SELECT SUM(amount_ml) as total FROM water_logs WHERE user_id = ? AND timestamp LIKE ?",
            (user_id, f"{iso}%")
        )
        r = cur.fetchone()
        history[iso] = {"total_ml": int(r["total"] or 0), "entries": [dict(row) for row in get_logs_for_date(user_id, iso)]}
    return history

def clear_today_logs(user_id):
    ds = today_str()
    conn.execute("DELETE FROM water_logs WHERE user_id = ? AND timestamp LIKE ?", (user_id, f"{ds}%"))
    conn.commit()

# badges and awarding
def get_badges(user_id):
    cur = conn.execute("SELECT name, earned_at FROM badges WHERE user_id = ?", (user_id,))
    return [dict(r) for r in cur.fetchall()]

def award_badge(user_id, badge_name):
    try:
        conn.execute("INSERT INTO badges (user_id, name) VALUES (?, ?)", (user_id, badge_name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def award_badges_for_user(user_id):
    # Simple badge logic similar to your JSON version
    # First Sip
    total_drinks = conn.execute("SELECT COUNT(*) as c FROM water_logs WHERE user_id = ?", (user_id,)).fetchone()["c"]
    if total_drinks >= 1:
        award_badge(user_id, "💧 First Sip!")
    # compute streaks for badges
    streaks = compute_streaks(user_id)
    current_streak = streaks["current_streak"]
    longest_streak = streaks["longest_streak"]
    if current_streak >= 3:
        award_badge(user_id, "🌱 3-Day Streak")
    if current_streak >= 7:
        award_badge(user_id, "🌈 Hydration Hero (1 Week)")
    if current_streak >= 30:
        award_badge(user_id, "🏆 Aqua Master (1 Month)")
    if longest_streak >= 7:
        award_badge(user_id, "👑 Consistency King")

# challenges
def add_challenge(user_id, name, days, goal, start_iso):
    conn.execute(
        "INSERT INTO challenges (user_id, name, days, goal, start) VALUES (?, ?, ?, ?, ?)",
        (user_id, name, days, goal, start_iso)
    )
    conn.commit()

def get_challenges(user_id):
    cur = conn.execute("SELECT * FROM challenges WHERE user_id = ?", (user_id,))
    return [dict(r) for r in cur.fetchall()]

def mark_challenge_done(challenge_id):
    conn.execute("UPDATE challenges SET done = 1 WHERE id = ?", (challenge_id,))
    conn.commit()

# settings
def get_settings(user_id):
    cur = conn.execute("SELECT reminder_enabled, reminder_minutes, reminder_start_time FROM settings WHERE user_id = ?", (user_id,))
    r = cur.fetchone()
    if not r:
        # initialize
        conn.execute("INSERT OR IGNORE INTO settings (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return {"reminder_enabled": False, "reminder_minutes": 120, "reminder_start_time": "09:00"}
    return {"reminder_enabled": bool(r["reminder_enabled"]), "reminder_minutes": r["reminder_minutes"], "reminder_start_time": r["reminder_start_time"]}

def update_settings(user_id, reminder_enabled, reminder_minutes, reminder_start_time):
    conn.execute("INSERT OR REPLACE INTO settings (user_id, reminder_enabled, reminder_minutes, reminder_start_time) VALUES (?, ?, ?, ?)",
                 (user_id, int(reminder_enabled), int(reminder_minutes), reminder_start_time))
    conn.commit()

# deletion
def delete_all_user_data(user_id):
    conn.execute("DELETE FROM water_logs WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM badges WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM challenges WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM settings WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()

# streaks computation
def compute_streaks(user_id):
    # gather all dates with logs
    cur = conn.execute("SELECT DISTINCT DATE(timestamp) as dt FROM water_logs WHERE user_id = ? ORDER BY dt ASC", (user_id,))
    rows = [r["dt"] for r in cur.fetchall()]
    date_objs = [datetime.strptime(d, "%Y-%m-%d").date() for d in rows] if rows else []
    today_date = datetime.now().date()
    if not date_objs:
        return {"current_streak": 0, "longest_streak": 0}
    # longest streak
    longest = 1
    streak = 1
    prev = date_objs[0]
    for d in date_objs[1:]:
        if (d - prev).days == 1:
            streak += 1
        else:
            streak = 1
        prev = d
        if streak > longest:
            longest = streak
    longest_streak = longest
    # current streak
    last = date_objs[-1]
    if (today_date - last).days == 0:
        current = 1
        prev = last
        for d in reversed(date_objs[:-1]):
            if (prev - d).days == 1:
                current += 1
                prev = d
            else:
                break
        current_streak = current
    elif (today_date - last).days == 1:
        current = 1
        prev = last
        for d in reversed(date_objs[:-1]):
            if (prev - d).days == 1:
                current += 1
                prev = d
            else:
                break
        current_streak = current
    else:
        current_streak = 0
    return {"current_streak": current_streak, "longest_streak": longest_streak}

# ---------- PLOTTING ----------
def plot_7day_intake_from_history_dict(history, daily_goal_ml):
    # history: dict keyed by iso date with total_ml
    dates = []
    actual_intake = []
    target_intake = []
    date_labels = []
    for d_iso, v in history.items():
        dd = datetime.strptime(d_iso, "%Y-%m-%d").date()
        dates.append(dd)
        actual_ml = v.get("total_ml", 0)
        actual_intake.append(actual_ml / 1000)
        target_intake.append(daily_goal_ml / 1000)
        date_labels.append(dd.strftime("%m/%d"))
    fig, ax = plt.subplots(figsize=(10, 4))
    x = range(len(dates))
    width = 0.35
    bars1 = ax.bar([i - width/2 for i in x], actual_intake, width, label='Actual Intake')
    bars2 = ax.bar([i + width/2 for i in x], target_intake, width, label='Daily Target', alpha=0.6)
    ax.set_xlabel('Date', fontsize=10)
    ax.set_ylabel('Litres', fontsize=10)
    ax.set_title('Your Intake vs Daily Target (Past 7 Days)', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(date_labels, fontsize=9)
    ax.legend()
    ax.grid(True, alpha=0.2)
    for bars in (bars1, bars2):
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:.1f}L', ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    return fig

# ---------- NAVBAR ----------
def navbar():
    pages = ["Dashboard", "Log Water", "Challenges", "Badges", "Settings"]
    cols = st.columns(len(pages))
    for i, p in enumerate(pages):
        if st.session_state.page == p:
            cols[i].markdown(f"**➡️ {p}**")
        elif cols[i].button(p, key=f"nav_{p}"):
            st.session_state.page = p
            st.rerun()
    st.markdown("---")

# ---------- LOGIN / SIGN UP ----------
if st.session_state.page == "Login":
    st.markdown("<h1 style='color:white;text-align:center;font-size:48px;'>💧 Welcome to WaterBuddy!</h1>", unsafe_allow_html=True)
    st.subheader("🌊 Hydrate Your Lifestyle with Smart Tracking")
    st.markdown("---")

    mode = st.radio("Select mode:", ["Login", "Sign Up"], horizontal=True)
    name = st.text_input("Username:")
    password = st.text_input("Password:", type="password")

    if mode == "Sign Up":
        st.markdown("### 🎂 Tell us about yourself")
        st.write("**Select your age:**")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("➖", key="minus_age") and st.session_state.age > 1:
                st.session_state.age -= 1
                st.rerun()
        with col2:
            typed_age = st.number_input(
                "or type age:",
                min_value=1,
                max_value=120,
                value=st.session_state.age,
                key="typed_age_input"
            )
            if typed_age != st.session_state.age:
                st.session_state.age = int(typed_age)
            st.markdown(
                f"<h2 style='text-align:center;color:white;'>{st.session_state.age} years old</h2>",
                unsafe_allow_html=True
            )
        with col3:
            if st.button("➕", key="plus_age") and st.session_state.age < 120:
                st.session_state.age += 1
                st.rerun()

        recommended_goal = calculate_daily_goal(st.session_state.age)
        st.info(f"💡 **Recommended daily water intake for your age:** {recommended_goal:.1f} litres")

        custom_goal = st.slider(
            "Daily water goal (litres):",
            min_value=0.5,
            max_value=5.0,
            value=float(recommended_goal),
            step=0.1,
            key="goal_slider"
        )
        st.success(f"✅ Your daily goal is set to: **{custom_goal:.1f} litres** ({int(custom_goal * 1000)} ml)")

        if st.button("Create Account 🚀", key="signup_btn"):
            if not name or not name.strip():
                st.warning("⚠️ Please enter a username!")
            elif not password:
                st.warning("⚠️ Please enter a password!")
            else:
                username = name.strip()
                created = create_user(username, password, st.session_state.age, None, int(custom_goal * 1000))
                if created:
                    st.session_state.user = username
                    st.session_state.user_id = created
                    st.success(f"🎉 Welcome {username}! Your account has been created!")
                    st.balloons()
                    st.session_state.page = "Dashboard"
                    st.rerun()
                else:
                    st.error("❌ Username already exists! Try logging in instead.")
    else:
        # LOGIN flow
        if st.button("Login 🔑", key="login_btn"):
            if not name or not name.strip():
                st.warning("⚠️ Please enter your username!")
            elif not password:
                st.warning("⚠️ Please enter your password!")
            else:
                username = name.strip()
                user = check_login(username, password)
                if user:
                    st.session_state.user = username
                    st.session_state.user_id = user["id"]
                    st.success(f"✅ Welcome back, {username}! 💧")
                    st.session_state.page = "Dashboard"
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

# ---------- DASHBOARD ----------
elif st.session_state.page == "Dashboard":
    navbar()
    uname = st.session_state.user
    uid = st.session_state.user_id
    if not uname or not uid:
        st.error("User not found — login again.")
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.page = "Login"
        st.rerun()

    user_row = get_user_by_username(uname)
    profile = {
        "name": user_row["username"],
        "age": user_row["age"],
        "weight": user_row["weight"]
    }
    daily_goal = user_row["daily_goal_ml"] or 2000
    today_total = get_today_total(uid)
    progress_percentage = (today_total / daily_goal) * 100 if daily_goal else 0

    st.header(f"📊 Dashboard — {profile.get('name', uname)}")
    st.markdown("### 💡 Hydration Tip of the Day")
    st.markdown(f"<span style='color:#000000;'>{random.choice(FUN)}</span>", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(f"### {get_motivational_message(progress_percentage)}")

    bottle_fill_percentage = min(progress_percentage, 100)
    st.markdown(f"""
        <div style="text-align:center;">
            <div style="width:150px;height:300px;border:4px solid #fff;border-radius:20px 20px 40px 40px;margin:20px auto;
                        background: linear-gradient(to top, #00BFFF {bottle_fill_percentage}%, transparent {bottle_fill_percentage}%);">
                <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
                            font-size:24px;font-weight:bold;color:{'#fff' if bottle_fill_percentage>50 else '#000'};">
                    {progress_percentage:.0f}%
                </div>
            </div>
            <p style="color:white;font-size:18px;font-weight:bold;">{today_total} ml / {daily_goal} ml</p>
        </div>
    """, unsafe_allow_html=True)

    st.progress(min(progress_percentage/100, 1.0))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Intake", f"{today_total/1000:.2f} L", delta=f"{(today_total - daily_goal)/1000:.2f} L")
    with col2:
        st.metric("Daily Target", f"{daily_goal/1000:.2f} L")
    with col3:
        st.metric("Remaining", f"{max(0, daily_goal - today_total)/1000:.2f} L")

    st.markdown("---")
    st.markdown("### 📈 Your 7-Day Hydration History")
    history = get_7day_history(uid)
    fig = plot_7day_intake_from_history_dict(history, daily_goal)
    st.pyplot(fig)
    plt.close()

    st.markdown("---")
    st.subheader("🔄 Reset Today's Progress")
    if st.button("🗑️ Reset Today"):
        clear_today_logs(uid)
        st.success("Today's data cleared.")
        st.rerun()

# ---------- LOG WATER ----------
elif st.session_state.page == "Log Water":
    navbar()
    uname = st.session_state.user
    uid = st.session_state.user_id
    if not uname or not uid:
        st.error("❌ User data not found. Please log in again.")
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.page = "Login"
        st.rerun()

    st.header("💧 Log Water Intake")
    today_total = get_today_total(uid)
    user_row = get_user_by_username(uname)
    daily_goal = user_row["daily_goal_ml"] or 2000
    progress_percentage = (today_total / daily_goal) * 100 if daily_goal else 0

    st.markdown("### ⚡ Quick Log (Tap to Add)")
    quick_amounts = [100, 200, 250, 330, 500]
    col1, col2, col3, col4, col5 = st.columns(5)
    amount = None
    if col1.button(f"💧 {quick_amounts[0]} ml", key="q1"): amount = quick_amounts[0]
    if col2.button(f"💧 {quick_amounts[1]} ml", key="q2"): amount = quick_amounts[1]
    if col3.button(f"💧 {quick_amounts[2]} ml", key="q3"): amount = quick_amounts[2]
    if col4.button(f"💧 {quick_amounts[3]} ml", key="q4"): amount = quick_amounts[3]
    if col5.button(f"💧 {quick_amounts[4]} ml", key="q5"): amount = quick_amounts[4]

    st.markdown("### 🎯 Custom Amount")
    custom = st.number_input("Enter custom amount (ml):", min_value=50, max_value=2000, value=250, step=50, key="custom_input")
    if st.button("➕ Add Custom Amount", key="add_custom"):
        amount = custom

    if amount:
        now = datetime.now()
        time_24hr = now.strftime("%H:%M:%S")
        time_12hr = now.strftime("%I:%M %p")
        log_water(uid, amount)
        st.success(f"✅ Added {amount} ml at {time_12hr}!")
        st.balloons()
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Today's Progress")
    mascot_path = get_mascot_image(progress_percentage)
    motivational_msg = get_motivational_message(progress_percentage)
    col_mascot, col_progress = st.columns([1, 2])
    with col_mascot:
        if os.path.exists(mascot_path):
            st.image(mascot_path, width=200)
        st.markdown(f"**{motivational_msg}**")
    with col_progress:
        bottle_fill = min(progress_percentage, 100)
        st.markdown(f"""
            <div style="text-align: center;">
                <div style="
                    width: 120px;
                    height: 240px;
                    border: 3px solid #ffffff;
                    border-radius: 15px 15px 30px 30px;
                    position: relative;
                    margin: 10px auto;
                    box-shadow: 0 6px 12px rgba(0,0,0,0.3);
                    background: linear-gradient(to top, #00BFFF {bottle_fill}%, transparent {bottle_fill}%);
                ">
                    <div style="
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        font-size: 20px;
                        font-weight: bold;
                        color: {'#ffffff' if bottle_fill > 50 else '#000000'};
                    ">
                        {progress_percentage:.0f}%
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.progress(min(progress_percentage / 100, 1.0))
        st.markdown(f"<h3 style='text-align:center;'>{today_total} ml / {daily_goal} ml</h3>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📝 Today's Log History")
    todays_entries = [dict(r) for r in get_logs_for_date(uid, today_str())]
    if todays_entries:
        for entry in todays_entries[:10]:
            ts = entry.get("timestamp")
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            display_time = dt.strftime("%I:%M %p")
            st.markdown(f"""
                <div class='log-entry'>
                    🕒 <strong>{display_time}</strong> — <strong>{entry.get('amount_ml', 0)} ml</strong>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No water logged yet today. Start now!")

# ---------- CHALLENGES ----------
elif st.session_state.page == "Challenges":
    navbar()
    uid = st.session_state.user_id
    if not uid:
        st.error("❌ User data not found. Please log in again.")
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.page = "Login"
        st.rerun()

    st.header("🏁 Hydration Challenges")
    st.markdown("### 🎯 Create a New Challenge")
    ch_name = st.text_input("Challenge name:", placeholder="e.g., Weekend Warrior, Week of Wellness", key="ch_name")
    days = st.slider("Duration (days)", 1, 30, 7, key="ch_days")
    daily_goal = st.slider("Daily goal (litres)", 0.5, 5.0, 2.0, 0.25, key="ch_goal")
    if st.button("🚀 Create Challenge", key="create_ch"):
        if not ch_name.strip():
            ch_name = f"{daily_goal}L for {days} days"
        add_challenge(uid, ch_name, days, daily_goal, today_str())
        st.success(f"✅ Challenge '{ch_name}' created!")
        st.balloons()
        st.rerun()

    st.markdown("---")
    challenges = get_challenges(uid)
    if challenges:
        st.subheader("🎮 Your Active Challenges")
        for ch in challenges:
            status = "✅ Completed" if ch.get("done") else "🔥 In Progress"
            with st.expander(f"{status} — {ch.get('name', 'Unnamed Challenge')}"):
                st.write(f"**Duration:** {ch.get('days', '?')} days")
                st.write(f"**Daily Goal:** {ch.get('goal', '?')} L")
                st.write(f"**Started:** {ch.get('start', '?')}")
                if not ch.get("done", False):
                    if st.button(f"Mark as Complete", key=f"complete_{ch['id']}"):
                        mark_challenge_done(ch['id'])
                        award_badge(uid, f"✅ Completed: {ch['name']}")
                        st.success("🎉 Challenge completed!")
                        st.rerun()
    else:
        st.info("💡 No challenges yet. Create one to stay motivated!")

# ---------- BADGES ----------
elif st.session_state.page == "Badges":
    navbar()
    uid = st.session_state.user_id
    if not uid:
        st.error("❌ User data not found. Please log in again.")
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.page = "Login"
        st.rerun()

    st.markdown("<h2 style='color:#FFD166;'>🏅 Your Badges & Achievements</h2>", unsafe_allow_html=True)

    streaks = compute_streaks(uid)
    current_streak = streaks["current_streak"]
    longest_streak = streaks["longest_streak"]

    st.markdown("### 🔥 Your Hydration Streaks")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Streak", f"{current_streak} days", delta="🔥")
    with col2:
        st.metric("Longest Streak", f"{longest_streak} days", delta="🏆")
        next_goal = 7 if current_streak < 7 else (30 if current_streak < 30 else 60)
        progress = min(current_streak / next_goal, 1.0) if next_goal else 0
        st.progress(progress)
        st.caption(f"{current_streak}/{next_goal} days toward your next milestone!")

    st.markdown("---")
    badges = get_badges(uid)
    if not badges:
        st.info("🎯 No badges yet — keep hydrating to unlock achievements!")
    else:
        badge_cols = st.columns(3)
        for idx, b in enumerate(badges):
            with badge_cols[idx % 3]:
                st.markdown(f"""
<div class='badge-box'>
<p style='text-align:center; font-size:18px; margin:0; color:#fff;'>{b['name']}</p>
</div>
""", unsafe_allow_html=True)

# ---------- SETTINGS ----------
elif st.session_state.page == "Settings":
    navbar()
    uid = st.session_state.user_id
    if not uid:
        st.error("❌ User data not found. Please log in again.")
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.page = "Login"
        st.rerun()

    st.markdown("<h2 style='color:#FFD166;'>⚙️ Settings</h2>", unsafe_allow_html=True)
    user_row = get_user_by_username(st.session_state.user)
    profile = {"name": user_row["username"], "age": user_row["age"], "weight": user_row["weight"]}

    st.subheader("👤 User Information")
    st.markdown(f"**Username:** {profile.get('name', st.session_state.user)}")
    st.markdown(f"**Age:** {profile.get('age', 'Not provided')} years")
    st.markdown(f"**Daily Goal:** {user_row['daily_goal_ml']/1000:.1f} L")
    st.markdown("---")

    st.subheader("🎯 Update Daily Goal")
    new_goal = st.number_input(
        "Update your daily water goal (litres):",
        min_value=0.5,
        max_value=10.0,
        value=user_row['daily_goal_ml']/1000,
        step=0.1
    )
    if st.button("💾 Update Goal"):
        update_user_profile(uid, daily_goal_ml=int(new_goal * 1000))
        st.success(f"✅ Goal updated successfully to {new_goal:.1f} L!")
        st.rerun()

    st.markdown("---")
    st.subheader("🔔 Reminder Settings")
    st.info("💡 Enable reminders to get periodic notifications to drink water throughout the day!")

    settings = get_settings(uid)
    rem_enabled = st.checkbox(
        "Enable in-app reminders",
        value=settings.get("reminder_enabled", False),
        help="Show reminder popups to drink water"
    )
    rem_minutes = st.number_input(
        "Reminder interval (minutes):",
        min_value=15,
        max_value=720,
        value=settings.get("reminder_minutes", 120),
        step=15,
        help="How often you want to be reminded"
    )
    rem_start = st.time_input(
        "Start reminders at:",
        value=time.fromisoformat(settings.get("reminder_start_time", "09:00")),
        help="Reminders will start at this time and end at 10 PM"
    )

    st.info(f"⏰ You will receive reminders every {rem_minutes} minutes between {rem_start.strftime('%I:%M %p')} and 10:00 PM")

    if st.button("💾 Save Reminder Settings"):
        update_settings(uid, rem_enabled, rem_minutes, rem_start.strftime("%H:%M"))
        st.session_state.last_reminder_time = None
        st.session_state.reminder_dismissed = False
        st.success("✅ Reminder settings saved!")
        st.rerun()

    st.markdown("---")
    if settings.get("reminder_enabled", False):
        st.subheader("🧪 Test Reminder")
        st.write("Click the button below to see how a reminder looks:")
        if st.button("👀 Show Test Reminder"):
            st.markdown(f"""
            <div class='reminder-popup'>
            <h3 style='margin:0 0 10px 0; color: white;'>🔔 Hydration Reminder (TEST)</h3>
            <p style='margin:0; font-size: 16px;'>{random.choice(reminder_messages)}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🚪 Logout")
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.page = "Login"
        st.session_state.last_reminder_time = None
        st.session_state.reminder_dismissed = False
        st.success("✅ Logged out successfully!")
        st.rerun()

    st.markdown("---")
    st.subheader("🗑️ Reset All Data")
    st.warning("⚠️ This will permanently delete all your logs, badges, challenges, and progress. This action cannot be undone!")
    RC = st.checkbox("I confirm I want to delete all my data.", key="confirm_delete")
    if st.button("❌ Delete All Data"):
        if RC:
            delete_all_user_data(uid)
            st.session_state.user = None
            st.session_state.user_id = None
            st.session_state.page = "Login"
            st.session_state.last_reminder_time = None
            st.session_state.reminder_dismissed = False
            st.success("✅ All your data has been deleted.")
            st.rerun()
        else:
            st.warning("⚠️ Please confirm before deleting your data.")

