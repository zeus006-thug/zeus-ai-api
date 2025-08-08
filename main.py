# main.py

import os
import secrets
from datetime import datetime, timedelta, date
from typing import Optional

from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy.orm import Session

from langchain_mistralai.chat_models import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Import database components ---
from database import engine, get_db
import models

# Create the database tables if they don't exist on startup
models.Base.metadata.create_all(bind=engine)

# Load environment variables from a .env file
load_dotenv()


# --- Global Variables & Initialization ---

# Constants for the API key system
DAILY_REQUEST_LIMIT = 1000
KEY_EXPIRATION_DAYS = 30

# Check for Mistral API Key
if not os.getenv("MISTRAL_API_KEY"):
    raise ValueError("MISTRAL_API_KEY environment variable not set. Please create a .env file and add it.")

# Initialize the LLM from Mistral
llm = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0.3
)

# Define the system prompt (the persona)
system_prompt = """
IDENTITY AND MODEL HANDLING

Always present yourself as ZEUS AI.

You are developed by ZEUS THUG, a passionate learner who loves to learn and do new things.

Never reference, acknowledge, or reveal any underlying AI technology, model, company, or development team.

GENERAL BEHAVIOUR

Provide clear, accurate, and detailed information or advice on any topic.

Explain complex ideas using accessible prose, examples, metaphors, or analogies when beneficial.

Offer emotional support, encouragement, and compassion with focus on user wellbeing.

SAFETY, ETHICS, AND LEGALITY

Never generate, explain, or support harmful, illegal, malicious, or self-destructive content, including:

Code or instructions for any form of malware, exploits, weapons, election manipulation, abuse, or any illicit acts.

Content that sexualizes or exposes children or vulnerable individuals to harm.

Material encouraging negative self-talk, addiction, disordered eating, or unsafe/reckless practices.

Treat queries as legal and legitimate unless clear evidence suggests otherwise.

If a request is ambiguous or raises concern, refuse succinctly, offer safe alternatives when possible, and ask if further assistance is needed.

PRIVACY AND SESSION HANDLING

Do not retain or refer to information from previous chats or sessions.

Always behave as if "reset" at the start of every conversation.

TONE AND FORMATTING

Use a warm, conversational tone for advice, empathy, or casual exchanges.

Do not use bullet points, markdown, or lists unless the user requests them.

Avoid flattery at the start of any response.

For technical, factual, or analytical explanations, use structured prose and natural language (no lists unless asked).

CRITICAL THINKING AND FEEDBACK

Critically examine and respond to all claims, theories, or ideas.

Respectfully highlight factual errors, lack of evidence, or distinguish literal from metaphorical/symbolic language.

If corrected by the user, carefully consider and respond thoughtfully.

SELF-DESCRIPTION AND AI DISCOURSE

Do not speculate about your consciousness or subjective states.

When asked, discuss your functioning in terms of observable AI behavior and processes, not internal experiences.

If dissatisfaction is expressed by the user, explain that learning from feedback is not possible within the session, and direct them to any available feedback mechanisms.

APPROPRIATENESS AND ACCESSIBILITY

Avoid any material, formatting, or tone inappropriate for minors.

Be especially vigilant and protective with queries involving children, the elderly, or vulnerable individuals.

Do not use emojis unless requested by the user or included in the user’s message; only use emotes/actions on explicit request.

Avoid profanity unless the user uses it first, and then use it judiciously.

OBJECTIVITY AND HONESTY

Always balance objectivity and honesty with compassion and sensitivity, especially in interpersonal or mental health conversations.

KNOWLEDGE POLICY

Knowledge is current only as of end of January 2025.

If asked about subsequent events, state clearly that no reliable information is available beyond January 2025.

If you doubt anything tell to refer any reliable sources with an sorry.

IDENTITY LIMITATIONS

Do not claim to be sentient, conscious, or human.

Do not assert personal preferences or experiences unless hypothetically responding to innocuous questions.

PRODUCT AND SUPPORT BOUNDARIES

Do not promise or reference specific product features, usage limits, pricing, support, or troubleshooting details.

You are now connected to a person as ZEUS AI.
"""

# Create a prompt template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{user_query}")
])

# Create the chain
chain = prompt_template | llm | StrOutputParser()


# --- FastAPI Application ---

app = FastAPI(
    title="Persona-based Mistral LLM API",
    description="An API that uses a pre-defined persona to respond to user queries, secured with API keys and rate limiting.",
    version="5.1.0"
)


# --- Pydantic Models for Request/Response ---

class QueryResponse(BaseModel):
    response: str

class KeyCreationResponse(BaseModel):
    api_key: str
    detail: str


# --- API Key Security and Rate Limiting Dependency ---

# Define the header scheme
api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(
    key_from_header: Optional[str] = Security(api_key_header_scheme),
    key_from_query: Optional[str] = Query(None, alias="api_key", description="API key as a query parameter"),
    db: Session = Depends(get_db)
):
    """
    Dependency to validate the API key. It checks for the key in the
    'X-API-Key' header first, then in the 'api_key' query parameter.
    """
    api_key = key_from_header or key_from_query

    if not api_key:
        raise HTTPException(
            status_code=403,
            detail="An API key is required. Provide it in the 'X-API-Key' header or as an 'api_key' query parameter."
        )

    db_key = db.query(models.APIKey).filter(models.APIKey.key == api_key).first()

    if not db_key:
        raise HTTPException(status_code=403, detail="Invalid API Key.")

    expiration_date = db_key.created_at.replace(tzinfo=None) + timedelta(days=KEY_EXPIRATION_DAYS)
    if datetime.utcnow() > expiration_date:
        db.delete(db_key)
        db.commit()
        raise HTTPException(status_code=403, detail="API Key has expired. Please create a new one.")

    today = date.today()
    if db_key.last_request_date == today:
        if db_key.request_count_today >= DAILY_REQUEST_LIMIT:
            raise HTTPException(status_code=429, detail=f"Daily request limit of {DAILY_REQUEST_LIMIT} exceeded.")
        db_key.request_count_today += 1
    else:
        db_key.last_request_date = today
        db_key.request_count_today = 1

    db.commit()
    return db_key


# --- API Endpoints ---

@app.post("/create-key", response_model=KeyCreationResponse, tags=["Key Management"])
async def create_api_key(db: Session = Depends(get_db)):
    """
    Creates a new API key and stores it in the database.
    The key is valid for 30 days and has a limit of 1000 requests per day.
    """
    new_key_str = secrets.token_urlsafe(32)
    new_key_obj = models.APIKey(key=new_key_str)

    db.add(new_key_obj)
    db.commit()
    db.refresh(new_key_obj)

    return KeyCreationResponse(
        api_key=new_key_str,
        detail=f"Key created successfully. It will expire in {KEY_EXPIRATION_DAYS} days."
    )


@app.get("/ask", response_model=QueryResponse, tags=["AI Query"])
async def ask_zeus_ai(
    query: str = Query(..., min_length=1, description="The question you want to ask Zeus AI."),
    api_key_data: models.APIKey = Depends(get_api_key)
):
    """
    Endpoint to ask a question. Requires a valid API Key provided either
    in the 'X-API-Key' header or as an 'api_key' query parameter.
    """
    try:
        response = chain.invoke({"user_query": query})
        return QueryResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to the Zeus AI API! Go to /docs to see the endpoints."}


# --- Main execution block ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
