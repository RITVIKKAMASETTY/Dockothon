"""
Chat router for patient report conversations using Groq LLM.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime

from database import get_db
from models import User, Patient, Entry, Report, Analysis
from dependencies import get_current_patient
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/chat", tags=["Chat"])

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    entry_id: int
    message: str
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    response: str
    entry_id: int


def get_groq_client():
    """Get Groq client instance."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")
    from groq import Groq
    return Groq(api_key=GROQ_API_KEY)


@router.post("/report", response_model=ChatResponse)
def chat_with_report(
    request: ChatRequest,
    current_user: User = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Chat with AI about a medical report.
    Patients can ask questions about their report and get explanations.
    """
    # Verify entry exists and belongs to this patient
    entry = db.query(Entry).filter(Entry.id == request.entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    if entry.patient_id != current_user.patient.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get report content
    reports = db.query(Report).filter(Report.entry_id == request.entry_id).all()
    report_content = ""
    for report in reports:
        if report.markdown_content:
            report_content += f"\n\n--- {report.title} ---\n{report.markdown_content}"
        elif report.description:
            report_content += f"\n\n--- {report.title} ---\n{report.description}"
    
    # Get analysis data if available
    analysis = db.query(Analysis).filter(Analysis.entry_id == request.entry_id).first()
    analysis_content = ""
    if analysis and analysis.qmax_report_json:
        import json
        try:
            qmax = json.loads(analysis.qmax_report_json)
            analysis_content = f"""
Uroflowmetry Analysis Results:
- Maximum Flow Rate (Qmax): {qmax.get('Qmax', 'N/A'):.2f} ml/s
- Voided Volume: {qmax.get('Voided_Volume', 'N/A'):.2f} ml
- Time to Qmax: {qmax.get('Time_to_Qmax', 'N/A'):.2f} seconds
- Average Flow Rate: {qmax.get('Average_Flow_Rate', 'N/A'):.2f} ml/s
"""
        except:
            pass
    
    # Build system prompt
    system_prompt = f"""You are a helpful medical assistant helping a patient understand their medical report.
Be friendly, clear, and explain medical terms in simple language.
IMPORTANT: Do not provide medical advice or diagnoses. Always suggest consulting with the doctor for medical decisions.

Here is the patient's medical report and analysis data:

{report_content}

{analysis_content}

Based on this information, answer the patient's questions clearly and helpfully."""

    # Build message history
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in request.history[-10:]:  # Keep last 10 messages for context
        messages.append({"role": msg.role, "content": msg.content})
    
    messages.append({"role": "user", "content": request.message})
    
    try:
        client = get_groq_client()
        
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        return ChatResponse(
            response=ai_response,
            entry_id=request.entry_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get AI response: {str(e)}"
        )
