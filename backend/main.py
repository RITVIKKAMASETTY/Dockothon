from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.auth_router import router as auth_router
from routers.doctor_router import router as doctor_router
from routers.patient_router import router as patient_router

app = FastAPI(
    title="Dockothon API",
    description="Medical platform API for doctors and patients",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(doctor_router)
app.include_router(patient_router)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Dockothon API is running"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
