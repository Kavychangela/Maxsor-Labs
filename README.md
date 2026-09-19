# Minimal AI Decision API

An AI-powered support-ticket decision assistant built with **FastAPI, Streamlit, SQLite, JWT authentication, Gemini, and Retrieval-Augmented Generation (RAG)**.

The system accepts a customer support ticket, retrieves relevant policy information from a local knowledge base, asks Gemini to determine the appropriate support action, validates the structured response, stores the decision, and displays the result through a Streamlit frontend.

---

## Features

* User registration and login
* Password hashing with bcrypt
* JWT-based authentication
* Protected API endpoints
* User-specific ticket history
* Cross-user authorization protection
* SQLite database using SQLAlchemy
* Local policy knowledge base
* RAG-based policy retrieval
* Gemini-powered decision generation
* Structured AI decision validation using Pydantic
* Policy source attribution
* Streamlit frontend
* Automated evaluation runner
* Automated tests

---

## Architecture

```text
                    ┌──────────────────────┐
                    │      Streamlit       │
                    │      Frontend        │
                    └──────────┬───────────┘
                               │ HTTP
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │       Backend        │
                    └──────────┬───────────┘
                               │
                  ┌────────────┴────────────┐
                  │                         │
                  ▼                         ▼
          ┌───────────────┐         ┌───────────────┐
          │ JWT / Auth    │         │    SQLite     │
          │               │         │ Users/Tickets │
          └───────────────┘         │  /Decisions   │
                                    └───────────────┘
                  │
                  ▼
          ┌───────────────────┐
          │   RAG Retrieval   │
          │ Local Policy KB   │
          └─────────┬─────────┘
                    │
                    ▼
          ┌───────────────────┐
          │      Gemini       │
          │  Decision Engine  │
          └─────────┬─────────┘
                    │
                    ▼
          ┌───────────────────┐
          │ Pydantic Decision │
          │    Validation     │
          └───────────────────┘
```

---

## Project Structure

```text
intern-project/
│
├── data/
│   ├── tickets.csv
│   └── vector_store.json
│
├── knowledge_base/
│   ├── cancellations.md
│   ├── damaged_goods.md
│   ├── defective_products.md
│   ├── returns.md
│   ├── shipping.md
│   └── wrong_item.md
│
├── src/
│   ├── __init__.py
│   ├── api.py
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── decision.py
│   ├── evaluate.py
│   ├── ingest.py
│   ├── init_db.py
│   ├── models.py
│   ├── retrieval.py
│   ├── schemas.py
│   ├── test_decision.py
│   └── test_retrieval.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_database.py
│   ├── test_decision.py
│   ├── test_retrieval.py
│   └── test_tickets.py
│
├── .env
├── .env.example
├── .gitignore
├── DEVELOPMENT.md
├── README.md
├── requirements.txt
├── sample_test_cases.json
├── streamlit_app.py
└── support_tickets.db
```

`support_tickets.db` is generated locally and should not be committed to Git.

---

## Technology Stack

### Backend

* Python
* FastAPI
* Uvicorn
* SQLAlchemy
* SQLite
* Pydantic

### Authentication

* JWT
* `python-jose`
* bcrypt / Passlib

### AI / RAG

* Google Gemini
* Gemini embeddings
* NumPy
* Local vector store
* Cosine similarity

### Frontend

* Streamlit
* Requests

### Testing

* pytest

---

## Environment Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd intern-project
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell activation is unavailable, use:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env`.

Example:

```text
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET=your_random_jwt_secret
```

Do not commit `.env`.

---

## Initialize the Database

Run:

```powershell
python -m src.init_db
```

Expected output:

```text
Database initialized successfully.
```

The SQLite database contains:

### `users`

```text
id
email
password_hash
created_at
```

### `tickets`

```text
id
user_id
message
created_at
```

### `decisions`

```text
id
ticket_id
action
reason
confidence
sources
created_at
```

---

## Build the RAG Vector Store

The policy documents are stored in:

```text
knowledge_base/
```

Build the local vector store with:

```powershell
python -m src.ingest
```

This generates:

```text
data/vector_store.json
```

The retrieval system:

1. Loads policy documents.
2. Splits them into chunks.
3. Generates embeddings.
4. Stores the embeddings locally.
5. Embeds incoming support tickets.
6. Calculates cosine similarity.
7. Returns the most relevant policy chunks.

---

## Run the FastAPI Backend

Start the API:

```powershell
uvicorn src.api:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### Register

```http
POST /register
```

Example:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Login

```http
POST /login
```

Returns a JWT access token.

### Current User

```http
GET /me
```

Requires:

```text
Authorization: Bearer <token>
```

### Create Ticket

```http
POST /tickets
```

Example:

```json
{
  "message": "My ₹3,500 order arrived damaged yesterday."
}
```

The backend:

```text
Authenticate user
       ↓
Create ticket
       ↓
Retrieve relevant policy
       ↓
Call Gemini
       ↓
Validate decision
       ↓
Store decision
       ↓
Return ticket + decision
```

### Get User Tickets

```http
GET /tickets
```

Returns tickets belonging only to the authenticated user.

### Get Ticket

```http
GET /tickets/{ticket_id}
```

Users cannot access another user's ticket.

---

## Example Decision

Input:

```text
My ₹3,500 order arrived damaged yesterday.
```

Example result:

```json
{
  "action": "REQUEST_PHOTOS",
  "confidence": 1.0,
  "reason": "The damaged order is valued at ₹3,500, which is above ₹2,000, and was reported within the 7-day window. Photos are required before approving a refund or replacement.",
  "sources": [
    "damaged_goods.md"
  ]
}
```

---

## Run the Streamlit Frontend

Start the backend first:

```powershell
uvicorn src.api:app --reload
```

Then open another terminal and run:

```powershell
streamlit run streamlit_app.py
```

The frontend provides:

* Login
* Registration
* New Decision
* AI recommendation
* Confidence
* Reasoning
* Policy sources
* Decision history
* Logout

---

## Evaluation

The supplied evaluation cases are stored in:

```text
sample_test_cases.json
```

Run:

```powershell
python -m src.evaluate
```

The evaluator sends each supplied ticket through the actual decision pipeline and compares the predicted action with the expected action.

Current evaluation result:

```text
S01  PASS
S02  PASS
S03  PASS
S04  PASS
S05  PASS

Accuracy: 5/5 (100.0%)
```

The evaluation does not hardcode predictions into the evaluator.

---

## Testing

Run the test suite with:

```powershell
python -m pytest -v
```

The tests cover:

* Database models
* Registration and authentication
* JWT-protected endpoints
* Ticket creation
* User authorization
* Cross-user ticket access
* Retrieval behavior
* AI decision schema validation

The evaluation runner can be executed separately with:

```powershell
python -m src.evaluate
```

---

## Security Considerations

* Passwords are hashed before storage.
* JWT tokens are required for protected endpoints.
* JWT expiration is configured.
* User IDs are derived from authenticated tokens rather than request payloads.
* Ticket queries are scoped to the authenticated user.
* AI actions are restricted to an explicit allowed-action set.
* AI confidence is validated between `0.0` and `1.0`.
* AI sources are validated against retrieved policy sources.
* API secrets are loaded from environment variables.
* `.env` is excluded from Git.

---

## Design Decisions

### Why local RAG?

The assignment has a small policy knowledge base, so a local vector store is sufficient. A managed vector database would add infrastructure without providing meaningful value for this scope.

### Why FastAPI?

FastAPI provides a simple REST API, request validation, dependency injection, and automatic OpenAPI documentation.

### Why SQLite?

The application has a small scope and does not require a production database. SQLite keeps the project easy to run and evaluate locally.

### Why Pydantic validation?

The LLM output is not trusted blindly. The response is parsed and validated before the decision is persisted.

### Why policy source attribution?

Returning the policy filenames used for a decision makes the AI recommendation easier to inspect and debug.

---

## Limitations

This is a focused take-home implementation rather than a production-scale support platform.

Current limitations include:

* SQLite is intended for the assignment's small scope.
* The local vector store is not designed for very large knowledge bases.
* Gemini API availability and model behavior depend on the configured API.
* AI decisions remain probabilistic and are validated against the allowed schema.
* The current evaluation set contains five supplied sample cases.

---

## Development Notes

See [DEVELOPMENT.md](intern-project/DEVELOPMENT.md) for implementation phases, development workflow, testing, and engineering decisions.
