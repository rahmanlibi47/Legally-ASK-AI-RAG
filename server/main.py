from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from urllib.parse import urlparse
from app.models import db, Document, DocumentChunk, ChatHistory    
from app.llm import llm_service
from app import create_app
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
        from langchain.document_loaders import WebBaseLoader
        loader = WebBaseLoader(url)
        docs = loader.load()
        text = docs[0].page_content if docs else ""
        # Get embedding for full document
        # Get and validate embedding for full document
        embedding_result = llm_service.get_embedding(text)
        if embedding_result is None:
            raise ValueError("Failed to generate embedding for the main document")

        if isinstance(embedding_result, list):  # convert it safely to array
            embedding_array = np.array(embedding_result, dtype=np.float32)
        else:
            embedding_array = embedding_result  # assume it's already a NumPy array

        embedding_bytes = embedding_array.tobytes()

        # Create new document with the scraped text
        document = Document(
            url=url,
            content=text,
            embedding=embedding_bytes
        )
        db.session.add(document)
        db.session.flush()

        # Process document chunks
        chunks = llm_service.chunk_text(text)
        for idx, chunk in enumerate(chunks):
            chunk_result = llm_service.get_embedding(chunk)
            if chunk_result is None:
                raise ValueError(f"Failed to generate embedding for chunk {idx}")

            if isinstance(chunk_result, list):
                chunk_array = np.array(chunk_result, dtype=np.float32)
            else:
                chunk_array = chunk_result

            chunk_embedding = chunk_array.tobytes()

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
        print("Question embedding start")
        question_embedding = np.array(llm_service.get_embedding(data['question']))

        # Find most relevant chunks
        chunks = DocumentChunk.query.all()
        similarities = []
        print("Similars", similarities)
        for chunk in chunks:
            if isinstance(chunk.embedding, list):
                # This shouldn't happen — maybe bad legacy data?
                raise ValueError(f"Chunk {chunk.id} has list-type embedding instead of bytes")

            chunk_embedding = np.frombuffer(chunk.embedding, dtype=np.float32)
            similarity = np.dot(question_embedding, chunk_embedding)
            similarities.append((similarity, chunk))


        print(similarities, 'similarities')
        # Sort by similarity and get top chunks
        similarities.sort(key=lambda x: x[0], reverse=True)
       
        top_chunks = [chunk.content for _, chunk in similarities[:3]]
        
        context = '\n'.join(top_chunks)

        # Generate response
        answer = llm_service.generate_response(data['question'], context)

        # Save to chat history
        chat_history = ChatHistory(
            question=data['question'],
            answer=answer,
            context=context
        )
        db.session.add(chat_history)
        db.session.commit()

        return jsonify({
            'answer': answer,
            'context': context
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
