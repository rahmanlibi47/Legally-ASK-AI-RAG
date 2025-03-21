from datetime import datetime
from . import db
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, PickleType
from sqlalchemy.orm import relationship

class Document(db.Model):
    __tablename__ = 'document'
    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(PickleType)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    context = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    document = relationship('Document', backref='chat_history')

class DocumentChunk(db.Model):
    __tablename__ = 'document_chunk'
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(PickleType)
    chunk_index = Column(Integer)
    document = relationship('Document', backref='chunks')