from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import User, Doctor, Entry, Report
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
