import os
import csv
import logging
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS, cross_origin
from bs4 import BeautifulSoup as bs
from playwright.sync_api import sync_playwright
import urllib.parse
import re

application = Flask(__name__)  # initializing a flask app
app = application

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional MongoDB — set MONGO_URI env variable to enable
MONGO_URI = os.environ.get("MONGO_URI")


def scrape_reviews(search_query):
    """
    Uses Playwright (headless Chromium) to scrape Flipkart product reviews.
    Accepts either a search keyword or a direct Flipkart product URL.
    Returns: (product_info, list of review dicts)
    """
    reviews = []
    product_info = {
        "title": "Unknown Product",
        "price": "N/A",
        "rating": "N/A",
        "image": "",
        "query": search_query
    }

    is_url = search_query.startswith("http") and "flipkart.com" in search_query

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        try:
            if not is_url:
                # Step 1: Search for the product on Flipkart
                search_url = "https://www.flipkart.com/search?q=" + urllib.parse.quote(search_query)
                logger.info(f"Navigating to search: {search_url}")
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)

                try:
                    close_btn = page.locator("button._2KpZ6l._2doB4z")
                    if close_btn.count() > 0:
                        close_btn.first.click()
                        page.wait_for_timeout(500)
                except Exception:
                    pass

                # Find the first product link
                product_link = None
                product_anchors = page.locator("a[href*='/p/']")
                count = product_anchors.count()
                logger.info(f"Found {count} product links")

                if count > 0:
                    href = product_anchors.first.get_attribute("href")
                    if href:
                        product_link = "https://www.flipkart.com" + href if href.startswith("/") else href

                if not product_link:
                    raise Exception("No products found for your search keyword. Try a different keyword.")
            else:
                # It's a direct URL
                product_link = search_query
            
            product_info["url"] = product_link
            
            logger.info(f"Navigating to product: {product_link}")
            page.goto(product_link, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            # Extract the raw page content
            page_html = page.content()
            soup = bs(page_html, "html.parser")

            # --- Extract Product Meta Info ---
            try:
                # Target Title: Usually an h1 or specific span class VU-TzV / B_NuCI
                h1_title = soup.find('h1')
                if h1_title:
                    product_info["title"] = h1_title.get_text(separator=' ', strip=True)

                # Target Price: Contains the ₹ symbol
                price_found = False
                if h1_title:
                    price_divs = h1_title.find_all_next("div", string=re.compile("₹"))
                    for div in price_divs:
                        text = div.get_text(strip=True)
                        if text.startswith("₹") and len(text) < 15:
                            product_info["price"] = text
                            price_found = True
                            break
                
                if not price_found:
                    price_divs = soup.find_all("div", string=re.compile("₹"))
                    for div in price_divs:
                        text = div.get_text(strip=True)
                        if text.startswith("₹") and len(text) < 15:
                            product_info["price"] = text
                            break

                # Target Overall Rating
                overall_rating_div = soup.find("div", class_=lambda c: c and any(x in c for x in ["_3LWZlK", "XQDdHH"]))
                if overall_rating_div:
                    product_info["rating"] = overall_rating_div.get_text(strip=True)

                # Target Main Image: Usually has specific dimensions or is early in the DOM
                images = soup.find_all("img")
                for img in images:
                    src = img.get("src", "")
                    if "image" in src and "http" in src and "q=" in src:
                        # Flipkart images usually have quality params
                        product_info["image"] = src
                        break

                logger.info(f"Extracted info: {product_info}")

            except Exception as e:
                logger.warning(f"Failed to extract some product metadata: {e}")

            # --- REVIEW EXTRACTION STRATEGY ---
            review_containers = []
            seen_ids = set()

            rating_divs = soup.find_all(
                "div", class_="css-146c3p1",
                string=lambda t: t and t.strip() in ["1", "2", "3", "4", "5"]
            )
            logger.info(f"Found {len(rating_divs)} rating elements on page")

            for rd in rating_divs:
                node = rd
                for _ in range(5):
                    if node.parent:
                        node = node.parent
                    else:
                        break

                node_id = id(node)
                text_len = len(node.get_text())

                if node_id in seen_ids or text_len > 500 or text_len < 10:
                    continue

                seen_ids.add(node_id)
                review_containers.append(node)

            logger.info(f"Found {len(review_containers)} review containers")

            for i, container in enumerate(review_containers):
                if i >= 20:
                    break
                try:
                    name = "Anonymous"
                    rating = "N/A"
                    comment_head = ""
                    comment = ""

                    all_inner_divs = container.find_all("div", recursive=True)

                    for div in all_inner_divs:
                        classes = div.get("class", [])
                        class_str = " ".join(classes)
                        text = div.get_text(strip=True)

                        if not text:
                            continue

                        if "css-146c3p1" in class_str and text in ["1", "2", "3", "4", "5"] and rating == "N/A":
                            rating = text

                        elif any("v1zwn24" in c for c in classes) and not comment_head:
                            comment_head = text

                        elif any("v1zwn26" in c for c in classes) and not comment:
                            comment = text.rstrip("more").rstrip("READ MORE").strip()
                            if comment.endswith("..."):
                                comment = comment

                        elif any("v1zwn27" in c for c in classes) and name == "Anonymous":
                            name = text

                    product_display_name = product_info["title"] if product_info["title"] != "Unknown Product" else ("Linked Product" if is_url else search_query)

                    review_dict = {
                        "Product": product_display_name,
                        "Name": name,
                        "Rating": rating,
                        "CommentHead": comment_head,
                        "Comment": comment if comment else comment_head,
                    }
                    reviews.append(review_dict)

                except Exception as e:
                    logger.warning(f"Error extracting review {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            raise

        finally:
            browser.close()

    return product_info, reviews


def save_to_csv(reviews, filename_hint):
    """Save reviews to a CSV file and return the generated filename."""
    # Sanitize the hint string
    safe_hint = re.sub(r'[^a-zA-Z0-9\s]', '', filename_hint).strip().replace(" ", "_")
    if not safe_hint:
        safe_hint = "flipkart"
    # Keep it short
    safe_hint = safe_hint[:30]
    
    filename = f"{safe_hint}_reviews.csv"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Product", "Name", "Rating", "CommentHead", "Comment"])
        writer.writeheader()
        writer.writerows(reviews)
    logger.info(f"Saved {len(reviews)} reviews to {filepath}")
    return filename


def save_to_mongo(reviews):
    """Save reviews to MongoDB if MONGO_URI is configured."""
    if not MONGO_URI:
        return
    try:
        import pymongo
        client = pymongo.MongoClient(MONGO_URI)
        db = client["review_scrap"]
        review_col = db["review_scrap_data"]
        review_col.insert_many(reviews)
        logger.info(f"Saved {len(reviews)} reviews to MongoDB")
    except Exception as e:
        logger.warning(f"MongoDB save failed (non-critical): {e}")


@app.route("/", methods=["GET"])
@cross_origin()
def homePage():
    return render_template("index.html")


@app.route("/review", methods=["POST", "GET"])
@cross_origin()
def index():
    if request.method == "POST":
        try:
            searchString = request.form["content"].strip()
            if not searchString:
                return render_template("error.html", error_message="Please enter a product name or flipkart URL.")

            logger.info(f"Processing input: {searchString}")

            # Scrape reviews using Playwright
            product_info, reviews = scrape_reviews(searchString)

            if not reviews:
                return render_template(
                    "error.html",
                    error_message=f'No reviews found. The product may not have reviews, or the structure could not be parsed.',
                )

            # Save to CSV
            filename_hint = product_info["title"] if product_info["title"] != "Unknown Product" else "product"
            csv_filename = save_to_csv(reviews, filename_hint)

            # Save to MongoDB (if configured)
            save_to_mongo(reviews)

            return render_template(
                "results.html", 
                reviews=reviews, 
                query=searchString, 
                product_info=product_info, 
                csv_filename=csv_filename
            )

        except Exception as e:
            logger.error(f"The Exception message is: {e}")
            return render_template(
                "error.html",
                error_message=str(e),
            )

    else:
        return render_template("index.html")

@app.route("/download/<filename>", methods=["GET"])
def download_csv(filename):
    """Endpoint for downloading the generated CSV file."""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    # Path traversal protection
    if not os.path.abspath(filepath).startswith(os.path.dirname(os.path.abspath(__file__))):
        return "Invalid file path", 400
        
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return "File not found", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

