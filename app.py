import streamlit as st
import requests
from openai import OpenAI
from datetime import datetime

# Load secrets
openai_api_key = st.secrets["api_keys"]["openai"]
hevy_api_key = st.secrets["api_keys"]["hevy"]

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

# App layout
st.set_page_config(page_title="Hevy Chat Analyzer", page_icon="💪", layout="centered")
st.title("💪 Hevy Chat Analyzer")

st.markdown(
    "Fetch your latest **Hevy workout** and receive an **AI-powered personalized analysis** "
    "to improve your training instantly."
)

if st.button("🚀 Fetch & Analyze Latest Workout"):
    with st.spinner("Fetching your latest workout from Hevy..."):
        response = requests.get(
            "https://api.hevyapp.com/v1/workouts?page=1&pageSize=5",
            headers={
                'accept': 'application/json',
                'api-key': hevy_api_key
            }
        )
        data = response.json()

    if data:
        workout = data['workouts'][0] # using your provided structure
        # st.write(workout)
        workout_title = workout.get('title', 'Untitled Workout')
        start_time = workout.get('start_time')
        end_time = workout.get('end_time')
        exercises = workout.get('exercises', [])

        # Format readable date and duration
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        duration = round((end_dt - start_dt).total_seconds() / 60, 1)

        st.success("✅ Workout fetched successfully!")
        st.subheader("📋 Workout Summary")
        st.markdown(f"**Title:** {workout_title}")
        st.markdown(f"**Date:** {start_dt.strftime('%Y-%m-%d %H:%M')}")
        st.markdown(f"**Duration:** {duration} min")
        st.markdown("**Exercises Performed:**")

        # Display exercises with set summaries
        exercise_summaries = []
        for ex in exercises:
            ex_title = ex.get('title', 'Unnamed Exercise')
            sets = ex.get('sets', [])
            set_summaries = [f"{s.get('reps', '?')} reps @ {s.get('weight_kg', '?')} kg" for s in sets]
            ex_summary = f"- **{ex_title}**: " + ", ".join(set_summaries[:3]) + (" ..." if len(set_summaries) > 3 else "")
            st.markdown(ex_summary)
            exercise_summaries.append(f"{ex_title} ({len(sets)} sets)")

        # Optional JSON for debugging
        with st.expander("🔍 View Raw JSON (optional)"):
            st.json(workout)

        # Generate AI analysis
        exercise_list_str = ", ".join(exercise_summaries[:6])
        prompt = (
            f"You are an experienced personal trainer. A user completed a workout titled '{workout_title}' "
            f"on {start_dt.strftime('%Y-%m-%d')} with the following exercises: {exercise_list_str}. "
            f"Provide a motivating, clear analysis of the workout, noting strengths and suggesting one actionable improvement for next time. "
            f"Keep the feedback short, practical, and encouraging."
        )

        with st.spinner("Analyzing workout with AI..."):
            completion = client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}]
            )
            analysis = completion.choices[0].message.content

        st.success("✅ AI Analysis Ready!")
        st.subheader("🤖 Your Personalized AI Feedback")
        st.markdown(analysis)

    else:
        st.error("❌ No workout data received. Please check your Hevy API key or your recent workouts.")

st.markdown("---")
st.caption("Built with ❤️ using Streamlit, Hevy, and ChatGPT.")
