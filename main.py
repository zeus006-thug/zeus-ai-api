import os
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from langchain_mistralai.chat_models import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Initialization ---

# Check for Mistral API Key for the LLM connection
if not os.getenv("MISTRAL_API_KEY"):
    raise ValueError("MISTRAL_API_KEY environment variable not set. Please set it in your Vercel project settings.")

# Initialize the LLM from Mistral
llm = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0.3
    # --- FIX 1: REMOVE the incorrect timeout parameter from here ---
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
    title="ZEUS ARTIFICIAL INTELLIGENCE",
    description="An Artificial Intelligence API made by ZEUS THUG.",
    version="1.1.0"
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Error: The 'query' parameter is required. Please provide a question, for example: /ask?query=who are you?"}
    )


# --- Pydantic Models for Request/Response ---

class QueryResponse(BaseModel):
    response: str


# --- API Endpoints ---

@app.get("/ask", response_model=QueryResponse, tags=["AI Query"])
async def ask_zeus_ai(query: str = Query(..., min_length=1, description="The question you want to ask Zeus AI.")):
    """
    Endpoint to ask a question. This endpoint is now public.
    """
    try:
        # --- FIX 2: ADD the timeout configuration here, in the invoke() call ---
        config = {"configurable": {"request_timeout": 60}}
        response = chain.invoke({"user_query": query}, config=config)
        return QueryResponse(response=response)
    
    except Exception as e:
        print(f"An unexpected error occurred with the AI service: {e}")
        raise HTTPException(
            status_code=503,
            detail="The AI service is currently unavailable. Please try again later."
        )


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to the Zeus Artificial Intelligence API! Go to /ask? endpoint to use the API."}
