from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import openai
import uuid

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")  # Update with your MongoDB URI
db = client["query_optimization"]
queries_collection = db["queries"]

# OpenAI API Key (Replace with your actual key)
openai.api_key = "your_openai_api_key"


# Function to generate system message with Auto-Priming
def generate_system_message(user_query):
    priming_prompt = f"Analyze the following query and determine the industry or domain it belongs to: {user_query}\nProvide only the industry name."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": priming_prompt}],
        max_tokens=50
    )
    industry = response["choices"][0]["message"]["content"].strip()

    return f"You are an expert in {industry}. Provide professional and accurate responses."


# Route to process user query
@app.route("/process_query", methods=["POST"])
def process_query():
    data = request.json
    user_query = data.get("query")

    if not user_query:
        return jsonify({"error": "Query is required"}), 400

    # Generate system message
    system_message = generate_system_message(user_query)

    # Generate response using OpenAI
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_query}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=500
    )

    optimized_response = response["choices"][0]["message"]["content"].strip()

    # Save to MongoDB
    query_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()
    query_data = {
        "query_id": query_id,
        "timestamp": timestamp,
        "user_query": user_query,
        "optimized_response": optimized_response
    }
    queries_collection.insert_one(query_data)

    return jsonify({"query_id": query_id, "response": optimized_response})


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)