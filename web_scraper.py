from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
import time

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
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
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        time.sleep(2)
        
        body_text = driver.find_element(By.TAG_NAME, "body").text
        return body_text.strip()
    
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def main():
    print("Web Scraper Started")
    print("Enter 'quit' to exit the program")
    
    try:
        driver = setup_driver()
        
        while True:
            url = input("\nEnter the URL to scrape: ").strip()
            
            if url.lower() == 'quit':
                break
            
            if not is_valid_url(url):
                print("Invalid URL format. Please enter a valid URL.")
                continue
            
            print("\nExtracting text from the webpage...")
            text = extract_text_from_page(driver, url)
            print("\nExtracted Text:")
            print("-" * 50)
            print(text)
            print("-" * 50)
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        if 'driver' in locals():
            driver.quit()
        print("\nWeb Scraper terminated.")

if __name__ == "__main__":
    main()