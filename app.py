import streamlit as st
import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta, date, time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# ---------- FILE HANDLING ----------
DATA_FILE = "waterbuddy_data.json"

def load_data():
    """Load data from JSON file"""
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"users": {}}

def save_data(data):
    """Save data to JSON file"""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

def today_str():
    """Return today's date as ISO string"""
    return date.today().isoformat()

# ---------- INITIALIZE SESSION STATE ----------
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "user" not in st.session_state:
    st.session_state.user = None
if "age" not in st.session_state:
    st.session_state.age = 18
if "show_reminder" not in st.session_state:
    st.session_state.show_reminder = False
if "last_reminder_time" not in st.session_state:
    st.session_state.last_reminder_time = None
if "reminder_dismissed_today" not in st.session_state:
    st.session_state.reminder_dismissed_today = []

# ---------- LOAD DATA ONCE ----------
if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# ---------- AGE-BASED GOAL CALCULATOR (FEATURE 1) ----------
def calculate_daily_goal(age, weight=None, activity_level="moderate"):
    """Calculate recommended daily water intake based on age"""
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
# ---------- REMINDER SYSTEM ----------
def check_reminder(user):
    """Check if reminder should be shown"""
    settings = user.get("settings", {})
    
    if not settings.get("reminder_enabled", False):
        return False
    
    now = datetime.now()
    today_key = now.strftime("%Y-%m-%d")
    
    # Reset dismissed list daily
    if st.session_state.reminder_dismissed_today and \
       st.session_state.reminder_dismissed_today[0] != today_key:
        st.session_state.reminder_dismissed_today = []
    
    # Check if already dismissed recently
    current_time_key = now.strftime("%Y-%m-%d %H:%M")
    if current_time_key in st.session_state.reminder_dismissed_today:
        return False
    
    # Get reminder settings
    reminder_interval = settings.get("reminder_minutes", 120)
    start_time_str = settings.get("reminder_start_time", "09:00")
    end_time_str = settings.get("reminder_end_time", "22:00")
    
    # Parse times
    try:
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
    except:
        start_time = datetime.strptime("09:00", "%H:%M").time()
        end_time = datetime.strptime("22:00", "%H:%M").time()
    
    current_time = now.time()
    
    # Check if within active hours
    if not (start_time <= current_time <= end_time):
        return False
    
    # Check last reminder time
    if st.session_state.last_reminder_time:
        try:
            last_reminder = datetime.fromisoformat(st.session_state.last_reminder_time)
            time_diff = (now - last_reminder).total_seconds() / 60
            
            if time_diff < reminder_interval:
                return False
        except:
            pass
    
    # Check if goal not met
    today_total = user["history"].get(today_str(), {}).get("total_ml", 0)
    daily_goal = user.get("daily_goal_ml", 2000)
    
    if today_total >= daily_goal:
        return False
    
    return True

def show_reminder_popup(user):
    """Display reminder popup"""
    today_total = user["history"].get(today_str(), {}).get("total_ml", 0)
    daily_goal = user.get("daily_goal_ml", 2000)
    remaining = daily_goal - today_total
    
    reminder_messages = [
        "💧 Time to hydrate! Your body needs water!",
        "🌊 Don't forget to drink water!",
        "💦 Stay hydrated, stay healthy!",
        "🥤 A glass of water keeps the doctor away!",
        "🌟 You're doing great! Keep drinking!",
        "🏃‍♀️ Hydration = Better performance!",
        "🧠 Water boosts your brain power!",
        "😊 Drink up and feel refreshed!"
    ]
    
    st.markdown(f"""
        <div class='reminder-popup' id='reminderPopup'>
            <div style='text-align: center;'>
                <h2 style='margin: 0; color: #333;'>💧 Hydration Reminder!</h2>
                <p style='font-size: 16px; color: #333; margin: 10px 0;'>
                    {random.choice(reminder_messages)}
                </p>
                <div style='background: white; padding: 10px; border-radius: 10px; margin: 10px 0;'>
                    <p style='margin: 5px 0; color: #333; font-weight: bold;'>
                        Today: {today_total} ml / {daily_goal} ml
                    </p>
                    <p style='margin: 5px 0; color: #FF6B6B; font-weight: bold;'>
                        Remaining: {remaining} ml
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def dismiss_reminder():
    """Dismiss current reminder"""
    now = datetime.now()
    current_time_key = now.strftime("%Y-%m-%d %H:%M")
    today_key = now.strftime("%Y-%m-%d")
    
    if not st.session_state.reminder_dismissed_today or \
       st.session_state.reminder_dismissed_today[0] != today_key:
        st.session_state.reminder_dismissed_today = [today_key]
    
    st.session_state.reminder_dismissed_today.append(current_time_key)
    st.session_state.last_reminder_time = now.isoformat()
    st.session_state.show_reminder = False
# ---------- MOTIVATIONAL MESSAGES (FEATURE 4) ----------
def get_motivational_message(percentage):
    """Return motivational message based on progress percentage"""
    if percentage == 0:
        return "🌵 Time to start hydrating! Your body needs water!"
    elif percentage < 20:
        return "💧 Great first step! Keep going!"
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
    """Return mascot image path based on progress"""
    if percentage < 20:
        return r"image/hardrated 1.webp"
    elif percentage < 50:
        return r"image/happy-cute hydration 2.gif"
    elif percentage < 100:
        return r"image/hydrated 3.webp"
    else:
        return r"image/strong 4.webp"

# ---------- FUN FACTS / DAILY TIPS ----------
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

# ---------- MATPLOTLIB GRAPH FUNCTION ----------
def plot_7day_intake(user):
    """Create a matplotlib bar chart showing 7-day water intake vs target"""
    daily_goal = user.get("daily_goal_ml", 2000)
    
    dates, actual_intake, target_intake = [], [], []
    date_labels = []
    
    for d in range(6, -1, -1):
        dd = date.today() - timedelta(days=d)
        dates.append(dd)
        actual_ml = user["history"].get(dd.isoformat(), {}).get("total_ml", 0)
        actual_intake.append(actual_ml / 1000)  # Convert to litres
        target_intake.append(daily_goal / 1000)
        date_labels.append(dd.strftime("%m/%d"))
    
    # Create figure with transparent background
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    
    x = range(len(dates))
    width = 0.35
    
    # Create bars
    bars1 = ax.bar([i - width/2 for i in x], actual_intake, width, 
                    label='Actual Intake', color='#00BFFF', edgecolor='white', linewidth=2)
    bars2 = ax.bar([i + width/2 for i in x], target_intake, width, 
                    label='Daily Target', color='#FF6B6B', alpha=0.7, edgecolor='white', linewidth=2)
    
    # Styling
    ax.set_xlabel('Date', fontsize=12, color='white', fontweight='bold')
    ax.set_ylabel('Water Intake (Litres)', fontsize=12, color='white', fontweight='bold')
    ax.set_title('Your Intake vs Daily Target (Past 7 Days)', fontsize=14, color='white', fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(date_labels, color='white', fontsize=10)
    ax.tick_params(axis='y', colors='white')
    ax.legend(facecolor='#4682B4', edgecolor='white', framealpha=0.8, labelcolor='white')
    
    # Grid
    ax.grid(True, alpha=0.3, color='white', linestyle='--')
    ax.set_axisbelow(True)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}L',
                       ha='center', va='bottom', color='white', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    return fig

# ---------- NAVBAR ----------
def navbar():
    """Display navigation bar"""
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
def ensure_user(name):
    """Ensure user exists in data, create if not"""
    if name not in data["users"]:
        data["users"][name] = {
            "profile": {
                "name": name,
                "password": "",
                "age": None,
                "weight": None,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        st.session_state.data = data
    return data["users"][name]

# ---------- LOGIN / SIGN UP ----------
if st.session_state.page == "Login":
    st.markdown("<h1 style='text-align:center;'>💧 Welcome to WaterBuddy!</h1>", unsafe_allow_html=True)
    st.subheader("🌊 Hydrate Your Lifestyle with Smart Tracking")
    st.markdown("---")

    mode = st.radio("Select mode:", ["Login", "Sign Up"], horizontal=True)
    name = st.text_input("Username:")
    password = st.text_input("Password:", type="password")

    if mode == "Sign Up":
        st.markdown("### YOUR AGE")

        # Age adjustment buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("➖") and st.session_state.age > 1:
                st.session_state.age -= 1
                st.rerun()
        with col2:
            st.markdown(f"<h3 style='text-align:center;'>{st.session_state.age} years old</h3>", unsafe_allow_html=True)
        with col3:
            if st.button("➕") and st.session_state.age < 120:
                st.session_state.age += 1
                st.rerun()

        # Number input for age (synced with buttons)
        age_input = st.number_input("Age:", 1, 120, st.session_state.age, key="age_input")
        if age_input != st.session_state.age:
            st.session_state.age = age_input
            st.rerun()

        # Calculate recommended goal based on age
        recommended_goal = calculate_daily_goal(st.session_state.age)
        st.info(f"💡 Recommended daily intake: {recommended_goal:.1f} L")

        # Custom goal slider
        custom_goal = st.slider("Adjust your goal (L):", 0.5, 5.0, recommended_goal, 0.1)
        st.success(f"✅ Your daily goal is set to: **{custom_goal:.1f} litres** ({int(custom_goal * 1000)} ml)")

        # Create Account button
        if st.button("Create Account 🚀"):
            if not name.strip() or not password.strip():
                st.warning("⚠️ Please enter both username and password!")
            elif name in data["users"]:
                st.error("❌ Username already exists! Try logging in.")
            else:
                # Create new user with all required data
                data["users"][name] = {
                    "profile": {
                        "name": name,
                        "password": password,
                        "age": st.session_state.age,
                        "weight": None,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "daily_goal_ml": int(custom_goal * 1000),
                    "history": {},
                    "badges": [],
                    "challenges": [],
                    "settings": {
                        "reminder_enabled": False,
                        "reminder_minutes": 120,
                        "reminder_start_time": "09:00"
                    }
                }
                
                # Save data to file
                save_data(data)
                st.session_state.data = data
                
                # Set user session
                st.session_state.user = name
                st.success(f"🎉 Account created for {name}!")
                st.balloons()
                st.session_state.page = "Dashboard"
                st.rerun()

    else:  # Login mode
        if st.button("Login 🔑"):
            if name not in data["users"]:
                st.error("❌ User not found! Please sign up first.")
            elif data["users"][name]["profile"]["password"] != password:
                st.error("❌ Incorrect password!")
            else:
                st.session_state.user = name
                st.success(f"✅ Welcome back, {name}!")
                st.session_state.page = "Dashboard"
                st.rerun()

# ---------- DASHBOARD ----------
elif st.session_state.page == "Dashboard":
    navbar()
    user = ensure_user(st.session_state.user)
    st.header(f"📊 Dashboard — {user['profile']['name']}")
    
    # Daily Hydration Tip
    st.markdown("### 💡 Hydration Tip of the Day")
    st.info(random.choice(fun_facts))
    
    st.markdown("---")

    # Get today's data
    today_total = user["history"].get(today_str(), {}).get("total_ml", 0)
    daily_goal = user.get("daily_goal_ml", 2000)
    progress_percentage = (today_total / daily_goal) * 100

    st.markdown(f"### {get_motivational_message(progress_percentage)}")
    
    # Animated water bottle visualization (FEATURE 3)
    bottle_fill_percentage = min(progress_percentage, 100)
    st.markdown(f"""
        <div style="text-align: center;">
            <div style="
                width: 150px;
                height: 300px;
                border: 4px solid #ffffff;
                border-radius: 20px 20px 40px 40px;
                position: relative;
                margin: 20px auto;
                box-shadow: 0 8px 16px rgba(0,0,0,0.3);
                background: linear-gradient(to top, #00BFFF {bottle_fill_percentage}%, transparent {bottle_fill_percentage}%);
                overflow: hidden;
            ">
                <div style="
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    font-size: 24px;
                    font-weight: bold;
                    color: {'#ffffff' if bottle_fill_percentage > 50 else '#000000'};
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                ">
                    {progress_percentage:.0f}%
                </div>
            </div>
            <p style="color: white; font-size: 18px; font-weight: bold;">
                {today_total} ml / {daily_goal} ml
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Progress bar
    st.progress(min(progress_percentage / 100, 1.0))

    # COMPARISON: Current vs Target
    st.markdown("### 📊 Your Progress vs Target")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Intake", f"{today_total/1000:.2f} L", delta=f"{(today_total - daily_goal)/1000:.2f} L")
    with col2:
        st.metric("Daily Target", f"{daily_goal/1000:.2f} L")
    with col3:
        remaining = max(0, daily_goal - today_total)
        st.metric("Remaining", f"{remaining/1000:.2f} L")

    st.markdown("---")

    # Past 7 days graph using Matplotlib
    st.markdown("### 📈 Your 7-Day Hydration History")
    fig = plot_7day_intake(user)
    st.pyplot(fig)
    plt.close()

    # FEATURE 5: Reset button for today
    st.markdown("---")
    st.subheader("🔄 Reset Today's Progress")
    st.warning("⚠️ This will clear all water intake logged for today. Use this if you made a mistake or want to start fresh.")
    
    col_reset1, col_reset2 = st.columns([3, 1])
    with col_reset2:
        if st.button("🗑️ Reset Today", type="primary"):
            today = today_str()
            if today in user["history"]:
                user["history"][today] = {"total_ml": 0, "entries": []}
                save_data(data)
                st.session_state.data = data
                st.success("✅ Today's progress has been reset!")
                st.rerun()
            else:
                st.info("No data found for today.")

# ---------- LOG WATER ----------
elif st.session_state.page == "Log Water":
    navbar()
    user = ensure_user(st.session_state.user)
    st.header("💧 Log Water Intake")

    # Get today's data
    today_total = user["history"].get(today_str(), {}).get("total_ml", 0)
    daily_goal = user.get("daily_goal_ml", 2000)
    progress_percentage = (today_total / daily_goal) * 100

    # FEATURE 2: Quick log buttons for common amounts
    st.markdown("### ⚡ Quick Log (Tap to Add)")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    quick_amounts = [100, 200, 250, 330, 500]
    amount = None
    
    if col1.button(f"💧 {quick_amounts[0]} ml", use_container_width=True, key="quick_100"): 
        amount = quick_amounts[0]
    if col2.button(f"💧 {quick_amounts[1]} ml", use_container_width=True, key="quick_200"): 
        amount = quick_amounts[1]
    if col3.button(f"💧 {quick_amounts[2]} ml", use_container_width=True, key="quick_250"): 
        amount = quick_amounts[2]
    if col4.button(f"💧 {quick_amounts[3]} ml", use_container_width=True, key="quick_330"): 
        amount = quick_amounts[3]
    if col5.button(f"💧 {quick_amounts[4]} ml", use_container_width=True, key="quick_500"): 
        amount = quick_amounts[4]

    st.markdown("### 🎯 Custom Amount")
    custom = st.number_input("Enter custom amount (ml):", min_value=50, max_value=2000, value=250, step=50)
    
    if st.button("➕ Add Custom Amount", type="primary", use_container_width=True):
        amount = custom

    # Process the logged water
    if amount:
        ds = today_str()
        if ds not in user["history"]:
            user["history"][ds] = {"total_ml": 0, "entries": []}
        
        # Use proper datetime formatting with 12-hour format
        now = datetime.now()
        time_24hr = now.strftime("%H:%M:%S")
        time_12hr = now.strftime("%I:%M %p")
        
        user["history"][ds]["entries"].append({
            "time": time_24hr,
            "time_display": time_12hr,
            "ml": int(amount),
            "timestamp": now.isoformat()
        })
        user["history"][ds]["total_ml"] += int(amount)
        save_data(data)
        st.session_state.data = data
        st.success(f"✅ Added {amount} ml at {time_12hr}!")
        st.balloons()
        st.rerun()

    st.markdown("---")

    # FEATURE 3: Real-time visual feedback
    st.markdown("### 📊 Today's Progress")
    
    # Mascot image based on progress (FEATURE 4)
    mascot_path = get_mascot_image(progress_percentage)
    motivational_msg = get_motivational_message(progress_percentage)
    
    col_mascot, col_progress = st.columns([1, 2])
    
    with col_mascot:
        if os.path.exists(mascot_path):
            st.image(mascot_path, width=200)
        st.markdown(f"**{motivational_msg}**")
    
    with col_progress:
        # Animated bottle
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

    # Show recent entries
    st.markdown("---")
    st.markdown("### 📝 Today's Log History")
    if today_str() in user["history"] and user["history"][today_str()].get("entries"):
        entries = user["history"][today_str()]["entries"]
        
        # Sort entries by timestamp
        try:
            sorted_entries = sorted(entries, key=lambda x: x.get("timestamp", x.get("time", "")), reverse=True)
        except:
            sorted_entries = entries[::-1]
        
        # Display last 10 entries
        for entry in sorted_entries[:10]:
            display_time = entry.get("time_display", entry.get("time", ""))
            if not display_time or ":" not in display_time:
                try:
                    time_obj = datetime.strptime(entry['time'], "%H:%M:%S")
                    display_time = time_obj.strftime("%I:%M %p")
                except:
                    display_time = entry.get('time', 'Unknown')
            
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
    user = ensure_user(st.session_state.user)
    st.header("🏁 Hydration Challenges")

    st.markdown("### 🎯 Create a New Challenge")
    ch_name = st.text_input("Challenge name:", placeholder="e.g., Weekend Warrior, Week of Wellness")
    days = st.slider("Duration (days)", 1, 30, 7)
    daily_goal_challenge = st.slider("Daily goal (litres)", 0.5, 5.0, 2.0, 0.25)
    
    if st.button("🚀 Create Challenge", type="primary"):
        if not ch_name.strip():
            ch_name = f"{daily_goal_challenge}L for {days} days"
        user["challenges"].append({
            "name": ch_name,
            "days": days,
            "goal": daily_goal_challenge,
            "start": today_str(),
            "done": False
        })
        save_data(data)
        st.session_state.data = data
        st.success(f"✅ Challenge '{ch_name}' created!")
        st.balloons()
        st.rerun()

    st.markdown("---")
    
    # Display active challenges
    if user["challenges"]:
        st.subheader("🎮 Your Active Challenges")
        for idx, ch in enumerate(user["challenges"]):
            status = "✅ Completed" if ch.get("done", False) else "🔥 In Progress"
            with st.expander(f"{status} — {ch.get('name', 'Unnamed Challenge')}"):
                st.write(f"**Duration:** {ch.get('days', '?')} days")
                st.write(f"**Daily Goal:** {ch.get('goal', '?')} L")
                st.write(f"**Started:** {ch.get('start', '?')}")
                
                if not ch.get("done", False):
                    if st.button(f"Mark as Complete", key=f"complete_{idx}"):
                        user["challenges"][idx]["done"] = True
                        badge_name = f"✅ Completed: {ch['name']}"
                        if badge_name not in user["badges"]:
                            user["badges"].append(badge_name)
                        save_data(data)
                        st.session_state.data = data
                        st.success("🎉 Challenge completed!")
                        st.rerun()
    else:
        st.info("💡 No challenges yet. Create one to stay motivated!")

# ---------- BADGES ----------
elif st.session_state.page == "Badges":
    navbar()
    user = ensure_user(st.session_state.user)

    st.markdown("<h2 style='color:#FFD166;'>🏅 Your Badges & Achievements</h2>", unsafe_allow_html=True)
    
    # Calculate streaks
    today = datetime.now().date()

    if user["history"]:
        sorted_days = sorted(user["history"].keys())
        streak = 1
        longest_streak = 1
        
        if len(sorted_days) > 0:
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

    # Display streaks
    st.markdown("### 🔥 Your Hydration Streaks")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Streak", f"{streak} days", delta="🔥")
    with col2:
        st.metric("Longest Streak", f"{longest_streak} days", delta="🏆")

    next_goal = 7 if streak < 7 else (30 if streak < 30 else 60)
    progress = min(streak / next_goal, 1.0)
    st.progress(progress)
    st.caption(f"{streak}/{next_goal} days toward your next milestone!")

    st.markdown("---")

    # Badge earning logic
    badges_earned = []
    total_drinks = sum(len(day.get("entries", [])) for day in user["history"].values())
    
    if total_drinks >= 1 and "💧 First Sip!" not in user["badges"]:
        user["badges"].append("💧 First Sip!")
        badges_earned.append("💧 First Sip! — You've started your hydration journey!")

    if streak >= 3 and "🌱 3-Day Streak" not in user["badges"]:
        user["badges"].append("🌱 3-Day Streak")
        badges_earned.append("🌱 3-Day Streak — Three days of consistent hydration!")

    if streak >= 7 and "🌈 Hydration Hero (1 Week)" not in user["badges"]:
        user["badges"].append("🌈 Hydration Hero (1 Week)")
        badges_earned.append("🌈 Hydration Hero — One week of staying hydrated!")

    if streak >= 30 and "🏆 Aqua Master (1 Month)" not in user["badges"]:
        user["badges"].append("🏆 Aqua Master (1 Month)")
        badges_earned.append("🏆 Aqua Master — 30 days of excellence!")

    if longest_streak >= 7 and "👑 Consistency King" not in user["badges"]:
        user["badges"].append("👑 Consistency King")
        badges_earned.append("👑 Consistency King — You've maintained a 7-day streak!")

    # Display badges
    st.markdown("### 🏆 Your Earned Badges")
    if not user["badges"]:
        st.info("🎯 No badges yet — keep hydrating to unlock achievements!")
    else:
        badge_cols = st.columns(3)
        for idx, badge in enumerate(user["badges"]):
            with badge_cols[idx % 3]:
                st.markdown(f"""
                    <div class='badge-box'>
                        <p style='text-align:center; font-size:18px; margin:0; color:#fff;'>{badge}</p>
                    </div>
                """, unsafe_allow_html=True)

    # Show newly earned badges
    if badges_earned:
        st.markdown("---")
        st.markdown("### 🎊 New Achievements Unlocked!")
        for badge in badges_earned:
            st.success(badge)
        st.balloons()

    save_data(data)  # FIX 3: Save after badge updates

# ---------- SETTINGS PAGE ----------
elif st.session_state.page == "Settings":
    navbar_pages = ["Dashboard", "Log Water", "Challenges", "Badges", "Settings"]
    cols = st.columns(len(navbar_pages))
    for i, p in enumerate(navbar_pages):
        if cols[i].button(p):
            st.session_state.page = p
            st.rerun()
    st.markdown("---")

    st.markdown("<h2>⚙️ Settings</h2>", unsafe_allow_html=True)
    user = ensure_user(st.session_state.user)
    profile = user.get("profile", {})

    st.subheader("👤 User Information")
    st.markdown(f"**Username:** {profile.get('name', 'Unknown')}")
    st.markdown(f"**Age:** {profile.get('age', 'Not provided')} years")
    st.markdown(f"**Daily Goal:** {user.get('daily_goal_ml', 2000)/1000:.1f} L")

    new_goal = st.number_input("Update goal (L):", 0.5, 10.0, user["daily_goal_ml"]/1000, 0.1)
    if st.button("💾 Update Goal"):
        user["daily_goal_ml"] = int(new_goal * 1000)
        save_data(data)
        st.success("✅ Goal updated successfully!")

    st.markdown("---")
    st.subheader("🚪 Logout")
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "Login"
        st.success("Logged out successfully!")
        st.rerun()

# ---------- SAVE ----------
save_data(data)









