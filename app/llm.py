from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import torch
import numpy as np

class LLMService:
    def __init__(self):
        self.model_path = "meta-llama/Llama-2-7b-chat-hf"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, local_files_only=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            local_files_only=True
        )
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def get_embedding(self, text):
        """Generate embeddings for the given text."""
        return self.embedding_model.encode(text)

    def generate_response(self, prompt, context="", max_length=512):
        """Generate response using LLaMA model with given prompt and context."""
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:"
        
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.split("Answer:")[-1].strip()

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