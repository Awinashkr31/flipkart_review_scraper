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
        
        h1_title = soup.find('h1') or soup.find('span', class_='B_NuCI')
        if h1_title:
            print('Title:', h1_title.get_text(separator=' ', strip=True))
            
            price_divs = h1_title.find_all_next("div", string=re.compile("₹"))
            found = False
            for div in price_divs:
                text = div.get_text(strip=True)
                if text.startswith("₹") and len(text) < 15:
                    print('Main Price Found:', text)
                    found = True
                    break
            if not found:
                print('Price not found after title')
        else:
            print('Title not found')
        
        browser.close()

if __name__ == "__main__":
    main()
