from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, Patient
from schemas import PatientResponse, PatientUpdate
from dependencies import get_current_patient

router = APIRouter(prefix="/patient", tags=["Patient Dashboard"])


@router.get("/me", response_model=PatientResponse)
def get_patient_profile(current_user: User = Depends(get_current_patient)):
    """Get the current patient's profile."""
    return current_user.patient


@router.put("/me", response_model=PatientResponse)
def update_patient_profile(
    data: PatientUpdate,
    current_user: User = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Update the current patient's profile."""
    patient = current_user.patient
    
    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(patient, field, value)
    
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient_by_id(
    patient_id: int,
    current_user: User = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Get a patient's profile by ID. Only accessible to the patient themselves."""
    # Patients can only view their own profile
    if current_user.patient.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only view your own profile."
        )
    return current_user.patient


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient_account(
    current_user: User = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Delete the current patient's account."""
    patient = current_user.patient
    user = current_user
    
    # Delete patient first (due to foreign key)
    db.delete(patient)
    db.delete(user)
    db.commit()
    
    return None
