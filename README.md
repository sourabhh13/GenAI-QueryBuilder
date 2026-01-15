# **GenAI-QueryBuilder**

**GenAI-QueryBuilder** allows users to generate and execute **SQL queries from natural-language prompts** using **Google Gemini**.  
It combines **AI, FastAPI, Streamlit, and MySQL** into a single system for intelligent data exploration.

The goal is to make databases accessible to **non-technical users** while still producing **optimized, production-grade SQL** for engineers and analysts.

---

## **Features**

- Convert plain English into optimized SQL  
- Execute queries directly on a live database  
- View results in tabular format  
- Browse databases, tables, and columns  
- Uses live schema to improve accuracy  
- Avoids inefficient queries such as `SELECT *`  

---

## **Tech Stack**

- **LLM**: Google Gemini  
- **Backend**: FastAPI  
- **Frontend**: Streamlit  
- **Database**: MySQL  
- **ORM**: SQLAlchemy  
- **Environment**: python-dotenv  

---

## **System Architecture**

User
↓
Streamlit UI
↓
FastAPI Backend
↓
Google Gemini (SQL Generation)
↓
MySQL Database
↓
Results returned to UI

## **Project Structure**
├── app.py
├── database.py
├── query_generator.py
├── ui.py
├── requirements.txt
├── .env

## **Environment Setup**

Create a `.env` file in the project root:
MYSQL_HOST=127.0.0.0
MYSQL_USER=genai_user
MYSQL_PASSWORD=StrongPass123!
MYSQL_DATABASE=test_db
MYSQL_PORT=3306

GEMINI_API_KEY=your_api_key_here


---

## **Installation**

```bash
git clone https://github.com/sourabhh13/GenAi-QueryBuilder.git
cd GenAi-QueryBuilder
pip install -r requirements.txt

Running the Backend
uvicorn app:app --reload

Running the Frontend
streamlit run ui.py
