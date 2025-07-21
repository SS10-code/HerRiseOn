import streamlit as st
import json
from checker_for_jobs import JobCollector
from checker_for_scholarships import main as check_scholarships

# Run only once per user session
if "data_loaded" not in st.session_state:
    check_scholarships()
    JobCollector().run()
    st.session_state["data_loaded"] = True

# Page config
st.set_page_config(page_title="Opportunity Finder for Women", layout="wide")

# Custom styling
st.markdown("""
<style>
    .stApp { background-color: #ffe4e1; color: black; }
    h1, h2, h3, h4, h5, h6, p, div, a { color: black !important; }
    [data-testid="stSidebar"] { background-color: #f7c8c3 !important; }
    [data-testid="stSidebar"] * { color: black !important; }
    div[data-baseweb="select"] {
        background-color: #f5f5dc !important;
        border-radius: 5px;
        color: black !important;
        font-weight: 600;
        border: 1px solid #ccc !important;
    }
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] *,
    li[role="option"],
    ul[role="listbox"] {
        background-color: #f5f5dc !important;
        color: black !important;
    }
    li[role="option"]:hover {
        background-color: #ffe4e1 !important;
    }
</style>
""", unsafe_allow_html=True)

# Load data
with open("opportunities.json") as f:
    opportunities = json.load(f)

with open("job_opportunities.json") as j:
    job_opportunities = json.load(j)

# Home page
def home():
    st.title("Welcome to HerRiseOn")
    st.markdown("""
    <div style="font-size: 18px; line-height: 1.6;">
    <p>
    HerRiseOn is your all-in-one hub to explore career and education opportunities tailored for <b>underrepresented women</b>.
    Our mission is to bridge the gap by making it easier to access resources that empower and elevate.
    </p>
    <p>
    Browse scholarships, discover meaningful job opportunities, and take a step closer to achieving your goals.
    </p>
    <p>
    Use the sidebar to get started.
    </p>
    </div>
    """, unsafe_allow_html=True)

# Scholarships page
def scholarships():
    st.title("Scholarships for Women")
    scholarships = [o for o in opportunities if o["type"].lower() == "scholarship"]

    def get_range(salary_str):
        try:
            amount = int(salary_str.replace("$", "").replace(",", ""))
            if amount < 1000: return "Less than $1,000"
            elif amount < 3000: return "$1,000 - $2,999"
            elif amount < 5000: return "$3,000 - $4,999"
            else: return "$5,000 and above"
        except:
            return "Not specified"

    for s in scholarships:
        s["amount_range"] = get_range(str(s.get("salary", "")))

    ranges = ["All", "Not specified", "Less than $1,000", "$1,000 - $2,999", "$3,000 - $4,999", "$5,000 and above"]
    selected_range = st.selectbox("Filter by Scholarship Amount Range", ranges)

    if selected_range != "All":
        scholarships = [s for s in scholarships if s["amount_range"] == selected_range]

    for opp in scholarships:
        field = opp["field"].strip() if isinstance(opp["field"], str) and opp["field"].strip() else "Not specified"
        salary = str(opp["salary"]) if opp.get("salary") else "Not specified"

        st.markdown(f"""
        <div style="background-color: #b3e5fc; padding: 1em; border-radius: 10px; margin-bottom: 10px; color: black;">
        <h4>{opp['title']}</h4>
        <p><i>For underrepresented women</i><br>
        <b>Field:</b> {field}<br>
        <b>Scholarship Amount:</b> {salary}<br>
        <b>Note:</b> none <br>
        <a href="{opp['link']}" target="_blank" style="color:black; text-decoration: underline;">Apply Now</a>
        </p>
        </div>
        """, unsafe_allow_html=True)

# Jobs page
def jobs():
    st.title("Jobs")
    jobs = [o for o in job_opportunities if o["type"].lower() == "job"]

    fields = sorted(set([o["field"] for o in jobs if isinstance(o["field"], str) and o["field"].strip()]))
    selected_field = st.selectbox("Filter by Field", ["All"] + fields)

    if selected_field != "All":
        jobs = [j for j in jobs if j["field"] == selected_field]

    for opp in jobs:
        field = opp["field"].strip() if isinstance(opp["field"], str) and opp["field"].strip() else "Not specified"
        location = str(opp.get("location", "") or "").strip() or "Not specified"

        salary_val = opp.get("salary")
        if isinstance(salary_val, (int, float)):
            salary = f"{salary_val}k"
        elif isinstance(salary_val, str) and salary_val.strip():
            salary = salary_val.strip()
        else:
            salary = "Not specified"

        st.markdown(f"""
        <div style="background-color: #ffccbc; padding: 1em; border-radius: 10px; margin-bottom: 10px; color: black;">
        <h4>{opp['title']}</h4>
        <p><i>For underrepresented women</i><br>
        <b>Field:</b> {field}<br>
        <b>Location:</b> {location}<br>
        <b>Salary:</b> {salary}<br>
        <b>Note:</b> {opp['note']}<br>
        <a href="{opp['link']}" target="_blank" style="color:black; text-decoration: underline;">Apply Now</a>
        </p>
        </div>
        """, unsafe_allow_html=True)

# Navigation
st.sidebar.title("HerRiseOn")
page = st.sidebar.radio("Go to", ["Home", "Scholarships", "Jobs"])

if page == "Home":
    home()
elif page == "Scholarships":
    scholarships()
else:
    jobs()
