from techxmodule.core import Tools
from techxmodule.utils import json_to_xml
from duckduckgo_search import DDGS


import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy import signals
from scrapy.signalmanager import dispatcher
from bs4 import BeautifulSoup
import re

import boto3, json


@Tools.tool("retrieve", "data")
def browsing_web(search_term):
    """
    Function to retrieve links and topics from internet browser
    """
    result = ""
    for i in DDGS().text(search_term, max_results=5):
        result += json_to_xml(i)
    return result
    
    
@Tools.tool("retrieve", "data")
def browsing_video(search_term):
    return json_to_xml(DDGS().videos(
        keywords=search_term,
        region="wt-wt",
        safesearch="off",
        timelimit="w",
        resolution="high",
        duration=None,
        max_results=1))

    
@Tools.tool("retrieve", "data")
def browsing_map(
        search_term: str, 
        place: str,
        street: str | None = None,
        city: str | None = None,
        county: str | None = None,
        state: str | None = None,
        country: str | None = None,
        postalcode: str | None = None,
        latitude: str | None = None,
        longitude: str | None = None,
        radius: int = 5,
        max_results: int = 5):
    result = ""
    for i in DDGS().maps(
            search_term,
            place,
            street,
            city,
            county,
            state,
            country,
            postalcode,
            latitude,
            longitude,
            radius,
            max_results):
        result += json_to_xml(i)
    return result


class WebpageSpider(scrapy.Spider):
    name = 'webpage_spider'
    
    def __init__(self, url=None, max_pages=5, *args, **kwargs):
        super(WebpageSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url]
        self.max_pages = max_pages
        self.pages_crawled = 0

    def parse(self, response):
        self.pages_crawled += 1
        yield {'url': response.url, 'content': response.text}

        if self.pages_crawled < self.max_pages:
            links = response.css('a::attr(href)').getall()
            for link in links:
                if link.startswith('/'):
                    yield response.follow(link, self.parse)


from bs4 import BeautifulSoup
import re

def clean_html(content):
    soup = BeautifulSoup(content, 'html.parser')
    
    # Remove unwanted tags
    for tag in soup(['script', 'style', 'svg', 'noscript']):
        tag.decompose()
    
    # Remove all attributes except href for links
    for tag in soup.find_all():
        if tag.name == 'a' and tag.has_attr('href'):
            tag.attrs = {}
        else:
            tag.attrs = {}
    
    # Convert the soup back to a string
    cleaned_html = str(soup.body) if soup.body else str(soup)
    
    # Remove extra whitespace
    cleaned_html = re.sub(r'\s+', ' ', cleaned_html).strip()
    
    # Remove empty tags
    cleaned_html = re.sub(r'<[^>]*>\s*</[^>]*>', '', cleaned_html)
    
    return cleaned_html

@Tools.tool("retrieve", "data")
def scrape_webpage(url, max_pages=5):
    results = []

    def crawler_results(signal, sender, item, response, spider):
        results.append(item)

    dispatcher.connect(crawler_results, signal=signals.item_passed)

    process = CrawlerProcess(settings={
        'LOG_LEVEL': 'ERROR',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    process.crawl(WebpageSpider, url=url, max_pages=max_pages)
    process.start()
    
    if results:
        all_content = '\n\n'.join([clean_html(item['content']) for item in results])
        return all_content
    else:
        return None

if __name__ == "__main__":
    url = "https://en.wikipedia.org/wiki/Boeing_777"
    content = scrape_webpage(url)
    print(content)