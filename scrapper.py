import requests
from logger_config import setup_logger
from bs4 import BeautifulSoup 


# logger = setup_logger(__name__)

def get_links(url: str) -> str:
    # logger.info(f"Fetching {url}")
    response = requests.get(url, timeout=10)
    bs=BeautifulSoup(response.text,"html.parser")
    links=bs.find_all("a")
    link_urls=[]
    for link in links:
        if not link["href"].startswith("http"):
            link_urls.append(link["href"])

    print(link_urls)    
    return response.text

if __name__=="__main__":
    get_links("https://verdant-soft.com/")