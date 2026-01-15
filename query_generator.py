import os
import sqlparse
import re
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from database import engine, list_databases, list_tables, list_columns
from google import genai  #  Gemini SDK

# Load environment variables
load_dotenv()

# Gemini API Key
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Limits to avoid token limit issues
MAX_TABLES = 5
MAX_COLUMNS_PER_TABLE = 5

# Candidate models to try (order: prefer newer, but fall back to older)
MODEL_CANDIDATES = ["gemini-2.5-pro", "gemini-1.5", "gemini-1.0", "gemini-1"]

def _extract_text_from_response(resp) -> str:
    """
    Extract text from several common GenAI response shapes safely.
    """
    if resp is None:
        return ""
    # direct .text (common)
    try:
        text = getattr(resp, "text", None)
        if isinstance(text, str) and text.strip():
            return text
    except Exception:
        pass

    # newer shape: resp.output -> list -> content -> list -> dict/text
    try:
        out = getattr(resp, "output", None)
        if out and isinstance(out, (list, tuple)) and len(out) > 0:
            first = out[0]
            content = getattr(first, "content", None) or (first.get("content") if isinstance(first, dict) else None)
            if content and isinstance(content, (list, tuple)) and len(content) > 0:
                c0 = content[0]
                if isinstance(c0, dict) and "text" in c0:
                    return c0["text"]
                if hasattr(c0, "text"):
                    return getattr(c0, "text")
    except Exception:
        pass

    # fallback to string representation
    try:
        return str(resp)
    except Exception:
        return ""

def clean_sql_output(response_text):
    """
    Remove triple-backtick fences (```sql ... ```) and extract the first SQL statement
    (SELECT/INSERT/UPDATE/DELETE/WITH). If none found, return cleaned text.
    """
    if not response_text:
        return ""

    # Remove common markdown fences like ```sql ... ``` or ```
    stripped = re.sub(r"```(?:sql)?\s*(.*?)\s*```", r"\1", response_text, flags=re.DOTALL | re.IGNORECASE)
    # Remove inline backticks
    stripped = re.sub(r"`(.+?)`", r"\1", stripped, flags=re.DOTALL)

    # Try to find a full statement ending with semicolon
    match = re.search(r"((?:WITH|SELECT|INSERT|UPDATE|DELETE)\s.*?;)", stripped, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: try to find a SELECT without semicolon
    match2 = re.search(r"(SELECT\s.*?$)", stripped, flags=re.IGNORECASE | re.MULTILINE)
    if match2:
        return match2.group(1).strip()

    # Last fallback: return the cleaned stripped text
    return stripped.strip()

def get_limited_schema():
    """
    Fetches a reduced database schema to fit within token limits.
    """
    schema = {}
    databases = list_databases().get("databases", [])
    for db in databases:
        schema[db] = {}
        tables = list_tables(db).get("tables", [])[:MAX_TABLES]
        for table in tables:
            schema[db][table] = list_columns(db, table).get("columns", [])[:MAX_COLUMNS_PER_TABLE]
    return schema

def generate_sql_query(nl_query):
    """Converts a natural language query into an optimized SQL query using Gemini."""
    schema = get_limited_schema()
    schema_text = "\n".join([
        f"{db}.{table}: {', '.join(columns)}"
        for db, tables in schema.items()
        for table, columns in tables.items()
    ])
    prompt = f"""
You are an SQL expert. Convert the following natural language query into an optimized MySQL query.
- Use indexing where applicable.
- Prefer JOINS over subqueries.
- Use GROUP BY for aggregations if needed.
- Avoid SELECT * unless explicitly requested.
- Return ONLY the SQL query (no explanation).

Database Schema (Limited View):
{schema_text}

User Query: {nl_query}

SQL Query:
"""

    # 1) Try any models that exist on the client (list), then fall back to MODEL_CANDIDATES
    candidates = []
    try:
        available = genai_client.models.list()
        for m in available:
            name = getattr(m, "name", None) or str(m)
            if name:
                candidates.append(name)
    except Exception:
        # ignore listing errors; we'll fall back to MODEL_CANDIDATES
        pass

    for m in MODEL_CANDIDATES:
        if m not in candidates:
            candidates.append(m)

    # 2) Try each candidate using supported call shapes
    errors = []
    for model_name in candidates:
        if not model_name:
            continue
        try:
            # Preferred new API: generate_content
            models_obj = getattr(genai_client, "models", None)
            if models_obj and hasattr(models_obj, "generate_content"):
                resp = genai_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                raw = _extract_text_from_response(resp)
                sql = clean_sql_output(raw)
                if sql:
                    return sql

            # Older shape: generate (messages)
            if models_obj and hasattr(models_obj, "generate"):
                resp = genai_client.models.generate(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a SQL optimization expert."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0
                )
                raw = _extract_text_from_response(resp)
                sql = clean_sql_output(raw)
                if sql:
                    return sql

        except Exception as e:
            errors.append((model_name, str(e)))
            # try next model

    # 3) Nothing worked — return helpful error for debugging
    return f"Error generating SQL query: no usable model/method found. Tried: {candidates}. Errors: {errors}"

def execute_query(sql_query):
    """
    Executes a validated and optimized SQL query and returns JSON-serializable results.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            rows = result.fetchall()

            # Get column names
            column_names = result.keys()

            # Convert results into a list of dictionaries
            formatted_results = [dict(zip(column_names, row)) for row in rows]

        return {"results": formatted_results}
    except SQLAlchemyError as e:
        return {"error": str(e)}
