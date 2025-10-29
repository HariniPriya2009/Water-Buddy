import streamlit as st
import pandas as pd
import altair as alt
import json
import os
from datetime import datetime, timedelta, date, time

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
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# ---------- FILE HANDLING ----------
DATA_FILE = "waterbuddy_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

def today_str():
    return date.today().isoformat()

data = load_data()

# ---------- INIT ----------
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "user" not in st.session_state:
    st.session_state.user = None

# ---------- NAVBAR ----------
def navbar():
    pages = ["Dashboard", "Log Water", "Challenges", "Badges", "Settings"]
    cols = st.columns(len(pages))
    for i, p in enumerate(pages):
        if st.session_state.page == p:
            cols[i].markdown(f"**➡️ {p}**")
        elif cols[i].button(p):
            st.session_state.page = p
            st.rerun()
    st.markdown("---")

# ---------- USER MANAGEMENT ----------
def ensure_user(name, password=None):
    if name not in data["users"]:
        data["users"][name] = {
            "profile": {"name": name, "password": password or "", "age_group": None},
            "history": {},
            "badges": [],
            "challenges": [],
            "settings": {
                "reminder_enabled": False,
                "reminder_minutes": 120,
                "reminder_start_time": "09:00"
            }
        }
    return data["users"][name]

# ---------- LOGIN ----------
if st.session_state.page == "Login":
    st.markdown("<h1 style='color:white;text-align:center;font-size:48px;'>Welcome to WaterBuddy!</h1>", unsafe_allow_html=True)
    st.subheader("💧 Hydrate Your Lifestyle with Smart Tracking")
    st.markdown("---")

    name = st.text_input("Enter your name:")
    password = st.text_input("Set a password:", type="password")
    age = st.radio("Select your age group:", ["<18", "18–30", "31–50", "50+"], horizontal=True)

    if st.button("Start 🚀"):
        if not name.strip() or not password.strip():
            st.warning("Please enter both name and password!")
        else:
            st.session_state.user = name.strip()
            user = ensure_user(st.session_state.user, password)
            user["profile"]["age_group"] = age
            save_data(data)
            st.session_state.page = "Dashboard"
            st.success(f"Welcome {name}! You're all set 🎉")
            st.rerun()

# ---------- DASHBOARD ----------
elif st.session_state.page == "Dashboard":
    navbar()
    user = ensure_user(st.session_state.user)
    st.header(f"📊 Dashboard — {user['profile']['name']}")

    # Past 7 days graph
    dates, totals = [], []
    for d in range(6, -1, -1):
        dd = date.today() - timedelta(days=d)
        dates.append(dd)
        totals.append(user["history"].get(dd.isoformat(), {}).get("total_ml", 0) / 1000)

    df = pd.DataFrame({"Date": dates, "Litres": totals})
    chart = alt.Chart(df).mark_bar(color="#00BFFF").encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Litres:Q", title="Water Intake (L)"),
        tooltip=["Date:T", "Litres:Q"]
    ).properties(title="Past 7 Days Water Intake")
    st.altair_chart(chart, use_container_width=True)

    today_total = user["history"].get(today_str(), {}).get("total_ml", 0)
    st.metric("Today's Intake", f"{today_total/1000:.2f} L")
    st.progress(min(1, today_total / 2000))

    # ---------- RESET TODAY’S PROGRESS ----------
    st.markdown("---")
    st.subheader("🔁 Reset Today's Progress")
    st.info("You can clear only today's water intake if you made a mistake or want to start fresh.")
    if st.button("Reset Today’s Progress"):
        today = today_str()
        if today in user["history"]:
            user["history"][today] = {"total_ml": 0, "entries": []}
            save_data(data)
            st.success("✅ Today's progress has been reset!")
            st.rerun()
        else:
            st.warning("No data found for today to reset.")

# ---------- LOG WATER ----------
elif st.session_state.page == "Log Water":
    navbar()
    user = ensure_user(st.session_state.user)
    st.header(" Log Water Intake")

    col1, col2, col3, col4 = st.columns(4)
    amount = None
    if col1.button("200 ml"): amount = 200
    if col2.button("250 ml"): amount = 250
    if col3.button("300 ml"): amount = 300
    if col4.button("500 ml"): amount = 500

    custom = st.number_input("Custom amount (ml):", 100, 1000, 250, 500)
    
    if st.button("Add Drink 💧"):
        amt = amount or custom
        ds = today_str()
        if ds not in user["history"]:
            user["history"][ds] = {"total_ml": 0, "entries": []}
        tnow = datetime.now().strftime("%H:%M:%S")
        user["history"][ds]["entries"].append({"time": tnow, "ml": int(amt)})
        user["history"][ds]["total_ml"] += int(amt)
        save_data(data)
        st.success(f"Added {amt} ml! 💧")
        st.rerun()

    today_total = user["history"].get(today_str(), {}).get("total_ml", 0)
    progress = today_total / 2000

    # Change mascot based on progress
    if progress < 0.2:
        mascot_path = r"image/hardrated 1.webp"
        message = "🌵 You're dehydrated! Start sipping!"
    elif progress < 0.5:
        mascot_path = r"image/happy-cute hydration 2.gif"
        message = "😊 Good start! Keep it up!"
    elif progress < 1.0:
        mascot_path = r"image/hydrated 3.webp"
        message = "💪 Almost there! You're doing great!"
    else:
        mascot_path = r"image/strong 4.webp"
        message = "🎉 Goal achieved! Excellent job!"

    st.markdown(f"### {message}")
    st.image(mascot_path, use_container_width=False)

    st.progress(min(progress, 1.0))
    st.write(f"**Today's Intake:** {today_total} ml / 2000 ml")

# ---------- CHALLENGES ----------
elif st.session_state.page == "Challenges":
    navbar()
    user = ensure_user(st.session_state.user)
    st.header("🏁 Challenges")

    # Cleanup old challenges without 'goal'
    for ch in user["challenges"]:
        if "goal" not in ch:
            ch["goal"] = 2.0
    save_data(data)

    ch_name = st.text_input("Challenge name:")
    days = st.slider("Duration (days)", 1, 30, 7)
    daily_goal = st.slider("Daily goal (litres)", 0.5, 5.0, 2.0, 0.25)
    if st.button("Create Challenge"):
        user["challenges"].append({
            "name": ch_name or f"{daily_goal}L × {days}d",
            "days": days,
            "goal": daily_goal,
            "start": today_str(),
            "done": False
        })
        save_data(data)
        st.success("Challenge created!")
        st.rerun()

    if user["challenges"]:
        st.subheader("Your Challenges")
        for ch in user["challenges"]:
            st.write(
                f"**{ch.get('name', 'Unnamed Challenge')}** — "
                f"{ch.get('days', '?')} days, "
                f"{ch.get('goal', '?')} L/day — "
                f"Started {ch.get('start', '?')}"
            )

# ---------- BADGES ----------
# ---------- BADGES + STREAKS (Styled) ----------
elif st.session_state.page == "Badges":
    navbar()
    data = load_data()
    users = data["users"]
    user = ensure_user(st.session_state.user)

    st.markdown("<h2 style='color:#FFD166;'>🏅 Your Badges & Streaks</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#F07167;'>🔥 Your Hydration Streaks</h3>", unsafe_allow_html=True)

    # --- streak calculation ---
    from datetime import datetime, timedelta
    today = datetime.now().date()

    if user["history"]:
        sorted_days = sorted(user["history"].keys())
        streak = 1
        longest_streak = 1
        prev_date = datetime.strptime(sorted_days[0], "%Y-%m-%d").date()

        for d in sorted_days[1:]:
            curr_date = datetime.strptime(d, "%Y-%m-%d").date()
            if (curr_date - prev_date).days == 1:
                streak += 1
                longest_streak = max(longest_streak, streak)
            else:
                streak = 1
            prev_date = curr_date

        last_date = datetime.strptime(sorted_days[-1], "%Y-%m-%d").date()
        if (today - last_date).days >= 2:
            streak = 0
    else:
        streak = 0
        longest_streak = 0

    # --- display streaks with white text ---
    st.markdown(f"""
        <div style='display:flex; justify-content:space-between; align-items:center; margin-top:10px;'>
            <div style='text-align:center;'>
                <p style='color:white; font-size:22px; font-weight:bold;'>Current Streak</p>
                <h1 style='color:white; font-size:42px; margin-top:-10px;'>💧 {streak} days</h1>
            </div>
            <div style='text-align:center;'>
                <p style='color:white; font-size:22px; font-weight:bold;'>Longest Streak</p>
                <h1 style='color:white; font-size:42px; margin-top:-10px;'>🏆 {longest_streak} days</h1>
            </div>
        </div>
    """, unsafe_allow_html=True)

    next_goal = 7 if streak < 7 else (30 if streak < 30 else 60)
    progress = min(streak / next_goal, 1.0)
    st.progress(progress)
    st.markdown(
        f"<p style='color:#ADE8F4;font-size:1.1rem;'>{streak}/{next_goal} days toward your next milestone!</p>",
        unsafe_allow_html=True
    )

    # --- motivational messages ---
    if streak == 0:
        st.markdown("<p style='color:#FFD6A5;font-size:1.1rem;'>💦 Let’s start your streak again today!</p>", unsafe_allow_html=True)
    elif streak < 7:
        st.markdown("<p style='color:#CAF0F8;font-size:1.1rem;'>Keep it up! You’re building your hydration habit 💧</p>", unsafe_allow_html=True)
    elif streak < 30:
        st.markdown("<p style='color:#BDE0FE;font-size:1.2rem;'>Amazing consistency! Stay hydrated like a pro 🥤</p>", unsafe_allow_html=True)
    else:
        st.balloons()
        st.markdown("<p style='color:#FFC8DD;font-size:1.3rem;font-weight:bold;'>You’re a hydration legend! 🌊👑</p>", unsafe_allow_html=True)

    # --- badges ---
    badges_earned = []
    total_drinks = sum(len(day.get("entries", [])) for day in user["history"].values())
    if total_drinks >= 1 and "💧 First Sip!" not in user["badges"]:
        user["badges"].append("💧 First Sip!")
        badges_earned.append("WOWW! You’ve got your first sip — great start!")

    if "start_date" not in user:
        user["start_date"] = sorted(user["history"].keys())[0] if user["history"] else today.strftime("%Y-%m-%d")

    try:
        start_date = datetime.strptime(user["start_date"], "%Y-%m-%d")
        days_since = (datetime.now() - start_date).days

        if days_since >= 7 and "🌈 Hydration Hero (1 Week)" not in user["badges"]:
            user["badges"].append("🌈 Hydration Hero (1 Week)")
            badges_earned.append("You've completed your first week — you’re a Hydration Hero! 💪")

        if days_since >= 30 and "🏆 Aqua Master (1 Month)" not in user["badges"]:
            user["badges"].append("🏆 Aqua Master (1 Month)")
            badges_earned.append("One month strong! You’ve earned the Aqua Master badge! 🌊")
    except Exception:
        pass

    if longest_streak >= 7 and "👑 Consistency King" not in user["badges"]:
        user["badges"].append("👑 Consistency King")
        badges_earned.append("You've logged water for 7 days in a row — you’re the Consistency King! 👑💧")

    for ch in user["challenges"]:
        if ch.get("done") and f"✅ Completed: {ch['name']}" not in user["badges"]:
            user["badges"].append(f"✅ Completed: {ch['name']}")
            badges_earned.append(f"Your challenge **{ch['name']}** was successfully completed! 🎉")

    # --- display badges ---
    st.markdown("<h3 style='color:#FFD166;'>🏆 Your Earned Badges</h3>", unsafe_allow_html=True)
    if not user["badges"]:
        st.info("No badges yet — keep hydrating to earn them!")
    else:
        for b in user["badges"]:
            st.markdown(f"<div class='badge-box'><span class='badge-title'>{b}</span></div>", unsafe_allow_html=True)

    if badges_earned:
        st.markdown("<h3 style='color:#FFF;'>🎉 New Achievements!</h3>", unsafe_allow_html=True)
        for msg in badges_earned:
            st.balloons()
            st.markdown(f"<div class='badge-box'><span class='badge-text'>{msg}</span></div>", unsafe_allow_html=True)

    users[st.session_state.user] = user
    save_data(data)

# ---------- SETTINGS PAGE ----------
elif st.session_state.page == "Settings":
    navbar()
    st.markdown("<h2 style='color:#FFD166;'>⚙️ Settings</h2>", unsafe_allow_html=True)

    user = ensure_user(st.session_state.user)

    # --- User Info Section ---
    st.subheader("👤 User Information")
    st.write(f"**Username:** {user['profile']['name']}")
    st.write(f"**Age Group:** {user['profile'].get('age_group', 'Not provided')}")
    st.write(f"**Daily Goal:** {user.get('goal', 2)} L")

    # Option to update daily goal
    new_goal = st.number_input(
        "Update your daily water goal (litres):",
        min_value=0.5,
        max_value=10.0,
        value=user.get("goal", 2.0),
        step=0.1
    )
    if st.button("💾 Update Goal"):
        user["goal"] = new_goal
        save_data(data)
        st.success("✅ Goal updated successfully!")

    st.markdown("---")

    # --- Reminder Settings ---
    st.subheader("🔔 Reminder Settings")
    rem_enabled = st.checkbox(
        "Enable in-app reminders (works while app is open)",
        value=user["settings"].get("reminder_enabled", False)
    )
    rem_minutes = st.number_input(
        "Reminder interval (minutes):",
        min_value=15, max_value=720,
        value=user["settings"].get("reminder_minutes", 120),
        step=15
    )
    rem_start = st.time_input(
        "Start reminders at:",
        value=time.fromisoformat(user["settings"].get("reminder_start_time", "09:00"))
    )

    if st.button("💾 Save Reminder Settings"):
        user["settings"]["reminder_enabled"] = rem_enabled
        user["settings"]["reminder_minutes"] = int(rem_minutes)
        user["settings"]["reminder_start_time"] = rem_start.strftime("%H:%M")
        save_data(data)
        st.success("Reminder settings saved!")

    st.markdown("---")

    # --- Logout Button ---
    st.subheader("🚪 Logout")
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "Login"
        st.success("Logged out successfully!")
        st.rerun()

    st.markdown("---")

    # --- Reset All Data ---
    st.subheader("🗑️ Reset All Data")
    st.warning("This will permanently delete all your logs, badges, and progress.")
    confirm = st.checkbox("I confirm I want to delete all my data.")
    if st.button("❌ Delete All Data"):
        if confirm:
            del data["users"][st.session_state.user]
            save_data(data)
            st.session_state.user = None
            st.session_state.page = "Login"
            st.success("All your data has been deleted.")
            st.rerun()
        else:
            st.warning("Please confirm before deleting your data.")

# ---------- SAVE ----------
save_data(data)
