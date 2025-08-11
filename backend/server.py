from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uuid
import shutil
from pathlib import Path
import mimetypes

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

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'training_db')

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
programs_collection = db.programs
modules_collection = db.modules
units_collection = db.units
content_collection = db.content

# Create uploads directory
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Pydantic Models
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

# Utility functions
def generate_id():
    return str(uuid.uuid4())

def get_current_timestamp():
    from datetime import datetime
    return datetime.utcnow().isoformat()

# API Routes

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Training Management API is running"}

# Programs endpoints
@app.post("/api/programs", response_model=Program)
async def create_program(program: ProgramCreate):
    program_id = generate_id()
    timestamp = get_current_timestamp()
    
    program_doc = {
        "id": program_id,
        "title": program.title,
        "description": program.description,
        "learning_objectives": program.learning_objectives,
        "expiry_duration": program.expiry_duration,
        "renewal_requirements": program.renewal_requirements,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    programs_collection.insert_one(program_doc)
    return Program(**program_doc)

@app.get("/api/programs", response_model=List[Program])
async def get_programs():
    programs = list(programs_collection.find({}, {"_id": 0}))
    return [Program(**program) for program in programs]

@app.get("/api/programs/{program_id}", response_model=Program)
async def get_program(program_id: str):
    program = programs_collection.find_one({"id": program_id}, {"_id": 0})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return Program(**program)

@app.put("/api/programs/{program_id}", response_model=Program)
async def update_program(program_id: str, program: ProgramCreate):
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
async def delete_program(program_id: str):
    # Delete related modules and units
    modules = list(modules_collection.find({"program_id": program_id}))
    for module in modules:
        units_collection.delete_many({"module_id": module["id"]})
    modules_collection.delete_many({"program_id": program_id})
    
    result = programs_collection.delete_one({"id": program_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Program not found")
    
    return {"message": "Program deleted successfully"}

# Modules endpoints
@app.post("/api/modules", response_model=Module)
async def create_module(module: ModuleCreate):
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
async def get_program_modules(program_id: str):
    modules = list(modules_collection.find({"program_id": program_id}, {"_id": 0}).sort("order", 1))
    return [Module(**module) for module in modules]

@app.put("/api/modules/{module_id}", response_model=Module)
async def update_module(module_id: str, module_data: dict):
    timestamp = get_current_timestamp()
    update_doc = {**module_data, "updated_at": timestamp}
    
    result = modules_collection.update_one({"id": module_id}, {"$set": update_doc})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Module not found")
    
    updated_module = modules_collection.find_one({"id": module_id}, {"_id": 0})
    return Module(**updated_module)

@app.delete("/api/modules/{module_id}")
async def delete_module(module_id: str):
    # Delete related units
    units_collection.delete_many({"module_id": module_id})
    
    result = modules_collection.delete_one({"id": module_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Module not found")
    
    return {"message": "Module deleted successfully"}

# Units endpoints
@app.post("/api/units", response_model=Unit)
async def create_unit(unit: UnitCreate):
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
async def get_module_units(module_id: str):
    units = list(units_collection.find({"module_id": module_id}, {"_id": 0}).sort("order", 1))
    return [Unit(**unit) for unit in units]

@app.put("/api/units/{unit_id}", response_model=Unit)
async def update_unit(unit_id: str, unit_data: dict):
    timestamp = get_current_timestamp()
    update_doc = {**unit_data, "updated_at": timestamp}
    
    result = units_collection.update_one({"id": unit_id}, {"$set": update_doc})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    updated_unit = units_collection.find_one({"id": unit_id}, {"_id": 0})
    return Unit(**updated_unit)

@app.delete("/api/units/{unit_id}")
async def delete_unit(unit_id: str):
    result = units_collection.delete_one({"id": unit_id})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    return {"message": "Unit deleted successfully"}

# Content endpoints
@app.post("/api/units/{unit_id}/content/upload")
async def upload_content(unit_id: str, file: UploadFile = File(...)):
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
async def get_unit_content(unit_id: str):
    content_items = list(content_collection.find({"unit_id": unit_id}, {"_id": 0}))
    return [ContentItem(**item) for item in content_items]

@app.delete("/api/content/{content_id}")
async def delete_content(content_id: str):
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
async def get_program_structure(program_id: str):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)