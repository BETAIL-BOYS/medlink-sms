"""
MedLink SMS - FastAPI Backend
Healthcare communication platform for sending lab results via Africa's Talking SMS API
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

AFRICASTALKING_USERNAME = os.getenv("AFRICASTALKING_USERNAME", "sandbox")
AFRICASTALKING_API_KEY = os.getenv("AFRICASTALKING_API_KEY", "mock-api-key")

# Database setup
DATABASE_URL = "sqlite:///./medlink.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
security = HTTPBearer()

# Initialize FastAPI
app = FastAPI(title="MedLink SMS API", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== DATABASE MODELS ==============

class User(Base):
    """User model for healthcare workers"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message_logs = relationship("MessageLog", back_populates="user")

class Patient(Base):
    """Patient model"""
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message_logs = relationship("MessageLog", back_populates="patient")

class MessageLog(Base):
    """Message log model for tracking SMS delivery"""
    __tablename__ = "message_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    message_text = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, sent, delivered, failed
    message_id = Column(String, nullable=True)  # Africa's Talking message ID
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="message_logs")
    patient = relationship("Patient", back_populates="message_logs")

# Create tables
Base.metadata.create_all(bind=engine)

# ============== PYDANTIC SCHEMAS ==============

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PatientCreate(BaseModel):
    name: str
    phone: str = Field(..., pattern=r'^\+?\d{10,15}$')

class SMSRequest(BaseModel):
    patient_id: int
    message_text: str = Field(..., min_length=1, max_length=500)

class DeliveryReport(BaseModel):
    """Webhook payload from Africa's Talking"""
    id: str
    status: str
    phoneNumber: str
    retryCount: Optional[int] = 0

class MessageLogResponse(BaseModel):
    id: int
    patient_name: str
    phone: str
    message_text: str
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True

# ============== HELPER FUNCTIONS ==============

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    # Ensure password is within bcrypt's 72 byte limit
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                     db: Session = Depends(get_db)) -> User:
    """Verify JWT token and return current user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def mock_africastalking_send_sms(phone: str, message: str) -> dict:
    """
    Mock Africa's Talking SMS API response
    Replace this with actual API call in production
    """
    import random
    message_id = f"ATXid_{random.randint(100000, 999999)}"
    
    return {
        "SMSMessageData": {
            "Message": "Sent to 1/1 Total Cost: KES 0.8000",
            "Recipients": [{
                "statusCode": 101,  # 101 = Success
                "number": phone,
                "status": "Success",
                "cost": "KES 0.8000",
                "messageId": message_id
            }]
        }
    }

# ============== API ENDPOINTS ==============

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "MedLink SMS API"}

@app.post("/register", response_model=Token)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register new healthcare worker"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": new_user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate healthcare worker"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/patients")
def create_patient(patient_data: PatientCreate, 
                   current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """Add a new patient"""
    new_patient = Patient(
        name=patient_data.name,
        phone=patient_data.phone,
        user_id=current_user.id
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    
    return {"id": new_patient.id, "name": new_patient.name, "phone": new_patient.phone}

@app.get("/patients")
def get_patients(current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """Get all patients for current user"""
    patients = db.query(Patient).filter(Patient.user_id == current_user.id).all()
    return patients

@app.post("/send_sms")
def send_sms(sms_data: SMSRequest,
             current_user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    """
    Send SMS to patient using Africa's Talking API
    Logs the message and returns delivery status
    """
    # Verify patient exists and belongs to user
    patient = db.query(Patient).filter(
        Patient.id == sms_data.patient_id,
        Patient.user_id == current_user.id
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Send SMS via Africa's Talking (mocked for now)
    try:
        response = mock_africastalking_send_sms(patient.phone, sms_data.message_text)
        recipient = response["SMSMessageData"]["Recipients"][0]
        
        # Create message log
        message_log = MessageLog(
            user_id=current_user.id,
            patient_id=patient.id,
            message_text=sms_data.message_text,
            status="sent" if recipient["statusCode"] == 101 else "failed",
            message_id=recipient.get("messageId")
        )
        db.add(message_log)
        db.commit()
        db.refresh(message_log)
        
        return {
            "success": True,
            "message": "SMS sent successfully",
            "log_id": message_log.id,
            "status": message_log.status,
            "cost": recipient.get("cost")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send SMS: {str(e)}")

@app.post("/delivery_report")
def delivery_report(report: DeliveryReport, db: Session = Depends(get_db)):
    """
    Webhook endpoint to receive delivery status from Africa's Talking
    Updates message status based on delivery confirmation
    """
    # Find message by Africa's Talking message ID
    message = db.query(MessageLog).filter(MessageLog.message_id == report.id).first()
    
    if not message:
        return {"status": "not_found", "message": "Message ID not found in logs"}
    
    # Update status based on delivery report
    status_mapping = {
        "Success": "delivered",
        "Sent": "sent",
        "Failed": "failed",
        "Rejected": "failed"
    }
    
    message.status = status_mapping.get(report.status, "unknown")
    db.commit()
    
    return {
        "status": "updated",
        "message_id": report.id,
        "new_status": message.status
    }

@app.get("/get_logs", response_model=List[MessageLogResponse])
def get_logs(current_user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    """
    Fetch all message logs for current user
    Includes patient details and delivery status
    """
    logs = db.query(MessageLog).filter(
        MessageLog.user_id == current_user.id
    ).order_by(MessageLog.timestamp.desc()).all()
    
    result = []
    for log in logs:
        result.append(MessageLogResponse(
            id=log.id,
            patient_name=log.patient.name,
            phone=log.patient.phone,
            message_text=log.message_text,
            status=log.status,
            timestamp=log.timestamp
        ))
    
    return result

@app.get("/analytics")
def get_analytics(current_user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """Get message delivery analytics"""
    total_messages = db.query(MessageLog).filter(MessageLog.user_id == current_user.id).count()
    delivered = db.query(MessageLog).filter(
        MessageLog.user_id == current_user.id,
        MessageLog.status == "delivered"
    ).count()
    failed = db.query(MessageLog).filter(
        MessageLog.user_id == current_user.id,
        MessageLog.status == "failed"
    ).count()
    pending = db.query(MessageLog).filter(
        MessageLog.user_id == current_user.id,
        MessageLog.status.in_(["pending", "sent"])
    ).count()
    
    return {
        "total_messages": total_messages,
        "delivered": delivered,
        "failed": failed,
        "pending": pending,
        "delivery_rate": round((delivered / total_messages * 100) if total_messages > 0 else 0, 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
