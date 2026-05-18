import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
from difflib import get_close_matches
import plotly.express as px

from database import create_table
from parser import parse_intern_text

create_table()

# ----------------------------
# COLUMN ALIASES
# ----------------------------

COLUMN_ALIASES = {
    "status": ["status", "intern status", "state"],
    "location": ["location", "city", "place"],
    "intern_type": ["intern type", "type"],
    "date_of_joining": ["date of joining", "joining date", "doj"],
    "duration": ["duration", "period", "tenure"],
    "fte_recommendation": ["fte", "fte recommendation"],
    "monthly_evaluation": ["evaluation", "feedback"],
    "expected completion date": ["completion date", "expected completion date"]
}

# ----------------------------
# HELPERS
# ----------------------------

def clean_text(text):
    if not isinstance(text, str):
        return ""
    return " ".join(
        text.lower().replace(".", " ").replace("-", " ").replace("_", " ").split()
    )

def match_column(col):
    col_clean = clean_text(col)

    candidates = {}
    keys = []

    for standard, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            a = clean_text(alias)
            candidates[a] = standard
            keys.append(a)

    match = get_close_matches(col_clean, keys, n=1, cutoff=0.6)

    if match:
        return candidates[match[0]]

    return None

def normalize_columns(df):
    rename = {}

    for col in df.columns:
        mapped = match_column(col)
        if mapped:
            rename[col] = mapped

    return df.rename(columns=rename)

def normalize_values(df):
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

        if col in ["status", "fte_recommendation", "Paid/Unpaid"]:
            df[col] = df[col].str.lower()

    return df

def calculate_completion(doj, duration):
    try:
        doj = pd.to_datetime(doj)
        duration = int(str(duration).split()[0])

        return (
            doj + relativedelta(months=duration)
        ).strftime("%Y-%m-%d")
    except:
        return None

def search_records(df, query):
    if not query:
        return df

    query = query.lower()

    mask = df.astype(str).apply(
        lambda row: row.str.lower().str.contains(query).any(),
        axis=1
    )

    return df[mask]

# ----------------------------
# DATABASE
# ----------------------------

def load_data():
    conn = sqlite3.connect("interns.db")

    try:
        df = pd.read_sql("SELECT * FROM interns", conn)
    except:
        df = pd.DataFrame()

    conn.close()
    return df

def save_data(df):
    conn = sqlite3.connect("interns.db")
    df.to_sql("interns", conn, if_exists="replace", index=False)
    conn.close()

def delete_record(record_id):
    df = load_data()

    df["ID"] = df["ID"].astype(str)

    df = df[df["ID"] != str(record_id)]

    save_data(df)

# ----------------------------
# MERGE
# ----------------------------

def merge_row(existing_df, new_df):

    if existing_df.empty:
        return new_df

    for col in new_df.columns:
        if col not in existing_df.columns:
            existing_df[col] = None

    for col in existing_df.columns:
        if col not in new_df.columns:
            new_df[col] = None

    new_df = new_df[existing_df.columns]

    if "ID" in new_df.columns:

        existing_df["ID"] = existing_df["ID"].astype(str)
        new_df["ID"] = new_df["ID"].astype(str)

        match = existing_df[
            existing_df["ID"] == new_df["ID"].iloc[0]
        ]

        if not match.empty:
            idx = match.index[0]

            for col in new_df.columns:
                val = new_df.iloc[0][col]

                if pd.notna(val):
                    existing_df.at[idx, col] = val

            return existing_df

    return pd.concat([existing_df, new_df], ignore_index=True)

# ----------------------------
# AI RESPONSE
# ----------------------------

def ai_response(query, df):
    q = query.lower()

    if "summary" in q:
        return f"Total Interns: {len(df)}"

    elif "fte" in q:
        return "\n".join(
            df[df["fte_recommendation"] == "yes"]["Name"].tolist()
        )

    elif "active" in q:
        return "\n".join(
            df[df["status"] == "pursuing"]["Name"].tolist()
        )

    return "Ask about summary, active interns, or FTE interns."

# ----------------------------
# REPORT
# ----------------------------

def generate_excel_report(df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    return output

# ----------------------------
# PAGE
# ----------------------------

st.set_page_config(page_title="AI Intern Management", layout="wide")

today = datetime.now().strftime("%d %B %Y")

st.markdown(f"""
<div style='padding:20px;
background:#111827;
color:white;
border-radius:15px;
margin-bottom:20px;'>

<h1>AI Intern Management System</h1>
<p>{today} | System Status: Active</p>

</div>
""", unsafe_allow_html=True)

# ----------------------------
# SIDEBAR
# ----------------------------

with st.sidebar:

    st.header("System Controls")

    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
    raw_text = st.text_area("Raw Intern Data")

    if st.button("Reset All Data"):
        save_data(pd.DataFrame())
        st.rerun()

# ----------------------------
# PROCESS
# ----------------------------

if st.sidebar.button("Process Data"):

    existing_df = load_data()

    if uploaded_file:

        df = pd.read_excel(uploaded_file)
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

        df = normalize_columns(df)
        df = normalize_values(df)

        if "date_of_joining" in df.columns and "duration" in df.columns:
            df["expected completion date"] = df.apply(
                lambda row: calculate_completion(
                    row["date_of_joining"],
                    row["duration"]
                ),
                axis=1
            )

        existing_df = df

    if raw_text.strip():

        parsed = parse_intern_text(raw_text)

        if parsed:
            parsed_df = pd.DataFrame([parsed])
            parsed_df = normalize_values(parsed_df)

            existing_df = merge_row(existing_df, parsed_df)

    save_data(existing_df)

    st.success("Data Processed Successfully")

# ----------------------------
# LOAD DATA
# ----------------------------

df = load_data()

if not df.empty:

    dashboard_tab, records_tab, ai_tab, reports_tab = st.tabs([
        "Dashboard",
        "Intern Records",
        "AI Assistant",
        "Reports"
    ])

    # ----------------------------
    # DASHBOARD
    # ----------------------------

    with dashboard_tab:

        c1, c2, c3 = st.columns(3)

        c1.metric("Total Interns", len(df))
        c2.metric("Active", len(df[df["status"] == "pursuing"]))
        c3.metric("FTE Ready", len(df[df["fte_recommendation"] == "yes"]))

        st.plotly_chart(
            px.pie(df, names="status", hole=0.4),
            use_container_width=True
        )

        st.plotly_chart(
            px.bar(
                df["location"].value_counts().reset_index(),
                x="location",
                y="count"
            ),
            use_container_width=True
        )

    # ----------------------------
    # RECORDS (STEP 7 + 8)
    # ----------------------------

    with records_tab:

        st.subheader("Editable Intern Records")

        search_query = st.text_input("Search Interns")

        searched_df = search_records(df, search_query)

        edited_df = st.data_editor(
            searched_df,
            use_container_width=True,
            num_rows="dynamic"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Save Table Changes"):
                save_data(edited_df)
                st.success("Changes saved successfully")
                st.rerun()

        with col2:
            delete_id = st.text_input("Enter ID to Delete")

            if st.button("Delete Record"):
                delete_record(delete_id)
                st.success(f"Record {delete_id} deleted")
                st.rerun()

    # ----------------------------
    # AI CHAT
    # ----------------------------

    with ai_tab:

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        prompt = st.chat_input("Ask Intern AI")

        if prompt:

            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })

            response = ai_response(prompt, df)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

            st.rerun()

    # ----------------------------
    # REPORTS
    # ----------------------------

    with reports_tab:

        st.download_button(
            "Download Report",
            generate_excel_report(df),
            "intern_report.xlsx"
        )

else:
    st.info("Upload data to begin.")