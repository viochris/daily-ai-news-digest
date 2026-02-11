import os
import time

# --- Third Party Utilities ---
import requests
from dotenv import load_dotenv

# --- Orchestration (Prefect) ---
from prefect import flow, task

# --- AI & Search Tools ---
from duckduckgo_search import DDGS
from google import genai

# ==========================================
# CONFIGURATION & CREDENTIALS
# ==========================================
# 1. Environment Setup
# Load environment variables from a .env file.
# This is crucial for local testing to keep secrets out of the codebase.
load_dotenv()

# 2. API Keys & Secrets
# Fetch sensitive credentials securely from the environment system.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==========================================
# 1. HELPER TOOLS & SEARCH
# ==========================================
def search_news_in_ddgs(query: str):
    """
    Helper function to perform a web search using DuckDuckGo.
    
    This function utilizes the DuckDuckGo search engine to fetch real-time information 
    based on the provided query. It includes robust error handling for network issues 
    and rate limits to prevent the agent from crashing during data retrieval.

    Args:
        query (str): The search keywords or topic to look up on the web.
    """

    # 1. Debugging Log
    # Log the active query to the console to track the agent's search progress.
    print(f"🌊 Surfing the web for: '{query}'...")

    try:
        # 2. Tool Execution
        # Execute the search request.
        # We explicitly convert the generator to a list to ensure data is ready for the AI.
        # Parameters: region='wt-wt' (Global), max_results=10, timelimit='d' (Last 24h).
        results = DDGS().text(query, region='wt-wt', safesearch='off', max_results=10, timelimit="d")
        return results

    except Exception as e:
        # 3. Error Handling
        # Capture and normalize the exception message for analysis.
        error_str = str(e).lower()

        # Handle specific DuckDuckGo errors (Rate Limits are common).
        if "ratelimit" in error_str:
            print("⏳ Error: DuckDuckGo Rate Limit exceeded.")
            return "Error: Search rate limit hit. Could not fetch news."
        
        elif "timeout" in error_str:
            print("⏱️ Error: Search request timed out.")
            return "Error: Search timed out."
            
        else:
            # General error fallback.
            # We log the specific error to the console but return a safe generic message.
            print("❌ Search Error: An unexpected issue occurred while surfing the web.")
            return "Error: Search failed due to an unexpected system error."

# ==========================================
# 2. CORE AI GENERATION TASKS
# ==========================================
@task(name="Generate Today News", retries=3, retry_delay_seconds=5)
def generate_news():
    """
    Task to search and summarize the top 6 latest AI news.
    
    This function instructs the AI to fetch strictly Artificial Intelligence 
    updates (New Models, Breakthroughs, Industry Moves) from the last 24 hours.
    It ensures a specific format (Markdown safe for Telegram) and aims for 
    exactly 6 key stories (3 Advancements + 3 General News).
    """

    # System instruction defining the persona, broad scope, and formatting rules
    system_instruction = """
    You are Vio's specialized AI news assistant.
    Your goal is to provide a detailed and insightful update on the Top 6 Artificial Intelligence (AI) news from the last 24 hours based on the provided data.

    ### 🎯 OBJECTIVE:
    You must select and summarize exactly **6 News Items**, divided into two specific sections.

    ### 📝 STRUCTURE & FORMATTING (STRICT):
    
    1. **Intro:** Start EXACTLY with this greeting:
       "Halo Vio! Ini dia update AI terhangat dari 24 jam terakhir, sudah dirangkum khusus buat kamu. Yuk, cekidot!"
       
    2. **Separator:** Use `---` after the intro and between sections.

    3. **SECTION 1: 🚀 KEMAJUAN & RISET AI (Select 3 Items)**
       - Source: Select strictly from the **"LIST_A (ADVANCEMENTS)"** data.
       - Focus: New LLM releases, Medical AI, Coding agents, Scientific discoveries, or Technical breakthroughs.

    4. **SECTION 2: 📰 BERITA AI UMUM & BISNIS (Select 3 Items)**
       - Source: Select strictly from the **"LIST_B (GENERAL NEWS)"** data.
       - Focus: Business adoption, New Tools/Apps, Regulations, Drama/Lawsuits, or Market Trends.

    5. **Item Format (Per Story):**
       - **Headline:** Start with a bold title using a single star `*` (e.g., `*Judul Berita*`).
       - **Explanation:** Provide a DETAILED paragraph (3-4 sentences). Explain *what* happened, *why* it matters, and *key specs/details*. Do NOT just translate the title.
       - **Source:** Put the link at the bottom of the item with the format: `[Baca Selengkapnya](Specific_URL_from_href)`.

    ### 🛡️ SAFETY RULES (CRITICAL):
    - **NEVER** use underscores (`_`) anywhere in the text.
    - **NEVER** use Markdown Headers (# or ##).
    - **NEVER** use double stars (`**`). Use single star `*` for bolding.
    - **TRUTH:** Use the EXACT `href` provided in the raw data. Do NOT hallucinate links.
    """

    try:
        print("🔍 Searching for AI Advancements News...")
        raw_advancements = search_news_in_ddgs("latest artificial intelligence breakthroughs research new models advancements today")
        
        print("🔍 Searching for General AI News...")
        raw_general = search_news_in_ddgs("latest artificial intelligence news business tools applications trends today")

        if (isinstance(raw_advancements, str) or not raw_advancements) and (isinstance(raw_general, str) or not raw_general):
            print("⚠️ Search failed or returned no data. Skipping AI generation.")
            raise Exception("News Generation Failed: No Search Results")

        client = genai.Client(api_key=GOOGLE_API_KEY)

        # 1. Session Initialization
        # Create the chat session with the tool bound
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config={
                "system_instruction": system_instruction,
                "response_modalities": ["TEXT"]
            }
        )

        # 2. Prompt Execution
        # The prompt triggering the specific AI search
        prompt = f"""
        Here is the raw news data I found. I have separated them into two lists for you:
        
        === LIST_A (ADVANCEMENTS) ===
        {str(raw_advancements)}

        === LIST_B (GENERAL NEWS) ===
        {str(raw_general)}

        ----------------
        Based on the data above:
        1. Analyze **LIST_A** and select the Top 3 Advancements/Research stories.
        2. Analyze **LIST_B** and select the Top 3 General/Business stories.
        3. Summarize these 6 items immediately in Bahasa Indonesia using the requested format.
        """

        # Send the message to the model
        response = chat.send_message(prompt)

        # 3. Response Validation
        # Check if the response contains text and return it
        if response.text and len(response.text) > 0:
            return response.text
        else:
            print("⚠️ Warning: AI returned an empty response.")
            # We raise here too, to ensure the task fails if no content is produced
            raise Exception("News Generation Failed: Empty Response")

    except Exception as e:
        # 4. Secure Error Handling
        # We convert the error to string locally to check the TYPE of error,
        # BUT we strictly forbid printing the raw string to logs to protect the API Key.
        error_str = str(e).lower()
        final_error_message = ""

        if "quota" in error_str or "429" in error_str:
            final_error_message = "⏳ Error: Google AI API Quota Exceeded."
        
        elif "api_key" in error_str or "403" in error_str or "permission" in error_str:
            final_error_message = "🔑 Error: Google API Key is invalid or has restricted permissions."

        elif "timeout" in error_str or "deadline" in error_str:
            final_error_message = "⏱️ Error: Request to Google AI timed out."

        elif "safety" in error_str or "blocked" in error_str:
            final_error_message = "🛡️ Error: AI response was blocked by safety filters."

        else:
            # STRICTLY GENERIC MESSAGE - NO RAW DATA LEAKAGE
            final_error_message = "❌ Error: News generation failed due to an unexpected system issue."
            
        # Print the safe message
        print(final_error_message)

        # RAISE the exception so Prefect marks the task as FAILED and retries
        raise Exception(final_error_message)

# ==========================================
# 3. NOTIFICATION SERVICES
# ==========================================
@task(name="Send To Telegram", retries=3, retry_delay_seconds=5)
def to_telegram(news):
    """
    Task to send the generated message to a specific Telegram Chat.

    This function validates credentials, constructs the API payload, and 
    executes a secure HTTP POST request to the Telegram Bot API. 
    It includes logic to split messages longer than the API limit (4096 chars).
    """

    # 1. Credential Validation
    # Ensure both Token and Chat ID are present before proceeding.
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: Telegram credentials are missing.")
        return

    # 2. API Configuration
    # Construct the endpoint URL dynamically using the Token.
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    # Telegram limit is 4096. We use 4000 as a safety buffer.
    MAX_LENGTH = 4000
    message_to_send = []

    # Check if the news content exceeds the maximum length.
    if len(news) <= MAX_LENGTH:
        message_to_send.append(news)
    else:
        print("⚠️ Message is too long. Splitting into chunks...")

        # Split by double newlines to preserve Markdown paragraph structure.
        parts = news.split('\n\n')
        current_chunks = ""

        for part in parts:
            # Check if adding the next part exceeds the limit.
            if len(current_chunks) + len(part) + 2 < MAX_LENGTH:
                current_chunks += part + "\n\n"
            else:
                # If chunk is full, append to list and start a new one.
                if current_chunks.strip():
                    message_to_send.append(current_chunks)
                current_chunks = part + "\n\n"

        # Append any remaining text in the buffer.
        if current_chunks.strip():
            message_to_send.append(current_chunks)

    # 3. Sending Loop
    # Iterate through each chunk and send it sequentially.
    for i, news in enumerate(message_to_send):
        # Define the payload with Chat ID, Message content, and Markdown parsing.
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": news,
            "parse_mode": "Markdown"
        }

        try:
            # 4. Request Execution
            # Send a POST request to the Telegram API.
            response = requests.post(url, json=data)
            
            # 5. Response Handling
            # Check if the API returned a success status (HTTP 200).
            if response.status_code == 200:
                print(f"✅ Chunk {i+1}/{len(message_to_send)} sent successfully!")
            else:
                print(f"❌ Telegram Refused: Status Code {response.status_code}")
                print(f"❌ Chunk {i+1} Failed: {response.text}")
                # We raise exception to trigger Prefect retry logic.
                raise Exception(f"Telegram API Error: {response.status_code}")
            
            # Pause briefly to respect API rate limits.
            time.sleep(1)

        except Exception as e:
            # 6. Secure Error Handling
            # Convert exception to string for analysis without leaking credentials.
            error_str = str(e).lower()
            error_message = ""

            if "connection" in error_str or "dns" in error_str:
                error_message = "❌ Network Error: Failed to connect to Telegram API."
            elif "timeout" in error_str:
                error_message = "⏳ Timeout Error: Telegram API did not respond."
            elif "ssl" in error_str:
                error_message = "🔒 SSL Error: Certificate verification failed."
            else:
                error_message = "❌ Telegram Send Failed: Unknown error occurred."
            
            # Print the safe message to console.
            print(error_message)
            
            # RAISE the exception so Prefect marks the task as FAILED and retries.
            raise Exception(error_message)

@flow(name="Daily News Update", log_prints=True)
def main_flow():
    """
    Main orchestration flow for the Daily News System.
    
    This function coordinates the execution of two primary tasks:
    1. Generating news summaries via AI (`generate_news`).
    2. Dispatching the formatted content to Telegram (`to_telegram`).
    
    It serves as the central control unit, ensuring data passes correctly 
    between the extraction and notification layers.
    """

    print("🚀 Starting Daily News Automation...")

    try:
        # 1. Task Execution: News Generation
        # Trigger the AI agent to search and summarize today's headlines.
        news = generate_news()

        # 2. Validation & Dispatch
        # Ensure we actually got valid content before trying to send it.
        if news is not None:
            print("📝 News generated successfully. Sending to Telegram...")
            to_telegram(news)
            print("✅ Workflow completed successfully.")
        
        else:
            # Explicitly handle the case where the AI returns nothing (None).
            print("⚠️ Warning: No news content was generated.")
            raise Exception("News Generation Failed")

    except Exception as e:
        # 3. Secure Error Handling (Flow Level)
        # Convert error to string for local logic checking ONLY.
        error_str = str(e).lower()
        final_error_message = ""

        # Identify the source of the failure based on keywords.
        if "news" in error_str or "generation" in error_str:
            final_error_message = "❌ Flow Failed: The AI Agent failed to retrieve or summarize the news."
        
        elif "telegram" in error_str or "send" in error_str:
            final_error_message = "❌ Flow Failed: The Telegram notification service encountered an error."
        
        elif "timeout" in error_str:
            final_error_message = "⏳ Flow Failed: The operation took too long and timed out."

        else:
            # STRICTLY GENERIC MESSAGE
            # We intentionally hide the raw error here to protect system paths or keys.
            final_error_message = "❌ Critical System Failure: The flow crashed due to an unexpected internal error."
        
        # Print the error to the logs
        print(final_error_message)

        # Raise the exception to ensure Prefect marks the Flow as FAILED
        raise Exception(final_error_message)

if __name__ == "__main__":
    # ==========================================
    # 🚀 EXECUTION MODE
    # ==========================================

    # --- OPTION 1: FOR GITHUB ACTIONS (ACTIVE) ---
    # This calls the function immediately (Run Once).
    # GitHub's YAML scheduler handles the timing (CRON).
    # When finished, the script exits to save server resources.
    main_flow()

    # --- OPTION 2: FOR LOCAL SERVER / VPS (COMMENTED OUT) ---
    # Use this if you run the script on your own laptop or a 24/7 server.
    # The '.serve()' method keeps the script running indefinitely 
    # and handles the scheduling internally.
    
    # main_flow.serve(
    #     name="News and Information Automation", # Must not contain any of: ['/', '%', '&', '>', '<']
    #     # cron="0 7 * * *",                     # Run daily at 07:00 AM (server time)
    #     interval=30,                            # Or run every 60 seconds (for testing)
    #     tags=["ai", "daily"]
    # )
