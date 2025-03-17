from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import LlamaCpp
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

def create_vector_store(text):
    # Split the text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    
    # Create embeddings using a lightweight model
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Create vector store
    vector_store = FAISS.from_texts(chunks, embeddings)
    return vector_store

def setup_qa_chain(vector_store):
    # Initialize the LLaMA model
    llm = LlamaCpp(
        model_path="models/llama-2-7b-chat.gguf",
        temperature=0.7,
        max_tokens=2000,
        top_p=1,
        verbose=True,
    )
    
    # Setup memory for conversation history
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # Create the conversational chain
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        memory=memory,
        return_source_documents=True,
    )
    
    return qa_chain

def ask_question(qa_chain, question):
    try:
        result = qa_chain({"question": question})
        return result["answer"]
    except Exception as e:
        return f"Error processing question: {str(e)}"

def main():
    print("Terms and Conditions Q&A System")
    print("Enter 'quit' to exit")
    
    # Get the scraped text from main.py
    from main import setup_driver, extract_text_from_page
    
    url = input("Enter the URL of the Terms and Conditions page: ").strip()
    
    try:
        # Setup and get text
        driver = setup_driver()
        text = extract_text_from_page(driver, url)
        driver.quit()
        
        print("\nCreating vector store...")
        vector_store = create_vector_store(text)
        
        print("Setting up QA chain...")
        qa_chain = setup_qa_chain(vector_store)
        
        print("\nReady for questions!")
        
        while True:
            question = input("\nEnter your question (or 'quit' to exit): ").strip()
            
            if question.lower() == 'quit':
                break
            
            answer = ask_question(qa_chain, question)
            print("\nAnswer:")
            print("-" * 50)
            print(answer)
            print("-" * 50)
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()