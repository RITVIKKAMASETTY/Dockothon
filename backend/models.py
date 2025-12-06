from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class User(Base):
    """User table with authentication fields."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)  # Should be hashed
    email = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor = relationship("Doctor", back_populates="user", uselist=False)
    patient = relationship("Patient", back_populates="user", uselist=False)


class Doctor(Base):
    """Doctor table with 1:1 relationship to User."""
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    hospital = Column(String(200), nullable=False)
    specialization = Column(String(100), nullable=False)
    qualification = Column(String(200), nullable=False)
    profile_picture = Column(String(500), nullable=True)  # URL or path to image
    age = Column(Integer, nullable=True)
    license_number = Column(String(50), unique=True, nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    auto_accept = Column(Boolean, default=False, nullable=False)  # Auto-accept patient requests
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="doctor")
    entries = relationship("Entry", back_populates="doctor")


class Patient(Base):
    """Patient table with 1:1 relationship to User."""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    phone_number = Column(String(20), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    medical_history = Column(Text, nullable=True)
    profile_picture = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="patient")
    entries = relationship("Entry", back_populates="patient")


class Entry(Base):
    """Entry table linking patient and doctor with medical examination data."""
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    time = Column(DateTime, default=datetime.utcnow, nullable=False)
    top_view_url = Column(String(500), nullable=True)
    bottom_view_url = Column(String(500), nullable=True)
    amount_voided = Column(Float, nullable=True)  # Amount in ml or appropriate unit
    diameter_of_commode = Column(Float, nullable=True)  # Diameter in cm or appropriate unit
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="entries")
    doctor = relationship("Doctor", back_populates="entries")
    reports = relationship("Report", back_populates="entry")
    analysis = relationship("Analysis", back_populates="entry", uselist=False)


class Report(Base):
    """Report table with 1:many relationship to Entry."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False)
    report_url = Column(String(500), nullable=False)
    report_type = Column(String(50), nullable=True)  # e.g., 'analysis', 'summary', 'detailed'
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entry = relationship("Entry", back_populates="reports")


class Analysis(Base):
    """Analysis table with 1:1 relationship to Entry for ML/video analysis results."""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), unique=True, nullable=False)
    annotated_video_url = Column(String(500), nullable=True)
    clinical_report_url = Column(String(500), nullable=True)
    flow_timeseries_url = Column(String(500), nullable=True)
    qmax_report_json = Column(Text, nullable=True)  # Store JSON as text
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entry = relationship("Entry", back_populates="analysis")
