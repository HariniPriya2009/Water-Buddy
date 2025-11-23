import streamlit as st
import pandas as pd
import json
import os
import random
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

# ---------- FILE HANDLING ----------
DATA_FILE = "waterbuddy_data.json"

def load_data():
    """Load data from JSON file with error handling."""
    try:
        if not os.path.exists(DATA_FILE):
            return {"users": {}}
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "users" not in data:
            return {"users": {}}
        return data
    except json.JSONDecodeError:
        st.warning("⚠️ Data file corrupted. A fresh file will be created.")
        return {"users": {}}
    except Exception as e:
        st.error(f"⚠️ Error loading data: {e}")
        return {"users": {}}

def save_data(data):
    """Save data to JSON file with error handling"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"⚠️ Error saving data: {e}")
        return False

def today_str():
    return date.today().isoformat()

# ---------- INIT SESSION STATE ----------
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "user" not in st.session_state:
    st.session_state.user = None
if "age" not in st.session_state:
    st.session_state.age = 25
if "last_reminder_time" not in st.session_state:
    st.session_state.last_reminder_time = None
if "reminder_dismissed" not in st.session_state:
    st.session_state.reminder_dismissed = False

# ---------- AGE-BASED GOAL CALCULATOR ----------
def calculate_daily_goal(age, weight=None, activity_level="moderate"):
    """Return recommended litres/day (float)"""
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
    """Return mascot image path (if present). Fallback gracefully if not found."""
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

fun_facts = [
    "💧 Drinking water can boost your mood and energy levels instantly!",
    "🌿 Your brain is around 75% water — stay hydrated to stay sharp!",
    "🚰 You lose about 1 litre of water every day just by breathing and sweating.",
    "🧊 Cold water can slightly increase your metabolism as your body warms it up!",
    "💦 Drinking enough water can improve your skin's glow naturally.",
    "🥤 Sometimes thirst feels like hunger — drinking water first can prevent overeating.",
    "🏃‍♀️ Proper hydration helps your muscles work more efficiently during workouts.",
    "🕐 Even mild dehydration (1-2%) can reduce your focus and concentration levels.",
    "🌊 Water helps regulate body temperature and flush out toxins.",
    "🍉 Hydrating foods like watermelon, cucumber, and oranges help boost your intake!"
]

# ---------- MATPLOTLIB GRAPH ----------
def plot_7day_intake(user):
    daily_goal = user.get("daily_goal_ml", 2000)
    dates = []
    actual_intake = []
    target_intake = []
    date_labels = []
    for d in range(6, -1, -1):
        dd = date.today() - timedelta(days=d)
        dates.append(dd)
        day_data = user.get("history", {}).get(dd.isoformat(), {})
        actual_ml = day_data.get("total_ml", 0)
        actual_intake.append(actual_ml / 1000)
        target_intake.append(daily_goal / 1000)
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

# ---------- USER MANAGEMENT ----------
def get_user_data(username):
    data = load_data()
    if not username:
        return None
    return data.get("users", {}).get(username)

def update_user_data(username, user_data):
    data = load_data()
    if "users" not in data:
        data["users"] = {}
    data["users"][username] = user_data
    return save_data(data)

def ensure_user(name, password=""):
    name = name.strip()
    data = load_data()
    if "users" not in data:
        data["users"] = {}
    if name not in data["users"]:
        data["users"][name] = {
            "profile": {
                "name": name,
                "password": password,
                "age": None,
                "weight": None
            },
            "history": {},
            "badges": [],
            "challenges": [],
            "daily_goal_ml": 2000,
            "settings": {
                "reminder_enabled": False,
                "reminder_minutes": 120,
                "reminder_start_time": "09:00"
            }
        }
        save_data(data)
    return data["users"][name]

def verify_user(username, password):
    username = username.strip()
    data = load_data()
    if username not in data.get("users", {}):
        return False, "User not found"
    user = data["users"][username]
    stored_password = user.get("profile", {}).get("password", "")
    if stored_password == password:
        return True, "Success"
    else:
        return False, "Incorrect password"

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
    # Manual age input
    typed_age = st.number_input(
        "or type age:",
        min_value=1,
        max_value=120,
        value=st.session_state.age,
        key="typed_age_input"
    )

    # Sync typed age with session_state
    if typed_age != st.session_state.age:
        st.session_state.age = typed_age

    # Display final age
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
                data = load_data()
                username = name.strip()
                if username in data.get("users", {}):
                    st.error("❌ Username already exists! Try logging in instead.")
                else:
                    new_user = {
                        "profile": {
                            "name": username,
                            "password": password,
                            "age": st.session_state.age,
                            "weight": None
                        },
                        "history": {},
                        "badges": [],
                        "challenges": [],
                        "daily_goal_ml": int(custom_goal * 1000),
                        "settings": {
                            "reminder_enabled": False,
                            "reminder_minutes": 120,
                            "reminder_start_time": "09:00"
                        }
                    }
                    data.setdefault("users", {})[username] = new_user
                    if save_data(data):
                        st.session_state.user = username
                        st.success(f"🎉 Welcome {username}! Your account has been created!")
                        st.balloons()
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    else:
                        st.error("❌ Failed to save account. Please try again.")
    else:
        if st.button("Login 🔑", key="login_btn"):
            if not name or not name.strip():
                st.warning("⚠️ Please enter your username!")
            elif not password:
                st.warning("⚠️ Please enter your password!")
            else:
                username = name.strip()
                ok, msg = verify_user(username, password)
                if ok:
                    st.session_state.user = username
                    st.success(f"✅ Welcome back, {username}! 💧")
                    st.session_state.page = "Dashboard"
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

# ---------- DASHBOARD ----------
elif st.session_state.page == "Dashboard":
    navbar()
    uname = st.session_state.user
    user = get_user(uname)
    if not user:
        st.error("User not found — login again.")
        st.session_state.user = None
        st.session_state.page = "Login"
        st.rerun()

    profile = user.get("profile", {})
    daily_goal = user.get("daily_goal_ml", 2000)
    today_total = get_daily_total(uname)
    progress_percentage = (today_total / daily_goal) * 100 if daily_goal else 0

    st.header(f"📊 Dashboard — {profile.get('name', uname)}")
    st.markdown("### 💡 Hydration Tip of the Day")
    FUN = [
        "💧 Drinking water can boost your mood and energy levels instantly!",
        "🌿 Your brain is around 75% water — stay hydrated to stay sharp!",
        "🚰 You lose about 1 litre of water every day just by breathing and sweating."
    ]
    st.info(random.choice(FUN))
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
    history = get_7day_history(uname)
    fig = plot_7day_intake_from_history(history, daily_goal)
    st.pyplot(fig)
    plt.close()

    st.markdown("---")
    st.subheader("🔄 Reset Today's Progress")
    if st.button("🗑️ Reset Today"):
        # delete today's logs
        today_str = date.today().isoformat()
        docs = user_doc_ref(uname).collection(LOGS_COL).where("date", "==", today_str).stream()
        deleted = 0
        for d in docs:
            d.reference.delete()
            deleted += 1
        # remove date from history_dates index
        ref = user_doc_ref(uname)
        doc = ref.get().to_dict()
        dates = set(doc.get("history_dates", []))
        if today_str in dates:
            dates.remove(today_str)
            ref.update({"history_dates": list(dates)})
        st.success("Today's data cleared.")
        st.rerun()

# ---------- LOG WATER ----------
elif st.session_state.page == "Log Water":
    navbar()
    user = get_user_data(st.session_state.user)
    if not user:
        st.error("❌ User data not found. Please log in again.")
        st.session_state.user = None
        st.session_state.page = "Login"
        st.rerun()

    st.header("💧 Log Water Intake")
    today_total = user.get("history", {}).get(today_str(), {}).get("total_ml", 0)
    daily_goal = user.get("daily_goal_ml", 2000)
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
        ds = today_str()
        if ds not in user.get("history", {}):
            user.setdefault("history", {})[ds] = {"total_ml": 0, "entries": []}
        now = datetime.now()
        time_24hr = now.strftime("%H:%M:%S")
        time_12hr = now.strftime("%I:%M %p")
        entry = {
            "time": time_24hr,
            "time_display": time_12hr,
            "ml": int(amount),
            "timestamp": now.isoformat()
        }
        user["history"].setdefault(ds, {"total_ml": 0, "entries": []})
        user["history"][ds]["entries"].append(entry)
        user["history"][ds]["total_ml"] = user["history"][ds].get("total_ml", 0) + int(amount)
        if update_user_data(st.session_state.user, user):
            st.success(f"✅ Added {amount} ml at {time_12hr}!")
            st.balloons()
            st.rerun()
        else:
            st.error("❌ Failed to save. Please try again.")

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
    todays_entries = user.get("history", {}).get(today_str(), {}).get("entries", [])
    if todays_entries:
        try:
            sorted_entries = sorted(todays_entries, key=lambda x: x.get("timestamp", x.get("time", "")), reverse=True)
        except:
            sorted_entries = todays_entries[::-1]
        for entry in sorted_entries[:10]:
            display_time = entry.get("time_display") or entry.get("time", "")
            st.markdown(f"""
                <div class='log-entry'>
                    🕒 <strong>{display_time}</strong> — <strong>{entry.get('ml', 0)} ml</strong>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No water logged yet today. Start now!")

# ---------- CHALLENGES ----------
elif st.session_state.page == "Challenges":
    navbar()
    user = get_user_data(st.session_state.user)
    if not user:
        st.error("❌ User data not found. Please log in again.")
        st.session_state.user = None
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
        user.setdefault("challenges", []).append({
            "name": ch_name,
            "days": days,
            "goal": daily_goal,
            "start": today_str(),
            "done": False
        })
        if update_user_data(st.session_state.user, user):
            st.success(f"✅ Challenge '{ch_name}' created!")
            st.balloons()
            st.rerun()

    st.markdown("---")
    if user.get("challenges"):
        st.subheader("🎮 Your Active Challenges")
        for idx, ch in enumerate(user.get("challenges", [])):
            status = "✅ Completed" if ch.get("done") else "🔥 In Progress"
            with st.expander(f"{status} — {ch.get('name', 'Unnamed Challenge')}"):
                st.write(f"**Duration:** {ch.get('days', '?')} days")
                st.write(f"**Daily Goal:** {ch.get('goal', '?')} L")
                st.write(f"**Started:** {ch.get('start', '?')}")
                if not ch.get("done", False):
                    if st.button(f"Mark as Complete", key=f"complete_{idx}"):
                        user["challenges"][idx]["done"] = True
                        badge_name = f"✅ Completed: {ch['name']}"
                        if badge_name not in user.get("badges", []):
                            user.setdefault("badges", []).append(badge_name)
                        if update_user_data(st.session_state.user, user):
                            st.success("🎉 Challenge completed!")
                            st.rerun()
    else:
        st.info("💡 No challenges yet. Create one to stay motivated!")

# ---------- BADGES ----------
elif st.session_state.page == "Badges":
    navbar()
    user = get_user_data(st.session_state.user)
    if not user:
        st.error("❌ User data not found. Please log in again.")
        st.session_state.user = None
        st.session_state.page = "Login"
        st.rerun()

    st.markdown("<h2 style='color:#FFD166;'>🏅 Your Badges & Achievements</h2>", unsafe_allow_html=True)

    # compute streaks robustly
    dates = sorted([d for d in user.get("history", {}).keys()])
    today_date = datetime.now().date()
    current_streak = 0
    longest_streak = 0
    if dates:
        # convert to date objects
        date_objs = sorted([datetime.strptime(d, "%Y-%m-%d").date() for d in dates])
        longest = 0
        streak = 1
        prev = date_objs[0]
        longest = 1
        for d in date_objs[1:]:
            if (d - prev).days == 1:
                streak += 1
            else:
                streak = 1
            prev = d
            if streak > longest:
                longest = streak
        longest_streak = longest
        # compute current streak (ending on most recent day)
        last = date_objs[-1]
        if (today_date - last).days == 0:
            # last logged today
            current = 1
            prev = last
            # go backwards
            for d in reversed(date_objs[:-1]):
                if (prev - d).days == 1:
                    current += 1
                    prev = d
                else:
                    break
            current_streak = current
        elif (today_date - last).days == 1:
            # last logged yesterday, check consecutive
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
    else:
        current_streak = 0
        longest_streak = 0

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
    # badge logic
    badges_earned = []
    total_drinks = sum(len(day.get("entries", [])) for day in user.get("history", {}).values())
    existing_badges = set(user.get("badges", []))

    def award(badge_key, text):
        if badge_key not in existing_badges:
            user.setdefault("badges", []).append(badge_key)
            badges_earned.append(text)

    if total_drinks >= 1:
        award("💧 First Sip!", "💧 First Sip! — You've started your hydration journey!")
    if current_streak >= 3:
        award("🌱 3-Day Streak", "🌱 3-Day Streak — Three days of consistent hydration!")
    if current_streak >= 7:
        award("🌈 Hydration Hero (1 Week)", "🌈 Hydration Hero — One week of staying hydrated!")
    if current_streak >= 30:
        award("🏆 Aqua Master (1 Month)", "🏆 Aqua Master — 30 days of excellence!")
    if longest_streak >= 7:
        award("👑 Consistency King", "👑 Consistency King — You've maintained a 7-day streak!")

    st.markdown("### 🏆 Your Earned Badges")
    if not user.get("badges"):
        st.info("🎯 No badges yet — keep hydrating to unlock achievements!")
    else:
        badge_cols = st.columns(3)
        for idx, badge in enumerate(user.get("badges", [])):
            with badge_cols[idx % 3]:
                st.markdown(f"""
<div class='badge-box'>
<p style='text-align:center; font-size:18px; margin:0; color:#fff;'>{badge}</p>
</div>
""", unsafe_allow_html=True)

    if badges_earned:
        st.markdown("---")
        st.markdown("### 🎊 New Achievements Unlocked!")
        for b in badges_earned:
            st.success(b)
        st.balloons()

    update_user_data(st.session_state.user, user)

# ---------- SETTINGS ----------
elif st.session_state.page == "Settings":
    navbar()
    user = get_user_data(st.session_state.user)
    if not user:
        st.error("❌ User data not found. Please log in again.")
        st.session_state.user = None
        st.session_state.page = "Login"
        st.rerun()

    st.markdown("<h2 style='color:#FFD166;'>⚙️ Settings</h2>", unsafe_allow_html=True)
    profile = user.get("profile", {})

    st.subheader("👤 User Information")
    st.markdown(f"**Username:** {profile.get('name', st.session_state.user)}")
    st.markdown(f"**Age:** {profile.get('age', 'Not provided')} years")
    st.markdown(f"**Daily Goal:** {user.get('daily_goal_ml', 2000)/1000:.1f} L")
    st.markdown("---")

    st.subheader("🎯 Update Daily Goal")
    new_goal = st.number_input(
        "Update your daily water goal (litres):",
        min_value=0.5,
        max_value=10.0,
        value=user.get("daily_goal_ml", 2000)/1000,
        step=0.1
    )
    if st.button("💾 Update Goal"):
        user["daily_goal_ml"] = int(new_goal * 1000)
        if update_user_data(st.session_state.user, user):
            st.success(f"✅ Goal updated successfully to {new_goal:.1f} L!")
            st.rerun()
        else:
            st.error("❌ Failed to save goal.")

    st.markdown("---")
    st.subheader("🔔 Reminder Settings")
    st.info("💡 Enable reminders to get periodic notifications to drink water throughout the day!")

    rem_enabled = st.checkbox(
        "Enable in-app reminders",
        value=user.get("settings", {}).get("reminder_enabled", False),
        help="Show reminder popups to drink water"
    )
    rem_minutes = st.number_input(
        "Reminder interval (minutes):",
        min_value=15,
        max_value=720,
        value=user.get("settings", {}).get("reminder_minutes", 120),
        step=15,
        help="How often you want to be reminded"
    )
    rem_start = st.time_input(
        "Start reminders at:",
        value=time.fromisoformat(user.get("settings", {}).get("reminder_start_time", "09:00")),
        help="Reminders will start at this time and end at 10 PM"
    )

    st.info(f"⏰ You will receive reminders every {rem_minutes} minutes between {rem_start.strftime('%I:%M %p')} and 10:00 PM")

    if st.button("💾 Save Reminder Settings"):
        user.setdefault("settings", {})["reminder_enabled"] = bool(rem_enabled)
        user["settings"]["reminder_minutes"] = int(rem_minutes)
        user["settings"]["reminder_start_time"] = rem_start.strftime("%H:%M")
        if update_user_data(st.session_state.user, user):
            st.session_state.last_reminder_time = None
            st.session_state.reminder_dismissed = False
            st.success("✅ Reminder settings saved!")
            if rem_enabled:
                st.info("🔔 Reminders are now active! You'll see notifications on your Dashboard and other pages.")
            st.rerun()
        else:
            st.error("❌ Failed to save reminder settings.")

    st.markdown("---")
    if user.get("settings", {}).get("reminder_enabled", False):
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
            data = load_data()
            if st.session_state.user in data.get("users", {}):
                del data["users"][st.session_state.user]
                save_data(data)
                st.session_state.user = None
                st.session_state.page = "Login"
                st.session_state.last_reminder_time = None
                st.session_state.reminder_dismissed = False
                st.success("✅ All your data has been deleted.")
                st.rerun()
        else:
            st.warning("⚠️ Please confirm before deleting your data.")




