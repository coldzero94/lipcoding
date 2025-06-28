from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form, Request, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, ValidationError
from typing import Optional, List, Literal
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Text, LargeBinary, ForeignKey, Enum
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
import base64
import os

# --- 환경설정 ---
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

SQLALCHEMY_DATABASE_URL = "sqlite:///./mentor_mentee.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 모델 정의 ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # mentor or mentee
    bio = Column(Text, default="")
    image = Column(LargeBinary, nullable=True)
    image_type = Column(String, nullable=True)  # 'jpg' or 'png'
    skills = Column(Text, default="")  # comma-separated for mentor

class MatchRequest(Base):
    __tablename__ = "match_requests"
    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("users.id"))
    mentee_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    status = Column(String, default="pending")  # pending, accepted, rejected, cancelled
    mentor = relationship("User", foreign_keys=[mentor_id])
    mentee = relationship("User", foreign_keys=[mentee_id])

Base.metadata.create_all(bind=engine)

# --- 보안/유틸 ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

app = FastAPI(title="Mentor-Mentee API", docs_url="/swagger-ui", openapi_url="/openapi.json")

@app.get("/openapi.json", include_in_schema=False)
def custom_openapi():
    return app.openapi()

@app.get("/swagger-ui", include_in_schema=False)
def custom_swagger():
    return RedirectResponse(url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/swagger-ui")

# --- Pydantic 모델 ---
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: Literal["mentor", "mentee"]

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    token: str

# --- 유틸 함수 ---
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": now,
        "nbf": now,
        "iss": "mentor-mentee-app",
        "aud": "mentor-mentee-client",
        "jti": os.urandom(8).hex(),
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 회원가입 ---
@app.post("/api/signup", status_code=201)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")
    user = User(
        email=req.email,
        hashed_password=get_password_hash(req.password),
        name=req.name,
        role=req.role,
        bio="",
        skills="" if req.role == "mentee" else "",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role, "name": user.name}

# --- 로그인 ---
from fastapi import Form
@app.post("/api/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(None),
    password: str = Form(None),
):
    # 1. Form 방식 우선 처리
    if username and password:
        user = db.query(User).filter(User.email == username).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
        token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.name,
        })
        return {"token": token}
    # 2. JSON 방식도 허용
    try:
        data = await request.json()
        username = data.get("username") or data.get("email")
        password = data.get("password")
    except Exception:
        username = None
        password = None
    if not username or not password:
        raise HTTPException(status_code=401, detail="username, password 필수")
    user = db.query(User).filter(User.email == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "name": user.name,
    })
    return {"token": token}

# --- 인증 유틸리티 ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience="mentor-mentee-client")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

# --- 내 정보 조회 ---
@app.get("/api/me")
def get_me(current_user: User = Depends(get_current_user)):
    profile = {
        "name": current_user.name,
        "bio": current_user.bio,
        "imageUrl": f"/api/images/{current_user.role}/{current_user.id}",
    }
    if current_user.role == "mentor":
        profile["skills"] = current_user.skills.split(",") if current_user.skills else []
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "profile": profile,
    }

# --- 프로필 수정 ---
class ProfileUpdateRequest(BaseModel):
    id: int
    name: str
    role: Literal["mentor", "mentee"]
    bio: str
    image: Optional[str] = None  # base64 인코딩
    skills: Optional[List[str]] = None  # mentor만

@app.put("/api/profile")
def update_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.id != current_user.id or req.role != current_user.role:
        raise HTTPException(status_code=400, detail="잘못된 요청입니다.")
    current_user.name = req.name
    current_user.bio = req.bio
    if req.image:
        try:
            img_data = base64.b64decode(req.image)
            if len(img_data) > 1024*1024:
                raise HTTPException(status_code=400, detail="이미지 크기는 1MB 이하만 허용됩니다.")
            # jpg/png 판별
            if img_data[:3] == b'\xff\xd8\xff':
                current_user.image_type = 'jpg'
            elif img_data[:8] == b'\x89PNG\r\n\x1a\n':
                current_user.image_type = 'png'
            else:
                raise HTTPException(status_code=400, detail="jpg/png만 허용됩니다.")
            current_user.image = img_data
        except Exception:
            raise HTTPException(status_code=400, detail="이미지 디코딩 실패")
    if current_user.role == "mentor":
        current_user.skills = ",".join(req.skills or [])
    db.commit()
    db.refresh(current_user)
    # 명세에 맞는 전체 유저 정보 반환
    profile = {
        "name": current_user.name,
        "bio": current_user.bio,
        "imageUrl": f"/api/images/{current_user.role}/{current_user.id}",
    }
    if current_user.role == "mentor":
        profile["skills"] = current_user.skills.split(",") if current_user.skills else []
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "profile": profile,
    }

# --- 프로필 이미지 제공 ---
@app.get("/api/images/{role}/{user_id}")
def get_profile_image(role: str, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.role == role).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")
    if user.image:
        ext = user.image_type or "jpg"
        return FileResponse(
            path=None,
            content_type=f"image/{ext}",
            filename=f"profile.{ext}",
            headers={"Content-Disposition": f"inline; filename=profile.{ext}"},
            media_type=f"image/{ext}",
            background=None,
            body=user.image,
        )
    # 기본 이미지
    if role == "mentor":
        return RedirectResponse("https://placehold.co/500x500.jpg?text=MENTOR")
    else:
        return RedirectResponse("https://placehold.co/500x500.jpg?text=MENTEE")

# --- 멘토 리스트 조회 (멘티 전용) ---
from fastapi import Query
@app.get("/api/mentors")
def get_mentors(
    skill: Optional[str] = Query(None),
    order_by: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "mentee":
        raise HTTPException(status_code=403, detail="멘티만 접근 가능합니다.")
    q = db.query(User).filter(User.role == "mentor")
    if skill:
        q = q.filter(User.skills.like(f"%{skill}%"))
    mentors = q.all()
    def mentor_profile(u):
        return {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "profile": {
                "name": u.name,
                "bio": u.bio,
                "imageUrl": f"/api/images/mentor/{u.id}",
                "skills": u.skills.split(",") if u.skills else [],
            },
        }
    result = [mentor_profile(u) for u in mentors]
    if order_by == "name":
        result.sort(key=lambda x: x["profile"]["name"])
    elif order_by == "skill":
        result.sort(key=lambda x: (x["profile"]["skills"][0] if x["profile"]["skills"] else ""))
    else:
        result.sort(key=lambda x: x["id"])
    return result

# --- 매칭 요청 생성 (멘티 전용) ---
class MatchRequestCreate(BaseModel):
    mentorId: int
    menteeId: int
    message: str

@app.post("/api/match-requests")
def create_match_request(
    req: MatchRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "mentee" or current_user.id != req.menteeId:
        raise HTTPException(status_code=403, detail="멘티만 요청 가능")
    mentor = db.query(User).filter(User.id == req.mentorId, User.role == "mentor").first()
    if not mentor:
        raise HTTPException(status_code=400, detail="멘토가 존재하지 않음")
    # 중복 요청 방지
    exists = db.query(MatchRequest).filter(
        MatchRequest.mentor_id == req.mentorId,
        MatchRequest.mentee_id == req.menteeId,
        MatchRequest.status == "pending"
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="이미 요청이 존재합니다.")
    match = MatchRequest(
        mentor_id=req.mentorId,
        mentee_id=req.menteeId,
        message=req.message,
        status="pending",
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return {
        "id": match.id,
        "mentorId": match.mentor_id,
        "menteeId": match.mentee_id,
        "message": match.message,
        "status": match.status,
    }

# --- 나에게 들어온 요청 목록 (멘토 전용) ---
@app.get("/api/match-requests/incoming")
def get_incoming_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "mentor":
        raise HTTPException(status_code=403, detail="멘토만 접근 가능")
    reqs = db.query(MatchRequest).filter(MatchRequest.mentor_id == current_user.id).all()
    return [
        {
            "id": r.id,
            "mentorId": r.mentor_id,
            "menteeId": r.mentee_id,
            "message": r.message,
            "status": r.status,
        } for r in reqs
    ]

# --- 내가 보낸 요청 목록 (멘티 전용) ---
@app.get("/api/match-requests/outgoing")
def get_outgoing_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "mentee":
        raise HTTPException(status_code=403, detail="멘티만 접근 가능")
    reqs = db.query(MatchRequest).filter(MatchRequest.mentee_id == current_user.id).all()
    return [
        {
            "id": r.id,
            "mentorId": r.mentor_id,
            "menteeId": r.mentee_id,
            "status": r.status,
        } for r in reqs
    ]

# --- 요청 수락 (멘토 전용) ---
@app.put("/api/match-requests/{req_id}/accept")
def accept_request(req_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "mentor":
        raise HTTPException(status_code=403, detail="멘토만 가능")
    req = db.query(MatchRequest).filter(MatchRequest.id == req_id, MatchRequest.mentor_id == current_user.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="요청 없음")
    # 한 명만 수락, 나머지 자동 거절
    others = db.query(MatchRequest).filter(
        MatchRequest.mentor_id == current_user.id,
        MatchRequest.status == "pending",
        MatchRequest.id != req_id
    ).all()
    for o in others:
        o.status = "rejected"
    req.status = "accepted"
    db.commit()
    db.refresh(req)
    return {
        "id": req.id,
        "mentorId": req.mentor_id,
        "menteeId": req.mentee_id,
        "message": req.message,
        "status": req.status,
    }

# --- 요청 거절 (멘토 전용) ---
@app.put("/api/match-requests/{req_id}/reject")
def reject_request(req_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "mentor":
        raise HTTPException(status_code=403, detail="멘토만 가능")
    req = db.query(MatchRequest).filter(MatchRequest.id == req_id, MatchRequest.mentor_id == current_user.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="요청 없음")
    req.status = "rejected"
    db.commit()
    db.refresh(req)
    return {
        "id": req.id,
        "mentorId": req.mentor_id,
        "menteeId": req.mentee_id,
        "message": req.message,
        "status": req.status,
    }

# --- 요청 삭제/취소 (멘티 전용) ---
@app.delete("/api/match-requests/{req_id}")
def cancel_request(req_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "mentee":
        raise HTTPException(status_code=403, detail="멘티만 가능")
    req = db.query(MatchRequest).filter(MatchRequest.id == req_id, MatchRequest.mentee_id == current_user.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="요청 없음")
    req.status = "cancelled"
    db.commit()
    db.refresh(req)
    return {
        "id": req.id,
        "mentorId": req.mentor_id,
        "menteeId": req.mentee_id,
        "message": req.message,
        "status": req.status,
    }

from fastapi.exception_handlers import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from pydantic import ValidationError as PydanticValidationError
from starlette.requests import Request as StarletteRequest

@app.exception_handler(FastAPIRequestValidationError)
async def validation_exception_handler(request: StarletteRequest, exc: FastAPIRequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )

@app.exception_handler(PydanticValidationError)
async def pydantic_validation_exception_handler(request: StarletteRequest, exc: PydanticValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )