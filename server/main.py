from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
import time
from llm_handler import LLMHandler
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

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--enable-javascript')
    chrome_options.add_argument('--enable-unsafe-swiftshader')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Enable JavaScript and WebGL with more permissive settings
    prefs = {
        'profile.default_content_setting_values': {
            'javascript': 1,
            'images': 1,
            'webgl': 1,
            'plugins': 1,
            'popups': 1
        },
        'profile.managed_default_content_settings': {
            'javascript': 1,
            'images': 1,
            'plugins': 1,
            'popups': 1
        }
    }
    chrome_options.add_experimental_option('prefs', prefs)
    
    # Disable automation detection
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Execute CDP commands to disable automation flags
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined })
            window.chrome = { runtime: {} }
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] })
        '''
    })
    
    return driver

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def extract_text_from_page(driver, url):
    try:
        driver.get(url)
        
        # Wait for page load and dynamic content with increased timeout
        WebDriverWait(driver, 45).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait for JavaScript to be ready
        driver.execute_script("return document.readyState") == "complete"
        
        # Wait for client-side rendering to complete
        try:
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script('return window.hasOwnProperty("__NEXT_DATA__") || window.hasOwnProperty("__NUXT__") || document.querySelector("[data-reactroot]") || document.querySelector("#__vue") || document.querySelector("#app")')
            )
        except:
            pass  # Continue if no framework-specific markers found
        
        # Wait for any loading indicators to disappear
        try:
            WebDriverWait(driver, 15).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".loading, .spinner, [role='progressbar'], .loader, #loading"))
            )
        except:
            pass
        
        # Scroll and wait for dynamic content with increased intervals
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 3
        
        while scroll_attempts < max_attempts:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Increased wait time
            
            # Calculate new scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1
        
        # Wait for network requests to complete
        time.sleep(8)  # Increased wait time
        
        # Try multiple methods to extract text
        try:
            # First try: Check for client-side rendered content
            body_text = driver.execute_script(
                "return Array.from(document.querySelectorAll('body *:not(.error-message):not(.error-container):not([class*=error]):not([id*=error])'))"
                ".filter(el => {"
                "    const style = window.getComputedStyle(el);"
                "    return el.offsetParent !== null && "
                "           style.display !== 'none' && "
                "           style.visibility !== 'hidden' && "
                "           !el.closest('.error-message, .error-container, [class*=error], [id*=error]');"
                "})"
                ".map(el => el.textContent)"
                ".filter(text => text.trim())"
                ".join(' ')"
            )
        except:
            # Fallback: Get text from specific content areas
            try:
                main_content = driver.find_elements(By.CSS_SELECTOR, "main, article, .content, #content, [role='main'], #__next, #app, #root")
                if main_content:
                    body_text = ' '.join([elem.text for elem in main_content if elem.text.strip()])
                else:
                    body_text = driver.find_element(By.TAG_NAME, "body").text
            except:
                body_text = "Unable to extract text from the page."
        
        # Check if we got error messages only
        if body_text and all(error_text in body_text.lower() for error_text in ["error", "exception", "failed"]):
            return "Unable to extract meaningful content - page appears to show only error messages."
        
        return body_text.strip() if body_text else "No visible text found on the page."
    
    except Exception as e:
        return f"Error extracting text: {str(e)}"

@app.route('/api/scrape', methods=['POST'])
def scrape_url():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data['url']
    if not is_valid_url(url):
        return jsonify({'error': 'Invalid URL format'}), 400
    
    try:
        driver = setup_driver()
        text = extract_text_from_page(driver, url)
        driver.quit()
        
        # Create new document with the scraped text
        document = Document(
            url=url,
            content=text,
            embedding=llm_service.get_embedding(text)
        )
        db.session.add(document)
        db.session.flush()

        # Process document chunks
        chunks = llm_service.chunk_text(text)
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
        
        return jsonify({
            'success': True,
            'text': text,
            'message': 'Text has been processed and stored in the database'
        })
    
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
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
        question_embedding = llm_service.get_embedding(data['question'])

        # Find most relevant chunks
        chunks = DocumentChunk.query.all()
        similarities = []
        for chunk in chunks:
            similarity = np.dot(question_embedding, chunk.embedding)
            similarities.append((similarity, chunk))

        # Sort by similarity and get top chunks
        similarities.sort(key=lambda x: x[0], reverse=True)
        print(similarities, 'similarities')
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
