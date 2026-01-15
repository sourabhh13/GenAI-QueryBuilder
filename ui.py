# streamlit_app.py
import streamlit as st
import requests
import os

# FastAPI backend URL - FIXED: removed /code and trailing slash
API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="GenAI Query Builder", page_icon="🤖", layout="wide")
st.title(" GENAI SQL Query Generator & Executor")
st.markdown("Generate SQL from plain English using Gemini (GenAI) and execute it against your database via FastAPI.")

# -------- Sidebar: DB inspection (optional API endpoints) --------
st.sidebar.header("Database Explorer (optional)")

selected_db = st.sidebar.text_input("Database name", key="db_name")
if st.sidebar.button("🌐 List Databases", key="btn_list_db"):
    try:
        r = requests.get(f"{API_URL}/list_databases/")
        r.raise_for_status()
        databases = r.json().get("databases", [])
        st.sidebar.write("### Available Databases")
        st.sidebar.write(databases or "No databases returned.")
    except Exception as e:
        st.sidebar.error(f"Error fetching databases: {e}")

if selected_db and st.sidebar.button("📂 Show Tables", key="btn_list_tables"):
    try:
        r = requests.get(f"{API_URL}/list_tables/{selected_db}")
        r.raise_for_status()
        tables = r.json().get("tables", [])
        st.sidebar.write(f"### Tables in `{selected_db}`")
        st.sidebar.write(tables or "No tables returned.")
    except Exception as e:
        st.sidebar.error(f"Error fetching tables: {e}")

selected_table = st.sidebar.text_input("Table name", key="table_name")
if selected_db and selected_table and st.sidebar.button("📋 Show Columns", key="btn_list_columns"):
    try:
        r = requests.get(f"{API_URL}/list_columns/{selected_db}/{selected_table}")
        r.raise_for_status()
        columns = r.json().get("columns", [])
        st.sidebar.write(f"### Columns in `{selected_table}`")
        st.sidebar.write(columns or "No columns returned.")
    except Exception as e:
        st.sidebar.error(f"Error fetching columns: {e}")

# -------- Main: Natural language -> SQL --------
st.header(" GenAI-QueryBuilder")
natural_language_query = st.text_area("Enter your query in plain English:", height=140)

if st.button("⚡ Generate SQL", key="btn_generate"):
    if not natural_language_query.strip():
        st.warning("Please enter a natural language query first.")
    else:
        try:
            with st.spinner("Generating SQL..."):
                payload = {"query": natural_language_query}
                # FastAPI route expects JSON body { "query": "..." }
                resp = requests.post(f"{API_URL}/generate_sql/", json=payload, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                generated_sql = data.get("sql_query") or data.get("sql") or ""
            if generated_sql:
                st.subheader("Generated SQL")
                st.code(generated_sql, language="sql")
            else:
                st.error("No SQL returned by backend.")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
        except Exception as e:
            st.error(f"Error: {e}")

# -------- Main: Manual SQL Execution --------
st.header("🌐 Execute SQL Query")
manual_sql_query = st.text_area("Enter SQL query to execute (or paste generated SQL above):", height=140)

if st.button("🔎 Run Query", key="btn_execute"):
    if not manual_sql_query.strip():
        st.warning("Please enter an SQL query to execute.")
    else:
        try:
            with st.spinner("Executing query..."):
                payload = {"query": manual_sql_query}
                resp = requests.post(f"{API_URL}/execute_sql/", json=payload, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                optimization_tips = data.get("optimization_tips", "")
            if results:
                st.subheader("Query Results")
                # display as dataframe/table; works if results is list of dicts
                try:
                    st.table(results)
                except Exception:
                    st.write(results)
            else:
                st.info("No results returned.")
            if optimization_tips:
                st.markdown("**Optimization tips:**")
                st.write(optimization_tips)
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
