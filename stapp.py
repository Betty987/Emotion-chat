import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader, TextLoader
import tempfile
import os
import sqlite3
from datetime import datetime

# Emotional Model Class
class EmotionalModel:
    def __init__(self):
        self.parameters = {
            "valence": 4,  # Default: neutral
            "arousal": 4,  # Default: neutral
            "selection_threshold": 4,  # Default: neutral
            "resolution_level": 4,  # Default: neutral
            "goal_directedness": 4,  # Default: neutral
            "securing_rate": 4,  # Default: neutral
        }

    def update_parameters(self, new_parameters):
        self.parameters.update(new_parameters)

    def calculate_anger(self):
        arousal = self.parameters["arousal"]
        valence = self.parameters["valence"]
        selection_threshold = self.parameters["selection_threshold"]
        anger = (arousal + (7 - valence) + selection_threshold) / 3
        return min(max(int(anger), 1), 5)

    def calculate_sadness(self):
        arousal = self.parameters["arousal"]
        valence = self.parameters["valence"]
        goal_directedness = self.parameters["goal_directedness"]
        sadness = ((7 - arousal) + (7 - valence) + (7 - goal_directedness)) / 3
        return min(max(int(sadness), 1), 5)

# Database Setup
def init_db():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  character TEXT,
                  role TEXT,
                  content TEXT,
                  anger INTEGER,
                  sadness INTEGER,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

# Save message to database
def save_message(user_id, character, role, content, anger, sadness):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute("INSERT INTO conversations (user_id, character, role, content, anger, sadness, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (user_id, character, role, content, anger, sadness, timestamp))
    conn.commit()
    conn.close()

# Retrieve conversation history for a specific user
def get_user_history(user_id):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("SELECT role, content, anger, sadness, timestamp FROM conversations WHERE user_id = ? ORDER BY timestamp", (user_id,))
    history = c.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1], "anger": row[2], "sadness": row[3], "timestamp": row[4]} for row in history]

# Search for a user’s past interactions by name or ID
def search_user_history(search_term):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("SELECT user_id, character, content, timestamp FROM conversations WHERE user_id LIKE ? OR content LIKE ? ORDER BY timestamp",
              (f"%{search_term}%", f"%{search_term}%"))
    results = c.fetchall()
    conn.close()
    return [{"user_id": row[0], "character": row[1], "content": row[2], "timestamp": row[3]} for row in results]

# Function to extract text from a file using LangChain loaders
def extract_text_from_file(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.type.split('/')[-1]}") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name
    
    try:
        if uploaded_file.type == "application/pdf":
            loader = PyPDFLoader(tmp_file_path)
        elif uploaded_file.type == "text/plain":
            loader = TextLoader(tmp_file_path)
        else:
            raise ValueError("Unsupported file type")
        
        documents = loader.load()
        text = "\n".join(doc.page_content for doc in documents)
        return text
    finally:
        os.unlink(tmp_file_path)

# Function to extract characters and styles using Groq API
def extract_characters_from_text(text, client):
    text_chunk = text[:10000] if len(text) > 10000 else text
    prompt = f"""
    You are an expert literary analyst. Given the following fictional text, identify the major characters and infer their speaking styles based on their dialogue, actions, and descriptions. For each character, provide a name and a concise description of their speaking style (e.g., "Harry Potter: Curious, brave, and straightforward"). Return the result as a list of "Name: Description" pairs. Here's the text:

    {text_chunk}
    """
    response = client.invoke(input=prompt)
    characters = {}
    for line in response.content.strip().split("\n"):
        if ":" in line:
            name, description = line.split(":", 1)
            characters[name.strip()] = description.strip()
    return characters

# Configure Groq API Key
api_key = "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"
if not api_key:
    st.error("API key not found. Please add it securely.", icon="🚫")
else:
    client = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.7, api_key=api_key)
    init_db()  # Initialize database

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []  # Start fresh, no pre-loading from DB
    if "dialogue_styles" not in st.session_state:
        st.session_state.dialogue_styles = {}
    if "emotional_model" not in st.session_state:
        st.session_state.emotional_model = EmotionalModel()
    if "user_id" not in st.session_state:
        st.session_state.user_id = st.text_input("Enter your User ID (e.g., your name):", "Anonymous")

    st.title("Emotion-Aware Chat with Fictional Characters 🗣️")
    st.write("Upload a fictional text (PDF or TXT), adjust emotion parameters, and chat with characters!")

    # File upload section
    uploaded_file = st.file_uploader("Upload a Fiction (PDF or TXT)", type=["pdf", "txt"])
    if uploaded_file is not None and not st.session_state.dialogue_styles:
        with st.spinner("Analyzing the text to extract characters..."):
            try:
                text = extract_text_from_file(uploaded_file)
                st.session_state.dialogue_styles = extract_characters_from_text(text, client)
                st.success(f"Extracted {len(st.session_state.dialogue_styles)} characters from {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

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

        # Update emotional model parameters
        new_parameters = {
            "valence": valence,
            "arousal": arousal,
            "selection_threshold": selection_threshold,
            "resolution_level": resolution,
            "goal_directedness": goal_directedness,
            "securing_rate": securing_rate
        }
        st.session_state.emotional_model.update_parameters(new_parameters)

        if character:
            st.write(f"**Character Profile:** {st.session_state.dialogue_styles[character]}")
        st.write(f"**Valence:** {valence}")
        st.write(f"**Arousal:** {arousal}")
        st.write(f"**Selection Threshold:** {selection_threshold}")
        st.write(f"**Resolution Level:** {resolution}")
        st.write(f"**Goal-Directedness:** {goal_directedness}")
        st.write(f"**Securing Rate:** {securing_rate}")

    # Display current session messages only (no pre-loading from DB)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "anger" in message and "sadness" in message:
                st.write(f"Anger: {message['anger']} | Sadness: {message['sadness']}")

    # User input and chat logic
    if st.session_state.dialogue_styles and character:
        if prompt := st.chat_input("Enter your topic or question:"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            save_message(st.session_state.user_id, character, "user", prompt, 0, 0)

            # Calculate emotional states
            anger = st.session_state.emotional_model.calculate_anger()
            sadness = st.session_state.emotional_model.calculate_sadness()

            # Check for user mention in prompt (e.g., "Do you know Birhanu Worku?")
            search_term = None
            if "do you know" in prompt.lower():
                search_term = prompt.lower().split("do you know")[-1].strip().rstrip("?")
                past_interactions = search_user_history(search_term)
                if past_interactions:
                    memory_context = "I recall past interactions: " + "; ".join(
                        [f"{i['character']} said '{i['content']}' to {i['user_id']} on {i['timestamp']}" for i in past_interactions[:3]]
                    )
                else:
                    memory_context = f"I don’t recall anyone named '{search_term}' from past interactions."
            else:
                memory_context = ""

            # Build system prompt based on emotional state
            if anger >= 4:
                system_prompt = (
                    f"You are {character} from the uploaded fiction. {st.session_state.dialogue_styles[character]} "
                    "You are irritated and impatient. Respond with short, direct, and sometimes sarcastic remarks. "
                    "Let the user know you're angry in your response. {memory_context}"
                )
            elif sadness >= 4:
                system_prompt = (
                    f"You are {character} from the uploaded fiction. {st.session_state.dialogue_styles[character]} "
                    "You are melancholic and sorrowful. Speak slowly and thoughtfully, with a deep, reflective tone. "
                    "Let the user know you're feeling down in your response. {memory_context}"
                )
            else:
                system_prompt = f"You are {character} from the uploaded fiction. {st.session_state.dialogue_styles[character]} {memory_context}"

            # Generate character response
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            response = client.invoke(input=messages)
            ai_response = response.content

            # Display AI response with emotions
            with st.chat_message("assistant"):
                st.markdown(ai_response)
                st.write(f"Anger: {anger} | Sadness: {sadness}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": ai_response,
                "anger": anger,
                "sadness": sadness
            })
            save_message(st.session_state.user_id, character, "assistant", ai_response, anger, sadness)
    else:
        st.info("Upload a fictional text to start chatting with its characters.")