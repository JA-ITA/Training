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

# Authentication Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "learner"  # admin, instructor, learner

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool = True
    created_at: str
    updated_at: str

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
    if user_data.role not in ["admin", "instructor", "learner"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user_id = generate_id()
    timestamp = get_current_timestamp()
    
    user_doc = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "role": user_data.role,
        "password_hash": get_password_hash(user_data.password),
        "is_active": True,
        "created_at": timestamp,
        "updated_at": timestamp
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
async def get_users(current_user: User = Depends(require_role(["admin"]))):
    users = list(users_collection.find({}, {"_id": 0, "password_hash": 0}))
    return [User(**user) for user in users]

# Programs endpoints (updated with authentication)
@app.post("/api/programs", response_model=Program)
async def create_program(program: ProgramCreate, current_user: User = Depends(require_role(["admin", "instructor"]))):
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
async def update_program(program_id: str, program: ProgramCreate, current_user: User = Depends(require_role(["admin", "instructor"]))):
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
async def delete_program(program_id: str, current_user: User = Depends(require_role(["admin"]))):
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
async def create_module(module: ModuleCreate, current_user: User = Depends(require_role(["admin", "instructor"]))):
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
async def update_module(module_id: str, module_data: dict, current_user: User = Depends(require_role(["admin", "instructor"]))):
    timestamp = get_current_timestamp()
    update_doc = {**module_data, "updated_at": timestamp}
    
    result = modules_collection.update_one({"id": module_id}, {"$set": update_doc})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Module not found")
    
    updated_module = modules_collection.find_one({"id": module_id}, {"_id": 0})
    return Module(**updated_module)

@app.delete("/api/modules/{module_id}")
async def delete_module(module_id: str, current_user: User = Depends(require_role(["admin", "instructor"]))):
    # Delete related units
    units_collection.delete_many({"module_id": module_id})
    
    result = modules_collection.delete_one({"id": module_id})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Module not found")
    
    return {"message": "Module deleted successfully"}

# Units endpoints (keep existing functionality)
@app.post("/api/units", response_model=Unit)
async def create_unit(unit: UnitCreate, current_user: User = Depends(require_role(["admin", "instructor"]))):
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
async def update_unit(unit_id: str, unit_data: dict, current_user: User = Depends(require_role(["admin", "instructor"]))):
    timestamp = get_current_timestamp()
    update_doc = {**unit_data, "updated_at": timestamp}
    
    result = units_collection.update_one({"id": unit_id}, {"$set": update_doc})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    updated_unit = units_collection.find_one({"id": unit_id}, {"_id": 0})
    return Unit(**updated_unit)

@app.delete("/api/units/{unit_id}")
async def delete_unit(unit_id: str, current_user: User = Depends(require_role(["admin", "instructor"]))):
    result = units_collection.delete_one({"id": unit_id})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    return {"message": "Unit deleted successfully"}

# Content endpoints (keep existing functionality)
@app.post("/api/units/{unit_id}/content/upload")
async def upload_content(unit_id: str, file: UploadFile = File(...), current_user: User = Depends(require_role(["admin", "instructor"]))):
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
async def delete_content(content_id: str, current_user: User = Depends(require_role(["admin", "instructor"]))):
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
async def create_question(question: QuestionCreate, current_user: User = Depends(require_role(["admin", "instructor"]))):
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
async def get_questions(current_user: User = Depends(require_role(["admin", "instructor"]))):
    questions = list(questions_collection.find({}, {"_id": 0}))
    return [Question(**question) for question in questions]

@app.get("/api/questions/{question_id}", response_model=Question)
async def get_question(question_id: str, current_user: User = Depends(require_role(["admin", "instructor"]))):
    question = questions_collection.find_one({"id": question_id}, {"_id": 0})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return Question(**question)

@app.put("/api/questions/{question_id}", response_model=Question)
async def update_question(question_id: str, question: QuestionCreate, current_user: User = Depends(require_role(["admin", "instructor"]))):
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
async def delete_question(question_id: str, current_user: User = Depends(require_role(["admin", "instructor"]))):
    result = questions_collection.delete_one({"id": question_id})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": "Question deleted successfully"}

# Assessment endpoints
@app.post("/api/assessments", response_model=Assessment)
async def create_assessment(assessment: AssessmentCreate, current_user: User = Depends(require_role(["admin", "instructor"]))):
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
    
    return {
        "attempt_id": attempt_id,
        "percentage": percentage,
        "is_passed": is_passed,
        "total_points": total_points,
        "earned_points": earned_points,
        "results": results
    }

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
async def get_program_enrollments(program_id: str, current_user: User = Depends(require_role(["admin", "instructor"]))):
    enrollments = list(enrollments_collection.find({"program_id": program_id}, {"_id": 0}))
    return [Enrollment(**enrollment) for enrollment in enrollments]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)