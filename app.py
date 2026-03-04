import streamlit as st
import google.generativeai as genai
import sqlite3
import datetime

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
    return f"""
You are an expert startup consultant with 20+ years of experience.

STARTUP DETAILS:
Idea: {idea}
Target Audience: {audience}
Budget: {budget}
Industry: {industry}
Risk Tolerance: {risk_level}

Provide a detailed validation report with these exact sections:

## SWOT Analysis
Strengths: (3-4 bullets)
Weaknesses: (3-4 bullets)
Opportunities: (3-4 bullets)
Threats: (3-4 bullets)

## Market Opportunity
(4 bullets: size, pain point, gap, competition)

## Revenue Model Suggestions
(3 models with explanations)

## Risk Analysis
(Top 3 risks with mitigations for {risk_level} risk and {budget} budget)

## 3 Actionable Next Steps
1. Action with timeline
2. Action with timeline
3. Action with timeline

## Overall Verdict
(2-3 honest sentences on viability)
"""

def call_gemini(prompt, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        return model.generate_content(prompt).text
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    init_db()

    st.title("🚀 Smart Startup Idea Validator")
    st.caption("AI-powered startup analysis — 100% free")

    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("Gemini API Key", type="password",
                                help="Get free key at aistudio.google.com/app/apikey")
        st.markdown("---")
        st.markdown("### Past Validations")
        for row in fetch_history():
            if st.button(f"#{row[0]} — {row[1][:25]}...", key=f"h{row[0]}"):
                st.session_state["view_id"] = row[0]

    if "view_id" in st.session_state:
        rec = fetch_one(st.session_state["view_id"])
        if rec:
            st.subheader(f"Past Result #{rec[0]}")
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
            st.warning("Please enter your Gemini API key in the sidebar.")
            return

        with st.spinner("Analyzing your idea... (15-30 seconds)"):
            result = call_gemini(build_prompt(idea, audience, budget, industry, risk_level), api_key)

        if result.startswith("Error"):
            st.error(result)
        else:
            st.success("Analysis Complete!")
            st.markdown("---")
            st.subheader("Your Startup Validation Report")
            st.markdown(result)
            save_to_db(idea, audience, budget, industry, risk_level, result)
            st.info("Saved to history.")
            st.download_button("Download Report", data=result,
                file_name=f"validation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain")

if __name__ == "__main__":
    main()