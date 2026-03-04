import streamlit as st
import sqlite3
import datetime
import requests

st.set_page_config(page_title="Smart Startup Validator", page_icon="🚀", layout="wide")

DB_FILE = "startup_ideas.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS validations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea TEXT, audience TEXT, budget TEXT,
            industry TEXT, risk_level TEXT,
            ai_response TEXT, created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(idea, audience, budget, industry, risk_level, ai_response):
    conn = sqlite3.connect(DB_FILE)
    conn.cursor().execute(
        "INSERT INTO validations (idea,audience,budget,industry,risk_level,ai_response,created_at) VALUES (?,?,?,?,?,?,?)",
        (idea, audience, budget, industry, risk_level, ai_response,
         datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def fetch_history():
    conn = sqlite3.connect(DB_FILE)
    rows = conn.cursor().execute(
        "SELECT id,idea,industry,created_at FROM validations ORDER BY id DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return rows

def fetch_one(rid):
    conn = sqlite3.connect(DB_FILE)
    row = conn.cursor().execute("SELECT * FROM validations WHERE id=?", (rid,)).fetchone()
    conn.close()
    return row

def build_prompt(idea, audience, budget, industry, risk_level):
    prompt = "You are an expert startup consultant with 20 years of experience.\n\n"
    prompt += "STARTUP DETAILS:\n"
    prompt += "Idea: " + idea + "\n"
    prompt += "Target Audience: " + audience + "\n"
    prompt += "Budget: " + budget + "\n"
    prompt += "Industry: " + industry + "\n"
    prompt += "Risk Tolerance: " + risk_level + "\n\n"
    prompt += "Provide a detailed validation report with these sections:\n\n"
    prompt += "## SWOT Analysis\n"
    prompt += "Strengths, Weaknesses, Opportunities, Threats (3-4 bullets each)\n\n"
    prompt += "## Market Opportunity\n"
    prompt += "4 bullets on size, pain point, gap, competition\n\n"
    prompt += "## Revenue Model Suggestions\n"
    prompt += "3 models with explanations\n\n"
    prompt += "## Risk Analysis\n"
    prompt += "Top 3 risks with mitigations\n\n"
    prompt += "## 3 Actionable Next Steps\n"
    prompt += "Numbered steps with timelines\n\n"
    prompt += "## Overall Verdict\n"
    prompt += "2-3 honest sentences on viability"
    return prompt

def call_ai(prompt, api_key):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        }
        data = {
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        if "error" in result:
            return "API Error: " + str(result["error"]["message"])
        return "Unexpected response: " + str(result)
    except Exception as e:
        return "Error: " + str(e)

def main():
    init_db()
    st.title("🚀 Smart Startup Idea Validator")
    st.caption("AI-powered startup analysis — 100% free")

    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("OpenRouter API Key", type="password",
                                help="Get free key at openrouter.ai")
        st.markdown("---")
        st.markdown("### Past Validations")
        for row in fetch_history():
            if st.button("#{} — {}...".format(row[0], row[1][:25]), key="h{}".format(row[0])):
                st.session_state["view_id"] = row[0]

    if "view_id" in st.session_state:
        rec = fetch_one(st.session_state["view_id"])
        if rec:
            st.subheader("Past Result #{}".format(rec[0]))
            st.markdown(rec[6])
        if st.button("Back"):
            del st.session_state["view_id"]
        return

    st.subheader("Enter Your Startup Details")
    col1, col2 = st.columns(2)

    with col1:
        idea = st.text_area("Your Startup Idea", placeholder="Describe your idea in 1-3 sentences", height=120)
        audience = st.selectbox("Target Audience", ["Students","Working Professionals","Small Businesses","Enterprises","Homemakers","Senior Citizens","General Public"])
        budget = st.selectbox("Available Budget", ["Under $500","$500-$2,000","$2,000-$10,000","$10,000-$50,000","Above $50,000"])

    with col2:
        industry = st.selectbox("Industry", ["AgriTech","EdTech","FinTech","HealthTech","E-Commerce","SaaS","Social Media","Gaming","CleanTech","FoodTech","Travel","Real Estate","Other"])
        risk_level = st.select_slider("Risk Tolerance", options=["Very Low","Low","Medium","High","Very High"], value="Medium")
        st.markdown("")
        validate_btn = st.button("🚀 Validate My Idea")

    if validate_btn:
        if not idea.strip():
            st.warning("Please describe your startup idea.")
            return
        if not api_key:
            st.warning("Please enter your OpenRouter API key in the sidebar.")
            return
        with st.spinner("Analyzing your idea... (15-30 seconds)"):
            result = call_ai(build_prompt(idea, audience, budget, industry, risk_level), api_key)
        if result.startswith("Error") or result.startswith("API Error") or result.startswith("Unexpected"):
            st.error(result)
        else:
            st.success("Analysis Complete!")
            st.markdown("---")
            st.subheader("Your Startup Validation Report")
            st.markdown(result)
            save_to_db(idea, audience, budget, industry, risk_level, result)
            st.info("Saved to history.")
            st.download_button("Download Report", data=result,
                file_name="validation_{}.txt".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S")),
                mime="text/plain")

if __name__ == "__main__":
    main()
