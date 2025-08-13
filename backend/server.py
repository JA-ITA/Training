from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any, Union
import os
import uuid
import shutil
from pathlib import Path
import mimetypes
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.colors import blue, black, red
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import qrcode
from PIL import Image as PILImage

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Training Management API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'training_db')

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_collection = db.users
programs_collection = db.programs
modules_collection = db.modules
units_collection = db.units
content_collection = db.content
assessments_collection = db.assessments
questions_collection = db.questions
enrollments_collection = db.enrollments
progress_collection = db.progress
certificates_collection = db.certificates
assessment_attempts_collection = db.assessment_attempts

# Create uploads directory
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Profile photos directory
PROFILE_PHOTOS_DIR = UPLOAD_DIR / "profile_photos"
PROFILE_PHOTOS_DIR.mkdir(exist_ok=True)

# Available roles in the system
AVAILABLE_ROLES = [
    "administrator",
    "administrative_assistant", 
    "lecturer",
    "learner",
    "administrator_supervisor"
]

# User status options
USER_STATUS = ["pending", "approved", "suspended", "deleted"]

# Authentication Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "learner"  # Will be requested role, needs admin approval

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    requested_role: Optional[str] = None
    status: str = "pending"  # pending, approved, suspended, deleted
    is_active: bool = True
    profile_photo: Optional[str] = None
    created_at: str
    updated_at: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class AdminUserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str
    status: str = "approved"

class UserApproval(BaseModel):
    user_id: str
    approved_role: str
    status: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Existing Models (Programs, Modules, Units, Content)
class ProgramCreate(BaseModel):
    title: str
    description: str
    learning_objectives: List[str]
    expiry_duration: int  # in months
    renewal_requirements: str

class Program(BaseModel):
    id: str
    title: str
    description: str
    learning_objectives: List[str]
    expiry_duration: int
    renewal_requirements: str
    created_by: str
    created_at: str
    updated_at: str

class ModuleCreate(BaseModel):
    program_id: str
    title: str
    description: str
    order: int

class Module(BaseModel):
    id: str
    program_id: str
    title: str
    description: str
    order: int
    created_at: str
    updated_at: str

class UnitCreate(BaseModel):
    module_id: str
    title: str
    learning_objectives: List[str]
    order: int

class Unit(BaseModel):
    id: str
    module_id: str
    title: str
    learning_objectives: List[str]
    order: int
    created_at: str
    updated_at: str

class ContentItem(BaseModel):
    id: str
    unit_id: str
    title: str
    content_type: str  # pdf, video, image, audio
    file_path: str
    file_size: int
    mime_type: str
    created_at: str

# Assessment Models
class QuestionOption(BaseModel):
    id: str
    text: str
    is_correct: bool = False

class QuestionCreate(BaseModel):
    question_text: str
    question_type: str  # multiple_choice, true_false, essay
    options: List[QuestionOption] = []
    correct_answer: Optional[str] = None  # For true/false and essay
    points: int = 1
    explanation: Optional[str] = None

class Question(BaseModel):
    id: str
    question_text: str
    question_type: str
    options: List[QuestionOption] = []
    correct_answer: Optional[str] = None
    points: int
    explanation: Optional[str] = None
    created_by: str
    created_at: str
    updated_at: str

class AssessmentCreate(BaseModel):
    title: str
    description: str
    program_id: Optional[str] = None
    module_id: Optional[str] = None
    unit_id: Optional[str] = None
    question_ids: List[str]
    pass_mark: int = 80
    time_limit: Optional[int] = None  # in minutes
    max_attempts: int = 3
    randomize_questions: bool = False

class Assessment(BaseModel):
    id: str
    title: str
    description: str
    program_id: Optional[str] = None
    module_id: Optional[str] = None
    unit_id: Optional[str] = None
    question_ids: List[str]
    pass_mark: int
    time_limit: Optional[int] = None
    max_attempts: int
    randomize_questions: bool
    created_by: str
    created_at: str
    updated_at: str

class AnswerSubmission(BaseModel):
    question_id: str
    selected_option_id: Optional[str] = None  # For multiple choice
    answer_text: Optional[str] = None  # For true/false and essay

class AssessmentSubmission(BaseModel):
    assessment_id: str
    answers: List[AnswerSubmission]

class EnrollmentCreate(BaseModel):
    user_id: str
    program_id: str

class Enrollment(BaseModel):
    id: str
    user_id: str
    program_id: str
    enrolled_at: str
    completed_at: Optional[str] = None
    status: str = "active"  # active, completed, suspended

# Certificate Models
class Certificate(BaseModel):
    id: str
    user_id: str
    program_id: str
    enrollment_id: str
    user_name: str
    program_title: str
    issued_date: str
    expiry_date: Optional[str] = None
    certificate_number: str
    verification_code: str
    is_valid: bool = True
    certificate_file_path: Optional[str] = None

class CertificateVerification(BaseModel):
    verification_code: str

# Utility functions
def generate_id():
    return str(uuid.uuid4())

def get_current_timestamp():
    return datetime.utcnow().isoformat()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = users_collection.find_one({"username": username}, {"_id": 0})
    if user is None:
        raise credentials_exception
    return User(**user)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

# Certificate Generation Utilities
def generate_certificate_number():
    """Generate a unique certificate number"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"ITA-{timestamp}-{generate_id()[:8].upper()}"

def generate_verification_code():
    """Generate a verification code for certificate"""
    return generate_id()[:12].upper()

def create_certificate_pdf(certificate_data, file_path):
    """Generate certificate PDF"""
    try:
        # Create PDF document
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=blue
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=black
        )
        
        content_style = ParagraphStyle(
            'CustomContent',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=black
        )
        
        # Certificate content
        story.append(Spacer(1, 50))
        story.append(Paragraph("CERTIFICATE OF COMPLETION", title_style))
        story.append(Spacer(1, 30))
        
        story.append(Paragraph("This is to certify that", content_style))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph(f"<b>{certificate_data['user_name']}</b>", subtitle_style))
        story.append(Spacer(1, 30))
        
        story.append(Paragraph("has successfully completed the training program", content_style))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph(f"<b>{certificate_data['program_title']}</b>", subtitle_style))
        story.append(Spacer(1, 30))
        
        story.append(Paragraph(f"Date of Completion: {certificate_data['completion_date']}", content_style))
        story.append(Paragraph(f"Certificate Number: {certificate_data['certificate_number']}", content_style))
        story.append(Paragraph(f"Verification Code: {certificate_data['verification_code']}", content_style))
        
        if certificate_data.get('expiry_date'):
            story.append(Paragraph(f"Valid Until: {certificate_data['expiry_date']}", content_style))
        
        story.append(Spacer(1, 50))
        
        # Generate QR code for verification
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"https://training.example.com/verify/{certificate_data['verification_code']}")
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Note: For simplicity, we'll skip adding the QR code image to avoid complex image handling
        story.append(Paragraph("Scan QR code or use verification code to verify this certificate", content_style))
        
        # Build PDF
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error generating certificate PDF: {e}")
        return False

def check_program_completion(user_id: str, program_id: str) -> bool:
    """Check if user has completed all requirements for a program"""
    try:
        # Get program assessments
        program_assessments = list(assessments_collection.find({"program_id": program_id}))
        
        if not program_assessments:
            # If no assessments, consider program completed (content-only programs)
            return True
        
        # Check if user has passed all assessments
        for assessment in program_assessments:
            # Get user's latest attempt for this assessment
            latest_attempt = assessment_attempts_collection.find_one(
                {"assessment_id": assessment["id"], "user_id": user_id},
                sort=[("submitted_at", -1)]
            )
            
            if not latest_attempt or not latest_attempt.get("is_passed"):
                return False
        
        return True
        
    except Exception as e:
        print(f"Error checking program completion: {e}")
        return False

def auto_generate_certificate(user_id: str, program_id: str, enrollment_id: str):
    """Automatically generate certificate when program is completed"""
    try:
        # Check if certificate already exists
        existing_cert = certificates_collection.find_one({
            "user_id": user_id,
            "program_id": program_id,
            "enrollment_id": enrollment_id
        })
        
        if existing_cert:
            return existing_cert["id"]
        
        # Get user and program data
        user = users_collection.find_one({"id": user_id})
        program = programs_collection.find_one({"id": program_id})
        
        if not user or not program:
            return None
        
        # Generate certificate data
        certificate_id = generate_id()
        certificate_number = generate_certificate_number()
        verification_code = generate_verification_code()
        issued_date = get_current_timestamp()
        
        # Calculate expiry date if program has expiry duration
        expiry_date = None
        if program.get("expiry_duration"):
            expiry_date = (datetime.utcnow() + timedelta(days=program["expiry_duration"] * 30)).isoformat()
        
        # Create certificate directory
        cert_dir = Path("/app/certificates")
        cert_dir.mkdir(exist_ok=True)
        
        # Generate PDF file path
        pdf_filename = f"certificate_{certificate_id}.pdf"
        pdf_path = cert_dir / pdf_filename
        
        # Certificate data for PDF generation
        cert_data = {
            "user_name": user["full_name"],
            "program_title": program["title"],
            "completion_date": datetime.utcnow().strftime("%B %d, %Y"),
            "certificate_number": certificate_number,
            "verification_code": verification_code,
            "expiry_date": datetime.fromisoformat(expiry_date.replace('Z', '+00:00')).strftime("%B %d, %Y") if expiry_date else None
        }
        
        # Generate PDF
        if create_certificate_pdf(cert_data, str(pdf_path)):
            # Save certificate to database
            certificate_doc = {
                "id": certificate_id,
                "user_id": user_id,
                "program_id": program_id,
                "enrollment_id": enrollment_id,
                "user_name": user["full_name"],
                "program_title": program["title"],
                "issued_date": issued_date,
                "expiry_date": expiry_date,
                "certificate_number": certificate_number,
                "verification_code": verification_code,
                "is_valid": True,
                "certificate_file_path": str(pdf_path)
            }
            
            certificates_collection.insert_one(certificate_doc)
            
            # Update enrollment status to completed
            enrollments_collection.update_one(
                {"id": enrollment_id},
                {"$set": {"status": "completed", "completed_at": issued_date}}
            )
            
            return certificate_id
        
        return None
        
    except Exception as e:
        print(f"Error auto-generating certificate: {e}")
        return None

# API Routes

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Training Management API is running"}

# Authentication endpoints
@app.post("/api/register", response_model=User)
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = users_collection.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Validate role
    if user_data.role not in AVAILABLE_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Available roles: {', '.join(AVAILABLE_ROLES)}")
    
    user_id = generate_id()
    timestamp = get_current_timestamp()
    
    # Auto-approve learners, others need admin approval
    status = "approved" if user_data.role == "learner" else "pending"
    
    user_doc = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "role": "learner" if status == "pending" else user_data.role,  # Set to learner until approved
        "requested_role": user_data.role if status == "pending" else None,
        "status": status,
        "password_hash": get_password_hash(user_data.password),
        "is_active": True,
        "profile_photo": None,
        "created_at": timestamp,
        "updated_at": timestamp,
        "approved_by": None,
        "approved_at": timestamp if status == "approved" else None
    }
    
    users_collection.insert_one(user_doc)
    user_response = user_doc.copy()
    del user_response["password_hash"]
    return User(**user_response)

@app.post("/api/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    user = users_collection.find_one({"username": user_credentials.username})
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Check user status
    user_status = user.get("status", "approved")
    if user_status == "pending":
        raise HTTPException(status_code=403, detail="Account pending approval. Please contact an administrator.")
    elif user_status == "suspended":
        raise HTTPException(status_code=403, detail="Account suspended. Please contact an administrator.")
    elif user_status == "deleted":
        raise HTTPException(status_code=403, detail="Account not found.")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    user_response = user.copy()
    del user_response["password_hash"]
    del user_response["_id"]
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**user_response)
    }

@app.get("/api/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/api/users", response_model=List[User])
async def get_users(current_user: User = Depends(require_role(["administrator", "administrator_supervisor"]))):
    users = list(users_collection.find({}, {"_id": 0, "password_hash": 0}))
    return [User(**user) for user in users]

# Enhanced User Management APIs
@app.get("/api/users/pending", response_model=List[User])
async def get_pending_users(current_user: User = Depends(require_role(["administrator", "administrator_supervisor"]))):
    """Get users pending approval"""
    users = list(users_collection.find({"status": "pending"}, {"_id": 0, "password_hash": 0}))
    return [User(**user) for user in users]

@app.post("/api/users", response_model=User)
async def admin_create_user(user_data: AdminUserCreate, current_user: User = Depends(require_role(["administrator", "administrator_supervisor"]))):
    """Admin creates a user directly (no approval needed)"""
    # Check if user already exists
    existing_user = users_collection.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Validate role
    if user_data.role not in AVAILABLE_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Available roles: {', '.join(AVAILABLE_ROLES)}")
    
    user_id = generate_id()
    timestamp = get_current_timestamp()
    
    user_doc = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "role": user_data.role,
        "requested_role": None,
        "status": user_data.status,
        "password_hash": get_password_hash(user_data.password),
        "is_active": True,
        "profile_photo": None,
        "created_at": timestamp,
        "updated_at": timestamp,
        "approved_by": current_user.id,
        "approved_at": timestamp
    }
    
    users_collection.insert_one(user_doc)
    user_response = user_doc.copy()
    del user_response["password_hash"]
    return User(**user_response)

@app.put("/api/users/{user_id}/approve", response_model=User)
async def approve_user(user_id: str, approval: UserApproval, current_user: User = Depends(require_role(["administrator", "administrator_supervisor"]))):
    """Approve a user and assign role"""
    user = users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if approval.approved_role not in AVAILABLE_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Available roles: {', '.join(AVAILABLE_ROLES)}")
    
    timestamp = get_current_timestamp()
    
    update_doc = {
        "role": approval.approved_role,
        "status": approval.status,
        "approved_by": current_user.id,
        "approved_at": timestamp,
        "updated_at": timestamp
    }
    
    users_collection.update_one({"id": user_id}, {"$set": update_doc})
    
    updated_user = users_collection.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    return User(**updated_user)

@app.put("/api/users/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: UserUpdate, current_user: User = Depends(require_role(["administrator", "administrator_supervisor"]))):
    """Update user information"""
    user = users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    timestamp = get_current_timestamp()
    update_doc = {"updated_at": timestamp}
    
    if user_update.full_name is not None:
        update_doc["full_name"] = user_update.full_name
    if user_update.email is not None:
        # Check if email is already taken by another user
        existing_user = users_collection.find_one({"email": user_update.email, "id": {"$ne": user_id}})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        update_doc["email"] = user_update.email
    if user_update.role is not None:
        if user_update.role not in AVAILABLE_ROLES:
            raise HTTPException(status_code=400, detail=f"Invalid role. Available roles: {', '.join(AVAILABLE_ROLES)}")
        update_doc["role"] = user_update.role
    if user_update.status is not None:
        if user_update.status not in USER_STATUS:
            raise HTTPException(status_code=400, detail=f"Invalid status. Available statuses: {', '.join(USER_STATUS)}")
        update_doc["status"] = user_update.status
    
    users_collection.update_one({"id": user_id}, {"$set": update_doc})
    
    updated_user = users_collection.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    return User(**updated_user)

@app.put("/api/users/{user_id}/suspend")
async def suspend_user(user_id: str, current_user: User = Depends(require_role(["administrator", "administrator_supervisor"]))):
    """Suspend a user"""
    result = users_collection.update_one(
        {"id": user_id}, 
        {"$set": {"status": "suspended", "updated_at": get_current_timestamp()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User suspended successfully"}

@app.put("/api/users/{user_id}/restore")
async def restore_user(user_id: str, current_user: User = Depends(require_role(["administrator", "administrator_supervisor"]))):
    """Restore a suspended user"""
    result = users_collection.update_one(
        {"id": user_id}, 
        {"$set": {"status": "approved", "updated_at": get_current_timestamp()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User restored successfully"}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(require_role(["administrator", "administrator_supervisor"]))):
    """Soft delete a user (mark as deleted)"""
    result = users_collection.update_one(
        {"id": user_id}, 
        {"$set": {"status": "deleted", "is_active": False, "updated_at": get_current_timestamp()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# User Profile Management APIs
@app.post("/api/users/{user_id}/profile-photo")
async def upload_profile_photo(user_id: str, file: UploadFile = File(...), current_user: User = Depends(get_current_active_user)):
    """Upload profile photo"""
    # Users can only update their own profile or admin can update any
    if current_user.id != user_id and current_user.role not in ["administrator", "administrator_supervisor"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    photo_filename = f"{user_id}_{generate_id()}{file_extension}"
    photo_path = PROFILE_PHOTOS_DIR / photo_filename
    
    # Save file
    with open(photo_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update user document
    photo_url = f"/api/users/{user_id}/profile-photo/{photo_filename}"
    users_collection.update_one(
        {"id": user_id}, 
        {"$set": {"profile_photo": photo_url, "updated_at": get_current_timestamp()}}
    )
    
    return {"message": "Profile photo uploaded successfully", "photo_url": photo_url}

@app.get("/api/users/{user_id}/profile-photo/{filename}")
async def get_profile_photo(user_id: str, filename: str):
    """Get user profile photo"""
    photo_path = PROFILE_PHOTOS_DIR / filename
    if not photo_path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(str(photo_path))

@app.put("/api/users/{user_id}/password")
async def update_password(user_id: str, password_update: PasswordUpdate, current_user: User = Depends(get_current_active_user)):
    """Update user password"""
    # Users can only update their own password
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this password")
    
    user = users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(password_update.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    new_password_hash = get_password_hash(password_update.new_password)
    users_collection.update_one(
        {"id": user_id}, 
        {"$set": {"password_hash": new_password_hash, "updated_at": get_current_timestamp()}}
    )
    
    return {"message": "Password updated successfully"}

# Grades and Assessment Results APIs
@app.get("/api/users/{user_id}/grades")
async def get_user_grades(user_id: str, current_user: User = Depends(get_current_active_user)):
    """Get user's assessment results and grades"""
    # Users can only see their own grades or admin/supervisor can see any
    if current_user.id != user_id and current_user.role not in ["administrator", "administrator_supervisor", "lecturer"]:
        raise HTTPException(status_code=403, detail="Not authorized to view these grades")
    
    # Get all assessment attempts for the user
    attempts = list(assessment_attempts_collection.find({"user_id": user_id}, {"_id": 0}))
    
    # Enrich with assessment details
    grades = []
    for attempt in attempts:
        assessment = assessments_collection.find_one({"id": attempt["assessment_id"]}, {"_id": 0})
        if assessment:
            grade_record = {
                "assessment_id": attempt["assessment_id"],
                "assessment_title": assessment["title"],
                "total_points": attempt["total_points"],
                "earned_points": attempt["earned_points"],
                "percentage": attempt["percentage"],
                "is_passed": attempt["is_passed"],
                "submitted_at": attempt["submitted_at"],
                "attempt_id": attempt["id"]
            }
            grades.append(grade_record)
    
    return {"user_id": user_id, "grades": grades}

# Course Assignment APIs
@app.post("/api/programs/{program_id}/assign-users")
async def assign_users_to_program(program_id: str, user_ids: List[str], current_user: User = Depends(require_role(["administrator", "administrator_supervisor"]))):
    """Assign multiple users to a program"""
    program = programs_collection.find_one({"id": program_id})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    results = []
    for user_id in user_ids:
        # Check if user exists
        user = users_collection.find_one({"id": user_id})
        if not user:
            results.append({"user_id": user_id, "status": "failed", "message": "User not found"})
            continue
        
        # Check if already enrolled
        existing_enrollment = enrollments_collection.find_one({"user_id": user_id, "program_id": program_id})
        if existing_enrollment:
            results.append({"user_id": user_id, "status": "skipped", "message": "Already enrolled"})
            continue
        
        # Create enrollment
        enrollment_id = generate_id()
        timestamp = get_current_timestamp()
        
        enrollment_doc = {
            "id": enrollment_id,
            "user_id": user_id,
            "program_id": program_id,
            "enrolled_at": timestamp,
            "completed_at": None,
            "status": "active",
            "assigned_by": current_user.id
        }
        
        enrollments_collection.insert_one(enrollment_doc)
        results.append({"user_id": user_id, "status": "success", "message": "Enrolled successfully"})
    
    return {"program_id": program_id, "results": results}

@app.delete("/api/programs/{program_id}/users/{user_id}")
async def remove_user_from_program(program_id: str, user_id: str, current_user: User = Depends(require_role(["administrator", "administrator_supervisor"]))):
    """Remove a user from a program"""
    result = enrollments_collection.delete_one({"user_id": user_id, "program_id": program_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    return {"message": "User removed from program successfully"}

# Programs endpoints (updated with authentication)
@app.post("/api/programs", response_model=Program)
async def create_program(program: ProgramCreate, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    program_id = generate_id()
    timestamp = get_current_timestamp()
    
    program_doc = {
        "id": program_id,
        "title": program.title,
        "description": program.description,
        "learning_objectives": program.learning_objectives,
        "expiry_duration": program.expiry_duration,
        "renewal_requirements": program.renewal_requirements,
        "created_by": current_user.id,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    programs_collection.insert_one(program_doc)
    return Program(**program_doc)

@app.get("/api/programs", response_model=List[Program])
async def get_programs(current_user: User = Depends(get_current_active_user)):
    programs = list(programs_collection.find({}, {"_id": 0}))
    return [Program(**program) for program in programs]

@app.get("/api/programs/{program_id}", response_model=Program)
async def get_program(program_id: str, current_user: User = Depends(get_current_active_user)):
    program = programs_collection.find_one({"id": program_id}, {"_id": 0})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return Program(**program)

@app.put("/api/programs/{program_id}", response_model=Program)
async def update_program(program_id: str, program: ProgramCreate, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    timestamp = get_current_timestamp()
    
    update_doc = {
        "title": program.title,
        "description": program.description,
        "learning_objectives": program.learning_objectives,
        "expiry_duration": program.expiry_duration,
        "renewal_requirements": program.renewal_requirements,
        "updated_at": timestamp
    }
    
    result = programs_collection.update_one({"id": program_id}, {"$set": update_doc})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Program not found")
    
    updated_program = programs_collection.find_one({"id": program_id}, {"_id": 0})
    return Program(**updated_program)

@app.delete("/api/programs/{program_id}")
async def delete_program(program_id: str, current_user: User = Depends(require_role(["administrator", "administrator_supervisor"]))):
    # Delete related modules and units
    modules = list(modules_collection.find({"program_id": program_id}))
    for module in modules:
        units_collection.delete_many({"module_id": module["id"]})
    modules_collection.delete_many({"program_id": program_id})
    
    result = programs_collection.delete_one({"id": program_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Program not found")
    
    return {"message": "Program deleted successfully"}

# Modules endpoints (keep existing functionality)
@app.post("/api/modules", response_model=Module)
async def create_module(module: ModuleCreate, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    # Verify program exists
    program = programs_collection.find_one({"id": module.program_id})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    module_id = generate_id()
    timestamp = get_current_timestamp()
    
    module_doc = {
        "id": module_id,
        "program_id": module.program_id,
        "title": module.title,
        "description": module.description,
        "order": module.order,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    modules_collection.insert_one(module_doc)
    return Module(**module_doc)

@app.get("/api/programs/{program_id}/modules", response_model=List[Module])
async def get_program_modules(program_id: str, current_user: User = Depends(get_current_active_user)):
    modules = list(modules_collection.find({"program_id": program_id}, {"_id": 0}).sort("order", 1))
    return [Module(**module) for module in modules]

@app.put("/api/modules/{module_id}", response_model=Module)
async def update_module(module_id: str, module_data: dict, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    timestamp = get_current_timestamp()
    update_doc = {**module_data, "updated_at": timestamp}
    
    result = modules_collection.update_one({"id": module_id}, {"$set": update_doc})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Module not found")
    
    updated_module = modules_collection.find_one({"id": module_id}, {"_id": 0})
    return Module(**updated_module)

@app.delete("/api/modules/{module_id}")
async def delete_module(module_id: str, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    # Delete related units
    units_collection.delete_many({"module_id": module_id})
    
    result = modules_collection.delete_one({"id": module_id})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Module not found")
    
    return {"message": "Module deleted successfully"}

# Units endpoints (keep existing functionality)
@app.post("/api/units", response_model=Unit)
async def create_unit(unit: UnitCreate, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    # Verify module exists
    module = modules_collection.find_one({"id": unit.module_id})
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    unit_id = generate_id()
    timestamp = get_current_timestamp()
    
    unit_doc = {
        "id": unit_id,
        "module_id": unit.module_id,
        "title": unit.title,
        "learning_objectives": unit.learning_objectives,
        "order": unit.order,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    units_collection.insert_one(unit_doc)
    return Unit(**unit_doc)

@app.get("/api/modules/{module_id}/units", response_model=List[Unit])
async def get_module_units(module_id: str, current_user: User = Depends(get_current_active_user)):
    units = list(units_collection.find({"module_id": module_id}, {"_id": 0}).sort("order", 1))
    return [Unit(**unit) for unit in units]

@app.put("/api/units/{unit_id}", response_model=Unit)
async def update_unit(unit_id: str, unit_data: dict, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    timestamp = get_current_timestamp()
    update_doc = {**unit_data, "updated_at": timestamp}
    
    result = units_collection.update_one({"id": unit_id}, {"$set": update_doc})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    updated_unit = units_collection.find_one({"id": unit_id}, {"_id": 0})
    return Unit(**updated_unit)

@app.delete("/api/units/{unit_id}")
async def delete_unit(unit_id: str, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    result = units_collection.delete_one({"id": unit_id})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    return {"message": "Unit deleted successfully"}

# Content endpoints (keep existing functionality)
@app.post("/api/units/{unit_id}/content/upload")
async def upload_content(unit_id: str, file: UploadFile = File(...), current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    # Verify unit exists
    unit = units_collection.find_one({"id": unit_id})
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    # Generate unique filename
    file_id = generate_id()
    file_extension = Path(file.filename).suffix
    safe_filename = f"{file_id}{file_extension}"
    file_path = UPLOAD_DIR / safe_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Determine content type
    mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    content_type = "unknown"
    
    if mime_type.startswith("image/"):
        content_type = "image"
    elif mime_type.startswith("video/"):
        content_type = "video"
    elif mime_type.startswith("audio/"):
        content_type = "audio"
    elif mime_type == "application/pdf":
        content_type = "pdf"
    elif mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        content_type = "document"
    
    # Save content metadata
    content_doc = {
        "id": file_id,
        "unit_id": unit_id,
        "title": file.filename,
        "content_type": content_type,
        "file_path": str(file_path),
        "file_size": file_path.stat().st_size,
        "mime_type": mime_type,
        "created_at": get_current_timestamp()
    }
    
    content_collection.insert_one(content_doc)
    return ContentItem(**content_doc)

@app.get("/api/units/{unit_id}/content", response_model=List[ContentItem])
async def get_unit_content(unit_id: str, current_user: User = Depends(get_current_active_user)):
    content_items = list(content_collection.find({"unit_id": unit_id}, {"_id": 0}))
    return [ContentItem(**item) for item in content_items]

@app.delete("/api/content/{content_id}")
async def delete_content(content_id: str, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    content = content_collection.find_one({"id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Delete file from filesystem
    file_path = Path(content["file_path"])
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    content_collection.delete_one({"id": content_id})
    return {"message": "Content deleted successfully"}

@app.get("/api/programs/{program_id}/structure")
async def get_program_structure(program_id: str, current_user: User = Depends(get_current_active_user)):
    # Get program
    program = programs_collection.find_one({"id": program_id}, {"_id": 0})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Get modules with units
    modules = list(modules_collection.find({"program_id": program_id}, {"_id": 0}).sort("order", 1))
    
    for module in modules:
        units = list(units_collection.find({"module_id": module["id"]}, {"_id": 0}).sort("order", 1))
        module["units"] = units
    
    return {
        "program": program,
        "modules": modules
    }

# Question Bank endpoints
@app.post("/api/questions", response_model=Question)
async def create_question(question: QuestionCreate, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    question_id = generate_id()
    timestamp = get_current_timestamp()
    
    # Generate IDs for options
    options_with_ids = []
    for option in question.options:
        options_with_ids.append({
            "id": generate_id(),
            "text": option.text,
            "is_correct": option.is_correct
        })
    
    question_doc = {
        "id": question_id,
        "question_text": question.question_text,
        "question_type": question.question_type,
        "options": options_with_ids,
        "correct_answer": question.correct_answer,
        "points": question.points,
        "explanation": question.explanation,
        "created_by": current_user.id,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    questions_collection.insert_one(question_doc)
    return Question(**question_doc)

@app.get("/api/questions", response_model=List[Question])
async def get_questions(current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    questions = list(questions_collection.find({}, {"_id": 0}))
    return [Question(**question) for question in questions]

@app.get("/api/questions/{question_id}", response_model=Question)
async def get_question(question_id: str, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    question = questions_collection.find_one({"id": question_id}, {"_id": 0})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return Question(**question)

@app.put("/api/questions/{question_id}", response_model=Question)
async def update_question(question_id: str, question: QuestionCreate, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    timestamp = get_current_timestamp()
    
    # Generate IDs for options
    options_with_ids = []
    for option in question.options:
        options_with_ids.append({
            "id": generate_id(),
            "text": option.text,
            "is_correct": option.is_correct
        })
    
    update_doc = {
        "question_text": question.question_text,
        "question_type": question.question_type,
        "options": options_with_ids,
        "correct_answer": question.correct_answer,
        "points": question.points,
        "explanation": question.explanation,
        "updated_at": timestamp
    }
    
    result = questions_collection.update_one({"id": question_id}, {"$set": update_doc})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    updated_question = questions_collection.find_one({"id": question_id}, {"_id": 0})
    return Question(**updated_question)

@app.delete("/api/questions/{question_id}")
async def delete_question(question_id: str, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    result = questions_collection.delete_one({"id": question_id})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": "Question deleted successfully"}

# Assessment endpoints
@app.post("/api/assessments", response_model=Assessment)
async def create_assessment(assessment: AssessmentCreate, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    assessment_id = generate_id()
    timestamp = get_current_timestamp()
    
    assessment_doc = {
        "id": assessment_id,
        "title": assessment.title,
        "description": assessment.description,
        "program_id": assessment.program_id,
        "module_id": assessment.module_id,
        "unit_id": assessment.unit_id,
        "question_ids": assessment.question_ids,
        "pass_mark": assessment.pass_mark,
        "time_limit": assessment.time_limit,
        "max_attempts": assessment.max_attempts,
        "randomize_questions": assessment.randomize_questions,
        "created_by": current_user.id,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    assessments_collection.insert_one(assessment_doc)
    return Assessment(**assessment_doc)

@app.get("/api/assessments", response_model=List[Assessment])
async def get_assessments(current_user: User = Depends(get_current_active_user)):
    assessments = list(assessments_collection.find({}, {"_id": 0}))
    return [Assessment(**assessment) for assessment in assessments]

@app.get("/api/programs/{program_id}/assessments", response_model=List[Assessment])
async def get_program_assessments(program_id: str, current_user: User = Depends(get_current_active_user)):
    assessments = list(assessments_collection.find({"program_id": program_id}, {"_id": 0}))
    return [Assessment(**assessment) for assessment in assessments]

@app.get("/api/assessments/{assessment_id}", response_model=Assessment)
async def get_assessment(assessment_id: str, current_user: User = Depends(get_current_active_user)):
    assessment = assessments_collection.find_one({"id": assessment_id}, {"_id": 0})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return Assessment(**assessment)

@app.get("/api/assessments/{assessment_id}/questions")
async def get_assessment_questions(assessment_id: str, current_user: User = Depends(get_current_active_user)):
    assessment = assessments_collection.find_one({"id": assessment_id}, {"_id": 0})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    questions = list(questions_collection.find({"id": {"$in": assessment["question_ids"]}}, {"_id": 0}))
    
    # For learners, don't show correct answers or explanations during assessment
    if current_user.role == "learner":
        for question in questions:
            if question["question_type"] in ["multiple_choice", "true_false"]:
                for option in question["options"]:
                    option["is_correct"] = False
            question["correct_answer"] = None
            question["explanation"] = None
    
    return questions

@app.post("/api/assessments/{assessment_id}/submit")
async def submit_assessment(assessment_id: str, submission: AssessmentSubmission, current_user: User = Depends(get_current_active_user)):
    assessment = assessments_collection.find_one({"id": assessment_id}, {"_id": 0})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Get questions for scoring
    questions = list(questions_collection.find({"id": {"$in": assessment["question_ids"]}}, {"_id": 0}))
    questions_dict = {q["id"]: q for q in questions}
    
    # Calculate score
    total_points = sum(q["points"] for q in questions)
    earned_points = 0
    
    results = []
    
    for answer in submission.answers:
        question = questions_dict.get(answer.question_id)
        if not question:
            continue
        
        is_correct = False
        
        if question["question_type"] == "multiple_choice":
            if answer.selected_option_id:
                selected_option = next((opt for opt in question["options"] if opt["id"] == answer.selected_option_id), None)
                if selected_option and selected_option["is_correct"]:
                    is_correct = True
                    earned_points += question["points"]
        
        elif question["question_type"] == "true_false":
            if answer.answer_text and answer.answer_text.lower() == question["correct_answer"].lower():
                is_correct = True
                earned_points += question["points"]
        
        elif question["question_type"] == "essay":
            # For essay questions, manual grading is needed - mark as requires review
            is_correct = None  # Will be graded manually
        
        results.append({
            "question_id": answer.question_id,
            "selected_option_id": answer.selected_option_id,
            "answer_text": answer.answer_text,
            "is_correct": is_correct,
            "points_earned": question["points"] if is_correct else 0
        })
    
    # Calculate percentage
    percentage = (earned_points / total_points * 100) if total_points > 0 else 0
    is_passed = percentage >= assessment["pass_mark"]
    
    # Save attempt
    attempt_id = generate_id()
    attempt_doc = {
        "id": attempt_id,
        "assessment_id": assessment_id,
        "user_id": current_user.id,
        "answers": results,
        "total_points": total_points,
        "earned_points": earned_points,
        "percentage": percentage,
        "is_passed": is_passed,
        "submitted_at": get_current_timestamp()
    }
    
    assessment_attempts_collection.insert_one(attempt_doc)
    
    # Check if this completion triggers program completion and certificate generation
    certificate_id = None
    if is_passed and assessment.get("program_id"):
        # Find user's enrollment in this program
        enrollment = enrollments_collection.find_one({
            "user_id": current_user.id,
            "program_id": assessment["program_id"],
            "status": "active"
        })
        
        if enrollment:
            # Check if program is now completed
            if check_program_completion(current_user.id, assessment["program_id"]):
                certificate_id = auto_generate_certificate(
                    current_user.id,
                    assessment["program_id"],
                    enrollment["id"]
                )
    
    response_data = {
        "attempt_id": attempt_id,
        "percentage": percentage,
        "is_passed": is_passed,
        "total_points": total_points,
        "earned_points": earned_points,
        "results": results
    }
    
    if certificate_id:
        response_data["certificate_generated"] = True
        response_data["certificate_id"] = certificate_id
    
    return response_data

# Enrollment endpoints
@app.post("/api/enrollments", response_model=Enrollment)
async def create_enrollment(enrollment: EnrollmentCreate, current_user: User = Depends(require_role(["admin"]))):
    # Check if user already enrolled
    existing = enrollments_collection.find_one({"user_id": enrollment.user_id, "program_id": enrollment.program_id})
    if existing:
        raise HTTPException(status_code=400, detail="User already enrolled in this program")
    
    enrollment_id = generate_id()
    timestamp = get_current_timestamp()
    
    enrollment_doc = {
        "id": enrollment_id,
        "user_id": enrollment.user_id,
        "program_id": enrollment.program_id,
        "enrolled_at": timestamp,
        "completed_at": None,
        "status": "active"
    }
    
    enrollments_collection.insert_one(enrollment_doc)
    return Enrollment(**enrollment_doc)

@app.get("/api/enrollments", response_model=List[Enrollment])
async def get_enrollments(current_user: User = Depends(require_role(["admin"]))):
    enrollments = list(enrollments_collection.find({}, {"_id": 0}))
    return [Enrollment(**enrollment) for enrollment in enrollments]

@app.get("/api/users/{user_id}/enrollments", response_model=List[Enrollment])
async def get_user_enrollments(user_id: str, current_user: User = Depends(get_current_active_user)):
    # Users can only see their own enrollments unless they're admin
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these enrollments")
    
    enrollments = list(enrollments_collection.find({"user_id": user_id}, {"_id": 0}))
    return [Enrollment(**enrollment) for enrollment in enrollments]

@app.get("/api/programs/{program_id}/enrollments", response_model=List[Enrollment])
async def get_program_enrollments(program_id: str, current_user: User = Depends(require_role(["administrator", "administrator_supervisor", "lecturer"]))):
    enrollments = list(enrollments_collection.find({"program_id": program_id}, {"_id": 0}))
    return [Enrollment(**enrollment) for enrollment in enrollments]

# Certificate Management endpoints
@app.get("/api/certificates", response_model=List[Certificate])
async def get_certificates(current_user: User = Depends(get_current_active_user)):
    # Users can only see their own certificates unless they're admin
    query = {}
    if current_user.role != "admin":
        query["user_id"] = current_user.id
    
    certificates = list(certificates_collection.find(query, {"_id": 0}))
    return [Certificate(**cert) for cert in certificates]

@app.get("/api/certificates/{certificate_id}", response_model=Certificate)
async def get_certificate(certificate_id: str, current_user: User = Depends(get_current_active_user)):
    certificate = certificates_collection.find_one({"id": certificate_id}, {"_id": 0})
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    # Users can only access their own certificates unless they're admin
    if current_user.role != "admin" and certificate["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this certificate")
    
    return Certificate(**certificate)

@app.get("/api/certificates/{certificate_id}/download")
async def download_certificate(certificate_id: str, current_user: User = Depends(get_current_active_user)):
    certificate = certificates_collection.find_one({"id": certificate_id}, {"_id": 0})
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    # Users can only download their own certificates unless they're admin
    if current_user.role != "admin" and certificate["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to download this certificate")
    
    if not certificate.get("certificate_file_path") or not Path(certificate["certificate_file_path"]).exists():
        raise HTTPException(status_code=404, detail="Certificate file not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=certificate["certificate_file_path"],
        filename=f"certificate_{certificate['certificate_number']}.pdf",
        media_type="application/pdf"
    )

@app.post("/api/certificates/verify")
async def verify_certificate(verification: CertificateVerification):
    certificate = certificates_collection.find_one({"verification_code": verification.verification_code}, {"_id": 0})
    
    if not certificate:
        return {"valid": False, "message": "Certificate not found"}
    
    if not certificate.get("is_valid"):
        return {"valid": False, "message": "Certificate has been revoked"}
    
    # Check expiry
    if certificate.get("expiry_date"):
        expiry = datetime.fromisoformat(certificate["expiry_date"].replace('Z', '+00:00'))
        if datetime.utcnow() > expiry:
            return {"valid": False, "message": "Certificate has expired"}
    
    return {
        "valid": True,
        "certificate": Certificate(**certificate),
        "message": "Certificate is valid"
    }

@app.post("/api/programs/{program_id}/generate-certificate")
async def manual_generate_certificate(program_id: str, user_id: str, current_user: User = Depends(require_role(["admin", "instructor"]))):
    """Manually generate certificate for a user (admin/instructor only)"""
    
    # Find user's enrollment
    enrollment = enrollments_collection.find_one({
        "user_id": user_id,
        "program_id": program_id
    })
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="User is not enrolled in this program")
    
    # Check if user has completed the program
    if not check_program_completion(user_id, program_id):
        raise HTTPException(status_code=400, detail="User has not completed all program requirements")
    
    # Generate certificate
    certificate_id = auto_generate_certificate(user_id, program_id, enrollment["id"])
    
    if not certificate_id:
        raise HTTPException(status_code=500, detail="Failed to generate certificate")
    
    certificate = certificates_collection.find_one({"id": certificate_id}, {"_id": 0})
    return Certificate(**certificate)

@app.delete("/api/certificates/{certificate_id}")
async def revoke_certificate(certificate_id: str, current_user: User = Depends(require_role(["admin"]))):
    """Revoke a certificate (admin only)"""
    result = certificates_collection.update_one(
        {"id": certificate_id},
        {"$set": {"is_valid": False}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    return {"message": "Certificate revoked successfully"}

@app.get("/api/content/{content_id}/stream")
async def stream_content(content_id: str, current_user: User = Depends(get_current_active_user)):
    """Stream content for video/audio playback"""
    content = content_collection.find_one({"id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    file_path = Path(content["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Content file not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(file_path),
        media_type=content["mime_type"],
        filename=content["title"]
    )

@app.post("/api/content/{content_id}/progress")
async def update_content_progress(
    content_id: str, 
    progress_data: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Update user's progress on specific content"""
    content = content_collection.find_one({"id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Update or create progress record
    progress_id = generate_id()
    timestamp = get_current_timestamp()
    
    progress_doc = {
        "id": progress_id,
        "user_id": current_user.id,
        "content_id": content_id,
        "unit_id": content["unit_id"],
        "progress_percentage": progress_data.get("progress_percentage", 0),
        "time_spent": progress_data.get("time_spent", 0),  # in seconds
        "completed": progress_data.get("completed", False),
        "last_position": progress_data.get("last_position", 0),  # for video/audio
        "updated_at": timestamp
    }
    
    # Upsert progress
    progress_collection.update_one(
        {"user_id": current_user.id, "content_id": content_id},
        {"$set": progress_doc},
        upsert=True
    )
    
    return {"message": "Progress updated successfully"}

@app.get("/api/content/{content_id}/progress")
async def get_content_progress(content_id: str, current_user: User = Depends(get_current_active_user)):
    """Get user's progress on specific content"""
    progress = progress_collection.find_one({
        "user_id": current_user.id,
        "content_id": content_id
    }, {"_id": 0})
    
    if not progress:
        return {
            "progress_percentage": 0,
            "time_spent": 0,
            "completed": False,
            "last_position": 0
        }
    
    return progress

@app.get("/api/users/{user_id}/progress")
async def get_user_progress(user_id: str, current_user: User = Depends(get_current_active_user)):
    """Get user's overall progress across all content"""
    # Users can only see their own progress unless they're admin
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this progress")
    
    progress_records = list(progress_collection.find({"user_id": user_id}, {"_id": 0}))
    return progress_records

@app.get("/api/programs/{program_id}/progress")
async def get_program_progress(program_id: str, current_user: User = Depends(get_current_active_user)):
    """Get user's progress in a specific program"""
    # Get all modules and units in the program
    modules = list(modules_collection.find({"program_id": program_id}, {"_id": 0}))
    
    program_progress = {
        "program_id": program_id,
        "modules": []
    }
    
    for module in modules:
        units = list(units_collection.find({"module_id": module["id"]}, {"_id": 0}))
        module_progress = {
            "module_id": module["id"],
            "module_title": module["title"],
            "units": []
        }
        
        for unit in units:
            # Get content for this unit
            content_items = list(content_collection.find({"unit_id": unit["id"]}, {"_id": 0}))
            
            unit_progress = {
                "unit_id": unit["id"],
                "unit_title": unit["title"],
                "content_items": []
            }
            
            for content in content_items:
                # Get user's progress for this content
                progress = progress_collection.find_one({
                    "user_id": current_user.id,
                    "content_id": content["id"]
                }, {"_id": 0})
                
                content_progress = {
                    "content_id": content["id"],
                    "content_title": content["title"],
                    "content_type": content["content_type"],
                    "progress_percentage": progress.get("progress_percentage", 0) if progress else 0,
                    "completed": progress.get("completed", False) if progress else False,
                    "time_spent": progress.get("time_spent", 0) if progress else 0
                }
                
                unit_progress["content_items"].append(content_progress)
            
            module_progress["units"].append(unit_progress)
        
        program_progress["modules"].append(module_progress)
    
    return program_progress

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)