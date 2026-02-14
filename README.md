# 📰 Daily AI News Digest: Automated Intelligence Bot

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![Prefect](https://img.shields.io/badge/Prefect-Orchestration-070E28?logo=prefect&logoColor=white)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-8E75B2?logo=google&logoColor=white)
![DuckDuckGo](https://img.shields.io/badge/Search-DuckDuckGo-DE5833?logo=duckduckgo&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Delivery-26A5E4?logo=telegram&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📌 Overview
**Daily AI News Digest** is a fully automated intelligence agent designed to keep you updated with the latest Artificial Intelligence breakthroughs and global trends.

Orchestrated by **Prefect**, this bot acts as your personal news analyst. It performs real-time web scraping using **DuckDuckGo**, synthesizes the data using **Google's Gemini 2.5 Flash** model into a structured Indonesian summary, and instantly delivers the report to a **Telegram Channel**. It features robust error handling, smart message chunking, and strict quality control mechanisms.

## ✨ Key Features

### 🧠 AI-Powered Analysis
* **Context-Aware Summarization:** Utilizes `google-genai` (Gemini 2.5 Flash) with a specialized system instruction to act as "Vio's Assistant."
* **Structured Output:** Enforces a strict format (Advancements vs. General News) with bold headlines and source citation, ensuring high readability.

### 🔍 Real-Time Information Retrieval
* **DuckDuckGo Search:** leverages `ddgs` with strict time limits (`timelimit='d'`) to fetch only news from the **last 24 hours**.
* **Anti-Hallucination:** The AI is fed raw search results directly into the context window, forcing it to base summaries on actual scraped data rather than training data.

### 🛡️ Robust Orchestration
* **Prefect Flows:** Wraps all logic in tasks with automatic **Retry Policies** (3 retries, 5s delay) to handle transient network glitches.
* **Smart Delivery:** Includes logic to split messages exceeding Telegram's 4096-character limit into readable chunks without breaking Markdown formatting.
* **Fail-Fast Logic:** Explicitly raises exceptions on empty search results or API quotas to ensure the pipeline status is accurately reflected in monitoring tools.

## ⚠️ Current Limitations & Disclaimer
Please be aware of the following limitations in the current version:

1. **Inaccurate 'Read More' or 'Baca Selengkapnya' Links:** The source links provided at the end of each topic might occasionally point to the publisher's main homepage rather than the specific news article.
2. **AI Hallucination Risk:** Because the system relies on short search snippets and the 'Read More' links can be imprecise (as mentioned in number 1), the AI might hallucinate or fill in missing context for its answers. Even if it does not hallucinate and the text sounds convincing, the unclear source links mean we must assume the information could still be wrong. Therefore, please treat this version as a general overview and **ALWAYS** check and recheck its truthfulness independently on the internet.

## 🛠️ Tech Stack
* **Orchestrator:** Prefect (Workflow Management)
* **Language:** Python 3.11
* **AI Engine:** Google GenAI SDK (`gemini-2.5-flash`)
* **Search Engine:** DuckDuckGo Search (`ddgs`)
* **Notification:** Telegram Bot API (`requests`)

## 🚀 The Automation Pipeline
1.  **Trigger:** Scheduled run (Daily).
2.  **Search (Extract):** Queries DuckDuckGo for "AI Advancements" and "General AI News".
3.  **Validate:** Checks if search results exist. If empty, raises an exception to stop costs/hallucinations.
4.  **Synthesize (Transform):** Sends raw data to Gemini with a prompt to select the Top 6 stories and summarize in Indonesian.
5.  **Deliver (Load):** Pushes the formatted text to Telegram. If the message is too long, it automatically splits into chunks.

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
pip install prefect requests python-dotenv google-genai ddgs
```

3. **Run the Automation**
```bash
python news_automation_tele.py
```

### 🖥️ Expected Output

You should see **Prefect** orchestrating the tasks (Search -> Generate -> Send) in real-time:

```text
🚀 Starting Daily News Automation...
07:00:01.123 | INFO    | Task run 'Generate Today News' - 🌊 Surfing the web for: 'latest artificial intelligence breakthroughs research...'
07:00:03.456 | INFO    | Task run 'Generate Today News' - 🌊 Surfing the web for: 'latest artificial intelligence news business tools...'
07:00:05.789 | INFO    | Task run 'Generate Today News' - 🔍 Analyzing raw data with Gemini 2.5 Flash...
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
