from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, Doctor, Patient
from schemas import (
    DoctorSignup, DoctorResponse,
    PatientSignup, PatientResponse,
    SigninRequest, TokenResponse, SignupResponse
)
from auth import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============ Doctor Signup ============
@router.post("/signup/doctor", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup_doctor(data: DoctorSignup, db: Session = Depends(get_db)):
    """Register a new doctor account."""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Check if license number already exists (if provided)
    if data.license_number:
        existing_license = db.query(Doctor).filter(Doctor.license_number == data.license_number).first()
        if existing_license:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License number already registered"
            )
    
    # Create user
    user = User(
        username=data.username,
        email=data.email,
        password=get_password_hash(data.password)
    )
    db.add(user)
    db.flush()  # Get user.id without committing
    
    # Create doctor profile
    doctor = Doctor(
        user_id=user.id,
        hospital=data.hospital,
        specialization=data.specialization,
        qualification=data.qualification,
        profile_picture=data.profile_picture,
        age=data.age,
        license_number=data.license_number,
        years_of_experience=data.years_of_experience,
        auto_accept=data.auto_accept
    )
    db.add(doctor)
    db.commit()
    
    return SignupResponse(
        message="Doctor registered successfully",
        user_id=user.id,
        role="doctor"
    )


# ============ Patient Signup ============
@router.post("/signup/patient", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup_patient(data: PatientSignup, db: Session = Depends(get_db)):
    """Register a new patient account."""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    user = User(
        username=data.username,
        email=data.email,
        password=get_password_hash(data.password)
    )
    db.add(user)
    db.flush()  # Get user.id without committing
    
    # Create patient profile
    patient = Patient(
        user_id=user.id,
        date_of_birth=data.date_of_birth,
        age=data.age,
        gender=data.gender,
        address=data.address,
        phone_number=data.phone_number,
        emergency_contact=data.emergency_contact,
        medical_history=data.medical_history,
        profile_picture=data.profile_picture
    )
    db.add(patient)
    db.commit()
    
    return SignupResponse(
        message="Patient registered successfully",
        user_id=user.id,
        role="patient"
    )


# ============ Common Signin ============
@router.post("/signin", response_model=TokenResponse)
def signin(data: SigninRequest, db: Session = Depends(get_db)):
    """Sign in with email and password. Returns JWT token with role."""
    # Find user by email
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Determine role
    role = None
    if user.doctor:
        role = "doctor"
    elif user.patient:
        role = "patient"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no associated role"
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": role
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=role,
        user_id=user.id
    )
