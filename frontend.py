# # frontend.py (updated user_id handling)
# import streamlit as st
# import requests
# import logging

# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# BACKEND_URL = "http://127.0.0.1:5000"

# def main():
#     if "messages" not in st.session_state:
#         st.session_state.messages = []
#     if "dialogue_styles" not in st.session_state:
#         st.session_state.dialogue_styles = {}
#     if "last_prompt" not in st.session_state:
#         st.session_state.last_prompt = None

#     # User ID input - always update session state
#     user_id_input = st.text_input("Enter your User ID (e.g., your name):", value="Anonymous", key="user_id_input")
#     st.session_state.user_id = user_id_input  # Update user_id on every change

#     st.title("Emotion-Aware Chat with Fictional Characters💬 ")
#     st.write("Upload a fictional text (PDF or TXT), adjust emotion parameters, and chat with characters!")
    

#     # File upload section
#     uploaded_file = st.file_uploader("Upload a Fiction (PDF or TXT)", type=["pdf", "txt"])
#     if uploaded_file is not None and not st.session_state.dialogue_styles:
#         with st.spinner("Analyzing the text to extract characters..."):
#             files = {"file": (uploaded_file.name, uploaded_file.read(), uploaded_file.type)}
#             logger.debug(f"Sending upload request to {BACKEND_URL}/upload")
#             try:
#                 response = requests.post(f"{BACKEND_URL}/upload", files=files, timeout=10)
#                 response.raise_for_status()
#                 st.session_state.dialogue_styles = response.json()["characters"]
#                 st.success(f"Extracted {len(st.session_state.dialogue_styles)} characters from {uploaded_file.name}")
#             except requests.exceptions.ConnectionError as e:
#                 logger.error(f"Upload connection error: {e}")
#                 st.error("Cannot connect to backend for upload. Ensure `python backend.py` is running.")
#             except Exception as e:
#                 logger.error(f"Upload error: {e}")
#                 st.error(f"Upload error: {str(e)}")

#     if st.session_state.dialogue_styles:
#         characters_str = "\n".join([f"{name}: {desc}" for name, desc in st.session_state.dialogue_styles.items()])
#         st.text_area("Extracted Characters", characters_str, height=150)

#     with st.sidebar:
#         st.header("⚙️ Settings")
#         if not st.session_state.dialogue_styles:
#             st.warning("Please upload a file to select a character.")
#             character = None
#         else:
#             character = st.selectbox("Choose a Character:", list(st.session_state.dialogue_styles.keys()))
#         valence = st.slider("Valence", min_value=1, max_value=7, value=4, step=1)
#         arousal = st.slider("Arousal", min_value=1, max_value=7, value=4, step=1)
#         selection_threshold = st.slider("Selection Threshold", min_value=1, max_value=7, value=4, step=1)
#         resolution = st.slider("Resolution Level", min_value=1, max_value=7, value=4, step=1)
#         goal_directedness = st.slider("Goal-Directedness", min_value=1, max_value=7, value=4, step=1)
#         securing_rate = st.slider("Securing Rate", min_value=1, max_value=7, value=4, step=1)
#         parameters = {
#             "valence": valence,
#             "arousal": arousal,
#             "selection_threshold": selection_threshold,
#             "resolution_level": resolution,
#             "goal_directedness": goal_directedness,
#             "securing_rate": securing_rate
#         }

#     # Display messages
#     for message in st.session_state.messages:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])
#             if message["role"] == "assistant" and "anger" in message:
#                 st.write(f"Anger: {message['anger']} | Sadness: {message['sadness']}")

#     # Chat logic
#     if st.session_state.dialogue_styles and character:
#         prompt = st.chat_input("Enter your topic or question:", key="chat_input")
#         if prompt and prompt != st.session_state.last_prompt:
#             logger.debug(f"New prompt detected: {prompt}")
#             st.session_state.last_prompt = prompt
#             st.session_state.messages.append({"role": "user", "content": prompt})
#             with st.chat_message("user"):
#                 st.markdown(prompt)

#             payload = {
#                 "user_id": st.session_state.user_id,  # This should now be "app"
#                 "character": character,
#                 "prompt": prompt,
#                 "dialogue_styles": st.session_state.dialogue_styles,
#                 "parameters": parameters
#             }
#             logger.debug(f"Sending chat request to {BACKEND_URL}/chat with payload: {payload}")
#             try:
#                 response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=10)
#                 response.raise_for_status()
#                 data = response.json()
#                 logger.debug(f"Received response: {data}")
#                 if "response" in data and "anger" in data and "sadness" in data:
#                     ai_response = data["response"]
#                     anger = data["anger"]
#                     sadness = data["sadness"]
#                     with st.chat_message("assistant"):
#                         st.markdown(ai_response)
#                         st.write(f"Anger: {anger} | Sadness: {sadness}")
#                     st.session_state.messages.append({
#                         "role": "assistant",
#                         "content": ai_response,
#                         "anger": anger,
#                         "sadness": sadness
#                     })
#                 else:
#                     st.error(f"Invalid response from backend: {data}")
#             except requests.exceptions.ConnectionError as e:
#                 logger.error(f"Chat connection error: {e}")
#                 st.error("Cannot connect to backend for chat. Ensure `python backend.py` is running.")
#             except Exception as e:
#                 logger.error(f"Chat error: {e}")
#                 st.error(f"Chat error: {str(e)}")

# if __name__ == "__main__":
#     main()
# frontend.py (beautified UI with fictional character theme)
import streamlit as st
import requests
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://127.0.0.1:5000"

# Custom CSS for fictional theme
st.markdown("""
    <style>
    /* Background and general styling */
    .stApp {
        background: linear-gradient(to bottom right, #1a1a3d, #2e2e5e);
        color: #e6e6fa;
        font-family: 'Georgia', serif;
    }
    /* Title styling */
    h1 {
        color: #ffd700;
        text-align: center;
        font-size: 2.5em;
        text-shadow: 2px 2px 4px #000000;
    }
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #2e2e5e;
        border-right: 2px solid #ffd700;
    }
    .stSlider > div > div > div > div {
        background-color: #ffd700;
    }
    /* Chat message styling */
    .stChatMessage {
        border-radius: 10px;
        margin: 10px 0;
        padding: 15px;
    }
    .stChatMessage.user {
        background-color: #483d8b;
        border: 2px solid #ffd700;
    }
    .stChatMessage.assistant {
        background-color: #6a5acd;
        border: 2px solid #e6e6fa;
    }
    /* Buttons and inputs */
    .stButton > button {
        background-color: #ffd700;
        color: #1a1a3d;
        border-radius: 8px;
    }
    .stTextInput > div > input {
        background-color: #e6e6fa;
        color: #1a1a3d;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "dialogue_styles" not in st.session_state:
        st.session_state.dialogue_styles = {}
    if "last_prompt" not in st.session_state:
        st.session_state.last_prompt = None

    # Header with fictional flair
    st.title("🌟 MythicWhispers: Chat with Legends 🌟")
    st.markdown("Step into a realm of fiction—upload a tale, tune the emotions, and converse with its heroes and villains!")

    # User ID input with a mystical twist
    user_id_input = st.text_input("📜 Your Name in the Saga:", value="Anonymous", key="user_id_input", help="Who are you in this story?")
    st.session_state.user_id = user_id_input

    # Main layout with containers
    main_container = st.container()
    with main_container:
        # File upload with a thematic touch
        uploaded_file = st.file_uploader("📖 Unveil a Fictional Tome (PDF or TXT)", type=["pdf", "txt"], help="Share a story to summon its characters!")
        if uploaded_file is not None and not st.session_state.dialogue_styles:
            with st.spinner("🔮 Scrying the text for characters..."):
                files = {"file": (uploaded_file.name, uploaded_file.read(), uploaded_file.type)}
                logger.debug(f"Sending upload request to {BACKEND_URL}/upload")
                try:
                    response = requests.post(f"{BACKEND_URL}/upload", files=files, timeout=10)
                    response.raise_for_status()
                    st.session_state.dialogue_styles = response.json()["characters"]
                    st.success(f"✨ Summoned {len(st.session_state.dialogue_styles)} characters from {uploaded_file.name}!")
                except requests.exceptions.ConnectionError as e:
                    logger.error(f"Upload connection error: {e}")
                    st.error("🚫 The arcane connection failed. Ensure the backend ritual (`python backend.py`) is active!")
                except Exception as e:
                    logger.error(f"Upload error: {e}")
                    st.error(f"⚠️ Error in the spell: {str(e)}")

        # Display extracted characters in an expander
        if st.session_state.dialogue_styles:
            with st.expander("📜 The Cast of Legends", expanded=True):
                characters_str = "\n".join([f"**{name}**: {desc}" for name, desc in st.session_state.dialogue_styles.items()])
                st.markdown(characters_str)

    # Sidebar for settings with a mystical vibe
    with st.sidebar:
        st.header("⚙️ Enchantments")
        if not st.session_state.dialogue_styles:
            st.warning("📖 No tale has been woven yet—upload a story to summon characters!")
            character = None
        else:
            character = st.selectbox("Choose Your Companion:", list(st.session_state.dialogue_styles.keys()), help="Pick a soul from the story!")
        
        # Emotional sliders with thematic labels
        valence = st.slider("🌞 Joy (Valence)", min_value=1, max_value=7, value=4, step=1, help="How bright is their spirit?")
        arousal = st.slider("⚡ Energy (Arousal)", min_value=1, max_value=7, value=4, step=1, help="How spirited are they?")
        selection_threshold = st.slider("🎯 Focus (Selection Threshold)", min_value=1, max_value=7, value=4, step=1, help="How sharp is their gaze?")
        resolution = st.slider("🧠 Insight (Resolution Level)", min_value=1, max_value=7, value=4, step=1, help="How deep do they ponder?")
        goal_directedness = st.slider("🏹 Purpose (Goal-Directedness)", min_value=1, max_value=7, value=4, step=1, help="How driven are they?")
        securing_rate = st.slider("🛡️ Caution (Securing Rate)", min_value=1, max_value=7, value=4, step=1, help="How guarded are they?")
        parameters = {
            "valence": valence,
            "arousal": arousal,
            "selection_threshold": selection_threshold,
            "resolution_level": resolution,
            "goal_directedness": goal_directedness,
            "securing_rate": securing_rate
        }

    # Chat section with character avatars
    chat_container = st.container()
    with chat_container:
        st.markdown("### 📜 The Great Discourse")
        for message in st.session_state.messages:
            # Assign avatars based on role
            avatar = "🧙‍♂️" if message["role"] == "user" else "👑"  # User as wizard, assistant as royalty
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])
                if message["role"] == "assistant" and "anger" in message:
                    st.markdown(f"🔥 **Anger**: {message['anger']} | 😢 **Sadness**: {message['sadness']}")

        # Chat input with fictional prompt
        if st.session_state.dialogue_styles and character:
            prompt = st.chat_input(f"Speak to {character}:", key="chat_input")
            if prompt and prompt != st.session_state.last_prompt:
                logger.debug(f"New prompt detected: {prompt}")
                st.session_state.last_prompt = prompt
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user", avatar="👤"):
                    st.markdown(prompt)

                payload = {
                    "user_id": st.session_state.user_id,
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
                        with st.chat_message("assistant", avatar="🧙‍♂️"):
                            st.markdown(ai_response)
                            st.markdown(f"😡 **Anger**: {anger} | 😢 **Sadness**: {sadness}")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": ai_response,
                            "anger": anger,
                            "sadness": sadness
                        })
                    else:
                        st.error(f"🚫 Scroll of Error: {data}")
                except requests.exceptions.ConnectionError as e:
                    logger.error(f"Chat connection error: {e}")
                    st.error("🚫 The ethereal link is broken. Ensure `python backend.py` is conjured!")
                except Exception as e:
                    logger.error(f"Chat error: {e}")
                    st.error(f"⚠️ Mystic Mishap: {str(e)}")

if __name__ == "__main__":
    main()