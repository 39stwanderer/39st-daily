import streamlit as st
from datetime import datetime
from utils.data import load_data, save_data, get_current_day
import pandas as pd

def main():
    df = load_data()
    current_day = get_current_day(df)

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

        st.subheader("Intensity Settings")

        # Initialize defaults
        if 'mins_value' not in st.session_state:
            st.session_state.mins_value = 10
        if 'tugs_value' not in st.session_state:
            st.session_state.tugs_value = 450

        col1, col2 = st.columns(2)

        with col1:
            mins = st.slider(
                "Clamped time (minutes)",
                5, 15, st.session_state.mins_value,
                step=1, key="add_mins"
            )

        with col2:
            tugs = st.slider(
                "Number of tugs",
                300, 600, st.session_state.tugs_value,
                step=10, key="add_tugs"
            )

        # Two-way sync
        if mins != st.session_state.mins_value:
            ratio = (mins - 5) / 10
            st.session_state.tugs_value = int(600 - ratio * 300)
            st.session_state.mins_value = mins
            st.rerun()

        if tugs != st.session_state.tugs_value:
            ratio = (tugs - 300) / 300
            st.session_state.mins_value = int(15 - ratio * 10)
            st.session_state.tugs_value = tugs
            st.rerun()

        reddit_user = st.text_input("Reddit username (optional)")

        submitted = st.form_submit_button("Submit training", type="primary", use_container_width=True)

        if submitted:
            with st.spinner("Saving training to Google Sheets... Please wait ⏳"):
                try:
                    new_row = {
                        "Day": current_day,
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Clamp Type": clamp,
                        "Minutes": st.session_state.mins_value,
                        "Tugs": st.session_state.tugs_value,
                        "Reddit Username": reddit_user.strip(),
                        "Status": "Pending",
                        "Notes": ""
                    }

                    # Make sure df is the latest before appending
                    df = load_data()   # ← reload fresh just before save (important!)

                    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(updated_df)

                    st.success(f"Training added for Day {current_day}!")
                    st.balloons()

                    # Reset sliders
                    st.session_state.mins_value = 10
                    st.session_state.tugs_value = 450

                    # Navigate away only after success
                    st.switch_page("pages/home.py")

                except Exception as e:
                    st.error(f"Failed to save training: {e}")
                    st.exception(e)   # shows traceback in expander — good for debugging



if __name__ == "__main__":
    main()