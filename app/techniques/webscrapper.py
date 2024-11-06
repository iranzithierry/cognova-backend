import re
import time
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel
from Levenshtein import ratio
from app.utils import compress_text
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import (
    MarkdownifyTransformer,
    Html2TextTransformer,
)

class ScrappedURL(BaseModel):
    status: int
    content: str
    url: str
    content_length: int
    content_hash: str
    content_type: str
    metadata: dict
    sync_time: float

def clean_text(content: str, hostname: str) -> str:
    cleaned = content.replace("(/", f"(https://{hostname}/").split(")[")
    cleaned = ")\n[".join(cleaned)
    compressed = compress_text(cleaned)
    return compressed

class WebScraper:
    def __init__(
        self,
        scrapper_path: Path = Path("../../bin/scrapper"),
        similarity_threshold: float = 0.7
    ):
        """Initialize WebScraper with a cache directory and similarity threshold."""
        self.scrapper_path = scrapper_path
        self.similarity_threshold = similarity_threshold
        self.scraped_contents: List[str] = []  # Store previously scraped contents

    def _generate_hash(self, content: str) -> str:
        """Generate MD5 hash for content to create unique cache keys."""
        return hashlib.md5(content.encode()).hexdigest()

    def _get_content_type(self, format: str):
        return {
            "md": "text/markdown",
            "txt": "text/txt",
        }.get(format, f"text/{format}")

    def _is_content_similar(self, new_content: str) -> bool:
        """
        Check if the new content is similar to any previously scraped content
        using Levenshtein distance ratio.
        """
        for existing_content in self.scraped_contents:
            similarity = ratio(new_content, existing_content)
            if similarity >= self.similarity_threshold:
                return True
        return False

    def scrape(self, urls: str, format="txt") -> List[Dict[str, ScrappedURL]]:
        """
        Scrape web pages and return structured content, skipping similar content.
        """
        time_started = time.time()
        loader = AsyncHtmlLoader(urls)
        html_content = loader.load()
        scrapped_content: List[Dict[str, ScrappedURL]] = []

        try:
            if format == "md":
                md = MarkdownifyTransformer()
                urls_content = md.transform_documents(html_content)
            else:
                ht = Html2TextTransformer()
                urls_content = ht.transform_documents(html_content)

            for url in urls_content:
                content = url.page_content
                current_url: str = url.metadata["source"]
                content = clean_text(content=content, hostname=current_url.split("/")[2])

                # Skip if content is too similar to previously scraped content
                if self._is_content_similar(content):
                    print(f"Skipping {current_url} - Similar content already scraped")
                    continue

                # Add to scraped contents if it's unique enough
                self.scraped_contents.append(content)
                
                content_type = self._get_content_type(format)
                content_hash = self._generate_hash(content)

                scrapped_content.append({
                    "status": 200,
                    "content": content,
                    "url": current_url,
                    "content_length": len(content),
                    "content_hash": content_hash,
                    "content_type": content_type,
                    "metadata": url.metadata,
                    "sync_time": time.time() - time_started,
                })

            return scrapped_content

        except Exception as e:
            print(f"Unexpected error scraping: {str(e)}")
            return [{
                "status": 500,
            }]

    def list_links(self, url: str) -> list:
        """List all links found at the URL using external scrapper"""
        try:
            cmd = [self.scrapper_path, "list", url, "--limit=6", "--threads=3"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
            links = url_pattern.findall(result.stdout)
            
            links_set = set()
            unique_links = []
            
            for link in links:
                if link not in links_set:
                    links_set.add(link)
                    unique_links.append(link)
                    
            return unique_links

        except subprocess.CalledProcessError as e:
            print(f"Error listing links from {url}: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error listing links from {url}: {str(e)}")
            return []