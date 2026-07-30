from sqlalchemy.orm import Session
from db.models import ChatMessage, SessionState

def save_message(db: Session, session_id: str, role: str, content: str):
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()

def get_recent_history(db: Session, session_id: str, limit: int = 10):
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()  # chronological order
    return [{"role": r.role, "content": r.content} for r in rows]

def get_prev_intent(db: Session, session_id: str):
    state = db.query(SessionState).filter(SessionState.session_id == session_id).first()
    return state.prev_intent if state else None

def set_prev_intent(db: Session, session_id: str, intent: str):
    state = db.query(SessionState).filter(SessionState.session_id == session_id).first()
    if state:
        state.prev_intent = intent
    else:
        state = SessionState(session_id=session_id, prev_intent=intent)
        db.add(state)
    db.commit()