# frontend.py (updated user_id handling)
import streamlit as st
import requests
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://127.0.0.1:5000"

def main():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "dialogue_styles" not in st.session_state:
        st.session_state.dialogue_styles = {}
    if "last_prompt" not in st.session_state:
        st.session_state.last_prompt = None

    # User ID input - always update session state
    user_id_input = st.text_input("Enter your User ID (e.g., your name):", value="Anonymous", key="user_id_input")
    st.session_state.user_id = user_id_input  # Update user_id on every change

    st.title("Timeless-Talks: Emotion-Aware Chat with Fictional Characters 🗣️")
    st.write("Upload a fictional text (PDF or TXT), adjust emotion parameters, and chat with characters!")
    st.write("Note: Backend must be running at http://localhost:5000 (run `python backend.py`).")

    # File upload section
    uploaded_file = st.file_uploader("Upload a Fiction (PDF or TXT)", type=["pdf", "txt"])
    if uploaded_file is not None and not st.session_state.dialogue_styles:
        with st.spinner("Analyzing the text to extract characters..."):
            files = {"file": (uploaded_file.name, uploaded_file.read(), uploaded_file.type)}
            logger.debug(f"Sending upload request to {BACKEND_URL}/upload")
            try:
                response = requests.post(f"{BACKEND_URL}/upload", files=files, timeout=10)
                response.raise_for_status()
                st.session_state.dialogue_styles = response.json()["characters"]
                st.success(f"Extracted {len(st.session_state.dialogue_styles)} characters from {uploaded_file.name}")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Upload connection error: {e}")
                st.error("Cannot connect to backend for upload. Ensure `python backend.py` is running.")
            except Exception as e:
                logger.error(f"Upload error: {e}")
                st.error(f"Upload error: {str(e)}")

    if st.session_state.dialogue_styles:
        characters_str = "\n".join([f"{name}: {desc}" for name, desc in st.session_state.dialogue_styles.items()])
        st.text_area("Extracted Characters", characters_str, height=150)

    with st.sidebar:
        st.header("⚙️ Settings")
        if not st.session_state.dialogue_styles:
            st.warning("Please upload a file to select a character.")
            character = None
        else:
            character = st.selectbox("Choose a Character:", list(st.session_state.dialogue_styles.keys()))
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

    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "anger" in message:
                st.write(f"Anger: {message['anger']} | Sadness: {message['sadness']}")

    # Chat logic
    if st.session_state.dialogue_styles and character:
        prompt = st.chat_input("Enter your topic or question:", key="chat_input")
        if prompt and prompt != st.session_state.last_prompt:
            logger.debug(f"New prompt detected: {prompt}")
            st.session_state.last_prompt = prompt
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            payload = {
                "user_id": st.session_state.user_id,  # This should now be "app"
                "character": character,
                "prompt": prompt,
                "dialogue_styles": st.session_state.dialogue_styles,
                "parameters": parameters
            }
            logger.debug(f"Sending chat request to {BACKEND_URL}/chat with payload: {payload}")
            try:
                response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=10)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Received response: {data}")
                if "response" in data and "anger" in data and "sadness" in data:
                    ai_response = data["response"]
                    anger = data["anger"]
                    sadness = data["sadness"]
                    with st.chat_message("assistant"):
                        st.markdown(ai_response)
                        st.write(f"Anger: {anger} | Sadness: {sadness}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": ai_response,
                        "anger": anger,
                        "sadness": sadness
                    })
                else:
                    st.error(f"Invalid response from backend: {data}")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Chat connection error: {e}")
                st.error("Cannot connect to backend for chat. Ensure `python backend.py` is running.")
            except Exception as e:
                logger.error(f"Chat error: {e}")
                st.error(f"Chat error: {str(e)}")

if __name__ == "__main__":
    main()