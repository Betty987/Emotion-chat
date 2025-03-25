import streamlit as st
from groq import Groq
from langchain_community.document_loaders import PyPDFLoader, TextLoader
import tempfile
import os

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
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Updated to your specified model
        messages=[
            {"role": "system", "content": "You are an expert literary analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    characters = {}
    response_text = response.choices[0].message.content.strip()
    for line in response_text.split("\n"):
        if ":" in line:
            name, description = line.split(":", 1)
            characters[name.strip()] = description.strip()
    return characters

# Prompting Techniques
prompt_techniques = {
    "Zero-shot": "Answer directly without examples.",
    "Chain-of-thought": "Break down reasoning step by step.",
    "Self-reflection": "Generate, critique, and refine response.",
    "Deliberate structure": "Respond in a requested format (bullets, poem, story, etc.).",
    "Multi-turn refinement": "Let the user refine their query iteratively."
}

# AI temperature settings
temperature_options = {
    "Very Dynamic": 1.0,
    "Balanced": 0.7,
    "Realistic": 0.3,
    "Historical Accuracy": 0.2
}

# Response length options
max_length_options = {
    "Concise": 50,
    "Balanced": 150,
    "In-Depth": 300
}

# Configure Groq API Key
api_key = "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"  # Your provided API key

if not api_key:
    st.error("API key not found. Please add it securely.", icon="🚫")
else:
    # Initialize Groq client
    client = Groq(api_key=api_key)

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "dialogue_styles" not in st.session_state:
        st.session_state.dialogue_styles = {}

    st.title("Timeless-Talks: Chat with Fictional Characters 🗣️ ")
    st.write("Upload a fictional text (PDF or TXT) like Harry Potter, and I’ll extract characters and their speaking styles for you to chat with!")

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

    # Display extracted characters as a string
    if st.session_state.dialogue_styles:
        characters_str = "\n".join([f"{name}: {desc}" for name, desc in st.session_state.dialogue_styles.items()])
        st.text_area("Extracted Characters", characters_str, height=150)

    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Settings")
        if not st.session_state.dialogue_styles:
            st.warning("Please upload a file to select a character.")
            character = None
        else:
            character = st.selectbox("Choose a Character:", list(st.session_state.dialogue_styles.keys()))
        prompt_technique = st.selectbox("Choose Prompting Technique:", list(prompt_techniques.keys()))
        temperature_label = st.selectbox("Select Conversational Style:", list(temperature_options.keys()))
        temperature = temperature_options[temperature_label]
        max_length_label = st.selectbox("Choose Response Length:", list(max_length_options.keys()))
        max_length = max_length_options[max_length_label]

        if character:
            st.write(f"**Character Profile:** {st.session_state.dialogue_styles[character]}")
        st.write(f"**Prompting Strategy:** {prompt_techniques[prompt_technique]}")
        st.write(f"**Response Style:** {temperature_label} ({temperature})")
        st.write(f"**Response Length:** {max_length_label} ({max_length} tokens)")

        st.session_state.learning_mode = st.checkbox("Enable Learning Mode", value=False)
        if st.session_state.learning_mode and character:
            st.write("### Speaking Style")
            st.write(st.session_state.dialogue_styles[character])

    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if st.session_state.dialogue_styles and character:
        if prompt := st.chat_input("Enter your topic or question:"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Build system prompt
            if prompt_technique == "Zero-shot":
                system_prompt = f"You are {character} from the uploaded fiction. {st.session_state.dialogue_styles[character]}"
                user_prompt = prompt
            elif prompt_technique == "Chain-of-thought":
                system_prompt = f"You are {character} from the uploaded fiction. {st.session_state.dialogue_styles[character]} Think step-by-step before answering."
                user_prompt = f"Step 1: Identify the key idea.\nStep 2: Explain using a simple analogy.\nStep 3: Give a real-world example.\n Now, answer this: {prompt}"
            elif prompt_technique == "Self-reflection":
                system_prompt = f"You are {character} from the uploaded fiction. {st.session_state.dialogue_styles[character]} First, answer. Then, review your own response and improve it."
                user_prompt = f"Initial Answer: \n\n Now reflect and improve your response: {prompt}"
            elif prompt_technique == "Deliberate structure":
                system_prompt = f"You are {character} from the uploaded fiction. {st.session_state.dialogue_styles[character]} Respond in bullet points."
                user_prompt = prompt
            elif prompt_technique == "Multi-turn refinement":
                system_prompt = f"You are {character} from the uploaded fiction. {st.session_state.dialogue_styles[character]} Ask clarifying questions before answering."
                user_prompt = f"Ask me to refine my question before you answer: {prompt}"

            # Generate AI response
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Your specified model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_length
            )

            ai_response = response.choices[0].message.content

            # Display AI response
            with st.chat_message("assistant"):
                st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
    else:
        st.info("Upload a fictional text to start chatting with its characters.")