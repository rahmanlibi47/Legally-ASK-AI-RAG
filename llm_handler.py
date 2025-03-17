import numpy as np
from typing import List, Dict, Any
import faiss
from transformers import AutoTokenizer, AutoModel
import torch
from nltk.tokenize import sent_tokenize
import nltk
nltk.download('punkt_tab')
import os
from dotenv import load_dotenv
from google.generativeai import GenerativeModel
from google.generativeai import configure

# Load environment variables
load_dotenv()

# Configure Google Generative AI with API key
configure(api_key=os.getenv('GEMINI_API_KEY'))

class LLMHandler:
    def __init__(self):
        # Initialize the tokenizer and model for embeddings
        self.tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
        self.model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
        
        # Initialize FAISS index for vector storage
        self.embedding_dim = 384  # Dimension of embeddings from MiniLM
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Store text chunks and their embeddings
        self.text_chunks: List[str] = []
        self.conversation_history: List[Dict[str, str]] = []
        
    def chunk_text(self, text: str, max_chunk_size: int = 512) -> List[str]:
        """Split text into chunks based on sentences."""
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.encode(sentence))
            if current_size + sentence_tokens > max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_size += sentence_tokens
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a text chunk using the model."""
        inputs = self.tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Use mean pooling to get text embedding
        attention_mask = inputs['attention_mask']
        token_embeddings = outputs.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        embedding = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        
        return embedding.numpy()
    
    def add_text_to_index(self, text: str):
        """Process text and add its chunks to the vector store."""
        chunks = self.chunk_text(text)
        for chunk in chunks:
            embedding = self.generate_embedding(chunk)
            self.index.add(embedding)
            self.text_chunks.append(chunk)
    
    def find_relevant_chunks(self, query: str, k: int = 3) -> List[str]:
        """Find the most relevant text chunks for a query."""
        query_embedding = self.generate_embedding(query)
        D, I = self.index.search(query_embedding, k)
        return [self.text_chunks[i] for i in I[0] if i < len(self.text_chunks)]
    
    def query_llm(self, prompt: str, context: str = "") -> str:
        """Query the Gemini model with prompt and context."""
        model = GenerativeModel('gemini-2.0-flash')
        
        try:
            prompt_text = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:"
            response = model.generate_content(prompt_text)
            return response.text
        except Exception as e:
            return f"Error querying Gemini API: {str(e)}"
    
    def process_query(self, query: str) -> str:
        """Process a query using relevant context and conversation history."""
        # Find relevant chunks
        relevant_chunks = self.find_relevant_chunks(query)
        context = '\n'.join(relevant_chunks)
        
        # Build conversation context
        conv_context = '\n'.join([f"{msg['role']}: {msg['content']}" 
                                 for msg in self.conversation_history[-5:]])
        
        # Combine all context
        full_context = f"Previous conversation:\n{conv_context}\n\nRelevant information:\n{context}"
        
        # Get response from LLM
        response = self.query_llm(query, full_context)
        
        # Update conversation history
        self.conversation_history.extend([
            {"role": "user", "content": query},
            {"role": "assistant", "content": response}
        ])
        
        return response
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
