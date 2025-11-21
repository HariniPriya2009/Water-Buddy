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
.reminder-popup {
    position: fixed;
    top: 20px;
    right: 20px;
    background: linear-gradient(135deg, #FF6B6B, #FF8E53);
    color: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.4);
    z-index: 9999;
    animation: slideIn 0.5s ease-out;
    max-width: 350px;
}
@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# ---------- FILE HANDLING ----------
DATA_FILE = "waterbuddy_data.json"

def load_data():
    """Load data from JSON file with error handling"""
    try:
        if not os.path.exists(DATA_FILE):
            return {"users": {}}
        
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            
        # Ensure proper structure
        if "users" not in data:
            data = {"users": {}}
            
        return data
    except json.JSONDecodeError:
        st.error("⚠️ Data file corrupted. Creating new file.")
        return {"users": {}}
    except Exception as e:
        st.error(f"⚠️ Error loading data: {str(e)}")
        return {"users": {}}

def save_data(data):
    """Save data to JSON file with error handling"""
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        st.error(f"⚠️ Error saving data: {str(e)}")
        return False

def today_str():
    """Return today's date as ISO string"""
    return date.today().isoformat()
# ---------- INIT ----------
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "user" not in st.session_state:
    st.session_state.user = None
if "last_reminder_time" not in st.session_state:
    st.session_state.last_reminder_time = None
if "reminder_dismissed" not in st.session_state:
    st.session_state.reminder_dismissed = False

# ---------- AGE-BASED GOAL CALCULATOR (FEATURE 1) ----------
def calculate_daily_goal(age, weight=None, activity_level="moderate"):
    """
    Calculate recommended daily water intake based on age and other factors
    Age ranges and recommendations based on health guidelines
    """
    if age < 4:
        return 1.3  # Toddlers: 1.3L
    elif age < 9:
        return 1.7  # Children 4-8: 1.7L
    elif age < 14:
        return 2.4 if age >= 9 else 2.1  # Pre-teens: 2.1-2.4L
    elif age < 19:
        return 2.8  # Teenagers: 2.8L
    elif age < 51:
        return 3.0  # Adults: 3.0L
    elif age < 71:
        return 2.8  # Middle-aged: 2.8L
    else:
        return 2.5  # Seniors: 2.5L

# ---------- MOTIVATIONAL MESSAGES (FEATURE 4) ----------
def get_motivational_message(percentage):
    """Return motivational message based on progress percentage"""
    if percentage == 0:
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
    elif percentage >= 100:
        return "🎉 GOAL ACHIEVED! You're a hydration champion! 🏆"
    else:
        return "💦 Keep drinking water!"

def get_mascot_image(percentage):
    """Return mascot image path based on progress"""
    if percentage < 20:
        return r"image/hardrated 1.webp"  # Dehydrated
    elif percentage < 50:
        return r"image/happy-cute hydration 2.gif"  # Getting there
    elif percentage < 100:
        return r"image/hydrated 3.webp"  # Almost done
    else:
        return r"image/strong 4.webp"  # Goal achieved!

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

# ---------- REMINDER MESSAGES ----------
reminder_messages = [
    "💧 Time to hydrate! Your body is calling for water!",
    "🚰 Don't forget to drink water! Stay refreshed!",
    "💦 Hydration check! Have you had water recently?",
    "🌊 Your brain is 75% water — give it what it needs!",
    "🥤 Quick reminder: Drink some water right now!",
    "💧 Staying hydrated = Staying healthy! Drink up!",
    "🔔 Ding ding! It's water o'clock!",
    "🌟 Small sips lead to big wins! Drink water now!",
    "💪 Keep your energy up! Time for some H2O!",
    "🎯 Goal-getter! Don't forget your hydration goal today!"
]

# ---------- REMINDER LOGIC ----------
def check_reminder(user):
    """Check if it's time to show a reminder"""
    settings = user.get("settings", {})
    
    # Check if reminders are enabled
    if not settings.get("reminder_enabled", False):
        return False
    
    # Get reminder settings
    interval_minutes = settings.get("reminder_minutes", 120)
    start_time_str = settings.get("reminder_start_time", "09:00")
    
    # Parse start time
    try:
        start_hour, start_minute = map(int, start_time_str.split(":"))
        start_time = time(start_hour, start_minute)
    except:
        start_time = time(9, 0)
    
    now = datetime.now()
    current_time = now.time()
    
    # Check if we're within active hours (start_time to 22:00)
    end_time = time(22, 0)
    if not (start_time <= current_time <= end_time):
        return False
    
    # Check last reminder time
    if st.session_state.last_reminder_time:
        time_since_last = (now - st.session_state.last_reminder_time).total_seconds() / 60
        if time_since_last < interval_minutes:
            return False
    
    # Check if reminder was dismissed recently (within 5 minutes)
    if st.session_state.reminder_dismissed:
        return False
    
    return True

def show_reminder():
    """Display reminder popup"""
    message = random.choice(reminder_messages)
    
    st.markdown(f"""
        <div class='reminder-popup'>
            <h3 style='margin:0 0 10px 0; color: white;'>🔔 Hydration Reminder</h3>
            <p style='margin:0; font-size: 16px;'>{message}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Update last reminder time
    st.session_state.last_reminder_time = datetime.now()
    st.session_state.reminder_dismissed = False

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
        actual_intake.append(actual_ml / 1000)
        target_intake.append(daily_goal / 1000)
        date_labels.append(dd.strftime("%m/%d"))
    
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    
    x = range(len(dates))
    width = 0.35
    
    bars1 = ax.bar([i - width/2 for i in x], actual_intake, width, 
                    label='Actual Intake', color='#00BFFF', edgecolor='white', linewidth=2)
    bars2 = ax.bar([i + width/2 for i in x], target_intake, width, 
                    label='Daily Target', color='#FF6B6B', alpha=0.7, edgecolor='white', linewidth=2)
    
    ax.set_xlabel('Date', fontsize=12, color='white', fontweight='bold')
    ax.set_ylabel('Water Intake (Litres)', fontsize=12, color='white', fontweight='bold')
    ax.set_title('Your Intake vs Daily Target (Past 7 Days)', fontsize=14, color='white', fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(date_labels, color='white', fontsize=10)
    ax.tick_params(axis='y', colors='white')
    ax.legend(facecolor='#4682B4', edgecolor='white', framealpha=0.8, labelcolor='white')
    
    ax.grid(True, alpha=0.3, color='white', linestyle='--')
    ax.set_axisbelow(True)
    
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
    pages = ["Dashboard", "Log Water", "Challenges", "Badges", "Settings"]
    cols = st.columns(len(pages))
    for i, p in enumerate(pages):
        if st.session_state.page == p:
            cols[i].markdown(f"**➡️ {p}**")
        elif cols[i].button(p):
            st.session_state.page = p
            st.rerun()
    st.markdown("---")


# ---------- COMPARISON VISUALIZATION ----------
def show_comparison_chart(current_ml, target_ml):
    """Visual comparison of current intake vs target"""
    st.markdown("### 📊 Current vs Target Comparison")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💧 Current Intake", f"{current_ml/1000:.2f} L")
    
    with col2:
        st.metric("🎯 Daily Target", f"{target_ml/1000:.2f} L")
    
    with col3:
        remaining = max(0, target_ml - current_ml)
        difference = current_ml - target_ml
        st.metric("📈 Remaining", f"{remaining/1000:.2f} L", 
                 delta=f"{difference/1000:.2f} L")
    
    # Visual bar comparison
    percentage = min((current_ml / target_ml) * 100, 100)
    
    st.markdown(f"""
    <div style='background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; margin-top: 15px;'>
        <h4 style='text-align: center; margin-bottom: 15px;'>Progress: {percentage:.1f}%</h4>
        <div style='background: rgba(255,255,255,0.2); height: 40px; border-radius: 20px; overflow: hidden;'>
            <div style='background: linear-gradient(90deg, #00BFFF, #1E90FF); height: 100%; width: {percentage}%; 
                        display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;
                        transition: width 0.5s ease;'>
                {percentage:.0f}%
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------- NAVBAR ----------
def navbar():
    pages = ["Dashboard", "Log Water", "Challenges", "Badges", "About", "Settings"]
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
            "profile": {"name": name, "password": password or "", "age": None, "weight": None},
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
    return data["users"][name]


# ---------- USER MANAGEMENT ----------
def ensure_user(name, password=None):
    data = load_data()
    
    if name not in data["users"]:
        data["users"][name] = {
            "profile": {"name": name, "password": password or "", "age": None, "weight": None},
            "history": {},
            "badges": [],
            "challenges": [],
            "daily_goal_ml": 2000,
            "settings": {
                "reminder_enabled": False,
                "reminder_minutes": 120,
                "reminder_start_time": "09:00",
                "theme": "light"
            }
        }
        save_data(data)
    
    return data["users"][name]

def get_user_data(username):
    """Get fresh user data from file"""
    data = load_data()
    return data["users"].get(username, None)

def update_user_data(username, user_data):
    """Update user data and save to file"""
    data = load_data()
    data["users"][username] = user_data
    save_data(data)

# ---------- CHECK AND SHOW REMINDER (For logged-in users) ----------
if st.session_state.user and st.session_state.page != "Login":
    user = get_user_data(st.session_state.user)
    if user and check_reminder(user):
        show_reminder()
        
        # Add dismiss button in sidebar
        with st.sidebar:
            if st.button("✅ Dismiss Reminder"):
                st.session_state.reminder_dismissed = True
                st.session_state.last_reminder_time = datetime.now()
                st.rerun()

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
        
    if mode == "Sign Up":
        st.markdown("### 🎂 Tell us about yourself")
        st.info("📌 We'll recommend a daily water goal based on your age!")

        if "age" not in st.session_state:
            st.session_state.age = 25

        # Age selector with +/- buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("➖", key="age_minus") and st.session_state.age > 1:
                st.session_state.age -= 1
                st.rerun()
        with col2:
            st.markdown(f"<h3 style='text-align:center;'>{st.session_state.age} years old</h3>", unsafe_allow_html=True)
        with col3:
            if st.button("➕", key="age_plus") and st.session_state.age < 120:
                st.session_state.age += 1
                st.rerun()


        # Calculate and display recommended goal
        recommended_goal = calculate_daily_goal(st.session_state.age)
        st.info(f"💡 **Recommended daily water intake for your age:** {recommended_goal:.1f} litres")
        st.markdown(f"""
        <div class='info-box'>
        <h4>💡 Recommended Daily Intake for Age {st.session_state.age}</h4>
        <h2 style='text-align: center; color: #FFD700;'>{recommended_goal:.1f} Litres</h2>
        <p style='text-align: center;'>({int(recommended_goal * 1000)} ml)</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🎯 Customize Your Goal (Optional)")
        custom_goal = st.slider("Adjust your daily goal (Litres):", 0.5, 5.0, recommended_goal, 0.1)
        
        if custom_goal != recommended_goal:
            st.warning(f"⚠️ You've adjusted from the recommended {recommended_goal:.1f}L to {custom_goal:.1f}L")
        
        st.success(f"✅ Your daily goal: **{custom_goal:.1f} litres** ({int(custom_goal * 1000)} ml)")  )
        

        if st.button("Create Account 🚀"):
            if not name.strip() or not password.strip():
                st.warning("⚠️ Please enter both username and password!")
            else:
                data = load_data()
                if name in data["users"]:
                    st.error("❌ Username already exists! Try logging in instead.")
                else:
                    st.session_state.user = name.strip()
                    user = ensure_user(st.session_state.user, password)
                    user["profile"]["age"] = st.session_state.age
                    user["profile"]["password"] = password
                    user["daily_goal_ml"] = int(custom_goal * 1000)
                    
                    update_user_data(st.session_state.user, user)
                    
                    st.success(f"🎉 Welcome {name}! Your account has been created!")
                    st.balloons()
                    st.session_state.page = "Dashboard"
                    st.rerun()

    else:  # Login mode
        if st.button("Login 🔑"):
            data = load_data()
            
            if name not in data["users"]:
                st.error("❌ User not found! Please sign up first.")
            elif data["users"][name]["profile"]["password"] != password:
                st.error("❌ Incorrect password! Please try again.")
            else:
                st.session_state.user = name
                st.success(f"✅ Welcome back, {name}! 💧")
                st.session_state.page = "Dashboard"
                st.rerun()

# ---------- DASHBOARD ----------
elif st.session_state.page == "Dashboard":
    navbar()
    user = get_user_data(st.session_state.user)
    st.header(f"📊 Dashboard — {user['profile']['name']}")
    
    # Daily Hydration Tip
    st.markdown("### 💡 Hydration Tip of the Day")
    st.info(random.choice(fun_facts))
    
    st.markdown("---")

      # Daily Tip
    st.markdown(f"""
    <div class='tip-box'>
    {random.choice(hydration_tips)}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    # Get today's data
    today_total = user["history"].get(today_str(), {}).get("total_ml", 0)
    daily_goal = user.get("daily_goal_ml", 2000)
    progress_percentage = (today_total / daily_goal) * 100



    st.markdown(f"### {get_motivational_message(progress_percentage)}")
    
    # Animated water bottle visualization
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

    # Reset button for today
    st.markdown("---")
    st.subheader("🔄 Reset Today's Progress")
    st.warning("⚠️ This will clear all water intake logged for today. Use this if you made a mistake or want to start fresh.")
    
    col_reset1, col_reset2 = st.columns([3, 1])
    with col_reset2:
        if st.button("🗑️ Reset Today", type="primary"):
            today = today_str()
            if today in user["history"]:
                user["history"][today] = {"total_ml": 0, "entries": []}
                update_user_data(st.session_state.user, user)
                st.success("✅ Today's progress has been reset!")
                st.rerun()
            else:
                st.info("No data found for today.")
# ---------- LOG WATER ----------
elif st.session_state.page == "Log Water":
    navbar()
    user = get_user_data(st.session_state.user)  # FIX: Get fresh data
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
    
    if col1.button(f"💧 {quick_amounts[0]} ml", use_container_width=True): amount = quick_amounts[0]
    if col2.button(f"💧 {quick_amounts[1]} ml", use_container_width=True): amount = quick_amounts[1]
    if col3.button(f"💧 {quick_amounts[2]} ml", use_container_width=True): amount = quick_amounts[2]
    if col4.button(f"💧 {quick_amounts[3]} ml", use_container_width=True): amount = quick_amounts[3]
    if col5.button(f"💧 {quick_amounts[4]} ml", use_container_width=True): amount = quick_amounts[4]

    st.markdown("### 🎯 Custom Amount")
    custom = st.number_input("Enter custom amount (ml):", min_value=50, max_value=2000, value=250, step=50)
    
    if st.button("➕ Add Custom Amount", type="primary", use_container_width=True):
        amount = custom

    # Process the logged water
    if amount:
        ds = today_str()
        if ds not in user["history"]:
            user["history"][ds] = {"total_ml": 0, "entries": []}
        tnow = datetime.now().strftime("%H:%M:%S")
        user["history"][ds]["entries"].append({"time": tnow, "ml": int(amount)})
        user["history"][ds]["total_ml"] += int(amount)
        update_user_data(st.session_state.user, user)  # FIX: Use update function
        st.success(f"✅ Added {amount} ml at {tnow}!")
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

    # Show recent entries - FIX: Better time display with sorting
    st.markdown("---")
    st.markdown("### 📝 Today's Log History")
    if today_str() in user["history"] and user["history"][today_str()]["entries"]:
        entries = user["history"][today_str()]["entries"]
        
        # Sort entries by timestamp if available, otherwise by time
        try:
            sorted_entries = sorted(entries, key=lambda x: x.get("timestamp", x.get("time", "")), reverse=True)
        except:
            sorted_entries = entries[::-1]  # Just reverse if sorting fails
        
        # Display last 10 entries
        st.markdown("""
        <style>
        .log-entry {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px 15px;
            margin: 5px 0;
            border-radius: 10px;
            border-left: 4px solid #00BFFF;
        }
        </style>
        """, unsafe_allow_html=True)
        
        for entry in sorted_entries[:10]:
            # Try to use display time first, fallback to converting 24hr time
            if "time_display" in entry:
                display_time = entry["time_display"]
            else:
                # Convert old format times to 12-hour format
                try:
                    time_obj = datetime.strptime(entry['time'], "%H:%M:%S")
                    display_time = time_obj.strftime("%I:%M %p")
                except:
                    display_time = entry['time']
            
            st.markdown(f"""
                <div class='log-entry'>
                    🕒 <strong>{display_time}</strong> — <strong>{entry['ml']} ml</strong>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No water logged yet today. Start now!")


# ---------- CHALLENGES ----------
elif st.session_state.page == "Challenges":
    navbar()
    user = get_user_data(st.session_state.user)
    st.header("🏁 Hydration Challenges")

    st.markdown("### 🎯 Create a New Challenge")
    ch_name = st.text_input("Challenge name:", placeholder="e.g., Weekend Warrior, Week of Wellness")
    days = st.slider("Duration (days)", 1, 30, 7)
    daily_goal = st.slider("Daily goal (litres)", 0.5, 5.0, 2.0, 0.25)
    
    if st.button("🚀 Create Challenge", type="primary"):
        if not ch_name.strip():
            ch_name = f"{daily_goal}L for {days} days"
        user["challenges"].append({
            "name": ch_name,
            "days": days,
            "goal": daily_goal,
            "start": today_str(),
            "done": False
        })
        update_user_data(st.session_state.user, user)
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
                        update_user_data(st.session_state.user, user)
                        st.success("🎉 Challenge completed!")
                        st.rerun()
    else:
        st.info("💡 No challenges yet. Create one to stay motivated!")

# ---------- BADGES ----------
elif st.session_state.page == "Badges":
    navbar()
    user = get_user_data(st.session_state.user)

    st.markdown("<h2 style='color:#FFD166;'>🏅 Your Badges & Achievements</h2>", unsafe_allow_html=True)
    
    # Calculate streaks
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

    # Save badge updates
    update_user_data(st.session_state.user, user)

# ---------- SETTINGS PAGE ----------
elif st.session_state.page == "Settings":
    navbar()
    st.markdown("<h2 style='color:#FFD166;'>⚙️ Settings</h2>", unsafe_allow_html=True)

    user = get_user_data(st.session_state.user)
    profile = user.get("profile", {})

    # --- User Info Section ---
    st.subheader("👤 User Information")
    st.markdown(f"**Username:** {profile.get('name', st.session_state.user)}")
    st.markdown(f"**Age:** {profile.get('age', 'Not provided')} years")
    st.markdown(f"**Daily Goal:** {user.get('daily_goal_ml', 2000)/1000:.1f} L")

    st.markdown("---")
    
    # --- Update Goal Section ---
    st.subheader("🎯 Update Daily Goal")
    new_goal = st.number_input(
        "Update your daily water goal (litres):",
        min_value=0.5,
        max_value=10.0,
        value=user.get("daily_goal_ml", 2000)/1000,
        step=0.1
    )
    
    if st.button("💾 Update Goal", type="primary"):
        user["daily_goal_ml"] = int(new_goal * 1000)
        update_user_data(st.session_state.user, user)
        st.success(f"✅ Goal updated successfully to {new_goal:.1f} L!")
        st.rerun()

    st.markdown("---")

    # --- Reminder Settings ---
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

    if st.button("💾 Save Reminder Settings", type="primary"):
        if "settings" not in user:
            user["settings"] = {}
        user["settings"]["reminder_enabled"] = rem_enabled
        user["settings"]["reminder_minutes"] = int(rem_minutes)
        user["settings"]["reminder_start_time"] = rem_start.strftime("%H:%M")
        update_user_data(st.session_state.user, user)
        
        # Reset reminder state to apply new settings
        st.session_state.last_reminder_time = None
        st.session_state.reminder_dismissed = False
        
        st.success("✅ Reminder settings saved!")
        if rem_enabled:
            st.info("🔔 Reminders are now active! You'll see notifications on your Dashboard and other pages.")
        st.rerun()

    st.markdown("---")

    # --- Test Reminder ---
    if rem_enabled:
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

    # --- Logout Section ---
    st.subheader("🚪 Logout")
    if st.button("Logout", type="secondary"):
        st.session_state.user = None
        st.session_state.page = "Login"
        st.session_state.last_reminder_time = None
        st.session_state.reminder_dismissed = False
        st.success("✅ Logged out successfully!")
        st.rerun()

    st.markdown("---")

    # --- Reset All Data ---
    st.subheader("🗑️ Reset All Data")
    st.warning("⚠️ **WARNING:** This will permanently delete all your logs, badges, challenges, and progress. This action cannot be undone!")

    RC = st.checkbox("I confirm I want to delete all my data.", key="confirm_delete")

    if st.button("❌ Delete All Data", type="primary"):
        if RC:
            data = load_data()
            if st.session_state.user in data["users"]:
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

# ---------- SAVE ----------
save_data(data)


