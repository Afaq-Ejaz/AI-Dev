# Phase 4, Step 2 — The `POST /triage` Endpoint

## What Was Done

We added exactly **three things** to `main.py`:

### 1. Two new imports (lines 17–18)

```python
from ai_dev.contract import TicketInput, TriageResult
from ai_dev.engine import triage
```

These pull in the pieces we already built in earlier phases:
- `TicketInput` — the Pydantic model that defines what a valid customer ticket looks like (email, subject, message).
- `TriageResult` — the Pydantic model that defines what the API sends back (ticket ID, classification, matched policy, response).
- `triage` — the function from `engine.py` that runs the full pipeline (classify → retrieve policy → route).

### 2. The endpoint itself (lines 96–108)

```python
@app.post(
    "/triage",
    tags=["Triage"],
    summary="Triage a customer support ticket",
    response_model=TriageResult,
)
async def triage_ticket(ticket: TicketInput):
    """
    Accepts a customer support ticket and runs the full pipeline:
    classification → semantic retrieval → routing.
    """
    return triage(ticket)
```

That's it. The entire endpoint is just **one function call** — `return triage(ticket)`. Everything complex already lives in `engine.py`.

---

## Breaking Down Every Piece

### `@app.post("/triage")`

This is a **decorator**. It tells FastAPI: *"When someone sends an HTTP POST request to the URL `/triage`, run the function below."*

- **Why POST and not GET?** — `GET` is for *reading* information (like checking the health of the server). `POST` is for *sending* new data for the server to process. A support ticket is new data — you're submitting something.

### `tags=["Triage"]`

This is just organizational. In the Swagger docs page (`/docs`), endpoints are grouped by tags. Our health check is under "System", this endpoint is under "Triage". It's like putting a label on a drawer.

### `response_model=TriageResult`

This tells FastAPI: *"The thing I return from this function will be shaped like a `TriageResult`."* FastAPI uses this for two things:
1. **Documentation** — Swagger automatically shows the exact shape of the response, so anyone using your API knows what to expect.
2. **Filtering** — If your function accidentally returned extra fields that aren't in `TriageResult`, FastAPI would strip them out. Only what the model defines gets sent back.

### `async def triage_ticket(ticket: TicketInput):`

This is where the magic happens, and there's a lot packed into this one line:

- **`ticket: TicketInput`** — This tells FastAPI *"the body of this HTTP request should be a JSON object that matches `TicketInput`."* FastAPI will automatically:
  1. Read the raw JSON bytes from the network.
  2. Try to parse them into a `TicketInput` object.
  3. Run all the Pydantic validators (is there an `@` in the email? Is subject ≤ 100 characters?).
  4. If anything is wrong, it **stops immediately** and sends back a `422 Unprocessable Entity` error — your `triage_ticket` function never even runs.
  5. If everything is valid, it hands you a clean, validated `ticket` object.

You wrote zero validation code here. Pydantic does it all because you already defined the rules back in Phase 1.

- **`async def`** — The `async` keyword means this function *can* let other requests be handled while it's waiting for something slow (like the Gemini API call inside `triage()`). Think of it like a restaurant waiter who takes another table's order while the kitchen is cooking yours, instead of standing frozen at your table staring at the kitchen door.

### `return triage(ticket)`

This calls the `triage()` function you built in Phase 3's `engine.py`. That function runs the whole pipeline:

```
TicketInput → classify (Gemini) → retrieve policy (cosine similarity) → route → TriageResult
```

The result is a `TriageResult` Pydantic object. FastAPI automatically converts it to JSON and sends it back to the caller with a `200 OK` status code.

---

## How It All Connects (The Full Picture)

```
Customer sends HTTP POST to /triage with JSON body
         │
         ▼
    FastAPI reads the raw JSON
         │
         ▼
    Pydantic validates it against TicketInput
    (bad email? → instant 422 error, stop here)
         │
         ▼
    triage_ticket() receives a clean TicketInput object
         │
         ▼
    Calls triage(ticket) from engine.py
         │
         ├── classifier.py: Gemini classifies the ticket
         ├── retrieval.py: finds the best-matching KB policy
         └── router.py: picks the right handler, builds the response
         │
         ▼
    Returns a TriageResult object
         │
         ▼
    FastAPI converts it to JSON, sends HTTP 200 OK
```

---

## What Wasn't Added (On Purpose)

- **No try/except blocks** — Error handling is a separate step in Phase 4.
- **No custom validation logic** — Pydantic already handles that from Phase 1.
- **No new models or data structures** — We reused everything from `contract.py`.
- **No changes to the engine, classifier, retrieval, or router** — The whole point of modular design is that adding an endpoint doesn't touch any of those files.

---

## Testing It

Once the server is running (`uv run ai-dev`), you can test the endpoint by going to `http://127.0.0.1:8000/docs`, clicking on the `POST /triage` section, clicking "Try it out", and pasting this JSON:

```json
{
  "customer_email": "alice@example.com",
  "subject": "Charged twice",
  "message": "I was charged $29.99 twice this month. Please refund."
}
```

Or from the terminal with `curl`:

```bash
curl -X POST http://127.0.0.1:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"customer_email":"alice@example.com","subject":"Charged twice","message":"I was charged $29.99 twice this month. Please refund."}'
```
