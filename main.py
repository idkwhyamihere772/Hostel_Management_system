from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from pymongo import MongoClient
from pydantic import BaseModel
import os
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
import jwt

dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

Secret_key = os.getenv("Secret_key") or os.getenv("secret_key")
Algorithm = "HS256"
Access_token_expire_minutes = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
def create_access_token(data: dict)->str:
    to_encode=data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=Access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, Secret_key, algorithm=Algorithm)

mongo_uri = os.getenv("mongo_uri")
cli = MongoClient(mongo_uri)

db = cli.MAIN
user_collection = db.User
user = user_collection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

class NewUser(BaseModel):
    username: str
    password : str
    role : str

class LoginRequest(BaseModel):
    username: str
    password: str

class UpdateStudent(BaseModel):
    name: str | None = None
    password: str | None = None
    gender: str | None = None
    college: str | None = None
    budget: int | None = None
    preferredSharing: str | None = None

class UpdateHostel(BaseModel):
    name: str | None = None
    ownerName: str | None = None
    type: str | None = None
    location: str | None = None
    rent: dict | None = None
    amenities: list[str] | None = None
    rating: float | None = None
    contactNumber: str | None = None

UpdateUser = UpdateStudent

# Backwards compatibility alias
New_User = NewUser

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return plain_password == hashed_password

admin_username = os.getenv("ADMIN_USERNAME", "admin")
admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

def ensure_admin():
    try:
        existing = user_collection.find_one({"username": admin_username})
        if not existing:
            user_collection.insert_one({
                "username": admin_username,
                "password": hash_password(admin_password),
                "role": "admin",
                "name": "System Administrator"
            })
    except Exception:
        pass

ensure_admin()

@app.get("/", response_class=HTMLResponse)
@app.get("/app", response_class=HTMLResponse)
def serve_ui():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Hostel & PG Management Backend is running</h1>"

@app.get("/api")
def root_api():
    return {"message": "Welcome"}

@app.get("/User")
def get_user():
    users = list(user_collection.find({},{"_id":0}))
    return{"total": len(users),
           "users" : users}

@app.post("/register",status_code=status.HTTP_201_CREATED)
def register_user(user: NewUser):
    if user.role.lower() not in ["student", "hostel owner", "hostel_owner", "admin"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cant register")
    user_dict = {"username" : user.username , 
                 "password" : hash_password(user.password) ,
                 "role" : user.role}
    
    user_collection.insert_one(user_dict)
    return{
        "message" : f"User {user.username} added"
    }

# Alias for compatibility if called as register_student
register_student = register_user

@app.post("/login", status_code=status.HTTP_200_OK, openapi_extra={
    "requestBody": {
        "content": {
            "application/x-www-form-urlencoded": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "password": {"type": "string"}
                    },
                    "required": ["username", "password"]
                }
            },
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "password": {"type": "string"}
                    },
                    "required": ["username", "password"]
                }
            }
        }
    }
})
async def login(request: Request):
    content_type = request.headers.get("content-type", "")
    username = None
    password = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("username")
            password = body.get("password")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON body"
            )
    else:
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
        except Exception:
            pass

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )

    user_record = user_collection.find_one({"username": username})
    if not user_record or not verify_password(password, user_record.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user_record["username"], "role": user_record.get("role", "student")}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user_record["username"],
        "role": user_record.get("role", "student")
    }

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, Secret_key, algorithms=[Algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    current_user = user_collection.find_one({"username": username}, {"_id": 0, "password": 0})
    if current_user is None:
        raise credentials_exception
    return current_user

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role", "").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@app.get("/me")
@app.get("/user/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    return {
        "status": "authenticated",
        "user": current_user
    }

@app.put("/student/{username}")
@app.put("/user/{username}")
def update_student(username: str, student_update: UpdateStudent):
    update_data = student_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No data provided to update")
    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])
        
    result = user_collection.update_one({"username": username}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No student exist with username {username}")
    
    return {
        "message": "Student updated",
        "Updated": update_data
    }

@app.put("/hostel/{username}")
def update_hostel(username: str, hostel_update: UpdateHostel):
    update_data = hostel_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No data provided to update")
        
    result = user_collection.update_one({"username": username}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No hostel exist with username {username}")
    
    return {
        "message": "Hostel updated",
        "Updated": update_data
    }

update_user = update_student

@app.delete("/user/{username}", status_code=status.HTTP_200_OK)
def delete_user(username: str, auth_user: dict = Depends(get_current_user)):
    user_role = auth_user.get("role", "").lower()
    if user_role != "admin" and auth_user.get("username") != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an administrator or the account owner can delete this profile"
        )
    result = user_collection.delete_one({"username": username})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User {username} not found")
    return {"message": f"User {username} deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        app_dir=os.path.dirname(os.path.abspath(__file__)),
    )

