from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import uuid

# Fix path to import 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import OrderAgent

app = Flask(__name__)
CORS(app)

agent = OrderAgent()

@app.route('/')
def home():
    return jsonify({"status": "active", "message": "Habibi Agent is running"})

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Message field is required"}), 400
    
    user_input = data.get('message')
    # Use existing session_id or create new one
    thread_id = data.get('session_id', str(uuid.uuid4()))

    try:
        response_text = agent.get_response(user_input, thread_id)
        return jsonify({
            "response": response_text,
            "session_id": thread_id
        })
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)