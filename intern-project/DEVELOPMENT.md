# Development Notes

## Project

Minimal AI Decision API with Streamlit, FastAPI, JWT, SQLite, Gemini, and RAG.

---

## 1. Development Objective

The objective was to build a small end-to-end AI support-ticket decision system that:

1. Authenticates users.
2. Accepts support tickets.
3. Retrieves relevant policy information.
4. Uses Gemini to generate a structured support decision.
5. Validates the AI response.
6. Persists the ticket and decision.
7. Displays the result through Streamlit.
8. Provides an evaluation runner and automated tests.

The implementation intentionally avoids unnecessary infrastructure because the assignment focuses on a small, understandable scope.

---

## 2. Development Approach

The project was developed incrementally.

### Phase 1 — Project Setup

Created the basic project structure:

```text
data/
knowledge_base/
src/
tests/
```

Added:

* `requirements.txt`
* `.env`
* `.env.example`
* `.gitignore`
* `README.md`
* `DEVELOPMENT.md`
* `streamlit_app.py`

---

## 3. Database Implementation

SQLAlchemy was used with SQLite.

The database contains three main entities:

```text
users
tickets
decisions
```

Relationships:

```text
User
 │
 └── Ticket
       │
       └── Decision
```

A ticket belongs to one user.

A decision belongs to one ticket.

The decision relationship is one-to-one in the current implementation.

---

## 4. Authentication

Authentication uses:

* bcrypt password hashing
* JWT access tokens
* `python-jose`
* FastAPI's HTTP Bearer authentication

### Registration

The registration flow:

```text
Email + Password
       ↓
Check duplicate email
       ↓
Hash password
       ↓
Store user
```

Plain-text passwords are not stored.

### Login

The login flow:

```text
Email + Password
       ↓
Find user
       ↓
Verify password hash
       ↓
Generate JWT
       ↓
Return access token
```

### Protected endpoints

Protected endpoints use the JWT to identify the authenticated user.

The user ID is taken from the token rather than trusting a user ID supplied by the client.

---

## 5. Authorization

Ticket access is scoped to the authenticated user.

For example:

```text
Alice
  │
  └── Ticket 1

Bob
  │
  └── Ticket 2
```

Alice's token cannot retrieve Bob's ticket.

The API checks both:

```text
ticket.id
AND
ticket.user_id == current_user.id
```

This prevents users from accessing another user's ticket by simply changing the ticket ID.

---

## 6. Knowledge Base

The policy documents supplied with the assignment are stored under:

```text
knowledge_base/
```

Current policy files:

```text
cancellations.md
damaged_goods.md
defective_products.md
returns.md
shipping.md
wrong_item.md
```

The documents contain the business rules used by the AI decision system.

---

## 7. RAG Implementation

The retrieval system was intentionally implemented without LangChain, LlamaIndex, Pinecone, or another external vector database.

The pipeline is:

```text
Policy Markdown Files
        ↓
Document Loading
        ↓
Chunking
        ↓
Gemini Embeddings
        ↓
Local Vector Store
        ↓
Ticket Embedding
        ↓
Cosine Similarity
        ↓
Top-K Policy Chunks
```

The vector store is stored locally as:

```text
data/vector_store.json
```

It can be regenerated using:

```powershell
python -m src.ingest
```

---

## 8. Decision Engine

The decision engine is implemented in:

```text
src/decision.py
```

The process is:

```text
Ticket
  ↓
Retrieve relevant policy
  ↓
Build policy context
  ↓
Construct decision prompt
  ↓
Gemini
  ↓
JSON response
  ↓
JSON parsing
  ↓
Pydantic validation
  ↓
Allowed-action validation
  ↓
Source validation
  ↓
AIDecision
```

---

## 9. Structured AI Output

The AI response is represented by the `AIDecision` Pydantic model.

The required fields are:

```text
action
confidence
reason
sources
```

Confidence is constrained to:

```text
0.0 <= confidence <= 1.0
```

The action must belong to the predefined action vocabulary.

Examples include:

```text
REQUEST_PHOTOS
APPROVE_RETURN
OPEN_SHIPPING_INVESTIGATION
REPLACE_CORRECT_ITEM
NEEDS_MORE_INFORMATION
```

This prevents arbitrary model output from being directly stored as an application decision.

---

## 10. Source Validation

The model is instructed to return policy filenames used for the decision.

The application verifies that returned sources are actually among the retrieved policy sources.

For example:

```text
Retrieved:
damaged_goods.md

AI:
sources = ["damaged_goods.md"]

Result:
Valid
```

If the AI references a source that was not retrieved, the decision is rejected.

---

## 11. Insufficient Information

The system explicitly supports:

```text
NEEDS_MORE_INFORMATION
```

This is important because the model should not invent missing ticket information.

For example:

```text
I want to return this.
```

does not provide enough information to determine the correct return policy.

The evaluation runner confirms that this case produces:

```text
NEEDS_MORE_INFORMATION
```

---

## 12. Streamlit Frontend

The frontend is implemented in:

```text
streamlit_app.py
```

The application currently provides:

### Authentication

```text
Login
Register
Logout
```

### New Decision

The user enters a support ticket.

The frontend sends:

```http
POST /tickets
```

with the JWT.

The response is displayed as:

```text
Action
Confidence
Reasoning
Policy Sources
```

### History

The frontend calls:

```http
GET /tickets
```

and displays the authenticated user's previous tickets and decisions.

---

## 13. Testing Strategy

Testing is split into two levels.

### Automated tests

Run:

```powershell
python -m pytest -v
```

These cover application behavior such as:

* database tables
* authentication
* ticket creation
* protected routes
* authorization
* retrieval
* decision schema validation

### AI evaluation

Run:

```powershell
python -m src.evaluate
```

This executes the supplied evaluation cases against the real decision pipeline.

The evaluator does not hardcode the predicted action.

---

## 14. Evaluation Result

The supplied five evaluation cases currently produce:

```text
S01 → PASS
S02 → PASS
S03 → PASS
S04 → PASS
S05 → PASS
```

Result:

```text
Accuracy: 5/5 (100.0%)
```

Cases include:

```text
S01
₹3,500 damaged order
→ REQUEST_PHOTOS

S02
Unopened non-food item returned within the policy window
→ APPROVE_RETURN

S03
Shipment dispatched 9 days ago and not delivered
→ OPEN_SHIPPING_INVESTIGATION

S04
Wrong item received
→ REPLACE_CORRECT_ITEM

S05
Insufficient return information
→ NEEDS_MORE_INFORMATION
```

---

## 15. API Testing

The FastAPI API can be tested interactively using:

```text
http://127.0.0.1:8000/docs
```

Important manual authorization test:

```text
1. Register/login as User A.
2. Create a ticket.
3. Register/login as User B.
4. Attempt to access User A's ticket using User B's token.
5. Verify that access is rejected.
```

This cross-user test was verified during development.

---

## 16. Error Handling

The application handles several failure conditions:

### Authentication failure

Invalid credentials result in an authentication error.

### Invalid JWT

Invalid or expired JWTs are rejected.

### Missing AI API key

The decision engine raises an explicit configuration error when the Gemini API key is missing.

### Empty Gemini response

An empty AI response is treated as a decision-service failure.

### Invalid JSON

If Gemini returns invalid JSON, the decision is rejected.

### Invalid AI action

If Gemini returns an action outside the allowed action set, the decision is rejected.

### Invalid sources

If Gemini references sources that were not retrieved, the decision is rejected.

---

## 17. Environment Variables

The application uses:

```text
GEMINI_API_KEY
JWT_SECRET
```

They are stored in `.env`.

`.env` should never be committed to Git.

The repository contains:

```text
.env.example
```

with placeholder values.

---

## 18. Local Development Workflow

### Terminal 1 — Backend

```powershell
.\venv\Scripts\Activate.ps1

python -m src.init_db

python -m src.ingest

uvicorn src.api:app --reload
```

### Terminal 2 — Frontend

```powershell
.\venv\Scripts\Activate.ps1

streamlit run streamlit_app.py
```

### Testing

```powershell
python -m pytest -v
```

### Evaluation

```powershell
python -m src.evaluate
```

---

## 19. Dependency / Environment Note

The project should always use the same Python environment for installation and testing.

Recommended commands:

```powershell
python -m pip install -r requirements.txt
```

and:

```powershell
python -m pytest -v
```

Using `python -m pytest` ensures pytest runs through the currently selected Python interpreter.

Verify the Gemini SDK with:

```powershell
python -m pip show google-genai
```

---

## 20. Engineering Tradeoffs

### SQLite instead of PostgreSQL

SQLite was selected because the assignment has a small scope and does not require concurrent production workloads.

### Local vector store instead of a managed database

The policy knowledge base is small, so local embeddings and cosine similarity are sufficient.

### Direct Gemini SDK instead of an LLM framework

Using the Gemini SDK directly keeps the decision pipeline explicit and makes the application easier to understand.

### Streamlit instead of a separate frontend framework

Streamlit is sufficient for the assignment's UI requirements and reduces frontend complexity.

---

## 21. Known Scope Limitations

This implementation is designed for the take-home assignment and is not intended to be a production-scale support platform.

Potential future improvements include:

* PostgreSQL for production persistence
* Redis or another shared cache
* More sophisticated vector indexing
* Background AI processing
* Rate limiting
* Observability and structured logging
* Automated CI/CD
* More extensive evaluation datasets
* Stronger transaction handling around AI failures

These are intentionally outside the current small-scope implementation.

---

## 22. Final Verification Checklist

Before submission:

```text
[ ] .env is not committed
[ ] .env.example exists
[ ] requirements.txt is up to date
[ ] Database initializes successfully
[ ] RAG ingestion works
[ ] FastAPI starts successfully
[ ] Streamlit starts successfully
[ ] Registration works
[ ] Login works
[ ] JWT protection works
[ ] Ticket creation works
[ ] AI decision works
[ ] Decision is persisted
[ ] History works
[ ] Cross-user authorization works
[ ] Automated tests pass
[ ] Evaluation runner works
[ ] Supplied evaluation cases produce expected actions
[ ] README contains setup instructions
```

---

## 23. Submission Commands

A clean local verification should include:

```powershell
python -m src.init_db
python -m src.ingest
python -m pytest -v
python -m src.evaluate
```

Then verify:

```powershell
uvicorn src.api:app --reload
```

and separately:

```powershell
streamlit run streamlit_app.py
```

The final repository should contain the source code, policy documents, tests, evaluation runner, documentation, and configuration templates, while excluding secrets and local database files.
