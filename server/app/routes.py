from flask import Blueprint, request, jsonify
from .models import db, Document, DocumentChunk, ChatHistory
from .llm import llm_service
import numpy as np
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/process_document', methods=['POST'])
def process_document():
    data = request.get_json()
    if not data or 'url' not in data or 'content' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Create new document
        document = Document(
            url=data['url'],
            content=data['content'],
            embedding=llm_service.get_embedding(data['content'])
        )
        db.session.add(document)
        db.session.flush()

        # Process document chunks
        chunks = llm_service.chunk_text(data['content'])
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
        return jsonify({'message': 'Document processed successfully', 'document_id': document.id})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@main_bp.route('/chat_history', methods=['GET'])
def get_chat_history():
    try:
        history = ChatHistory.query.order_by(ChatHistory.created_at.desc()).all()
        return jsonify([
            {
                'id': h.id,
                'question': h.question,
                'answer': h.answer,
                'created_at': h.created_at.isoformat()
            } for h in history
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500