from fastapi import FastAPI
from pydantic import BaseModel
from core.generation import generate_response
from intent_routing.needs_retrieval import handle_retrieval
from intent_routing.needs_web import web_search
from intent_routing.needs_tool import handle_tool
from fastapi import Depends
from sqlalchemy.orm import Session
from db.database import get_db, engine, Base
from db.models import ChatMessage, SessionState
from db import memory_store

Base.metadata.create_all(bind=engine) 

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def classify_intent(query,prev_intent):
    
    system_prompt = (
            "You are an expert intent classification routing agent. "
            "Your job is to analyze a user query and output EXACTLY one of these five tags: "
            "[needs_retrieval, needs_web, chat, direct_answer, needs_tool]. "
            "Do not include any other text, explanation, or punctuation."
        )
        
    prompt = f"""Classify the user query into one of these five intents: needs_retrieval, needs_web, needs_tool, chat, direct_answer.

Definitions:
- needs_retrieval: user asks about personal documents, uploaded files, or private data.
- needs_web: user asks about real-time events, weather, news, or anything requiring a web search.
- needs_tool: user wants a local action — open an app, read/inspect a local file, list a directory, set a reminder.
- chat: greeting, casual banter, small talk.
- direct_answer: general knowledge, logic puzzle, or creative task needing no external data.

Examples:
Query: Hello there!
Intent: chat

Query: hi
Intent: chat

Query: hey, how are you
Intent: chat

Query: good morning
Intent: chat

Query: Open Firefox for me
Intent: needs_tool

Query: How many lines does report.txt have?
Intent: needs_tool

Query: List what's in my downloads folder
Intent: needs_tool

Query: What is the weather in Pokhara right now?
Intent: needs_web

Query: Who is the current prime minister of Nepal?
Intent: needs_web

Query: What happened in the news today?
Intent: needs_web

Query: could you summarize the document i uploaded
Intent: needs_retrieval

Query: what does the file say about X
Intent: needs_retrieval

Query: What is the capital of Nepal
Intent: direct_answer

Previous intent: {prev_intent if prev_intent else None}
Query: {query}
Intent:"""

    return generate_response(prompt, system_prompt=system_prompt,max_new_tokens=20,conversation_history=None).strip()

def update_history(history, query, result):
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": result})
    return history[-10:]


def update_session(db, session_id, query, intent, result):
    memory_store.save_message(db, session_id, "user", query)
    memory_store.save_message(db, session_id, "assistant", result)
    memory_store.set_prev_intent(db, session_id, intent)
    
class ChatRequest(BaseModel):
    query:str
    session_id:str


class ChatResponse(BaseModel):
    response:str
    intent:str
    session_id:str

from fastapi.responses import FileResponse

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

@app.post("/chat")
def chat(request: ChatRequest,db:Session= Depends(get_db)):
    
    history = memory_store.get_recent_history(db, request.session_id, limit=10)
    prev_intent = memory_store.get_prev_intent(db, request.session_id)

    intent = classify_intent(request.query,prev_intent)

    if intent == "chat" or intent == "direct_answer":
            response_text = generate_response(request.query, system_prompt="You are Operus. You are a helpful assistant.", max_new_tokens=200, conversation_history=history)
            update_session(db, request.session_id, request.query, intent, response_text)
            return {"response": response_text, "intent": intent}

    elif intent == "needs_retrieval":
            top_relevant_chunk = handle_retrieval(request.query)
            response_text = generate_response(query=request.query, system_prompt=f"You are Operus. You are a helpful assistant. summaraize this given document{top_relevant_chunk}", max_new_tokens=200, conversation_history=history)
            update_session(db, request.session_id, request.query, intent, response_text)
            return {"response": response_text, "intent": intent}

    elif intent == "needs_web":
            response_text = web_search(request.query, history)
            update_session(db, request.session_id, request.query, intent, response_text)
            return {"response": response_text, "intent": intent}

    elif intent == "needs_tool":
            response_text = handle_tool(request.query)
            update_session(db, request.session_id, request.query, intent, response_text)
            return {"response": response_text, "intent": intent}

    return {"message": "did not understand could you clarify your intent."}
    

@app.get("/health")
def health():
    return {"status":"okay"}