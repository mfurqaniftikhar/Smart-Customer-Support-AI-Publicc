# 🤖 Smart Customer Support AI

An **AI-powered Customer Support System** built with **FastAPI** and **Streamlit**, designed to automate customer interactions, manage orders and leads, and dynamically build company profiles from website data using LLMs.

---

## 🚀 Features

✅ **LLM-Powered Chatbot** — Provides intelligent responses with contextual understanding.  
✅ **Dynamic Company Profiles** — Automatically extract tone, about info, and products from a business website.  
✅ **Knowledge Base System** — Store, search, and manage support-related data.  
✅ **Order Management** — Capture and view orders placed by customers.  
✅ **Lead Management** — Save potential customer leads automatically.  
✅ **FastAPI Backend + Streamlit Frontend** — Complete and modern full-stack AI system.  
✅ **SQLite + SQLAlchemy Async** — Lightweight, fast, and reliable database.  

---

## 🏗️ Project Structure

Smart-Customer-Support-AI/
│
├── backend/
│ ├── main.py # FastAPI app (chat, orders, KB, company setup)
│ ├── db.py # Async DB connection setup
│ ├── models.py # Database models
│ ├── llm_client.py # LLM API (Gemini / OpenAI)
│ ├── kb_manager.py # Knowledge base manager
│ ├── company_manager.py # Extract company info from website
│ └── init_db.py # Database initialization script
│
├── frontend/
│ └── frontend.py # Streamlit-based customer support UI
│
├── bot.db # SQLite database (auto-created)
└── requirements.txt # Python dependencies

yaml
Copy code

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/Smart-Customer-Support-AI.git
cd Smart-Customer-Support-AI
2️⃣ Create a Virtual Environment
bash
Copy code
python -m venv venv
source venv/bin/activate       # (Linux/Mac)
venv\Scripts\activate          # (Windows)
3️⃣ Install Requirements
bash
Copy code
pip install -r requirements.txt
4️⃣ Run the Backend (FastAPI)
bash
Copy code
uvicorn backend.main:app --reload
Your backend will run at 👉 http://127.0.0.1:8000

5️⃣ Run the Frontend (Streamlit)
bash
Copy code
streamlit run frontend/frontend.py
Your frontend will open at 👉 http://localhost:8501

🧩 Environment Variables
Create a .env file in the project root:

bash
Copy code
DATABASE_URL=sqlite+aiosqlite:///./bot.db
API_KEY=your_gemini_or_openai_key_here
🏢 Company Profile Setup Example
You can setup a company profile directly via API or frontend:

json
Copy code
{
  "company_name": "Premium Fashion Hub",
  "website_url": "https://www.premiumfashionhub.com",
  "username": "furqan"
}
Once setup, the chatbot automatically adapts its tone and responses to match the company's brand and style.

📡 API Endpoints Overview
Endpoint	Method	Description
/chat	POST	Chat with AI support bot
/order	POST	Place a new order
/lead	POST	Capture customer lead
/add_kb	POST	Add new knowledge base entry
/kb_stats	GET	Get KB stats
/setup_company	POST	Build company profile from website
/get_company_profile/{username}	GET	Retrieve company profile
/orders	GET	View all orders (admin)

🧠 LLM Integration
This project uses a modular LLM client (llm_client.py) to connect with APIs like:

Google Gemini API

OpenAI GPT models

You can customize the prompt and tone inside generate_response().

🧰 Tech Stack
Layer	Technology
Frontend	Streamlit
Backend	FastAPI
Database	SQLite (Async SQLAlchemy)
AI/LLM	Gemini API or OpenAI GPT
Web Scraping	BeautifulSoup + Requests
Environment	Python 3.10+
