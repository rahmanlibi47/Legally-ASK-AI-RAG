from langchain.document_loaders import UnstructuredURLLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
import asyncio
import aiohttp
import time

class WebScraper:
    def __init__(self, max_workers: int = 5, timeout: int = 30):
        self.max_workers = max_workers
        self.timeout = timeout
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    async def _fetch_url_content(self, url: str) -> Optional[str]:
        """Asynchronously fetch content from a single URL."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                loader = WebBaseLoader(url, client=session)
                documents = await loader.aload()
                return documents[0].page_content if documents else None
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None

    async def scrape_urls(self, urls: List[str]) -> List[str]:
        """Scrape multiple URLs concurrently and return their content."""
        tasks = [self._fetch_url_content(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    def process_content(self, content: str) -> List[str]:
        """Process and split the scraped content into chunks."""
        return self.text_splitter.split_text(content)

    def scrape_and_process(self, urls: List[str]) -> List[str]:
        """Main method to scrape URLs and process their content."""
        start_time = time.time()
        
        # Run async scraping in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        contents = loop.run_until_complete(self.scrape_urls(urls))
        loop.close()
        
        # Process contents in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            chunks = list(executor.map(self.process_content, contents))
        
        # Flatten the chunks list
        all_chunks = [chunk for sublist in chunks for chunk in sublist]
        
        print(f"Scraped and processed {len(urls)} URLs in {time.time() - start_time:.2f} seconds")
        return all_chunks