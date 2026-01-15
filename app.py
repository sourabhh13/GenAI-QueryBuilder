from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from database import list_databases, list_tables, list_columns
from query_generator import generate_sql_query, execute_query

# Initialize FastAPI
app = FastAPI(title="AI SQL Query Generator API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Pydantic models for request validation
class QueryRequest(BaseModel):
    query: str

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "AI SQL Query Generator API is running!"}

# API: List all databases
@app.get("/list_databases/")
def get_databases():
    try:
        return list_databases()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API: List tables in a database
@app.get("/list_tables/{database_name}")
def get_tables(database_name: str):
    try:
        return list_tables(database_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API: List columns in a table
@app.get("/list_columns/{database_name}/{table_name}")
def get_columns(database_name: str, table_name: str):
    try:
        return list_columns(database_name, table_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API: Generate SQL query from Natural Language
@app.post("/generate_sql/")
def generate_sql(request: QueryRequest):
    """Generate SQL from natural language query"""
    try:
        logging.debug(f"Generating SQL for: {request.query}")
        sql_query = generate_sql_query(request.query)
        if sql_query:
            return {"sql_query": sql_query}
        return {"error": "Failed to generate SQL"}
    except Exception as e:
        logging.error(f"Error generating SQL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API: Execute SQL query
@app.post("/execute_sql/")
def execute_sql(request: QueryRequest):
    """Execute the given SQL query and return results in JSON format"""
    try:
        logging.debug(f"Executing SQL: {request.query}")
        result = execute_query(request.query)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error executing SQL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.0", port=8000, reload=True)
