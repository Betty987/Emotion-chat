from flask import Flask, request, jsonify
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader, TextLoader
import tempfile
import os
from config import API_KEY
from database import init_db, save_message, search_user_history

app = Flask(__name__)
client = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.7, api_key=API_KEY)

class EmotionalModel:
    def __init__(self):
        self.parameters = {
            "valence": 4,
            "arousal": 4,
            "selection_threshold": 4,
            "resolution_level": 4,
            "goal_directedness": 4,
            "securing_rate": 4
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

emotional_model = EmotionalModel()

def extract_text_from_file(file_content, file_type):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type.split('/')[-1]}") as tmp_file:
        tmp_file.write(file_content)
        tmp_file_path = tmp_file.name
    
    try:
        if file_type == "application/pdf":
            loader = PyPDFLoader(tmp_file_path)
        elif file_type == "text/plain":
            loader = TextLoader(tmp_file_path)
        else:
            raise ValueError("Unsupported file type")
        
        documents = loader.load()
        text = "\n".join(doc.page_content for doc in documents)
        return text
    finally:
        os.unlink(tmp_file_path)

def extract_characters_from_text(text):
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

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    text = extract_text_from_file(file.read(), file.content_type)
    characters = extract_characters_from_text(text)
    return jsonify({"characters": characters})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_id = data.get("user_id")
    character = data.get("character")
    prompt = data.get("prompt")
    dialogue_styles = data.get("dialogue_styles")
    parameters = data.get("parameters")

    if not all([user_id, character, prompt, dialogue_styles]):
        return jsonify({"error": "Missing required fields"}), 400

    # Update emotional model
    emotional_model.update_parameters(parameters)

    # Save user message
    save_message(user_id, character, "user", prompt, 0, 0)

    # Calculate emotions
    anger = emotional_model.calculate_anger()
    sadness = emotional_model.calculate_sadness()

    # Check for user mention in prompt
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

    # Build system prompt
    if anger >= 4:
        system_prompt = (
            f"You are {character} from the uploaded fiction. {dialogue_styles[character]} "
            "You are irritated and impatient. Respond with short, direct, and sometimes sarcastic remarks. "
            "Let the user know you're angry in your response. {memory_context}"
        )
    elif sadness >= 4:
        system_prompt = (
            f"You are {character} from the uploaded fiction. {dialogue_styles[character]} "
            "You are melancholic and sorrowful. Speak slowly and thoughtfully, with a deep, reflective tone. "
            "Let the user know you're feeling down in your response. {memory_context}"
        )
    else:
        system_prompt = f"You are {character} from the uploaded fiction. {dialogue_styles[character]} {memory_context}"

    # Generate response
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    response = client.invoke(input=messages)
    ai_response = response.content

    # Save assistant message
    save_message(user_id, character, "assistant", ai_response, anger, sadness)

    return jsonify({"response": ai_response, "anger": anger, "sadness": sadness})

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)