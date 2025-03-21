from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from urllib.parse import urlparse
from llm_handler import LLMHandler
from app.models import db, Document, DocumentChunk, ChatHistory    
from app.llm import llm_service
from app import create_app
from langchain.document_loaders import WebBaseLoader
import numpy as np

main_bp = Blueprint('main', __name__)


app = create_app()
CORS(app)

# Global variables to store the QA chain and vector store
qa_chain = None
vector_store = None

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

@app.route('/api/scrape', methods=['POST'])
def scrape_url():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data['url']
    if not is_valid_url(url):
        return jsonify({'error': 'Invalid URL format'}), 400
    
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        text = docs[0].page_content if docs else ""
        
        # Create new document with the scraped text
        document = Document(
            url=url,
            content=text,
            embedding=llm_service.get_embedding(text)
        )
        db.session.add(document)
        db.session.flush()

        # Process document chunks
        chunks = llm_service.chunk_text(text)
        for idx, chunk in enumerate(chunks):
            chunk_embedding = llm_service.get_embedding(chunk)
            doc_chunk = DocumentChunk(
                document_id=document.id,
                content=chunk,
                embedding=chunk_embedding,
                chunk_index=idx
            )
            db.session.add(doc_chunk)

        db.session.commit()
        
        return jsonify({
            'success': True,
            'text': text,
            'message': 'Text has been processed and stored in the database'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    print("started")
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': 'Question is required'}), 400

    try:
        # Get question embedding
        question_embedding = llm_service.get_embedding(data['question'])

        # Find most relevant chunks
        chunks = DocumentChunk.query.all()
        similarities = []
        for chunk in chunks:
            similarity = np.dot(question_embedding, chunk.embedding)
            similarities.append((similarity, chunk))

        # Sort by similarity and get top chunks
        similarities.sort(key=lambda x: x[0], reverse=True)
        print(similarities, 'similarities')
        top_chunks = [chunk.content for _, chunk in similarities[:3]]
        
        context = '\n'.join(top_chunks)

        # Generate response
        answer = llm_service.generate_response(data['question'], context)

        # Save to chat history
        # chat_history = ChatHistory(
        #     question=data['question'],
        #     answer=answer,
        #     context=context
        # )
        # db.session.add(chat_history)
        # db.session.commit()

        return jsonify({
            'answer': answer,
            'context': context
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
