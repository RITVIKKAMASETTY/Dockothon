from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from models import User, Entry, Analysis
from schemas import AnalysisCreate, AnalysisResponse
from dependencies import get_current_doctor, get_current_user

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_analysis(
    data: AnalysisCreate,
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """Create or update an analysis for an entry. Only doctors can create analyses."""
    entry_id = int(data.entry_id)
    
    # Verify entry exists and belongs to this doctor
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    if entry.doctor_id != current_user.doctor.id:
        raise HTTPException(status_code=403, detail="You can only add analysis to your own entries")
    
    # Check if analysis already exists for this entry
    analysis = db.query(Analysis).filter(Analysis.entry_id == entry_id).first()
    
    if analysis:
        # Update existing analysis
        if data.annotated_video_url is not None:
            analysis.annotated_video_url = data.annotated_video_url
        if data.clinical_report_url is not None:
            analysis.clinical_report_url = data.clinical_report_url
        if data.flow_timeseries_url is not None:
            analysis.flow_timeseries_url = data.flow_timeseries_url
        if data.qmax_report_json is not None:
            analysis.qmax_report_json = data.qmax_report_json
    else:
        # Create new analysis
        analysis = Analysis(
            entry_id=entry_id,
            annotated_video_url=data.annotated_video_url,
            clinical_report_url=data.clinical_report_url,
            flow_timeseries_url=data.flow_timeseries_url,
            qmax_report_json=data.qmax_report_json
        )
        db.add(analysis)
    
    db.commit()
    db.refresh(analysis)
    return analysis


@router.get("/entry/{entry_id}", response_model=AnalysisResponse)
def get_analysis_for_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analysis for a specific entry."""
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Check access
    if current_user.patient and entry.patient_id != current_user.patient.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.doctor and entry.doctor_id != current_user.doctor.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    analysis = db.query(Analysis).filter(Analysis.entry_id == entry_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found for this entry")
    
    return analysis


@router.delete("/entry/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(
    entry_id: int,
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """Delete analysis for an entry. Only the doctor can delete."""
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    if entry.doctor_id != current_user.doctor.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    analysis = db.query(Analysis).filter(Analysis.entry_id == entry_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    db.delete(analysis)
    db.commit()
    return None


@router.post("/run/{entry_id}", response_model=AnalysisResponse)
def run_analysis(
    entry_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    """Manually trigger analysis for an entry. Only the doctor can run analysis."""
    from analysis_runner import run_analysis_for_entry
    
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    if entry.doctor_id != current_user.doctor.id:
        raise HTTPException(status_code=403, detail="You can only run analysis on your own entries")
    
    if not entry.top_view_url and not entry.bottom_view_url:
        raise HTTPException(status_code=400, detail="No video URLs available for analysis")
    
    # Run analysis synchronously for immediate feedback
    result = run_analysis_for_entry(
        top_view_url=entry.top_view_url,
        bottom_view_url=entry.bottom_view_url,
        volume=entry.amount_voided,
        entry_id=entry_id
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))
    
    # Check if analysis already exists - update instead of create
    existing = db.query(Analysis).filter(Analysis.entry_id == entry_id).first()
    
    if existing:
        # Update existing analysis
        existing.annotated_video_url = result.get("annotated_video_url")
        existing.clinical_report_url = result.get("clinical_report_url")
        existing.flow_timeseries_url = result.get("flow_timeseries_url")
        existing.qmax_report_json = result.get("qmax_report_json")
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new analysis record
        analysis = Analysis(
            entry_id=entry_id,
            annotated_video_url=result.get("annotated_video_url"),
            clinical_report_url=result.get("clinical_report_url"),
            flow_timeseries_url=result.get("flow_timeseries_url"),
            qmax_report_json=result.get("qmax_report_json")
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis
