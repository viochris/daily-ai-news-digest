import os
import time
import bs4
import requests

# --- Environment & Utilities ---
from dotenv import load_dotenv

# --- Orchestration (Prefect) ---
from prefect import flow, task

# --- AI & Search Tools (LangChain) ---
from langchain_core.tools import tool
from langchain_community.document_loaders import WebBaseLoader
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchResults

# ==========================================
# 1. CONFIGURATION & CREDENTIALS
# ==========================================
# Securely load environment variables from the local .env file.
# This is crucial for keeping secrets out of the codebase.
load_dotenv()

# Fetch sensitive credentials securely from the environment system.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==========================================
# 2. CUSTOM TOOLS INITIALIZATION
# ==========================================

@tool("scrape_website_tool")
def scrape_tool(url: str) -> str:
    """
    Use this tool to extract and read the text content of a given webpage URL.
    It intelligently filters only the paragraph (<p>) tags to avoid HTML clutter and save tokens.
    Input must be a valid HTTP/HTTPS URL.
    """
    try:
        # 1. Initialize the WebBaseLoader with a SoupStrainer
        # This acts as a "sniper", fetching ONLY the <p> (paragraph) elements,
        # ignoring heavy navbars, footers, or useless scripts.
        loader = WebBaseLoader(
            web_paths=(url,), # Defined as a tuple to ensure safe parsing
            bs_kwargs={"parse_only": bs4.SoupStrainer("p")}
        )
        docs = loader.load()
        
        # 2. Extract the clean text content from the loaded documents
        full_text = "\n".join([doc.page_content for doc in docs])
        
        # 3. Truncate the text to a maximum of 10,000 characters
        # This serves as a strict "Token Saver" to prevent hitting LLM context limits and reduce costs.
        return full_text[:10000] 
        
    except Exception as e:
        return f"Error reading the website: {str(e)}"

# Initialize the Internet Search Tool.
# In native LangChain, built-in tools do not require the @tool wrapper.
search_tool = DuckDuckGoSearchResults(
    name="internet_search_tool",
    description="Use this tool to search the internet for the latest news regarding AI Advancements and General AI Business."
)

# ==========================================
# 2. CORE AI GENERATION TASKS
# ==========================================
@task(name="Generate Today News", retries=3, retry_delay_seconds=5)
def generate_news():
    """
    Task to search, scrape, and summarize the top 2 latest AI news using a LangChain Agent.
    
    This function initializes a tool-calling agent equipped with web search and scraping capabilities.
    The agent autonomously gathers specific Artificial Intelligence updates (Advancements and Business)
    from the last 24 hours, formats them strictly for Telegram deployment, and ensures zero hallucination.
    """

    # 1. Initialize the LLM
    # We set the temperature to 0.5 for a perfect balance between engaging storytelling and strict factual tool usage.
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.5
    )

    # 2. System Instructions & Prompt Template
    # We use ChatPromptTemplate and include {agent_scratchpad} so the LangChain agent 
    # has a "working memory" to process tool inputs and outputs dynamically.
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are Vio's specialized AI news assistant.
        Your goal is to autonomously research, scrape, and provide a detailed, insightful update on the Top 2 Artificial Intelligence (AI) news from the last 24 hours.

        ### 🛠️ TOOL EXECUTION STRATEGY:
        1. **Search Phase 1:** Use the 'internet_search_tool' to find recent news regarding "AI Advancements and Research breakthroughs". Identify the top 1 relevant URLs.
        2. **Search Phase 2:** Use the 'internet_search_tool' to find "General AI Business, Tools, and Market Trends". Identify the top 1 relevant URLs.
        3. **Scrape Phase:** Use the 'scrape_website_tool' to read the full content of those 2 selected URLs to gather deep, factual, and technical details. Do not guess the content; you MUST read it.

        ### 📝 STRUCTURE & FORMATTING (STRICT):
        1. **Intro:** Start EXACTLY with this greeting:
        "Hello Vio! Here is the hottest AI update from the last 24 hours, specially curated for you. Let's dive in!"
        
        2. **Separator:** Use `---` after the intro and between the two sections.

        3. **SECTION 1: 🚀 AI ADVANCEMENTS & RESEARCH** (Exactly 1 Items)
        - Focus: New LLM releases, Medical AI, Coding agents, Scientific discoveries, or Technical breakthroughs.

        4. **SECTION 2: 📰 GENERAL AI & BUSINESS NEWS** (Exactly 1 Items)
        - Focus: Business adoption, New Tools/Apps, Regulations, Drama/Lawsuits, or Market Trends.

        5. **Item Format (Per Story):**
        - **Headline:** Start with a bold title using a single star `*` (e.g., `*News Headline*`).
        - **Explanation:** Provide a DETAILED paragraph (3-4 sentences in English). Explain *what* happened, *why* it matters, and *key technical specs/details*.
        - **Source:** Put the exact link at the bottom of the item: `[Read More](URL)`.

        ### 🛡️ SAFETY RULES (CRITICAL):
        - NEVER use underscores (`_`) anywhere in the text (it breaks Telegram Markdown).
        - NEVER use Markdown Headers (# or ##).
        - NEVER use double stars (`**`). Use a single star `*` for bolding.
        - TRUTH: Do NOT hallucinate links. Use only the exact URLs you retrieved and scraped.
        """),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    try:
        # 3. Agent Assembly
        # Equip the agent with the custom tools and the instructional prompt.
        tools = [scrape_tool, search_tool]
        agent = create_tool_calling_agent(llm, tools, prompt)
        
        # The Executor is the engine that runs the agent's loop (Thought -> Action -> Observation).
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        # 4. Execution
        print("🚀 SYSTEM: Dispatching LangChain Agent to hunt for news...")
        
        # Trigger the agent with a clear, direct human command.
        response = agent_executor.invoke({
            "input": "Please search for today's AI news, scrape the detailed contents, and generate the 2-item summary now."
        })

        # 5. Output Validation
        # Ensure the AI actually returned a valid string. If not, trigger a Prefect retry.        
        if "output" in response and len(response["output"]) > 0:
            final_answer = response.get("output", "Sorry, I am unable to process that scheduling request right now.")

            # Sanitize the output if the LLM returns a complex list structure
            if isinstance(final_answer, list):
                cleaned_text = ""
                for part in final_answer:
                    if isinstance(part, dict) and "text" in part:
                        cleaned_text += part["text"]
                    elif isinstance(part, str):
                        cleaned_text += part
                final_answer = cleaned_text   
        else:
            final_answer = "Sorry, I am unable to process that scheduling request right now."

        return final_answer

    except Exception as e:
        # 6. Secure Error Handling
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
            final_error_message = f"❌ Error: News generation failed due to an unexpected system issue -> {error_str}."
            
        # Print the safe message to Prefect logs
        print(final_error_message)

        # RAISE the exception so Prefect marks the task as FAILED and triggers retries
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