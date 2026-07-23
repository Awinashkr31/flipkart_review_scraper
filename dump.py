import sys
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup as bs
def main():
    sys.stdout.reconfigure(encoding='utf-8')
    url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        
        html = page.content()
        soup = bs(html, 'html.parser')
        print('Title:', soup.title.string if soup.title else 'No Title')
        
        h1_title = soup.find('span', class_='B_NuCI') or soup.find('h1')
        print('Title:', h1_title.get_text(strip=True) if h1_title else 'No Title')
        
        # Try to find price near the title by going up the parents
        if h1_title:
            parent = h1_title
            for _ in range(5):
                parent = parent.parent
                if not parent: break
                price_div = parent.find("div", string=re.compile("₹"))
                if price_div:
                    print(f"Found price near title: {price_div.get_text(strip=True)}")
                    break
        
        browser.close()

if __name__ == "__main__":
    main()
