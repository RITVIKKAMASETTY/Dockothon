from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import User, Doctor, Patient, Entry, Analysis
from schemas import EntryCreate, EntryResponse, EntryWithDetails
from dependencies import get_current_patient, get_current_user
from email_service import send_new_entry_notification
from analysis_runner import run_analysis_for_entry

router = APIRouter(prefix="/entry", tags=["Entries"])


def run_auto_analysis(entry_id: int, top_view_url: str, bottom_view_url: str, amount_voided: float):
    """Background task to run analysis and store results."""
    from database import SessionLocal
    
    result = run_analysis_for_entry(
        top_view_url=top_view_url,
        bottom_view_url=bottom_view_url,
        volume=amount_voided,
        entry_id=entry_id
    )
    
    if result.get("success"):
        # Store in database
        db = SessionLocal()
        try:
            analysis = Analysis(
                entry_id=entry_id,
                annotated_video_url=result.get("annotated_video_url"),
                clinical_report_url=result.get("clinical_report_url"),
                flow_timeseries_url=result.get("flow_timeseries_url"),
                qmax_report_json=result.get("qmax_report_json")
            )
            db.add(analysis)
            db.commit()
            print(f"Analysis saved for entry {entry_id}")
        except Exception as e:
            print(f"Error saving analysis: {e}")
        finally:
            db.close()


@router.post("/", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    data: EntryCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Create a new entry. Only patients can create entries."""
    # Convert doctor_id to int (handles string IDs from frontend)
    doctor_id = int(data.doctor_id)
    
    # Verify doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    # Get patient
    patient = current_user.patient
    
    # Create entry
    entry = Entry(
        patient_id=patient.id,
        doctor_id=doctor_id,
        time=datetime.utcnow(),
        top_view_url=data.top_view_url,
        bottom_view_url=data.bottom_view_url,
        amount_voided=data.amount_voided,
        diameter_of_commode=data.diameter_of_commode,
        notes=data.notes
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    # Send email notification to doctor (if enabled)
    doctor_user = doctor.user
    send_new_entry_notification(
        doctor_email=doctor_user.email,
        doctor_name=doctor_user.username,
        patient_name=current_user.username,
        entry_time=entry.time.strftime("%Y-%m-%d %H:%M:%S UTC")
    )
    
    # Auto-run analysis if doctor has auto_accept enabled
    if doctor.auto_accept and (data.top_view_url or data.bottom_view_url):
        # Run analysis in background
        background_tasks.add_task(
            run_auto_analysis,
            entry_id=entry.id,
            top_view_url=data.top_view_url,
            bottom_view_url=data.bottom_view_url,
            amount_voided=data.amount_voided
        )
    
    return entry


@router.get("/my-entries")
def get_my_entries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get entries for the current user with patient/doctor details."""
    if current_user.patient:
        entries = db.query(Entry).filter(Entry.patient_id == current_user.patient.id).all()
    elif current_user.doctor:
        entries = db.query(Entry).filter(Entry.doctor_id == current_user.doctor.id).all()
    else:
        raise HTTPException(status_code=400, detail="No role assigned")
    
    # Build response with patient/doctor names
    result = []
    for entry in entries:
        entry_dict = {
            "id": entry.id,
            "patient_id": entry.patient_id,
            "doctor_id": entry.doctor_id,
            "time": entry.time.isoformat(),
            "top_view_url": entry.top_view_url,
            "bottom_view_url": entry.bottom_view_url,
            "amount_voided": entry.amount_voided,
            "diameter_of_commode": entry.diameter_of_commode,
            "notes": entry.notes,
            "created_at": entry.created_at.isoformat(),
            "patient_name": entry.patient.user.username if entry.patient else None,
            "doctor_name": entry.doctor.user.username if entry.doctor else None,
        }
        result.append(entry_dict)
    
    return result


@router.get("/{entry_id}", response_model=EntryWithDetails)
def get_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific entry with full details."""
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Check access - only the patient or doctor involved can view
    if current_user.patient and entry.patient_id != current_user.patient.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.doctor and entry.doctor_id != current_user.doctor.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return entry
