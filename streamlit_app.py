import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# ─── Session state initialization ───
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'page' not in st.session_state:
    st.session_state.page = "home"

# ─── Simple slave login (from secrets) ───
def login():
    st.session_state.logged_in = True
    st.rerun()

def logout():
    st.session_state.logged_in = False
    st.rerun()

SLAVE_USERNAME = st.secrets["slave_login"]["username"]
SLAVE_PASSWORD = st.secrets["slave_login"]["password"]

# ─── Google Sheets connection ───
conn = st.connection("gsheets", type=GSheetsConnection)

# ─── Data loading (no cache for real-time updates) ───
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

    # ─── Manual refresh button ───
    if st.button("🔄 Refresh Data"):
        st.rerun()

    # ─── Stats section ───
    st.subheader("Fun Stats")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Completed Tasks", total_completed)
    col2.metric("Avg Clamped Time", f"{avg_mins:.1f} min" if avg_mins > 0 else "—")
    col3.metric("Avg Tugs", f"{avg_tugs:.0f}" if avg_tugs > 0 else "—")

    st.subheader("Clamp Type Breakdown")
    if not clamp_counts.empty:
        st.bar_chart(clamp_counts)
    else:
        st.info("No completed tasks yet.")

    # ─── All Tasks Table ───
    st.subheader("All Tasks")
    if not df.empty:
        def highlight_completed(row):
            return ['background-color: #d4edda' if row["Status"] == "Completed" else '' for _ in row]

        st.dataframe(
            df.style.apply(highlight_completed, axis=1),
            width="stretch",
            hide_index=True
        )
    else:
        st.info("No tasks recorded yet.")

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

        if st.button("➕ Add Daily Training", type="primary", width="stretch"):
            st.session_state.page = "add"
            st.rerun()

    # ─── Login / Logout ───
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
        "4-pronged claw clamps"
    ]

    with st.form("add_task_form", clear_on_submit=True):
        clamp = st.selectbox("Clamp type", clamp_types)

        # ─── Linked sliders (no toggles) ───
        st.subheader("Intensity Settings")

        # Init session state if needed
        if 'mins_value' not in st.session_state:
            st.session_state.mins_value = 10
        if 'tugs_value' not in st.session_state:
            st.session_state.tugs_value = 450

        col1, col2 = st.columns(2)

        with col1:
            mins = st.slider(
                "Clamped time (minutes)",
                min_value=5, max_value=15, value=st.session_state.mins_value,
                step=1, key="mins_slider"
            )

        with col2:
            tugs = st.slider(
                "Number of tugs",
                min_value=300, max_value=600, value=st.session_state.tugs_value,
                step=10, key="tugs_slider"
            )

        # Sync sliders (check for change and update the other)
        updated = False
        if mins != st.session_state.mins_value:
            ratio = (mins - 5) / 10.0
            st.session_state.tugs_value = int(600 - ratio * 300)
            st.session_state.mins_value = mins
            updated = True
        if tugs != st.session_state.tugs_value:
            ratio = (tugs - 300) / 300.0
            st.session_state.mins_value = int(15 - ratio * 10)
            st.session_state.tugs_value = tugs
            updated = True

        if updated:
            st.rerun()  # Single rerun if any change

        reddit_user = st.text_input("Reddit username (optional)")

        submitted = st.form_submit_button("Submit training", type="primary", width="stretch")

        if submitted:
            mins_final = st.session_state.mins_value
            tugs_final = st.session_state.tugs_value

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
            current_df = load_data()  # Fresh load (no cache)
            updated_df = pd.concat([current_df, new_row_df], ignore_index=True)

            # ─── SAVE ───
            conn.update(worksheet=0, data=updated_df)

            st.success(f"Training added for Day {current_day}!")
            st.balloons()

            # Reset sliders & go home with fresh data
            st.session_state.mins_value = 10
            st.session_state.tugs_value = 450
            st.session_state.page = "home"
            st.rerun()  # Immediate refresh

    if st.button("← Back to Dashboard"):
        st.session_state.page = "home"
        st.rerun()