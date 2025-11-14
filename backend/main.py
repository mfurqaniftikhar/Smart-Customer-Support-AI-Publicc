from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.db import Base, get_db, engine
from backend.models import Lead, Conversation, Order
from backend.llm_client import generate_response
from backend.kb_manager import search_knowledge_base, add_to_knowledge_base, get_kb_stats
from backend.company_manager import build_company_profile
from backend.rag_manager import add_website_data_to_rag, search_rag  

app = FastAPI(title="Customer Support Chatbot")

company_profiles = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    username: str | None = None
    company_profile: dict | None = None

class ChatResponse(BaseModel):
    response: str
    kb_context: list

class LeadRequest(BaseModel):
    name: str
    email: str  

class OrderRequest(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    house_number: str | None = None
    product_details: str
    additional_notes: str | None = None
    username: str | None = None

class MessageResponse(BaseModel):
    message: str

class CompanySetupRequest(BaseModel):
    company_name: str
    website_url: str
    username: str

class CompanyProfileResponse(BaseModel):
    success: bool
    profile: dict | None = None
    error: str | None = None

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized")

@app.post("/setup_company", response_model=CompanyProfileResponse)
async def setup_company(request: CompanySetupRequest):
    try:
        print(f"🏢 Setting up company: {request.company_name}")
        print(f"🌐 Website: {request.website_url}")
        
        profile = build_company_profile(request.website_url)

        if profile.get("error"):
            return CompanyProfileResponse(success=False, profile=None, error=profile["error"])
        
        if request.company_name:
            profile["company_name"] = request.company_name
        
        company_profiles[request.username] = profile
        print(f"✅ Company profile created for user: {request.username}")

        if "chunks" in profile and profile["chunks"]:
            add_website_data_to_rag(request.website_url, profile["chunks"])
            print(f"💾 RAG data saved for {request.website_url}")
        else:
            print("⚠️ No chunks found to add to RAG.")

        return CompanyProfileResponse(success=True, profile=profile, error=None)

    except Exception as e:
        print(f"❌ Error setting up company: {e}")
        return CompanyProfileResponse(success=False, profile=None, error=str(e))

@app.get("/get_company_profile/{username}")
async def get_company_profile(username: str):
    profile = company_profiles.get(username)
    if profile:
        return {"success": True, "profile": profile}
    return {"success": False, "profile": None, "message": "No company profile found for this user"}

@app.delete("/clear_company_profile/{username}")
async def clear_company_profile(username: str):
    if username in company_profiles:
        del company_profiles[username]
        return {"success": True, "message": "Company profile cleared"}
    return {"success": False, "message": "No profile found"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session: AsyncSession = Depends(get_db)):
    query = request.query.strip()
    username = request.username or "guest"

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        company_profile = company_profiles.get(username) or request.company_profile

        # Search knowledge base
        kb_results = search_knowledge_base(query, top_k=3)
        kb_texts = []
        if kb_results and isinstance(kb_results, list):
            for res in kb_results:
                if isinstance(res, dict) and "text" in res:
                    kb_texts.append(str(res["text"]))
                elif isinstance(res, str):
                    kb_texts.append(res)

        # Search RAG
        rag_results = search_rag(query, top_k=3)
        rag_texts = []
        if rag_results and isinstance(rag_results, list):
            for res in rag_results:
                if isinstance(res, str):
                    rag_texts.append(res)
                elif isinstance(res, dict):
                    rag_texts.append(str(res.get("text", res)))

        # Build context - FIX THE JOIN ERROR
        kb_context_str = "\n".join(kb_texts) if kb_texts else "No KB info."
        rag_context_str = "\n".join(rag_texts) if rag_texts else "No RAG data."
        
        combined_context = f"""Knowledge Base Context:
{kb_context_str}

RAG Retrieved Context:
{rag_context_str}"""

        system_prompt = "You are a helpful customer support chatbot."
        
        if company_profile:
            company_name = company_profile.get("company_name", "our company")
            tone = company_profile.get("tone", "professional and helpful")
            about = company_profile.get("short_about", "")
            products = company_profile.get("products", [])
            
            # Ensure products is a list
            if not isinstance(products, list):
                products = []

            products_str = ", ".join(products) if products else "various products"

            system_prompt = f"""You are a customer support chatbot for {company_name}.

Company Info:
- About: {about}
- Products/Services: {products_str}

Tone: {tone}

Instructions:
- Use both the Knowledge Base and RAG context to answer.
- Be helpful and concise.
- If unsure, say: "I'm not sure about that, please contact support."
"""

        user_prompt = f"""User Question: {query}

{combined_context}

Please provide a helpful response based on the above context."""

        # Generate response with Ollama
        print(f"🤖 Generating response for: {query[:50]}...")
        answer = generate_response(
            message=user_prompt,
            system_prompt=system_prompt
        )
        print(f"✅ Response generated: {answer[:100]}...")

        # Save to database
        new_chat = Conversation(username=username, user_message=query, bot_response=answer)
        session.add(new_chat)
        await session.commit()

        # Return combined context for frontend display
        all_context = kb_texts + rag_texts

        return {"response": answer, "kb_context": all_context}

    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/chat_history/{username}")
async def get_chat_history(username: str, session: AsyncSession = Depends(get_db)):
    try:
        result = await session.execute(
            select(Conversation).where(Conversation.username == username).order_by(Conversation.created_at.asc())
        )
        chats = result.scalars().all()
        return {"history": [{"user": c.user_message, "bot": c.bot_response} for c in chats]}
    except Exception as e:
        print(f"❌ Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_chat")
async def save_chat(username: str, user_message: str, bot_response: str, session: AsyncSession = Depends(get_db)):
    new_chat = Conversation(username=username, user_message=user_message, bot_response=bot_response)
    session.add(new_chat)
    await session.commit()
    return {"status": "saved"}

@app.post("/order", response_model=MessageResponse)
async def place_order(order: OrderRequest, session: AsyncSession = Depends(get_db)):
    try:
        new_order = Order(
            username=order.username or "guest",
            name=order.name,
            email=order.email,
            phone=order.phone,
            address=order.address,
            house_number=order.house_number,
            product_details=order.product_details,
            additional_notes=order.additional_notes,
            status="pending"
        )
        session.add(new_order)
        await session.commit()
        print(f"✅ New order received from {order.name} - {order.email}")
        return {"message": "Order placed successfully!"}
    except Exception as e:
        await session.rollback()
        print(f"❌ Error placing order: {e}")
        raise HTTPException(status_code=500, detail=f"Error placing order: {str(e)}")

@app.get("/orders")
async def get_orders(session: AsyncSession = Depends(get_db)):
    try:
        result = await session.execute(select(Order).order_by(Order.created_at.desc()))
        orders = result.scalars().all()
        return {
            "orders": [
                {
                    "id": o.id,
                    "username": o.username,
                    "name": o.name,
                    "email": o.email,
                    "phone": o.phone,
                    "address": o.address,
                    "house_number": o.house_number,
                    "product_details": o.product_details,
                    "additional_notes": o.additional_notes,
                    "status": o.status,
                    "created_at": o.created_at.isoformat()
                }
                for o in orders
            ]
        }
    except Exception as e:
        print(f"❌ Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_kb", response_model=MessageResponse)
async def add_kb(text: str = Form(...)):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        add_to_knowledge_base(text)
        return {"message": "Knowledge added successfully (KB + optional RAG)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding knowledge: {str(e)}")

@app.post("/lead", response_model=MessageResponse)
async def add_lead(data: LeadRequest, session: AsyncSession = Depends(get_db)):
    try:
        new_lead = Lead(name=data.name, email=data.email, message="")
        session.add(new_lead)
        await session.commit()
        return {"message": "Lead saved successfully."}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving lead: {str(e)}")

@app.get("/kb_stats")
async def kb_stats():
    try:
        return get_kb_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "Customer Support Chatbot Backend is running 🚀"}

print("🚀 FastAPI Customer Support Chatbot Backend is running")
print("✅ RAG system integrated with FAISS + PKL persistence")