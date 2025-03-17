from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import LlamaCpp
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from transformers import AutoTokenizer
# Global variables to store the QA chain and vector store
qa_chain = None
vector_store = None

def create_vector_store(text):
    # Initialize tokenizer for token-aware text splitting
    tokenizer = AutoTokenizer.from_pretrained("all-MiniLM-L6-v2")
    
    # Preprocess text more efficiently
    import re
    text = re.sub(r'[\r\n\t]+', ' ', text)  # Replace newlines and tabs with spaces
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = re.sub(r'[^\w\s.,!?-]', '', text)  # Remove special characters
    text = text.strip()
    
    # Use RecursiveCharacterTextSplitter for better token handling
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )
    chunks = text_splitter.split_text(text)
    
    # Create embeddings using a lightweight model
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Create vector store with optimized parameters
    vector_store = FAISS.from_texts(
        texts=chunks,
        embedding=embeddings,
        metadatas=[{"chunk": i} for i in range(len(chunks))]
    )
    return vector_store

def setup_qa_chain(vector_store):
    # Initialize the LLaMA model with optimized parameters
    llm = LlamaCpp(
        model_path="models/llama-2-7b-chat.gguf",
        temperature=0.3,
        max_tokens=256,
        top_p=0.9,
        verbose=False,
        n_ctx=512,
        n_batch=8,
    )
    
    # Setup memory with token limit
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        max_token_limit=150
    )
    
    # Create the conversational chain with optimized settings
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 2}),
        memory=memory,
        return_source_documents=True,
        max_tokens_limit=200,
    )
    
    return qa_chain

def ask_question(qa_chain, question):
    try:
        # Preprocess question
        question = question.strip()
        if len(question) > 200:  # Limit question length
            question = question[:200]
        
        result = qa_chain({"question": question})
        return result["answer"]
    except Exception as e:
        return f"Error processing question: {str(e)}"