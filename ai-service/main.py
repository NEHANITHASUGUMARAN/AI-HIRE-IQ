import uvicorn
import os
import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
import google.generativeai as genai

# Load env
load_dotenv()

# Config
AI_SERVICE_PORT = int(os.getenv("AI_SERVICE_PORT", 8000))
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# App
app = FastAPI(title="AI Interviewer Microservice", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_lock = asyncio.Semaphore(5)

# ================= MODELS =================

class QuestionRequest(BaseModel):
    role: str = "MERN Stack Developer"
    level: str = "Junior"
    count: int = 5
    interview_type: str = "coding-mix"

class QuestionResponse(BaseModel):
    questions: list[str]
    options: Optional[list[list[str]]] = None
    model_used: str

class EvaluationRequest(BaseModel):
    question: str
    question_type: str
    role: str
    level: str
    user_answer: Optional[str] = None
    user_code: Optional[str] = None

class EvaluationResponse(BaseModel):
    technicalScore: int
    confidenceScore: int
    aiFeedback: str
    idealAnswer: str

class ResumeRequest(BaseModel):
    resume_text: str
    job_role: str

class ResumeResponse(BaseModel):
    atsScore: int
    skillsFound: list[str]
    missingSkills: list[str]
    improvements: list[str]
    feedback: str

# ================= ROUTES =================

@app.get("/")
async def root():
    return {"message": "AI Service Running 🚀", "model": GEMINI_MODEL_NAME}

# ---------- QUESTIONS ----------

@app.post("/generate-questions", response_model=QuestionResponse)
async def generate_questions(request: QuestionRequest):
    try:
        user_prompt = f"Generate exactly {request.count} interview questions for a {request.level} {request.role}"

        system_prompt = (
            "You are a professional technical interviewer. "
            "Return ONLY questions, no explanation."
        )

        async with api_lock:
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL_NAME,
                system_instruction=system_prompt
            )
            response = await model.generate_content_async(user_prompt)

        questions = [q.strip() for q in response.text.split("\n") if q.strip()]
        return QuestionResponse(
            questions=questions[:request.count],
            model_used=GEMINI_MODEL_NAME
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- EVALUATION ----------

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest):
    try:
        system_prompt = (
            "You are a strict technical interviewer. "
            "Return JSON only with keys: technicalScore, confidenceScore, aiFeedback, idealAnswer"
        )

        user_prompt = f"""
        Role: {request.role}
        Question: {request.question}
        Answer: {request.user_answer}
        Code: {request.user_code}
        """

        async with api_lock:
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL_NAME,
                system_instruction=system_prompt
            )
            response = await model.generate_content_async(
                user_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )

        data = json.loads(response.text)

        return EvaluationResponse(
            technicalScore=data.get("technicalScore", 0),
            confidenceScore=data.get("confidenceScore", 0),
            aiFeedback=data.get("aiFeedback", ""),
            idealAnswer=str(data.get("idealAnswer", ""))
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- RESUME ----------

@app.post("/analyze-resume", response_model=ResumeResponse)
async def analyze_resume(request: ResumeRequest):
    try:
        system_prompt = (
            "You are an ATS system. Return JSON only with atsScore, skillsFound, missingSkills, improvements, feedback"
        )

        user_prompt = f"""
        Job Role: {request.job_role}
        Resume: {request.resume_text}
        """

        async with api_lock:
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL_NAME,
                system_instruction=system_prompt
            )
            response = await model.generate_content_async(
                user_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )

        data = json.loads(response.text)

        return ResumeResponse(
            atsScore=int(data.get("atsScore", 50)),
            skillsFound=data.get("skillsFound", []),
            missingSkills=data.get("missingSkills", []),
            improvements=data.get("improvements", []),
            feedback=data.get("feedback", "")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================= RUN =================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=AI_SERVICE_PORT)