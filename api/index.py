# api/index.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# --- PATH CONFIGURATION FOR VERCEL ---
# Add the parent directory to sys.path so we can import from 'core'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Now we can import our organized logic
from core.agent import OrderAgent

app = Flask(__name__)
CORS(app) # Allow cross-origin requests from your frontend

# Initialize the agent logic
agent = OrderAgent()

@app.route('/')
def home():
    return jsonify({"status": "active", "message": "Order Agent API is running"})

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    
    # 1. Validation
    if not data or 'message' not in data:
        return jsonify({"error": "Message field is required"}), 400

    user_input = data.get('message')

    try:
        # 2. Call the isolated agent logic
        response_text = agent.get_response(user_input)
        
        # 3. Return JSON
        return jsonify({"response": response_text})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Required for local testing (python api/index.py)
if __name__ == '__main__':
    app.run(debug=True, port=5000)