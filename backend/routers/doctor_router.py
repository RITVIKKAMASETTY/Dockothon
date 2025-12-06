from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, Doctor
from schemas import DoctorResponse, DoctorUpdate
from dependencies import get_current_doctor

router = APIRouter(prefix="/doctor", tags=["Doctor Dashboard"])


@router.get("/me", response_model=DoctorResponse)
def get_doctor_profile(current_user: User = Depends(get_current_doctor)):
    """Get the current doctor's profile."""
    return current_user.doctor


@router.put("/me", response_model=DoctorResponse)
def update_doctor_profile(
    data: DoctorUpdate,
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """Update the current doctor's profile."""
    doctor = current_user.doctor
    
    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(doctor, field, value)
    
    db.commit()
    db.refresh(doctor)
    return doctor


@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor_by_id(doctor_id: int, db: Session = Depends(get_db)):
    """Get a doctor's public profile by ID."""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    return doctor


@router.get("/", response_model=list[DoctorResponse])
def list_doctors(
    skip: int = 0,
    limit: int = 20,
    specialization: str = None,
    db: Session = Depends(get_db)
):
    """List all doctors with optional filtering."""
    query = db.query(Doctor)
    
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    
    doctors = query.offset(skip).limit(limit).all()
    return doctors


@router.patch("/me/auto-accept", response_model=DoctorResponse)
def toggle_auto_accept(
    auto_accept: bool,
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """Toggle the auto-accept setting for the doctor."""
    doctor = current_user.doctor
    doctor.auto_accept = auto_accept
    db.commit()
    db.refresh(doctor)
    return doctor
