# Flipkart Review Scraper Pro 🔍

A robust, production-ready web application built with Flask and Playwright to instantly extract, analyze, and export product reviews from Flipkart.

## Features
- **Intelligent Scraping**: Bypasses bot detection by running Playwright in `headless=False` mode, wrapper inside an X virtual framebuffer (Xvfb) for headless production servers.
- **Dynamic Analysis**: Automatically extracts product name, price, overall rating, and all individual customer reviews.
- **Clean UI Dashboard**: A sleek, professional dashboard to view rating distributions, filter reviews by stars, and read feedback.
- **CSV Export**: Instantly download all scraped reviews as a clean CSV file.
- **Production Ready**: Fully Dockerized with Gunicorn and MongoDB support.

---

## 🚀 Quick Start (Production via Docker)

The easiest way to run the scraper in a production-like environment (or locally) without worrying about GUI dependencies is using Docker.

### Prerequisites
- Docker & Docker Compose

### Running the App
1. Clone the repository and navigate to the root directory.
2. Build and start the containers:
   ```bash
   docker-compose up --build
   ```
3. Open your browser and visit: `http://localhost:8000`

---

## 🛠️ Local Development Setup

If you prefer to run the application directly on your local machine for development:

### 1. Create a Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Playwright Browsers
```bash
playwright install
```

### 4. Run the Application
```bash
python application.py
```
The app will be available at `http://localhost:8000`. 
*Note: Because it runs Playwright in `headless=False` mode to bypass captchas, a Chromium window will briefly pop up during scraping.*

---

## ⚙️ Environment Variables

Copy the `.env.example` file to `.env` to configure your environment:

```env
PORT=8000
FLASK_ENV=production
# Optional: Setup MongoDB connection
MONGO_URI=mongodb://mongodb:27017/flipkart
```

## 🏗️ Architecture Notes

- **Why Xvfb?** Flipkart has strict bot protections that block standard headless browsers. To solve this, the scraper runs Playwright in "headful" mode. To make this work on a server without a physical monitor, the Docker container utilizes `Xvfb` (X virtual framebuffer) to simulate a display.
- **Flask + Gunicorn**: The backend is powered by Flask, served via Gunicorn in production (`start.sh`).
- **Styling**: The UI uses a custom, lightweight CSS framework utilizing a clean, modern SaaS design system.
