import json
from .decision import decide
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from .auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from .database import Base, engine, get_db
from .models import Decision, Ticket, User
from .schemas import (
    DecisionResponse,
    LoginRequest,
    RegisterRequest,
    TicketCreate,
    TicketResponse,
    TokenResponse,
    UserResponse,
)


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Support Ticket Decision API",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "AI Support Ticket Decision API",
        "status": "running",
    }


# ============================================================
# AUTHENTICATION
# ============================================================

@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@app.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if user is None or not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )


@app.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


# ============================================================
# TICKETS
# ============================================================

@app.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    request: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Create ticket belonging to authenticated user
    ticket = Ticket(
        user_id=current_user.id,
        message=request.message,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    try:
        ai_decision = decide(
            ticket=request.message,
            top_k=4,
        )
    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI decision service failed: {exc}",
        )

    decision = Decision(
        ticket_id=ticket.id,
        action=ai_decision.action,
        reason=ai_decision.reason,
        confidence=ai_decision.confidence,
        sources=json.dumps(
            ai_decision.sources
        ),
    )

    db.add(decision)
    db.commit()
    db.refresh(decision)

    return {
        "id": ticket.id,
        "user_id": ticket.user_id,
        "message": ticket.message,
        "created_at": ticket.created_at,
        "decision": {
            "id": decision.id,
            "ticket_id": decision.ticket_id,
            "action": decision.action,
            "reason": decision.reason,
            "confidence": decision.confidence,
            "sources": json.loads(decision.sources),
            "created_at": decision.created_at,
        },
    }


@app.get(
    "/tickets",
    response_model=list[TicketResponse],
)
def get_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tickets = (
        db.query(Ticket)
        .filter(Ticket.user_id == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    results = []

    for ticket in tickets:
        decision_data = None

        if ticket.decision:
            decision_data = {
                "id": ticket.decision.id,
                "ticket_id": ticket.decision.ticket_id,
                "action": ticket.decision.action,
                "reason": ticket.decision.reason,
                "confidence": ticket.decision.confidence,
                "sources": json.loads(ticket.decision.sources),
                "created_at": ticket.decision.created_at,
            }

        results.append(
            {
                "id": ticket.id,
                "user_id": ticket.user_id,
                "message": ticket.message,
                "created_at": ticket.created_at,
                "decision": decision_data,
            }
        )

    return results


@app.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = (
        db.query(Ticket)
        .filter(
            Ticket.id == ticket_id,
            Ticket.user_id == current_user.id,
        )
        .first()
    )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    decision_data = None

    if ticket.decision:
        decision_data = {
            "id": ticket.decision.id,
            "ticket_id": ticket.decision.ticket_id,
            "action": ticket.decision.action,
            "reason": ticket.decision.reason,
            "confidence": ticket.decision.confidence,
            "sources": json.loads(ticket.decision.sources),
            "created_at": ticket.decision.created_at,
        }

    return {
        "id": ticket.id,
        "user_id": ticket.user_id,
        "message": ticket.message,
        "created_at": ticket.created_at,
        "decision": decision_data,
    }