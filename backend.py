

from flask import Flask, request, jsonify
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader, TextLoader
import tempfile
import os
from database import save_message, get_user_history, search_user_history
from textblob import TextBlob  # For sentiment analysis
from config import API_KEY


app = Flask(__name__)

# Configure Groq API Key
api_key = API_KEY
client = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.7, api_key=api_key)

# Emotional Model Class
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

    def adjust_from_sentiment(self, text):
        # Analyze sentiment of the user's input
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 (negative) to 1 (positive)
        
        # Adjust valence and arousal based on sentiment
        if polarity < -0.3:  # Negative sentiment (e.g., annoying)
            self.parameters["valence"] = max(1, self.parameters["valence"] - 2)  # Lower valence (more negative)
            self.parameters["arousal"] = min(7, self.parameters["arousal"] + 2)  # Higher arousal (more intense)
        elif polarity > 0.3:  # Positive sentiment (e.g., happy)
            self.parameters["valence"] = min(7, self.parameters["valence"] + 2)  # Higher valence (more positive)
            self.parameters["arousal"] = min(7, self.parameters["arousal"] + 1)  # Slightly higher arousal
        # Neutral sentiment (polarity between -0.3 and 0.3) leaves parameters unchanged

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

    def calculate_joy(self):
        valence = self.parameters["valence"]
        arousal = self.parameters["arousal"]
        securing_rate = self.parameters["securing_rate"]
        joy = (valence + arousal + securing_rate) / 3
        return min(max(int(joy), 1), 5)

# Global instances
emotional_model = EmotionalModel()
dialogue_styles = {}

def extract_text_from_file(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.mimetype.split('/')[-1]}") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name
    try:
        if uploaded_file.mimetype == "application/pdf":
            loader = PyPDFLoader(tmp_file_path)
        elif uploaded_file.mimetype == "text/plain":
            loader = TextLoader(tmp_file_path)
        else:
            raise ValueError("Unsupported file type")
        documents = loader.load()
        return "\n".join(doc.page_content for doc in documents)
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
            characters[name.strip("1234567890. *")] = description.strip()
    return characters

@app.route("/upload", methods=["POST"])
def upload_file():
    global dialogue_styles
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    try:
        text = extract_text_from_file(file)
        dialogue_styles = extract_characters_from_text(text)
        return jsonify({"characters": dialogue_styles}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_id = data.get("user_id", "Anonymous")
    character = data.get("character")
    prompt = data.get("prompt")
    parameters = data.get("parameters", {})

    if not character or not prompt or character not in dialogue_styles:
        return jsonify({"error": "Invalid character or prompt"}), 400

    # Update emotional model with slider parameters
    emotional_model.update_parameters(parameters)

    # Adjust emotional state based on sentiment of user's prompt
    emotional_model.adjust_from_sentiment(prompt)

    # Calculate emotional states
    anger = emotional_model.calculate_anger()
    sadness = emotional_model.calculate_sadness()
    joy = emotional_model.calculate_joy()

    # Retrieve recent history
    history = get_user_history(user_id)
    recent_history = [h for h in history if h["character"] == character][-3:]
    memory_context = "Here’s what we’ve talked about recently: " + "; ".join(
        [f"{h['role']}: {h['content']} (Anger: {h['anger']}, Sadness: {h['sadness']}, Joy: {h['joy']})" 
         for h in recent_history]
    ) if recent_history else "We haven’t chatted much yet!"

    # Check for "Do you know" query
    if "do you know" in prompt.lower():
        search_term = prompt.lower().split("do you know")[-1].strip().rstrip("?")
        past_interactions = search_user_history(search_term)
        if past_interactions:
            memory_context += " I also recall: " + "; ".join(
                [f"{i['character']} said '{i['content']}' to {i['user_id']} on {i['timestamp']}" 
                 for i in past_interactions[:3]]
            )
        else:
            memory_context += f" I don’t recall anyone named '{search_term}' from past interactions."

    # Build system prompt
    if anger >= 4:
        system_prompt = (
            f"You are {character} from the uploaded fiction. {dialogue_styles[character]} "
            "You are irritated and impatient. Respond with short, direct, and sometimes sarcastic remarks. "
            f"Let the user know you're angry in your response. {memory_context}"
        )
    elif sadness >= 4:
        system_prompt = (
            f"You are {character} from the uploaded fiction. {dialogue_styles[character]} "
            "You are melancholic and sorrowful. Speak slowly and thoughtfully, with a deep, reflective tone. "
            f"Let the user know you're feeling down in your response. {memory_context}"
        )
    elif joy >= 4:
        system_prompt = (
            f"You are {character} from the uploaded fiction. {dialogue_styles[character]} "
            "You are cheerful and excited. Respond with enthusiasm, positivity, and an upbeat tone. "
            f"Let the user know you're joyful in your response. {memory_context}"
        )
    else:
        system_prompt = f"You are {character} from the uploaded fiction. {dialogue_styles[character]} {memory_context}"

    # Generate response
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
    response = client.invoke(input=messages)
    ai_response = response.content

    # Save to database
    save_message(user_id, character, "user", prompt, 0, 0, 0)
    save_message(user_id, character, "assistant", ai_response, anger, sadness, joy)

    return jsonify({
        "response": ai_response,
        "anger": anger,
        "sadness": sadness,
        "joy": joy
    }), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
