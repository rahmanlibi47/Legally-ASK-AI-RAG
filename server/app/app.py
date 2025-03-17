from flask import Flask, request, jsonify
from llm import llm_service

app = Flask(__name__)

@app.route('/api/query', methods=['POST'])
def query():
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({'error': 'No prompt provided'}), 400
    
    prompt = data['prompt']
    context = data.get('context', '')
    max_length = data.get('max_length', 512)
    
    response = llm_service.generate_response(prompt, context, max_length)
    return jsonify({'response': response})

@app.route('/api/embed', methods=['POST'])
def embed():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    text = data['text']
    embedding = llm_service.get_embedding(text)
    return jsonify({'embedding': embedding})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)