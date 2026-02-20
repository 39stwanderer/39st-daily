import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ─── Simple login (only for slave to edit) ───
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.session_state.logged_in = True
    st.rerun()

def logout():
    st.session_state.logged_in = False
    st.rerun()

# Load from secrets (will raise error if missing → good for debugging)
SLAVE_USERNAME = st.secrets["slave_login"]["username"]
SLAVE_PASSWORD = st.secrets["slave_login"]["password"]

# ─── Connect to Google Sheet ───
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)  # refresh every 5 min
def load_data():
    df = conn.read(worksheet=0, usecols=[0,1,2,3,4,5,6,7], header=0)
    if df.empty:
        df = pd.DataFrame(columns=["Day", "Timestamp", "Clamp Type", "Minutes", "Tugs", "Reddit Username", "Status", "Notes"])
    df["Day"] = pd.to_numeric(df["Day"], errors='coerce').fillna(0).astype(int)
    return df.sort_values("Day", ascending=False)

df = load_data()

# ─── Calculate stats for dashboard ───
completed = df[df["Status"] == "Completed"]
total_completed = len(completed)
clamp_counts = completed["Clamp Type"].value_counts()
avg_mins = completed["Minutes"].mean() if not completed.empty else 0
avg_tugs = completed["Tugs"].mean() if not completed.empty else 0

max_day = df["Day"].max() if not df.empty else 0
current_day = max_day + 1   # Next day to assign

# ─── Sidebar navigation ───
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Add Daily Training"])

if page == "Home":
    st.title("Slave Daily Training Dashboard")

    # Fun facts section
    st.subheader("Fun Stats")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Completed Tasks", total_completed)
    col2.metric("Avg Clamped Time", f"{avg_mins:.1f} min" if avg_mins else "—")
    col3.metric("Avg Tugs", f"{avg_tugs:.0f}" if avg_tugs else "—")

    st.subheader("Clamp Type Breakdown")
    st.bar_chart(clamp_counts)

    st.subheader("All Tasks")
    st.dataframe(df.style.apply(lambda row: ['background: lightgreen' if row["Status"] == "Completed" else '' for _ in row], axis=1))

    if not st.session_state.logged_in:
        with st.expander("Slave Login (to update statuses)"):
            uname = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            if st.button("Login"):
                if uname == SLAVE_USERNAME and pwd == SLAVE_PASSWORD:
                    login()
                else:
                    st.error("Wrong credentials")
    else:
        st.success("Logged in as Slave")
        if st.button("Logout"):
            logout()

        st.subheader("Edit Tasks (Slave only)")
        edit_day = st.number_input("Select Day to edit", min_value=1, value=current_day, step=1)
        edit_row = df[df["Day"] == edit_day]
        if not edit_row.empty:
            row = edit_row.iloc[0]
            new_mins = st.number_input("New Minutes (can only increase or keep)", min_value=int(row["Minutes"]), value=int(row["Minutes"]))
            new_tugs = st.number_input("New Tugs (can only increase or keep)", min_value=int(row["Tugs"]), value=int(row["Tugs"]))
            new_status = st.selectbox("Status", ["Pending", "Completed", "Archived"], index=["Pending", "Completed", "Archived"].index(row["Status"]))
            notes = st.text_input("Notes", value=row.get("Notes", ""))

            if st.button("Update Task"):
                idx = df[df["Day"] == edit_day].index[0]
                df.at[idx, "Minutes"] = new_mins
                df.at[idx, "Tugs"] = new_tugs
                df.at[idx, "Status"] = new_status
                df.at[idx, "Notes"] = notes
                conn.update(worksheet=0, data=df)
                st.success("Updated!")
                st.rerun()
        else:
            st.info("No task for this day yet.")

elif page == "Add Daily Training":
    st.title(f"Add Daily Training - Day {current_day}")

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

    with st.form("add_task"):
        clamp = st.selectbox("Choose clamp type", clamp_types)

        col1, col2 = st.columns(2)
        use_time = col1.toggle("Apply Time (clamped minutes)", value=True)
        use_tugs = col2.toggle("Apply Tugs", value=False)

        mins = 0
        tugs = 0

        if use_time:
            mins = st.slider("Clamped time (minutes)", 5, 15, 10)

        if use_tugs:
            # Inverse: more tugs for shorter time
            tug_slider = st.slider("Intensity (higher = more tugs, shorter effective time)", 300, 600, 450)
            tugs = tug_slider

        reddit_user = st.text_input("Your Reddit username (optional)")

        submitted = st.form_submit_button("Submit to Sir")

        if submitted:
            if not use_time and not use_tugs:
                st.error("Select at least Time or Tugs!")
            else:
                # Prepare the new row as a dict
                new_row_dict = {
                    "Day": current_day,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Clamp Type": clamp,
                    "Minutes": mins,
                    "Tugs": tugs,
                    "Reddit Username": reddit_user,
                    "Status": "Pending",
                    "Notes": ""
                }

                # Convert to 1-row DataFrame
                new_row_df = pd.DataFrame([new_row_dict])

                # Load current data (already have df = load_data(), but refresh it here to be safe)
                current_df = load_data()  # or conn.read(...) directly if you prefer

                # Append the new row
                updated_df = pd.concat([current_df, new_row_df], ignore_index=True)

                # Write back the full updated sheet
                conn.update(worksheet=0, data=updated_df)

                st.success(f"Added for Day {current_day}! Sir will review.")
                st.balloons()

                # Optional: Force reload stats/table on home page by clearing cache or rerunning
                load_data.clear()  # clears the cache so next load_data() fetches fresh
                st.rerun()  # or just let user navigate back to home