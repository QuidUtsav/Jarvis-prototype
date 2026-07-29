from fastapi import FastAPI
from pydantic import BaseModel
from core.generation import generate_response
from intent_routing.needs_retrieval import handle_retrieval
from intent_routing.needs_web import web_search
from intent_routing.needs_tool import handle_tool

app = FastAPI()
sessions={}
last_5_conversation_history=[]
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def update_history(history, query, result):
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": result})
    return history[-10:]
def classify_intent(query,prev_intent):
    
    system_prompt = (
            "You are an expert intent classification routing agent. "
            "Your job is to analyze a user query and output EXACTLY one of these five tags: "
            "[needs_retrieval, needs_web, chat, direct_answer, needs_tool]. "
            "Do not include any other text, explanation, or punctuation."
        )
        
    prompt = f"""Classify the user query into one of the following intents:
    - needs_retrieval: If the user asks about personal documents, uploaded files, or private data.
    - needs_web: If the user asks about real-time events, weather, news, or things requiring a Google search.
    - needs_tool: If the user wants to perform a local action — open an application, read/inspect a local file, list a directory, set a reminder, or anything requiring interaction with the local system rather than the internet or stored documents.

    Examples:
    Query: Open Firefox for me
    Intent: needs_tool

    Query: How many lines does report.txt have?
    Intent: needs_tool

    Query: List what's in my downloads folder
    Intent: needs_tool
    
    - chat: If it's a greeting, casual banter, or small talk.
    - direct_answer: If it's a general knowledge question, logic puzzle, or creative task that requires no external data.

    Examples:
    Query: Hello there!
    Intent: chat

    Query: What is the weather in Pokhara right now?
    Intent: needs_web

    Query: Sumarize the PDF report I uploaded yesterday.
    Intent: needs_retrieval

    Query: summarize the document i uploaded
    Intent: needs_retrieval

    Query: Can you check in the internet?
    Intent: needs_web
    
    Query: Who is the current prime minister of Nepal?
    Intent: needs_web

    Query: Who is the CEO of OpenAI right now?
    Intent: needs_web

    Query: What happened in the news today?
    Intent: needs_web
    
    Query : could you sumarize the document i uploaded
    intent : needs_retrieval

    Query: what does the file say about X
    Intent: needs_retrieval

    Query: could you go through the document and find X
    Intent: needs_retrieval

    Query: What is the capital of Nepal
    Intent: direct_answer

    Previous intent: {prev_intent if prev_intent else "none"}

    Query: {query}
    Intent:"" """

    return generate_response(prompt, system_prompt=system_prompt,max_new_tokens=20,conversation_history=None).strip()

def update_history(history, query, result):
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": result})
    return history[-10:]
def update_session(session,session_id,query,intent,result):
    session["history"]=update_history(session["history"],query,result)
    session["prev_intent"]=intent
    sessions[session_id]=session
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
def chat(request: ChatRequest):
    session = sessions.get(request.session_id, {"history": [], "prev_intent": None})

    intent = classify_intent(request.query,session["prev_intent"])
    if intent=="chat" or intent=="direct_answer":
         
        response_text = generate_response(request.query,system_prompt=f"You are Operus. You are a helpful assistant.",max_new_tokens=200,conversation_history=session["history"])
        result ={"response":response_text,
                 "intent":intent}
        update_session(session=session,session_id=request.session_id,query=request.query,intent=intent,result=response_text)
        return result
    elif intent=="needs_retrieval":
        top_relevant_chunk = handle_retrieval(request.query)
         
        response_text = generate_response(query=request.query,system_prompt=f"You are Operus. You are a helpful assistant. summaraize this given document{top_relevant_chunk}",max_new_tokens=200,conversation_history=session["history"])
        result ={"response":response_text,
                 "intent":intent}
        update_session(session=session,session_id=request.session_id,query=request.query,intent=intent,result=response_text)
        return result
    elif intent=="needs_web":
         
        response_text = web_search(request.query,session["history"])
        result ={"response":response_text,
                 "intent":intent}
        update_session(session=session,session_id=request.session_id,query=request.query,intent=intent,result=response_text)
        return result
    
    elif intent=="needs_tool":
        response_text = handle_tool(request.query)
        result = {"response": response_text, "intent": intent}
        update_session(session=session, session_id=request.session_id, query=request.query, intent=intent, result=response_text)
        return result
    
    return {"message":"did not understand could you clarify your intent."}

@app.get("/health")
def health():
    return {"status":"okay"}