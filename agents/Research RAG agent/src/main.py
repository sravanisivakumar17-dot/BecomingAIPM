import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# --- 1. LOAD OPENROUTER CONFIG ---
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "..", ".env")
load_dotenv(dotenv_path=env_path)

# Look for the OpenRouter key specifically
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    print(f"❌ ERROR: OPENROUTER_API_KEY not found in .env!")
    exit()
else:
    print(f"✅ OpenRouter Key Loaded: {api_key[:10]}...")

# --- 2. AGENT LOGIC ---
INTEL_PROMPT = """
You are a Sr. Product Manager at Zscaler. You are researching a competitor's latest technical move.
Use the search results below to provide a high-level strategic intelligence report.

SEARCH RESULTS:
{context}

USER RESEARCH REQUEST: {question}

---
STRATEGIC INTELLIGENCE REPORT:
1. THE NEWS: (What exactly was announced?)
2. TECHNICAL THREAT: (How does this impact Zscaler?)
3. ARCHITECTURAL GAP: (What are they missing?)
4. RECOMMENDED ACTION: (Pivot, Feature-parity, or Monitor?)
"""

def save_intel_report(query, report):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    clean_query = "".join([c if c.isalnum() else "_" for c in query[:30]])
    filename = f"report_{timestamp}_{clean_query}.md"
    
    data_dir = os.path.join(current_dir, "..", "data", "intel_reports")
    os.makedirs(data_dir, exist_ok=True)
    
    filepath = os.path.join(data_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# RESEARCH QUERY: {query}\n\n{report}")
    return filepath

def run_intel_scout(competitor_query):
    print(f"\n--- Scouting Intelligence via OpenRouter for: {competitor_query} ---")
    
    # We use the ChatOpenAI tool but point it at OpenRouter
    llm = ChatOpenAI(
        model_name="openai/gpt-4o", 
        openai_api_key=api_key,             # Use your OpenRouter Key
        openai_api_base="https://openrouter.ai/api/v1", # Point to OpenRouter
        temperature=0,
        max_completion_tokens=800
    )
    
    search = DuckDuckGoSearchRun()
    prompt = ChatPromptTemplate.from_template(INTEL_PROMPT)
    
    chain = (
        {"context": search, "question": RunnablePassthrough()}
        | prompt
        | llm
    )
    
    try:
        response = chain.invoke(competitor_query)
        path = save_intel_report(competitor_query, response.content)
        print(f"✅ Success! Report saved to: {path}")
        return response.content
    except Exception as e:
        print(f"❌ Agent Error: {e}")
        return None

if __name__ == "__main__":
    # Change this to any competitor you want to research
    query = "Okta latest AI identity protection features 2024"
    run_intel_scout(query)
