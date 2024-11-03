from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select
from models import User
from db.dbConfig import SessionDep
from passlib.context import CryptContext
from utils.validation import is_valid_email


# Creates an API router for handling authentication-related endpoints.
auth_router = APIRouter()

# Defines the base directory path for the current file.(app/*)
BASE_DIR = Path(__file__).resolve().parent.parent

# Sets up Jinja2 template rendering using the 'templates' directory.
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Configures the password hashing context using the bcrypt algorithm.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hashes a given password using the configured password hashing context.
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Login route
@auth_router.get("/login")
def login(email: str, password: str, session: SessionDep):
    user = session.exec(select(User).where(User.email == email)).first()
    
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify password
    if not pwd_context.verify(password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
 
    return JSONResponse(content={
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username
        }
    })

# Register Route
@auth_router.post("/register")
def create_user(username: str, password: str, email: str, session: SessionDep):
   
    # Check if user already exists
    user_exists = session.exec(select(User).where(User.email == email)).first()
    
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    if user_exists:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create new user
    hashed_password = hash_password(password)
    new_user = User(username=username, password=hashed_password, email=email)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return JSONResponse(content={
        "message": "User created successfully",
        "user": {
            "id": new_user.id,
            "username": new_user.username
        }
    })
    