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
            print("response", response)
            response.raise_for_status()
            result = response.json()
            
            if 'embedding' not in result:
                raise ValueError("No embedding found in API response")
                
            import numpy as np
            embedding = np.array(result['embedding'], dtype=np.float32)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return None

    def chunk_text(self, text, chunk_size=512):
        """Split text into semantically meaningful chunks for processing.
        Args:
            text (str): The input text to be chunked
            chunk_size (int): Target size for each chunk in characters
        Returns:
            list: List of text chunks
        """
        # Split into paragraphs first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            # Split paragraph into sentences (simple approach)
            sentences = [s.strip() for s in paragraph.split('.') if s.strip()]
            
            for sentence in sentences:
                sentence = sentence.strip() + '.'
                sentence_length = len(sentence)
                
                # If single sentence exceeds chunk size, split by words
                if sentence_length > chunk_size:
                    words = sentence.split()
                    temp_chunk = []
                    temp_length = 0
                    
                    for word in words:
                        word_length = len(word) + 1  # +1 for space
                        if temp_length + word_length > chunk_size:
                            chunks.append(' '.join(temp_chunk))
                            temp_chunk = [word]
                            temp_length = word_length
                        else:
                            temp_chunk.append(word)
                            temp_length += word_length
                    
                    if temp_chunk:
                        chunks.append(' '.join(temp_chunk))
                    continue
                
                # Check if adding this sentence would exceed chunk size
                if current_length + sentence_length > chunk_size and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [sentence]
                    current_length = sentence_length
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_length
        
        # Add any remaining text
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

# Initialize LLM service as a singleton
llm_service = LLMService()