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
    "Fetch your latest **Hevy workouts** and receive an **AI-powered personalized analysis** "
    "to improve your training instantly."
)

# New: Let user choose how many workouts to fetch
num_workouts = st.number_input(
    "How many recent workouts to analyze?", min_value=1, max_value=20, value=5, step=1
)

if st.button("🚀 Fetch & Analyze Workouts"):
    with st.spinner(f"Fetching your last {num_workouts} workouts from Hevy..."):
        response = requests.get(
            f"https://api.hevyapp.com/v1/workouts?page=1&pageSize={num_workouts}",
            headers={
                'accept': 'application/json',
                'api-key': hevy_api_key
            }
        )
        data = response.json()

    if data and data.get('workouts'):
        workouts = data['workouts']
        summaries = []
        ai_summaries = []
        for i, workout in enumerate(workouts):
            workout_title = workout.get('title', 'Untitled Workout')
            start_time = workout.get('start_time')
            end_time = workout.get('end_time')
            exercises = workout.get('exercises', [])
            # Format readable date and duration
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            duration = round((end_dt - start_dt).total_seconds() / 60, 1)
            exercise_summaries = []
            for ex in exercises:
                ex_title = ex.get('title', 'Unnamed Exercise')
                sets = ex.get('sets', [])
                set_summaries = [f"{s.get('reps', '?')} reps @ {s.get('weight_kg', '?')} kg" for s in sets]
                ex_summary = f"- **{ex_title}**: " + ", ".join(set_summaries[:3]) + (" ..." if len(set_summaries) > 3 else "")
                exercise_summaries.append(f"{ex_title} ({len(sets)} sets)")
            # For display
            summaries.append({
                'title': workout_title,
                'date': start_dt.strftime('%Y-%m-%d %H:%M'),
                'duration': duration,
                'exercises': exercise_summaries,
                'raw': workout
            })
            # For AI prompt
            ai_summaries.append(
                f"'{workout_title}' on {start_dt.strftime('%Y-%m-%d')}: " + ", ".join(exercise_summaries[:6])
            )
        st.success(f"✅ {len(workouts)} Workouts fetched successfully!")
        st.subheader("📋 Workouts Summary")
        for i, s in enumerate(summaries):
            st.markdown(f"**{i+1}. {s['title']}**  ")
            st.markdown(f"Date: {s['date']} | Duration: {s['duration']} min")
            st.markdown("Exercises: " + ", ".join(s['exercises']))
            with st.expander(f"🔍 View Raw JSON for Workout {i+1} (optional)"):
                st.json(s['raw'])
        # AI prompt for all workouts
        ai_prompt = (
            f"You are an experienced personal trainer. Here are the user's last {len(workouts)} workouts: "
            + "; ".join(ai_summaries)
            + ". Give a motivating, clear analysis of the user's recent training, noting strengths and suggesting one actionable improvement for the next week. "
            "Keep the feedback short, practical, and encouraging. Focus on overall trends, and end with a suggested future workout plan. "
        )
        with st.spinner("Analyzing workouts with AI..."):
            completion = client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": ai_prompt}]
            )
            analysis = completion.choices[0].message.content
        st.success("✅ AI Analysis Ready!")
        st.subheader("🤖 Your Personalized AI Feedback")
        st.markdown(analysis)
    else:
        st.error("❌ No workout data received. Please check your Hevy API key or your recent workouts.")

st.markdown("---")
