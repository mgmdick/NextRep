import streamlit as st
from openai import OpenAI
from utils import fetch_hevy_workouts, parse_workout_summary, build_ai_prompt

# Load secrets
openai_api_key = st.secrets["api_keys"]["openai"]

# Secure Hevy API key input (default to your secret, but user can override)
default_hevy_key = st.secrets["api_keys"]["hevy"] if "api_keys" in st.secrets and "hevy" in st.secrets["api_keys"] else ""
hevy_api_key = st.text_input(
    "Enter your Hevy API key (leave as default for Matt)",
    value=default_hevy_key,
    type="password",
    help="Your key is only used for this session and never stored."
)

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

# App layout
st.set_page_config(page_title="Matt's Hevy Analyzer", page_icon="💪", layout="wide")
# Mobile-friendly CSS tweaks
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
        max-width: 100vw;
    }
    .stButton>button, .stTextInput>div>input {
        min-height: 48px;
        font-size: 1.1rem;
    }
    .stExpanderHeader {
        font-size: 1.1rem;
    }
    @media (max-width: 600px) {
        .block-container {
            padding-left: 0.2rem;
            padding-right: 0.2rem;
        }
        .stExpanderHeader {
            font-size: 1rem;
        }
        .stButton>button, .stTextInput>div>input {
            min-height: 44px;
            font-size: 1rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("💪 Matt's Hevy Analyzer")
st.markdown(
    "Fetch Matt's latest **Hevy workouts** and receive an **AI-powered personalized analysis** "
    "to improve your training instantly."
)

# New: Let user choose how many workouts to fetch
num_workouts = st.number_input(
    "How many recent workouts to analyze?", min_value=1, max_value=20, value=5, step=1
)

# Coach persona selection
coach_persona = st.selectbox(
    "Choose your coach's focus:",
    [
        "Motivational",
        "Technical",
        "Hypertrophy",
        "Endurance",
        "Strength"
    ],
    index=0,
    help="Select the style and focus of your AI feedback."
)

# Advanced config for answer verbosity/detail
with st.expander("⚙️ Advanced Config", expanded=False):
    verbosity = st.selectbox(
        "Answer verbosity/detail:",
        ["Short", "Normal", "Detailed", "Very Detailed"],
        index=1,
        help="Control how much detail the AI gives in its feedback."
    )

if st.button("🚀 Fetch & Analyze Workouts"):
    with st.spinner(f"Fetching your last {num_workouts} workouts from Hevy..."):
        workouts = fetch_hevy_workouts(hevy_api_key, num_workouts)
    if workouts:
        summaries = [parse_workout_summary(w) for w in workouts]
        ai_summaries = [
            f"'{s['title']}' on {s['date'].split()[0]}: " + ", ".join(s['exercises'][:6])
            for s in summaries
        ]
        st.success(f"✅ {len(workouts)} Workouts fetched successfully!")
        st.subheader("🤖 Your Personalized AI Feedback")
        ai_prompt = build_ai_prompt(workouts, ai_summaries, coach_persona, verbosity)
        with st.spinner("Analyzing workouts with AI..."):
            completion = client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": ai_prompt}]
            )
            analysis = completion.choices[0].message.content
        st.session_state['workouts'] = summaries
        st.session_state['analysis'] = analysis
        st.session_state['last_analysis'] = analysis
        st.session_state['chat_history'] = [
            {"role": "assistant", "content": analysis}
        ]
    else:
        st.error("❌ No workout data received. Please check your Hevy API key or your recent workouts.")

# Only show AI/chat/workouts if analysis exists in session_state
if 'analysis' in st.session_state:
    st.subheader("🤖 Your Personalized AI Feedback")
    st.markdown(st.session_state['analysis'])
    st.markdown("---")
    st.subheader("💬 Continue the Conversation")
    # Handle chat input and response before rendering chat history
    user_input = st.chat_input("Ask a follow-up question about your workouts...", key="workout_chat")
    if user_input:
        # Only process if this is a new message
        if 'last_user_input' not in st.session_state or st.session_state['last_user_input'] != user_input:
            st.session_state['chat_history'].append({"role": "user", "content": user_input})
            with st.spinner("AI is thinking..."):
                chat_response = client.chat.completions.create(
                    model="gpt-4.1-nano",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state['chat_history']]
                )
                ai_reply = chat_response.choices[0].message.content
            st.session_state['chat_history'].append({"role": "assistant", "content": ai_reply})
            st.session_state['last_user_input'] = user_input
    # Now render the full chat history (including new response)
    for msg in st.session_state['chat_history']:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**AI:** {msg['content']}")
    st.markdown("---")
    # Collapse the workouts summary in an expander
    with st.expander("📋 Workouts Summary", expanded=False):
        for i, s in enumerate(st.session_state['workouts']):
            st.markdown(f"**{i+1}. {s['title']}**  ")
            st.markdown(f"Date: {s['date']} | Duration: {s['duration']} min")
            st.markdown("Exercises: " + ", ".join(s['exercises']))
            with st.expander(f"🔍 View Raw JSON for Workout {i+1} (optional)"):
                st.json(s['raw'])
