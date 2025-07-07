import requests
from datetime import datetime

def fetch_hevy_workouts(api_key, num_workouts):
    """Fetch recent workouts from the Hevy API."""
    response = requests.get(
        f"https://api.hevyapp.com/v1/workouts?page=1&pageSize={num_workouts}",
        headers={
            'accept': 'application/json',
            'api-key': api_key
        }
    )
    data = response.json()
    return data.get('workouts', [])


def parse_workout_summary(workout):
    """Extract summary info from a workout dict."""
    workout_title = workout.get('title', 'Untitled Workout')
    start_time = workout.get('start_time')
    end_time = workout.get('end_time')
    exercises = workout.get('exercises', [])
    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    duration = round((end_dt - start_dt).total_seconds() / 60, 1)
    exercise_summaries = []
    for ex in exercises:
        ex_title = ex.get('title', 'Unnamed Exercise')
        sets = ex.get('sets', [])
        set_summaries = [f"{s.get('reps', '?')} reps @ {s.get('weight_kg', '?')} kg" for s in sets]
        ex_summary = f"- {ex_title}: " + ", ".join(set_summaries[:3]) + (" ..." if len(set_summaries) > 3 else "")
        exercise_summaries.append(f"{ex_title} ({len(sets)} sets)")
    return {
        'title': workout_title,
        'date': start_dt.strftime('%Y-%m-%d %H:%M'),
        'duration': duration,
        'exercises': exercise_summaries,
        'raw': workout
    }


def build_ai_prompt(workouts, ai_summaries, coach_persona, verbosity):
    """Build the AI prompt string for OpenAI completion."""
    persona_instructions = {
        "Motivational": "Be highly encouraging and focus on mindset, effort, and consistency.",
        "Technical": "Give detailed, technical feedback on form, technique, and training principles.",
        "Hypertrophy": "Focus on muscle growth, volume, and hypertrophy-specific advice.",
        "Endurance": "Emphasize stamina, cardiovascular improvements, and endurance training tips.",
        "Strength": "Highlight strength gains, progressive overload, and powerlifting principles."
    }
    verbosity_instructions = {
        "Short": "Keep the feedback very brief (2-3 sentences).",
        "Normal": "Keep the feedback concise and practical.",
        "Detailed": "Provide a thorough, multi-paragraph analysis with specific examples.",
        "Very Detailed": "Give an in-depth, highly detailed analysis, including technical breakdowns and actionable steps."
    }
    persona_text = persona_instructions.get(coach_persona, "Be supportive and practical.")
    verbosity_text = verbosity_instructions.get(verbosity, "Keep the feedback concise and practical.")
    return (
        f"You are an experienced personal trainer with a {coach_persona.lower()} focus. {persona_text} {verbosity_text} "
        f"Here are the user's last {len(workouts)} workouts: "
        + "; ".join(ai_summaries)
        + ". Give a motivating, clear analysis of the user's recent training, noting strengths and suggesting one actionable improvement for the next week. "
        "Focus on overall trends, and end with a suggested future workout plan. "
    )
