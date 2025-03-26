
import streamlit as st
import requests
from database import init_db

# Backend API URL
BACKEND_URL = "http://127.0.0.1:5000"

# Initialize database
init_db()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "dialogue_styles" not in st.session_state:
    st.session_state.dialogue_styles = {}
if "user_id" not in st.session_state:
    st.session_state.user_id = "Anonymous"

# User ID input
user_id_input = st.text_input("Enter your User ID (e.g., your name):", value=st.session_state.user_id, key="user_id_input")
if user_id_input != st.session_state.user_id:
    st.session_state.user_id = user_id_input

st.title("Emotion-Aware Chat with Fictional Characters 💬")
st.write("Upload a fictional text (PDF or TXT), adjust emotion parameters, and chat with characters!")

# File upload section
uploaded_file = st.file_uploader("Upload a Fiction (PDF or TXT)", type=["pdf", "txt"])
if uploaded_file is not None and not st.session_state.dialogue_styles:
    with st.spinner("Analyzing the text to extract characters..."):
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        response = requests.post(f"{BACKEND_URL}/upload", files=files)
        if response.status_code == 200:
            st.session_state.dialogue_styles = response.json()["characters"]
            st.success(f"Extracted {len(st.session_state.dialogue_styles)} characters from {uploaded_file.name}")
        else:
            st.error(f"Error processing file: {response.json().get('error', 'Unknown error')}")

# Display extracted characters
if st.session_state.dialogue_styles:
    characters_str = "\n".join([f"{name}: {desc}" for name, desc in st.session_state.dialogue_styles.items()])
    st.text_area("Extracted Characters", characters_str, height=150)

# Sidebar settings with sliders
with st.sidebar:
    st.header("⚙️ Settings")
    if not st.session_state.dialogue_styles:
        st.warning("Please upload a file to select a character.")
        character = None
    else:
        character = st.selectbox("Choose a Character:", list(st.session_state.dialogue_styles.keys()))

    # Add sliders (1-7 scale)
    valence = st.slider("Valence", min_value=1, max_value=7, value=4, step=1)
    arousal = st.slider("Arousal", min_value=1, max_value=7, value=4, step=1)
    selection_threshold = st.slider("Selection Threshold", min_value=1, max_value=7, value=4, step=1)
    resolution = st.slider("Resolution Level", min_value=1, max_value=7, value=4, step=1)
    goal_directedness = st.slider("Goal-Directedness", min_value=1, max_value=7, value=4, step=1)
    securing_rate = st.slider("Securing Rate", min_value=1, max_value=7, value=4, step=1)

    parameters = {
        "valence": valence,
        "arousal": arousal,
        "selection_threshold": selection_threshold,
        "resolution_level": resolution,
        "goal_directedness": goal_directedness,
        "securing_rate": securing_rate
    }

    if character:
        st.write(f"**Character Profile:** {st.session_state.dialogue_styles[character]}")
    st.write(f"**Valence:** {valence}")
    st.write(f"**Arousal:** {arousal}")
    st.write(f"**Selection Threshold:** {selection_threshold}")
    st.write(f"**Resolution Level:** {resolution}")
    st.write(f"**Goal-Directedness:** {goal_directedness}")
    st.write(f"**Securing Rate:** {securing_rate}")

# Display current session messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "anger" in message and "sadness" in message and "joy" in message:
            st.write(f" Anger: {message['anger']} |  Sadness: {message['sadness']} |  Joy: {message['joy']}")

# User input and chat logic
if st.session_state.dialogue_styles and character:
    if prompt := st.chat_input("Enter your topic or question:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Send request to backend
        payload = {
            "user_id": st.session_state.user_id,
            "character": character,
            "prompt": prompt,
            "parameters": parameters
        }
        response = requests.post(f"{BACKEND_URL}/chat", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data["response"]
            anger = data["anger"]
            sadness = data["sadness"]
            joy = data["joy"]

            with st.chat_message("assistant"):
                st.markdown(ai_response)
                st.write(f"😡Anger: {anger} | 😢 Sadness: {sadness} | 😀 Joy: {joy}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": ai_response,
                "anger": anger,
                "sadness": sadness,
                "joy": joy
            })
        else:
            st.error(f"Error: {response.json().get('error', 'Unknown error')}")
else:
    st.info("Upload a fictional text to start chatting with its characters.")