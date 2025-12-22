from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import User, Doctor, Entry, Report, Analysis, Patient
from schemas import ReportCreate, ReportResponse
from dependencies import get_current_doctor, get_current_user

router = APIRouter(prefix="/report", tags=["Reports"])


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    data: ReportCreate,
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """Create a new report for an entry. Only doctors can create reports."""
    # Convert entry_id to int
    entry_id = int(data.entry_id)
    
    # Verify entry exists and belongs to this doctor
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    if entry.doctor_id != current_user.doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add reports to your own entries"
        )
    
    # Create report
    report = Report(
        entry_id=entry_id,
        report_url=data.report_url,
        report_type=data.report_type,
        title=data.title,
        description=data.description
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return report


@router.get("/entry/{entry_id}", response_model=list[ReportResponse])
def get_reports_for_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reports for a specific entry."""
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Check access
    if current_user.patient and entry.patient_id != current_user.patient.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.doctor and entry.doctor_id != current_user.doctor.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    reports = db.query(Report).filter(Report.entry_id == entry_id).all()
    return reports


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """Delete a report. Only the doctor who created it can delete."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check that the entry belongs to this doctor
    entry = db.query(Entry).filter(Entry.id == report.entry_id).first()
    if entry.doctor_id != current_user.doctor.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(report)
    db.commit()
    return None


@router.post("/generate/{entry_id}", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_ai_report(
    entry_id: int,
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """
    Generate an AI-powered medical report for an entry.
    Uses Groq LLM to create a comprehensive report based on patient data and analysis results.
    The report is saved as PDF to Cloudinary and stored in the database.
    """
    # Verify entry exists and belongs to this doctor
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    if entry.doctor_id != current_user.doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only generate reports for your own entries"
        )
    
    # Get patient data
    patient = db.query(Patient).filter(Patient.id == entry.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get doctor data
    doctor = current_user.doctor
    
    # Get analysis data if available
    analysis = db.query(Analysis).filter(Analysis.entry_id == entry_id).first()
    
    # Prepare data for report generation
    patient_data = {
        "username": patient.user.username if patient.user else "Unknown",
        "age": patient.age,
        "gender": patient.gender,
        "medical_history": patient.medical_history,
        "phone_number": patient.phone_number,
        "address": patient.address
    }
    
    doctor_data = {
        "username": doctor.user.username if doctor.user else "Unknown",
        "specialization": doctor.specialization,
        "hospital": doctor.hospital,
        "license_number": doctor.license_number,
        "qualification": doctor.qualification
    }
    
    entry_data = {
        "time": entry.time.isoformat() if entry.time else None,
        "amount_voided": entry.amount_voided,
        "notes": entry.notes,
        "diameter_of_commode": entry.diameter_of_commode
    }
    
    analysis_data = None
    if analysis:
        analysis_data = {
            "qmax_report_json": analysis.qmax_report_json,
            "annotated_video_url": analysis.annotated_video_url,
            "clinical_report_url": analysis.clinical_report_url
        }
    
    # Generate report using AI
    try:
        from report_generator import generate_and_upload_report
        
        result = generate_and_upload_report(
            patient_data=patient_data,
            doctor_data=doctor_data,
            entry_data=entry_data,
            analysis_data=analysis_data,
            entry_id=entry_id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to generate report")
            )
        
        # Create report record
        report = Report(
            entry_id=entry_id,
            report_url=result.get("report_url"),  # May be None if PDF generation failed
            report_type="ai_generated",
            title=f"AI Medical Report - {datetime.now().strftime('%Y-%m-%d')}",
            description="AI-generated comprehensive medical examination report",
            markdown_content=result.get("markdown_content"),
            is_ai_generated=True
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return report
        
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generator module not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )
