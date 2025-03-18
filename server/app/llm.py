import os
from google.generativeai import GenerativeModel
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

class LLMService:
    def __init__(self):
        # Initialize Google Generative AI with API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = GenerativeModel('gemini-2.0-flash')
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def generate_response(self, prompt, context="", max_length=512):
        """Generate response using Gemini model with given prompt and context."""
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:"
        
        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    'max_output_tokens': max_length,
                    'temperature': 0.7
                }
            )
            return response.text.strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def get_embedding(self, text):
        """Generate embeddings for the given text using SentenceTransformer."""
        try:
            # Generate embeddings using SentenceTransformer
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            return f"Error generating embedding: {str(e)}"

    def chunk_text(self, text, chunk_size=512):
        """Split text into chunks for processing."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_length += len(word) + 1  # +1 for space
            if current_length > chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

# Initialize LLM service as a singleton
llm_service = LLMService()