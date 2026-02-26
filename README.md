# 📰 Daily AI News Digest: Automated Intelligence Bot

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![Prefect](https://img.shields.io/badge/Prefect-Orchestration-070E28?logo=prefect&logoColor=white)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-8E75B2?logo=google&logoColor=white)
![LangChain](https://img.shields.io/badge/Framework-LangChain-1C3C3C?logo=chainlink&logoColor=white)
![DuckDuckGo](https://img.shields.io/badge/Search-DuckDuckGo-DE5833?logo=duckduckgo&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Delivery-26A5E4?logo=telegram&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📌 Overview
**Daily AI News Digest** is a fully automated intelligence agent designed to keep you updated with the latest Artificial Intelligence breakthroughs and global trends.

Orchestrated by **Prefect**, this bot acts as your personal news analyst. It performs real-time web searching, synthesizes the data using **Google's Gemini 2.5 Flash** model into a structured summary, and instantly delivers the report to a **Telegram Channel**. It features robust error handling, smart message chunking, and strict quality control mechanisms.

This repository provides **two distinct versions** of the automation, allowing you to balance execution speed, API quota limits, and data accuracy based on your needs.

## 🚀 Available Versions

### 1️⃣ Version 1: The Lightweight Scraper (`news_automation_tele.py`)
* **Method:** Uses standard DuckDuckGo search (`ddgs`) and the base `google-genai` SDK to read search snippets.
* **Output:** Generates **6 news items** (3 Advancements, 3 Business).
* **Pros:** Fast execution and highly efficient with API quota.
* **Cons:** Lower reliability. Because it relies only on short search snippets rather than full articles, there is a higher risk of AI hallucination and the source links may be inaccurate.

### 2️⃣ Version 2: The Advanced LangChain Agent (`news_automation_fixed.py`)
* **Method:** Utilizes a LangChain agent (`create_tool_calling_agent`). It performs a two-step process: searching for URLs and then actively **scraping the full website content** using `WebBaseLoader`.
* **Output:** Generates **2 news items** (1 Advancement, 1 Business).
* **Pros:** High reliability and zero hallucination. The AI summarizes based on the actual article text, providing highly accurate information and precise source links.
* **Cons:** Slower execution and highly resource-intensive. Deep scraping consumes significantly more API quota, which is why the output is limited to 2 items to prevent API exhaustion.

## ✨ Key Features

### 🧠 AI-Powered Analysis
* **Context-Aware Summarization:** Enforces a strict format (Advancements vs. General News) with bold headlines and source citation, ensuring high readability.
* **Agentic Execution (V2):** Empowers the AI with custom tools to autonomously scrape and extract technical details directly from web pages.

### 🔍 Real-Time Information Retrieval
* **DuckDuckGo Search:** Fetches only news from the **last 24 hours**.
* **Anti-Hallucination (V2):** The AI is fed raw scraped data directly into the context window, forcing it to base summaries on actual content rather than training data.

### 🛡️ Robust Orchestration
* **Prefect Flows:** Wraps all logic in tasks with automatic **Retry Policies** (3 retries, 5s delay) to handle transient network glitches.
* **Smart Delivery:** Includes logic to split messages exceeding Telegram's 4096-character limit into readable chunks without breaking Markdown formatting.
* **Fail-Fast Logic:** Explicitly raises exceptions on empty search results or API quotas to ensure the pipeline status is accurately reflected in monitoring tools.

## ⚠️ Current Limitations & Disclaimer

* **Version 1 Limitations:**
  1. **Inaccurate Links:** The source links provided at the end of each topic might occasionally point to the publisher's main homepage rather than the specific news article.
  2. **AI Hallucination Risk (Missing Context):** Because Version 1 only extracts short preview snippets from the search engine rather than reading the full article, the AI lacks complete information. To fulfill the requirement of writing a detailed summary, the AI may fabricate or "hallucinate" the missing facts based on its training data. Therefore, please treat the output of this version as a high-level overview and **ALWAYS** independently verify the details.
* **Version 2 Limitations:**
  1. **API Cost:** The full-text scraping approach is token-heavy. Attempting to generate more than 2 items simultaneously may trigger Google API rate limits (`429 Quota Exceeded`).
  2. **Scraping Blocks:** Highly secured websites (e.g., Cloudflare protections, paywalls) may block the scraper from reading the content.

## 🛠️ Tech Stack
* **Orchestrator:** Prefect (Workflow Management)
* **Language:** Python 3.11
* **Framework (V2):** LangChain & LangChain Agents
* **AI Engine:** Google GenAI SDK & `langchain-google-genai` (`gemini-2.5-flash`)
* **Search Engine:** DuckDuckGo Search (`ddgs` / `DuckDuckGoSearchResults`)
* **Web Scraper (V2):** BeautifulSoup4 (`bs4`)
* **Notification:** Telegram Bot API (`requests`)

## 🚀 The Automation Pipeline
1. **Trigger:** Scheduled run (Daily).
2. **Search (Extract):** Queries DuckDuckGo for "AI Advancements" and "General AI News".
3. **Scrape & Validate:** Checks if search results exist. In V2, the agent proceeds to read the full HTML content of the target URLs.
4. **Synthesize (Transform):** Sends data to Gemini to format a structured summary (6 items for V1, 2 items for V2).
5. **Deliver (Load):** Pushes the formatted text to Telegram, splitting into chunks if necessary.

## ⚙️ Configuration (Environment Variables)
Create a `.env` file in the root directory:

```ini
GOOGLE_API_KEY=your_gemini_api_key
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_target_chat_id
```

## 📦 Local Installation
1. **Clone the Repository**
```bash
git clone https://github.com/viochris/daily-ai-news-digest.git
cd daily-ai-news-digest
```

2. **Install Dependencies**
```bash
pip install prefect requests python-dotenv langchain-google-genai duckduckgo-search beautifulsoup4 langchain langchain-community
```

3. **Run the Automation**
To run the Advanced LangChain version (High Accuracy, 2 Items):
```bash
python news_automation_fixed.py
```

To run the Lightweight version (Fast, 6 Items):
```bash
python news_automation_tele.py
```

### 🖥️ Expected Output
You should see **Prefect** orchestrating the tasks in real-time:

```text
🚀 Starting Daily News Automation...
07:00:01.123 | INFO    | Task run 'Generate Today News' - 🚀 SYSTEM: Dispatching LangChain Agent to hunt for news...
07:00:10.223 | INFO    | Task run 'Generate Today News' - ✅ News generated successfully.
07:00:10.556 | INFO    | Task run 'Send To Telegram' - ⚠️ Message is too long. Splitting into chunks...
07:00:11.889 | INFO    | Task run 'Send To Telegram' - ✅ Chunk 1/2 sent successfully!
07:00:13.100 | INFO    | Task run 'Send To Telegram' - ✅ Chunk 2/2 sent successfully!
07:00:13.200 | INFO    | Flow run 'Daily News Update' - ✅ Workflow completed successfully.

```

## 🚀 Deployment Options

This bot supports two release methods depending on your infrastructure:

| Method | Description | Use Case |
| --- | --- | --- |
| **GitHub Actions** | **Serverless.** Uses `cron` scheduling in `.github/workflows/daily_news.yml`. Runs on GitHub servers for free. | Best for daily/scheduled runs without paying for a VPS. |
| **Local / VPS** | **Always On.** Uses `main_flow.serve()` to run as a background service on your own server or Docker container. | Best if you need sub-minute updates or complex triggers. |

---

**Author:** [Silvio Christian, Joe](https://www.linkedin.com/in/silvio-christian-joe)
*"Automate the boring stuff, generate the beautiful stuff."*
