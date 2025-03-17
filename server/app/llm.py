import requests
import json

class LLMService:
    def __init__(self):
        self.model_name = "llama3.2:latest"
        self.api_base = "http://localhost:11434"

    def generate_response(self, prompt, context="", max_length=512):
        """Generate response using LLaMA model with given prompt and context."""
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:"
        
        try:
            response = requests.post(
                f"{self.api_base}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "max_length": max_length
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            return result['response'].strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def get_embedding(self, text):
        """Generate embeddings for the given text using Ollama's embedding endpoint."""
        try:
            response = requests.post(
                f"{self.api_base}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                }
            )
            response.raise_for_status()
            result = response.json()
            return result['embedding']
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