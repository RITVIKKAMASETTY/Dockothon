from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ============ User Schemas ============
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Doctor Schemas ============
class DoctorSignup(BaseModel):
    # User fields
    username: str
    email: EmailStr
    password: str
    # Doctor fields
    hospital: str
    specialization: str
    qualification: str
    profile_picture: Optional[str] = None
    age: Optional[int] = None
    license_number: Optional[str] = None
    years_of_experience: Optional[int] = None
    auto_accept: bool = False


class DoctorUpdate(BaseModel):
    """Schema for updating doctor profile."""
    hospital: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    profile_picture: Optional[str] = None
    age: Optional[int] = None
    license_number: Optional[str] = None
    years_of_experience: Optional[int] = None
    auto_accept: Optional[bool] = None


class DoctorResponse(BaseModel):
    id: int
    user_id: int
    hospital: str
    specialization: str
    qualification: str
    profile_picture: Optional[str] = None
    age: Optional[int] = None
    license_number: Optional[str] = None
    years_of_experience: Optional[int] = None
    auto_accept: bool
    user: UserResponse

    class Config:
        from_attributes = True


# ============ Patient Schemas ============
class PatientSignup(BaseModel):
    # User fields
    username: str
    email: EmailStr
    password: str
    # Patient fields
    date_of_birth: Optional[datetime] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_history: Optional[str] = None
    profile_picture: Optional[str] = None


class PatientUpdate(BaseModel):
    """Schema for updating patient profile."""
    date_of_birth: Optional[datetime] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_history: Optional[str] = None
    profile_picture: Optional[str] = None


class PatientResponse(BaseModel):
    id: int
    user_id: int
    date_of_birth: Optional[datetime] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_history: Optional[str] = None
    profile_picture: Optional[str] = None
    user: UserResponse

    class Config:
        from_attributes = True


# ============ Auth Schemas ============
class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str  # "doctor" or "patient"
    user_id: int


class SignupResponse(BaseModel):
    message: str
    user_id: int
    role: str

