import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# ─── Session state initialization ───
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'page' not in st.session_state:
    st.session_state.page = "home"

# ─── Simple slave login (credentials from secrets) ───
def login():
    st.session_state.logged_in = True
    st.rerun()

def logout():
    st.session_state.logged_in = False
    st.rerun()

SLAVE_USERNAME = st.secrets["slave_login"]["username"]
SLAVE_PASSWORD = st.secrets["slave_login"]["password"]

# ─── Google Sheets connection ───
conn = st.connection("gsheets", type=GSheetsConnection)  # alias type as string is also accepted

# ─── Data loading ───
@st.cache_data(ttl=300)  # 5 minutes
def load_data():
    df = conn.read(worksheet=0, usecols=[0,1,2,3,4,5,6,7], header=0)
    if df.empty:
        df = pd.DataFrame(columns=[
            "Day", "Timestamp", "Clamp Type", "Minutes", "Tugs",
            "Reddit Username", "Status", "Notes"
        ])
    df["Day"] = pd.to_numeric(df["Day"], errors='coerce').fillna(0).astype(int)
    return df.sort_values("Day", ascending=False)

df = load_data()

# ─── Dashboard stats ───
completed = df[df["Status"] == "Completed"]
total_completed = len(completed)
clamp_counts = completed["Clamp Type"].value_counts()
avg_mins = completed["Minutes"].mean() if not completed.empty else 0
avg_tugs = completed["Tugs"].mean() if not completed.empty else 0

max_day = df["Day"].max() if not df.empty else 0
current_day = int(max_day + 1)

# ─── Page routing ───
if st.session_state.page == "home":
    st.title("Slave Daily Training Dashboard")

    # ─── Stats section ───
    st.subheader("Fun Stats")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Completed Tasks", total_completed)
    col2.metric("Avg Clamped Time", f"{avg_mins:.1f} min" if avg_mins else "—")
    col3.metric("Avg Tugs", f"{avg_tugs:.0f}" if avg_tugs else "—")

    st.subheader("Clamp Type Breakdown")
    if not clamp_counts.empty:
        st.bar_chart(clamp_counts)
    else:
        st.info("No completed tasks yet.")

    # ─── Add button & daily limit check ───
    today_records = df[df["Day"] == current_day]
    count_today = len(today_records)
    MAX_PER_DAY = 10

    if count_today >= MAX_PER_DAY:
        now = datetime.now()
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_left = (midnight - now).total_seconds()
        hours_left = int(seconds_left // 3600)
        mins_left = int((seconds_left % 3600) // 60)
        st.warning(
            f"No more tasks can be added today (already {count_today}/{MAX_PER_DAY}).\n"
            f"Reset in {hours_left} hours {mins_left} mins."
        )
    else:
        remaining = MAX_PER_DAY - count_today
        st.info(f"You can still add {remaining} more task{'s' if remaining != 1 else ''} today.")

        if st.button("➕ Add Daily Training", type="primary", use_container_width=True):
            st.session_state.page = "add"
            st.rerun()

    # ─── Login / Logout (only show when needed) ───
    if not st.session_state.logged_in:
        with st.expander("Slave Login (to edit tasks)"):
            uname = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            if st.button("Login"):
                if uname == SLAVE_USERNAME and pwd == SLAVE_PASSWORD:
                    login()
                else:
                    st.error("Incorrect credentials")
    else:
        st.success("Logged in as Slave")
        if st.button("Logout"):
            logout()

elif st.session_state.page == "add":
    st.title(f"Add Daily Training – Day {current_day}")

    clamp_types = [
        "Metal spiked clover clamps",
        "Rubber spiked clover clamps",
        "Regular clover clamps",
        "Sleeveless nipple clamps",
        "Plastic clothespins",
        "Metal clothespins",
        "Alligator clips",
        "4-pronged claw clamps"   # corrected name for consistency
    ]

    with st.form("add_task_form", clear_on_submit=True):
        clamp = st.selectbox("Clamp type", clamp_types)

        col1, col2 = st.columns(2)
        use_time = col1.toggle("Apply Time (minutes clamped)", value=True)
        use_tugs  = col2.toggle("Apply Tugs", value=False)

        mins_slider = st.slider(
            "Clamped time (minutes)",
            min_value=5, max_value=15, value=10, step=1,
            disabled=not use_time
        )

        tugs_slider = st.slider(
            "Number of tugs",
            min_value=300, max_value=600, value=450, step=10,
            disabled=not use_tugs
        )

        reddit_user = st.text_input("Reddit username (optional)")

        submitted = st.form_submit_button("Submit training", type="primary", use_container_width=True)

        if submitted:
            if not use_time and not use_tugs:
                st.error("Enable at least one: Time or Tugs.")
            else:
                mins_final = mins_slider if use_time else 0
                tugs_final = tugs_slider if use_tugs else 0

                # Auto-scale the missing value
                if use_time and not use_tugs:
                    ratio = (mins_final - 5) / 10.0
                    tugs_final = int(600 - ratio * 300)
                elif use_tugs and not use_time:
                    ratio = (tugs_final - 300) / 300.0
                    mins_final = int(15 - ratio * 10)

                new_row_dict = {
                    "Day": current_day,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Clamp Type": clamp,
                    "Minutes": mins_final,
                    "Tugs": tugs_final,
                    "Reddit Username": reddit_user.strip(),
                    "Status": "Pending",
                    "Notes": ""
                }

                new_row_df = pd.DataFrame([new_row_dict])
                current_df = load_data()
                updated_df = pd.concat([current_df, new_row_df], ignore_index=True)

                # ─── SAVE LOGIC ───
                conn.update(worksheet=0, data=updated_df)

                st.success(f"Training added for Day {current_day}!")
                st.balloons()

                # Return to home
                st.session_state.page = "home"
                load_data.clear()
                st.rerun()

    # Back button outside form
    if st.button("← Back to Dashboard"):
        st.session_state.page = "home"
        st.rerun()