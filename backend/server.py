from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, BackgroundTasks, File, UploadFile
from fastapi.responses import PlainTextResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from functools import wraps
import hmac
import hashlib
import base64
import shutil
import mimetypes

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DAYS = 7

# Uploads directory
UPLOADS_DIR = ROOT_DIR / 'uploads' / 'photos'
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password: Optional[str] = None
    google_id: Optional[str] = None
    name: str
    phone: Optional[str] = None
    role: str = "user"  # user, owner, admin
    is_owner: bool = False  # Flag for owner profile completion
    altin_tac: int = 0
    suspended: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FieldModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    name: str
    city: str
    address: str
    location: Dict[str, float]  # {"lat": 41.0, "lng": 29.0}
    price: float  # base_price_per_hour
    base_price_per_hour: float
    subscription_price_4_match: Optional[float] = None
    photos: List[str] = []  # List of photo URLs
    cover_photo_url: Optional[str] = None  # Cover photo (first photo if not set)
    phone: str
    tax_number: Optional[str] = None  # tax_id
    iban: Optional[str] = None
    approved: bool = False
    tax_verified: bool = False
    subscription_prices_pending_review: bool = True
    rating: float = 0.0
    review_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    field_id: str
    start_datetime: str  # ISO format datetime
    end_datetime: str  # ISO format datetime
    date: str  # YYYY-MM-DD (for backward compatibility)
    time: str  # HH:MM (for backward compatibility)
    duration: int = 90  # minutes
    status: str = "paid"  # paid, confirmed, cancelled, completed
    total_amount_user_paid: float
    owner_share_amount: float
    platform_fee_amount: float = 50.0
    amount: float  # Total amount (for backward compatibility)
    is_subscription: bool = False
    matches_remaining: int = 1
    merchant_oid: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: str
    amount: float
    commission: float = 50.0  # Fixed 50 TL
    status: str = "pending"  # pending, success, failed
    paytr_data: Optional[Dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Review(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    field_id: str
    rating: int  # 1-5
    comment: str
    approved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeamSearch(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    field_id: Optional[str] = None
    location_city: Optional[str] = None
    location_district: Optional[str] = None
    location_text: Optional[str] = None
    date: str
    time: str
    position: str  # kaleci, defans, orta saha, forvet, farketmez
    missing_players_count: int = 1
    intensity_level: str = "orta"  # hafif, orta, rekabetçi
    message: str
    participants: List[str] = []  # user IDs who joined
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # booking, payment, review, team
    message: str
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    admin_email: str
    action: str  # approve_field, reject_field, suspend_user, etc.
    target_type: str  # field, user, booking, etc.
    target_id: str
    details: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SupportTicket(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    requester_user_id: str
    requester_email: str
    requester_name: str
    role: str  # user, owner, admin
    subject: str
    message: str  # Initial message
    status: str = "open"  # open, in_progress, resolved, closed
    priority: str = "medium"  # low, medium, high
    assignee_user_id: Optional[str] = None
    admin_response: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SupportMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    sender_user_id: str
    sender_name: str
    sender_role: str
    body: str
    attachments: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OwnerProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Unique reference to user
    tax_number: str
    iban: str
    phone: str
    address: Optional[str] = None
    business_name: Optional[str] = None
    status: str = "active"  # pending, active, verified, suspended
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== REQUEST/RESPONSE MODELS ====================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    role: str = "user"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    session_id: str

class FieldCreate(BaseModel):
    name: str
    city: str
    address: str
    location: Dict[str, float]
    base_price_per_hour: float
    subscription_price_4_match: Optional[float] = None
    photos: List[str] = []
    phone: str
    tax_number: str  # tax_id - required
    iban: str  # required

class BookingCreate(BaseModel):
    field_id: str
    start_datetime: str
    end_datetime: str
    date: Optional[str] = None  # For backward compatibility
    time: Optional[str] = None  # For backward compatibility
    is_subscription: bool = False

class ReviewCreate(BaseModel):
    field_id: str
    rating: int
    comment: str

class TeamSearchCreate(BaseModel):
    field_id: Optional[str] = None
    location_city: Optional[str] = None
    location_district: Optional[str] = None
    location_text: Optional[str] = None
    date: str
    time: str
    position: str
    missing_players_count: int = 1
    intensity_level: str = "orta"
    message: str

class OwnerProfileCreate(BaseModel):
    tax_number: str
    iban: str
    phone: str
    address: Optional[str] = None
    business_name: Optional[str] = None

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> Dict:
    """Get authenticated user - NO ADMIN FALLBACK"""
    # Check cookie first
    session_token = request.cookies.get('session_token')
    
    # Fallback to Authorization header
    if not session_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            session_token = auth_header.split(' ')[1]
    
    # NO TOKEN = NO ACCESS (no admin fallback)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(session_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload['user_id']}, {"_id": 0})
        
        # User must exist in database
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Check if user is suspended
        if user.get('suspended', False):
            raise HTTPException(status_code=403, detail="Account suspended")
        
        # SECURITY: Log authentication details
        logger.debug(f"Authenticated user: {user['id']} ({user['email']}) - role: {user['role']}")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(request: Request) -> Dict:
    """Admin-only authentication"""
    user = await get_current_user(request)
    if user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def create_audit_log(admin_id: str, admin_email: str, action: str, target_type: str, target_id: str, details: Dict = None):
    """Create audit log entry"""
    log = AuditLog(
        admin_id=admin_id,
        admin_email=admin_email,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {}
    )
    log_dict = log.model_dump()
    log_dict['created_at'] = log_dict['created_at'].isoformat()
    await db.audit_logs.insert_one(log_dict)
    logger.info(f"Audit log: {action} by {admin_email} on {target_type}:{target_id}")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(req: RegisterRequest):
    # Prevent admin registration through public endpoint
    if req.role == "admin":
        raise HTTPException(status_code=403, detail="Admin hesapları sadece sistem yöneticileri tarafından oluşturulabilir")
    
    # Check if user exists
    existing = await db.users.find_one({"email": req.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=req.email,
        password=hash_password(req.password),
        name=req.name,
        phone=req.phone,
        role=req.role
    )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    token = create_jwt_token(user.id, user.email, user.role)
    
    return {
        "status": "success",
        "session_token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    }

@api_router.post("/auth/login")
async def login(req: LoginRequest, response: Response):
    user = await db.users.find_one({"email": req.email}, {"_id": 0})
    if not user or not user.get('password'):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(req.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user['id'], user['email'], user['role'])
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=JWT_EXPIRATION_DAYS * 24 * 60 * 60,
        path="/"
    )
    
    return {
        "status": "success",
        "session_token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "role": user['role']
        }
    }

@api_router.post("/auth/google")
async def google_auth(req: GoogleAuthRequest, response: Response):
    """Process Emergent Google OAuth session"""
    import requests
    
    try:
        # Get session data from Emergent
        session_response = requests.get(
            'https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data',
            headers={'X-Session-ID': req.session_id},
            timeout=10
        )
        
        if session_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        session_data = session_response.json()
        
        # Check if user exists
        user = await db.users.find_one({"email": session_data['email']}, {"_id": 0})
        
        if not user:
            # Create new user
            new_user = User(
                email=session_data['email'],
                google_id=session_data['id'],
                name=session_data['name'],
                role="user"
            )
            user_dict = new_user.model_dump()
            user_dict['created_at'] = user_dict['created_at'].isoformat()
            await db.users.insert_one(user_dict)
            user = user_dict
        
        token = create_jwt_token(user['id'], user['email'], user['role'])
        
        # Set cookie
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=JWT_EXPIRATION_DAYS * 24 * 60 * 60,
            path="/"
        )
        
        return {
            "status": "success",
            "session_token": token,
            "user": {
                "id": user['id'],
                "email": user['email'],
                "name": user['name'],
                "role": user['role']
            }
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@api_router.get("/auth/session")
async def get_session(user: Dict = Depends(get_current_user)):
    return {
        "id": user['id'],
        "email": user['email'],
        "name": user['name'],
        "role": user['role']
    }

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("session_token", path="/")
    return {"status": "success"}

# ==================== FIELDS ROUTES ====================

@api_router.get("/fields")
async def get_fields(city: Optional[str] = None, date: Optional[str] = None, time: Optional[str] = None):
    query = {}
    if city:
        query['city'] = city
    
    fields = await db.fields.find(query, {"_id": 0}).to_list(1000)
    
    # TODO: Filter by availability based on date and time
    return {"fields": fields}

@api_router.get("/fields/{field_id}")
async def get_field(field_id: str):
    field = await db.fields.find_one({"id": field_id}, {"_id": 0})
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field

@api_router.post("/fields")
async def create_field(field: FieldCreate, user: Dict = Depends(get_current_user)):
    # Check if user has owner role
    if user['role'] != 'owner':
        raise HTTPException(
            status_code=403, 
            detail="Saha eklemek için Owner hesabınız olmalı. Lütfen Owner olarak kaydolun."
        )
    
    # Check if owner profile exists and is active
    owner_profile = await db.owner_profiles.find_one({"user_id": user['id']}, {"_id": 0})
    
    if not owner_profile:
        raise HTTPException(
            status_code=403,
            detail="Saha eklemek için önce Owner Profilinizi tamamlamanız gerekiyor. Lütfen profil bilgilerinizi girin (Vergi No, IBAN, Telefon)."
        )
    
    if owner_profile.get('status') not in ['active', 'verified']:
        raise HTTPException(
            status_code=403,
            detail=f"Owner hesabınız henüz aktif değil. Durum: {owner_profile.get('status', 'unknown')}. Lütfen destek ile iletişime geçin."
        )
    
    # Validate required fields
    if not field.tax_number or not field.iban:
        raise HTTPException(status_code=400, detail="Vergi numarası ve IBAN zorunludur")
    
    # Validate tax_number format (basic check)
    if len(field.tax_number.strip()) < 10:
        raise HTTPException(status_code=400, detail="Geçersiz vergi numarası formatı")
    
    # Validate IBAN format (basic check)
    if not field.iban.strip().startswith('TR') or len(field.iban.strip()) < 20:
        raise HTTPException(status_code=400, detail="Geçersiz IBAN formatı (TR ile başlamalı)")
    
    # SECURITY: Force owner_id to be the authenticated user
    new_field = FieldModel(
        owner_id=user['id'],  # ENFORCED - always use authenticated user
        name=field.name,
        city=field.city,
        address=field.address,
        location=field.location,
        price=field.base_price_per_hour,  # For backward compatibility
        base_price_per_hour=field.base_price_per_hour,
        subscription_price_4_match=field.subscription_price_4_match,
        photos=field.photos,
        phone=field.phone,
        tax_number=field.tax_number,
        iban=field.iban,
        approved=False,
        tax_verified=False,
        subscription_prices_pending_review=True
    )
    
    field_dict = new_field.model_dump()
    field_dict['created_at'] = field_dict['created_at'].isoformat()
    
    result = await db.fields.insert_one(field_dict)
    
    logger.info(f"Field created: {field_dict['id']} by owner {user['id']} ({user['email']})")
    
    # Return the field data without MongoDB _id
    return {"status": "success", "field": {
        "id": field_dict['id'],
        "name": field_dict['name'],
        "city": field_dict['city'],
        "price": field_dict['price'],
        "approved": field_dict['approved'],
        "message": "Saha eklendi. Admin onayı bekleniyor."
    }}

@api_router.get("/fields/{field_id}/availability")
async def get_availability(field_id: str, date: str):
    # Get all bookings for this field on this date
    bookings = await db.bookings.find({
        "field_id": field_id,
        "date": date,
        "status": {"$in": ["confirmed", "pending"]}
    }, {"_id": 0}).to_list(100)
    
    booked_times = [b['time'] for b in bookings]
    
    # Generate all possible time slots (09:00 - 23:00)
    all_slots = [f"{h:02d}:00" for h in range(9, 24)]
    available_slots = [slot for slot in all_slots if slot not in booked_times]
    
    return {
        "date": date,
        "available_slots": available_slots,
        "booked_slots": booked_times
    }

@api_router.get("/fields/{field_id}/calendar")
async def get_field_calendar(field_id: str):
    """Get weekly calendar view for a field with 24-hour slots"""
    from datetime import date, timedelta
    
    field = await db.fields.find_one({"id": field_id}, {"_id": 0})
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    
    # Get pricing
    base_price = field.get('base_price_per_hour') or field.get('price', 0)
    
    # Get next 7 days
    today = date.today()
    days_data = []
    
    for day_offset in range(7):
        current_date = today + timedelta(days=day_offset)
        date_str = current_date.isoformat()
        
        # Get bookings for this date
        bookings = await db.bookings.find({
            "field_id": field_id,
            "date": date_str,
            "status": {"$in": ["confirmed", "pending", "paid"]}
        }, {"_id": 0}).to_list(100)
        
        # Create 24-hour slots (00:00 - 23:00)
        slots = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        for hour in range(24):
            start_time = f"{hour:02d}:00"
            end_hour = (hour + 1) % 24
            end_time = f"{end_hour:02d}:00"
            
            # Format label
            label = f"{start_time} - {end_time}"
            
            # Check if this slot is booked
            is_booked = any(b['time'] == start_time for b in bookings)
            
            # Check if it's in the past
            slot_datetime = datetime.fromisoformat(f"{date_str}T{start_time}:00")
            is_past = slot_datetime < now
            
            # Determine status
            if is_past:
                status = "past"
                status_label = "GEÇMİŞ"
                bookable = False
            elif is_booked:
                # Check if it's subscription
                booking = next((b for b in bookings if b['time'] == start_time), None)
                if booking and booking.get('is_subscription'):
                    status = "subscription_locked"
                    status_label = "ABONELİKLİ"
                else:
                    status = "reserved"
                    status_label = "DOLU"
                bookable = False
            else:
                status = "available"
                status_label = "BOŞ"
                bookable = True
            
            slots.append({
                "start": start_time,
                "end": end_time,
                "label": label,
                "status": status,
                "status_label": status_label,
                "bookable": bookable,
                "price": base_price
            })
        
        days_data.append({
            "date": date_str,
            "day_name": current_date.strftime("%A"),
            "day_number": current_date.day,
            "slots": slots
        })
    
    return {
        "field_id": field_id,
        "field_name": field['name'],
        "base_price": base_price,
        "days": days_data
    }

# ==================== BOOKINGS ROUTES ====================

@api_router.post("/bookings")
async def create_booking(booking: BookingCreate, user: Dict = Depends(get_current_user)):
    # SECURITY: Prevent admin from making bookings
    if user['role'] == 'admin':
        raise HTTPException(status_code=403, detail="Admin hesabı ile rezervasyon yapılamaz")
    
    # SECURITY: Check if user is suspended
    if user.get('suspended', False):
        raise HTTPException(status_code=403, detail="Hesabınız askıya alınmış")
    
    # Get field
    field = await db.fields.find_one({"id": booking.field_id}, {"_id": 0})
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    
    # Validate datetime fields
    if not booking.start_datetime or not booking.end_datetime:
        raise HTTPException(status_code=400, detail="Lütfen saat seçin")
    
    # Check if field has pricing
    base_price = field.get('base_price_per_hour') or field.get('price')
    if not base_price:
        raise HTTPException(status_code=400, detail="Bu saha için fiyat tanımlı değil")
    
    # Extract date and time for backward compatibility
    try:
        start_dt = datetime.fromisoformat(booking.start_datetime.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(booking.end_datetime.replace('Z', '+00:00'))
        date_str = start_dt.strftime("%Y-%m-%d")
        time_str = start_dt.strftime("%H:%M")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Geçersiz tarih formatı")
    
    # Check availability
    existing = await db.bookings.find_one({
        "field_id": booking.field_id,
        "date": date_str,
        "time": time_str,
        "status": {"$in": ["paid", "confirmed", "pending"]}
    }, {"_id": 0})
    
    if existing:
        raise HTTPException(status_code=400, detail="Bu saat dolu")
    
    # Calculate amounts - NO LOYALTY DISCOUNT
    platform_fee = 50.0
    
    if booking.is_subscription:
        # 4 matches subscription - simple calculation
        base_amount = base_price * 4
        total_amount_user_paid = base_amount + (platform_fee * 4)
        owner_share_amount = base_amount
        matches_remaining = 4
    else:
        # Single match - simple calculation
        total_amount_user_paid = base_price + platform_fee
        owner_share_amount = base_price
        matches_remaining = 1
    
    # SECURITY: Force user_id to be the authenticated user (no client override)
    # Create booking with ENFORCED user_id
    new_booking = Booking(
        user_id=user['id'],  # ENFORCED - always use authenticated user
        field_id=booking.field_id,
        start_datetime=booking.start_datetime,
        end_datetime=booking.end_datetime,
        date=date_str,
        time=time_str,
        status="paid",
        total_amount_user_paid=total_amount_user_paid,
        owner_share_amount=owner_share_amount,
        platform_fee_amount=platform_fee,
        amount=total_amount_user_paid,  # For backward compatibility
        is_subscription=booking.is_subscription,
        matches_remaining=matches_remaining
    )
    
    booking_dict = new_booking.model_dump()
    booking_dict['created_at'] = booking_dict['created_at'].isoformat()
    
    await db.bookings.insert_one(booking_dict)
    
    # Create audit log for booking
    await create_audit_log(
        admin_id=user['id'],
        admin_email=user['email'],
        action="create_booking",
        target_type="booking",
        target_id=booking_dict['id'],
        details={
            "field_id": booking.field_id,
            "date": date_str,
            "time": time_str,
            "amount": total_amount_user_paid,
            "user_role": user['role']
        }
    )
    
    logger.info(f"Booking created: {booking_dict['id']} by user {user['id']} ({user['email']}) - role: {user['role']}")
    
    # Return clean booking data without _id
    return {"status": "success", "booking": {
        "id": booking_dict['id'],
        "field_id": booking_dict['field_id'],
        "start_datetime": booking_dict['start_datetime'],
        "end_datetime": booking_dict['end_datetime'],
        "status": booking_dict['status'],
        "total_amount_user_paid": booking_dict['total_amount_user_paid'],
        "owner_share_amount": booking_dict['owner_share_amount'],
        "platform_fee_amount": booking_dict['platform_fee_amount'],
        "user_id": booking_dict['user_id'],  # Include for verification
        "user_email": user['email']  # Include for verification
    }}

@api_router.get("/bookings")
async def get_bookings(user: Dict = Depends(get_current_user)):
    if user['role'] == 'owner':
        # Get owner's fields
        fields = await db.fields.find({"owner_id": user['id']}, {"_id": 0}).to_list(100)
        field_ids = [f['id'] for f in fields]
        bookings = await db.bookings.find({"field_id": {"$in": field_ids}}, {"_id": 0}).to_list(1000)
    else:
        bookings = await db.bookings.find({"user_id": user['id']}, {"_id": 0}).to_list(1000)
    
    return {"bookings": bookings}

@api_router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: str, user: Dict = Depends(get_current_user)):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking['user_id'] != user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check 72-hour rule
    booking_datetime = datetime.fromisoformat(f"{booking['date']}T{booking['time']}:00")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    hours_until = (booking_datetime - now).total_seconds() / 3600
    
    if hours_until < 72:
        raise HTTPException(status_code=400, detail="Cannot cancel within 72 hours of booking")
    
    # Update booking status
    await db.bookings.update_one({"id": booking_id}, {"$set": {"status": "cancelled"}})
    
    # Simulated refund (in production, integrate with PayTR refund API)
    logger.info(f"SIMULATED REFUND: Booking {booking_id}, Amount {booking['amount']} TL")
    
    return {"status": "success", "message": "Booking cancelled and refund processed"}

# ==================== PAYMENTS ROUTES (SIMULATED) ====================

@api_router.post("/payments/initiate/{booking_id}")
async def initiate_payment(booking_id: str, user: Dict = Depends(get_current_user)):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking['user_id'] != user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Generate merchant order ID
    merchant_oid = f"{booking_id}_{uuid.uuid4().hex[:8]}"
    
    await db.bookings.update_one({"id": booking_id}, {"$set": {"merchant_oid": merchant_oid}})
    
    # SIMULATED: In production, call PayTR API to get iframe token
    logger.info(f"SIMULATED PAYMENT: Booking {booking_id}, Amount {booking['amount']} TL")
    
    return {
        "status": "success",
        "merchant_oid": merchant_oid,
        "payment_url": f"/api/payments/simulate/{merchant_oid}",
        "simulated": True
    }

@api_router.get("/payments/simulate/{merchant_oid}")
async def simulate_payment(merchant_oid: str):
    """Simulated payment page for testing"""
    booking = await db.bookings.find_one({"merchant_oid": merchant_oid}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simulated Payment</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
            .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; }}
            button {{ padding: 12px 24px; margin: 10px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }}
            .success {{ background: #2E7D32; color: white; }}
            .fail {{ background: #d32f2f; color: white; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Simulated Payment Page</h2>
            <p><strong>Merchant Order ID:</strong> {merchant_oid}</p>
            <p><strong>Amount:</strong> {booking['amount']} TL</p>
            <p>This is a simulated payment. Choose an option:</p>
            <button class="success" onclick="completePayment(true)">Simulate Success</button>
            <button class="fail" onclick="completePayment(false)">Simulate Failure</button>
        </div>
        <script>
            async function completePayment(success) {{
                const response = await fetch('/api/payments/callback', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                    body: new URLSearchParams({{
                        merchant_oid: '{merchant_oid}',
                        status: success ? 'success' : 'failed',
                        total_amount: '{int(booking["amount"] * 100)}'
                    }})
                }});
                
                if (success) {{
                    window.location.href = '/api/payments/success/{merchant_oid}';
                }} else {{
                    window.location.href = '/api/payments/failure/{merchant_oid}';
                }}
            }}
        </script>
    </body>
    </html>
    """)

@api_router.post("/payments/callback")
async def payment_callback(request: Request, background_tasks: BackgroundTasks):
    """PayTR callback webhook (simulated)"""
    form_data = await request.form()
    callback_data = dict(form_data)
    
    merchant_oid = callback_data.get('merchant_oid')
    status = callback_data.get('status')
    
    booking = await db.bookings.find_one({"merchant_oid": merchant_oid}, {"_id": 0})
    if not booking:
        return PlainTextResponse("OK")
    
    if status == 'success':
        # Update booking
        await db.bookings.update_one({"id": booking['id']}, {"$set": {"status": "confirmed"}})
        
        # Create transaction
        transaction = Transaction(
            booking_id=booking['id'],
            amount=booking['amount'],
            commission=50.0,
            status="success"
        )
        trans_dict = transaction.model_dump()
        trans_dict['created_at'] = trans_dict['created_at'].isoformat()
        await db.transactions.insert_one(trans_dict)
        
        # NO LOYALTY UPDATE - System removed
        
        # Create notification for field owner
        field = await db.fields.find_one({"id": booking['field_id']}, {"_id": 0})
        if field:
            notif = Notification(
                user_id=field['owner_id'],
                type="booking",
                message=f"Yeni rezervasyon: {booking['date']} {booking['time']}"
            )
            notif_dict = notif.model_dump()
            notif_dict['created_at'] = notif_dict['created_at'].isoformat()
            await db.notifications.insert_one(notif_dict)
        
        logger.info(f"Payment successful for booking {booking['id']}")
    else:
        await db.bookings.update_one({"id": booking['id']}, {"$set": {"status": "cancelled"}})
        logger.warning(f"Payment failed for booking {booking['id']}")
    
    return PlainTextResponse("OK")

@api_router.get("/payments/success/{merchant_oid}")
async def payment_success(merchant_oid: str):
    booking = await db.bookings.find_one({"merchant_oid": merchant_oid}, {"_id": 0})
    if not booking:
        return HTMLResponse("<h1>Rezervasyon bulunamadı</h1>", status_code=404)
    
    # Get user to determine redirect
    user = await db.users.find_one({"id": booking['user_id']}, {"_id": 0})
    redirect_url = "/dashboard"
    
    if user:
        if user['role'] == 'admin':
            redirect_url = "/admin"
        elif user['role'] == 'owner':
            redirect_url = "/owner"
        else:
            redirect_url = "/dashboard"
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ödeme Başarılı</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
            .success {{ color: #2E7D32; }}
        </style>
        <script>
            setTimeout(function() {{
                window.location.href = '{redirect_url}';
            }}, 3000);
        </script>
    </head>
    <body>
        <div class="success">
            <h1>✓ Ödeme Başarılı</h1>
            <p>Rezervasyonunuz onaylandı.</p>
            <p>Tutar: {booking['amount']} TL</p>
            <p>3 saniye içinde yönlendirileceksiniz...</p>
            <a href="{redirect_url}">Hemen Git</a>
        </div>
    </body>
    </html>
    """)

@api_router.get("/payments/failure/{merchant_oid}")
async def payment_failure(merchant_oid: str):
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ödeme Başarısız</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .error { color: #d32f2f; }
        </style>
    </head>
    <body>
        <div class="error">
            <h1>✗ Ödeme Başarısız</h1>
            <p>Ödemeniz işlenemedi. Lütfen tekrar deneyin.</p>
            <a href="/">Ana Sayfaya Dön</a>
        </div>
    </body>
    </html>
    """)

# ==================== REVIEWS ROUTES ====================

@api_router.post("/reviews")
async def create_review(review: ReviewCreate, user: Dict = Depends(get_current_user)):
    # Check if user has completed booking for this field
    booking = await db.bookings.find_one({
        "user_id": user['id'],
        "field_id": review.field_id,
        "status": "completed"
    }, {"_id": 0})
    
    if not booking:
        raise HTTPException(status_code=400, detail="You must complete a booking before reviewing")
    
    new_review = Review(
        user_id=user['id'],
        field_id=review.field_id,
        rating=review.rating,
        comment=review.comment
    )
    
    review_dict = new_review.model_dump()
    review_dict['created_at'] = review_dict['created_at'].isoformat()
    
    await db.reviews.insert_one(review_dict)
    
    return {"status": "success", "message": "Review submitted for approval"}

@api_router.get("/reviews/{field_id}")
async def get_reviews(field_id: str):
    reviews = await db.reviews.find({"field_id": field_id, "approved": True}, {"_id": 0}).to_list(1000)
    return {"reviews": reviews}

# ==================== TEAM SEARCH ROUTES ====================

@api_router.post("/team-search")
async def create_team_search(team: TeamSearchCreate, user: Dict = Depends(get_current_user)):
    """Create a new team search ad"""
    
    # Validate required fields
    if not team.date or not team.time:
        raise HTTPException(status_code=400, detail="Lütfen konum, tarih ve mevki bilgilerini doldurun.")
    
    if not team.position:
        raise HTTPException(status_code=400, detail="Lütfen konum, tarih ve mevki bilgilerini doldurun.")
    
    # Check location - either field_id OR manual location required
    if not team.field_id:
        if not team.location_city or not team.location_district:
            raise HTTPException(status_code=400, detail="Lütfen konum, tarih ve mevki bilgilerini doldurun.")
    
    if not team.message or len(team.message.strip()) < 10:
        raise HTTPException(status_code=400, detail="Lütfen en az 10 karakter açıklama yazın.")
    
    new_team = TeamSearch(
        user_id=user['id'],
        **team.model_dump()
    )
    
    team_dict = new_team.model_dump()
    team_dict['created_at'] = team_dict['created_at'].isoformat()
    
    await db.team_searches.insert_one(team_dict)
    
    return {
        "success": True,
        "message": "İlan başarıyla oluşturuldu.",
        "ad_id": team_dict['id']
    }

@api_router.get("/team-search")
async def get_team_searches(
    city: Optional[str] = None,
    position: Optional[str] = None,
    intensity: Optional[str] = None
):
    query = {}
    if city:
        query['location_city'] = city
    if position and position != 'farketmez':
        query['position'] = position
    if intensity:
        query['intensity_level'] = intensity
    
    searches = await db.team_searches.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with field and user data
    for search in searches:
        if search.get('field_id'):
            field = await db.fields.find_one({"id": search['field_id']}, {"_id": 0})
            if field:
                search['field_name'] = field['name']
                search['field_city'] = field['city']
        
        user = await db.users.find_one({"id": search['user_id']}, {"_id": 0})
        if user:
            search['creator_name'] = user['name']
    
    return {"team_searches": searches}

@api_router.post("/team-search/{search_id}/join")
async def join_team_search(search_id: str, user: Dict = Depends(get_current_user)):
    """Join a team search"""
    search = await db.team_searches.find_one({"id": search_id}, {"_id": 0})
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    
    # Check if user already joined
    participants = search.get('participants', [])
    if user['id'] in participants:
        raise HTTPException(status_code=400, detail="Already joined")
    
    # Check if creator
    if search['user_id'] == user['id']:
        raise HTTPException(status_code=400, detail="Cannot join your own search")
    
    # Add participant
    participants.append(user['id'])
    await db.team_searches.update_one(
        {"id": search_id},
        {"$set": {"participants": participants}}
    )
    
    # Create notification for creator
    notif = Notification(
        user_id=search['user_id'],
        type="team",
        message=f"{user['name']} takım aramanıza katıldı!"
    )
    notif_dict = notif.model_dump()
    notif_dict['created_at'] = notif_dict['created_at'].isoformat()
    await db.notifications.insert_one(notif_dict)
    
    return {"status": "success", "message": "Takıma katıldınız!"}

@api_router.delete("/team-search/{search_id}")
async def delete_team_search(search_id: str, user: Dict = Depends(get_current_user)):
    search = await db.team_searches.find_one({"id": search_id}, {"_id": 0})
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    
    if search['user_id'] != user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.team_searches.delete_one({"id": search_id})
    return {"status": "success"}

# ==================== NOTIFICATIONS ROUTES ====================

@api_router.get("/notifications")
async def get_notifications(user: Dict = Depends(get_current_user)):
    notifs = await db.notifications.find({"user_id": user['id']}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"notifications": notifs}

@api_router.put("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, user: Dict = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notif_id, "user_id": user['id']},
        {"$set": {"read": True}}
    )
    return {"status": "success"}

# ==================== OWNER PROFILE ROUTES ====================

@api_router.post("/owner/profile")
async def create_owner_profile(profile: OwnerProfileCreate, user: Dict = Depends(get_current_user)):
    """Create or update owner profile"""
    # Check if user has owner role
    if user['role'] != 'owner':
        raise HTTPException(status_code=403, detail="Sadece owner hesapları profil oluşturabilir")
    
    # Check if profile already exists
    existing_profile = await db.owner_profiles.find_one({"user_id": user['id']}, {"_id": 0})
    
    if existing_profile:
        # Update existing profile
        update_data = profile.model_dump()
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        await db.owner_profiles.update_one(
            {"user_id": user['id']},
            {"$set": update_data}
        )
        
        # Update user is_owner flag
        await db.users.update_one(
            {"id": user['id']},
            {"$set": {"is_owner": True}}
        )
        
        logger.info(f"Owner profile updated for user {user['id']}")
        return {"status": "success", "message": "Owner profili güncellendi", "action": "updated"}
    else:
        # Create new profile
        new_profile = OwnerProfile(
            user_id=user['id'],
            tax_number=profile.tax_number,
            iban=profile.iban,
            phone=profile.phone,
            address=profile.address,
            business_name=profile.business_name,
            status="active"
        )
        
        profile_dict = new_profile.model_dump()
        profile_dict['created_at'] = profile_dict['created_at'].isoformat()
        profile_dict['updated_at'] = profile_dict['updated_at'].isoformat()
        
        await db.owner_profiles.insert_one(profile_dict)
        
        # Update user is_owner flag
        await db.users.update_one(
            {"id": user['id']},
            {"$set": {"is_owner": True}}
        )
        
        logger.info(f"Owner profile created for user {user['id']}")
        return {"status": "success", "message": "Owner profili oluşturuldu. Artık saha ekleyebilirsiniz!", "action": "created"}

@api_router.get("/owner/profile")
async def get_owner_profile(user: Dict = Depends(get_current_user)):
    """Get owner profile"""
    if user['role'] != 'owner':
        raise HTTPException(status_code=403, detail="Sadece owner hesapları bu bilgiye erişebilir")
    
    profile = await db.owner_profiles.find_one({"user_id": user['id']}, {"_id": 0})
    
    if not profile:
        return {
            "status": "not_found",
            "has_profile": False,
            "message": "Owner profili bulunamadı. Lütfen profil bilgilerinizi girin."
        }
    
    return {
        "status": "success",
        "has_profile": True,
        "profile": profile
    }

@api_router.get("/debug/me")
async def debug_user_info(user: Dict = Depends(get_current_user)):
    """Debug endpoint to check user info and owner profile status"""
    owner_profile = None
    has_owner_profile = False
    owner_status = None
    
    if user['role'] == 'owner':
        owner_profile = await db.owner_profiles.find_one({"user_id": user['id']}, {"_id": 0})
        has_owner_profile = owner_profile is not None
        owner_status = owner_profile.get('status') if owner_profile else None
    
    return {
        "user_id": user['id'],
        "email": user['email'],
        "name": user['name'],
        "role": user['role'],
        "is_owner": user.get('is_owner', False),
        "has_owner_profile": has_owner_profile,
        "owner_status": owner_status,
        "can_create_fields": user['role'] == 'owner' and has_owner_profile and owner_status in ['active', 'verified'],
        "suspended": user.get('suspended', False)
    }

# ==================== LOYALTY ROUTES (DISABLED) ====================
# Loyalty system has been removed as per business requirement

# @api_router.get("/loyalty/status")
# async def get_loyalty_status(user: Dict = Depends(get_current_user)):
#     return {
#         "altin_tac": 0,
#         "progress": 0,
#         "eligible_for_discount": False,
#         "message": "Sadakat sistemi devre dışı bırakılmıştır"
#     }

# ==================== PHOTO UPLOAD ROUTES ====================

@api_router.post("/fields/{field_id}/photos")
async def upload_field_photo(
    field_id: str,
    file: UploadFile = File(...),
    user: Dict = Depends(get_current_user)
):
    """Upload a photo for a field (Owner only)"""
    # Check if user is owner
    if user['role'] != 'owner':
        raise HTTPException(status_code=403, detail="Sadece saha sahipleri fotoğraf yükleyebilir")
    
    # Check if field belongs to owner
    field = await db.fields.find_one({"id": field_id, "owner_id": user['id']}, {"_id": 0})
    if not field:
        raise HTTPException(status_code=404, detail="Saha bulunamadı veya size ait değil")
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Desteklenmeyen dosya formatı. Lütfen JPG, PNG veya WEBP yükleyin.")
    
    # Check file size (5MB limit)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=400, detail="Dosya boyutu en fazla 5 MB olabilir.")
    
    # Check photo count (max 10)
    current_photos = field.get('photos', [])
    if len(current_photos) >= 10:
        raise HTTPException(status_code=400, detail="En fazla 10 fotoğraf yükleyebilirsiniz.")
    
    # Save file
    timestamp = int(datetime.now().timestamp())
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"{field_id}_{timestamp}.{file_extension}"
    file_path = UPLOADS_DIR / filename
    
    try:
        with open(file_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail="Fotoğraf yüklenemedi, lütfen tekrar deneyin.")
    
    # Generate URL
    photo_url = f"/api/uploads/photos/{filename}"
    
    # Update field photos
    current_photos.append(photo_url)
    update_data = {"photos": current_photos}
    
    # If this is the first photo, set it as cover
    if len(current_photos) == 1:
        update_data["cover_photo_url"] = photo_url
    
    await db.fields.update_one({"id": field_id}, {"$set": update_data})
    
    return {
        "status": "success",
        "photo_url": photo_url,
        "message": "Fotoğraf başarıyla yüklendi"
    }

@api_router.delete("/fields/{field_id}/photos")
async def delete_field_photo(
    field_id: str,
    photo_url: str,
    user: Dict = Depends(get_current_user)
):
    """Delete a photo from a field"""
    # Check if user is owner
    if user['role'] != 'owner':
        raise HTTPException(status_code=403, detail="Sadece saha sahipleri fotoğraf silebilir")
    
    # Check if field belongs to owner
    field = await db.fields.find_one({"id": field_id, "owner_id": user['id']}, {"_id": 0})
    if not field:
        raise HTTPException(status_code=404, detail="Saha bulunamadı")
    
    # Remove photo from list
    photos = field.get('photos', [])
    if photo_url not in photos:
        raise HTTPException(status_code=404, detail="Fotoğraf bulunamadı")
    
    photos.remove(photo_url)
    
    # Delete file
    try:
        filename = photo_url.split('/')[-1]
        file_path = UPLOADS_DIR / filename
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        logger.error(f"File deletion error: {e}")
    
    # Update field
    update_data = {"photos": photos}
    
    # If deleted photo was cover, set new cover
    if field.get('cover_photo_url') == photo_url:
        update_data["cover_photo_url"] = photos[0] if photos else None
    
    await db.fields.update_one({"id": field_id}, {"$set": update_data})
    
    return {"status": "success", "message": "Fotoğraf silindi"}

@api_router.put("/fields/{field_id}/cover-photo")
async def set_cover_photo(
    field_id: str,
    photo_url: str,
    user: Dict = Depends(get_current_user)
):
    """Set cover photo for a field"""
    # Check if user is owner
    if user['role'] != 'owner':
        raise HTTPException(status_code=403, detail="Sadece saha sahipleri kapak fotoğrafı belirleyebilir")
    
    # Check if field belongs to owner
    field = await db.fields.find_one({"id": field_id, "owner_id": user['id']}, {"_id": 0})
    if not field:
        raise HTTPException(status_code=404, detail="Saha bulunamadı")
    
    # Check if photo exists in field photos
    photos = field.get('photos', [])
    if photo_url not in photos:
        raise HTTPException(status_code=404, detail="Fotoğraf bulunamadı")
    
    # Set as cover
    await db.fields.update_one({"id": field_id}, {"$set": {"cover_photo_url": photo_url}})
    
    return {"status": "success", "message": "Kapak fotoğrafı güncellendi"}

@api_router.get("/uploads/photos/{filename}")
async def get_photo(filename: str):
    """Serve uploaded photos"""
    file_path = UPLOADS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fotoğraf bulunamadı")
    
    return FileResponse(file_path)

# ==================== ADMIN ROUTES ====================

@api_router.get("/admin/dashboard")
async def admin_dashboard(admin: Dict = Depends(get_admin_user)):
    """Get admin dashboard statistics"""
    # Count statistics
    total_users = await db.users.count_documents({})
    total_owners = await db.users.count_documents({"role": "owner"})
    total_fields = await db.fields.count_documents({})
    pending_fields = await db.fields.count_documents({"approved": False})
    total_bookings = await db.bookings.count_documents({})
    
    # Revenue calculations
    bookings = await db.bookings.find({"status": {"$in": ["paid", "confirmed"]}}, {"_id": 0}).to_list(10000)
    total_revenue = sum(b.get('total_amount_user_paid', 0) for b in bookings)
    platform_revenue = sum(b.get('platform_fee_amount', 50) for b in bookings)
    owner_revenue = sum(b.get('owner_share_amount', 0) for b in bookings)
    
    # Get recent activities
    recent_fields = await db.fields.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    recent_bookings = await db.bookings.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "statistics": {
            "total_users": total_users,
            "total_owners": total_owners,
            "total_fields": total_fields,
            "pending_fields": pending_fields,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "platform_revenue": platform_revenue,
            "owner_revenue": owner_revenue
        },
        "recent_fields": recent_fields,
        "recent_bookings": recent_bookings
    }

@api_router.get("/admin/fields")
async def admin_get_fields(admin: Dict = Depends(get_admin_user), status: Optional[str] = None):
    """Get all fields with filter options"""
    query = {}
    if status == "pending":
        query["approved"] = False
    elif status == "approved":
        query["approved"] = True
    
    fields = await db.fields.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich with owner data
    for field in fields:
        owner = await db.users.find_one({"id": field['owner_id']}, {"_id": 0})
        if owner:
            field['owner_name'] = owner['name']
            field['owner_email'] = owner['email']
            field['owner_phone'] = owner.get('phone', '')
    
    return {"fields": fields}

@api_router.post("/admin/fields/{field_id}/approve")
async def admin_approve_field(field_id: str, admin: Dict = Depends(get_admin_user)):
    """Approve a field"""
    field = await db.fields.find_one({"id": field_id}, {"_id": 0})
    if not field:
        raise HTTPException(status_code=404, detail="Saha bulunamadı")
    
    # Update field
    await db.fields.update_one(
        {"id": field_id},
        {"$set": {
            "approved": True,
            "tax_verified": True,
            "subscription_prices_pending_review": False
        }}
    )
    
    # Create audit log
    await create_audit_log(
        admin['id'],
        admin['email'],
        "approve_field",
        "field",
        field_id,
        {"field_name": field['name'], "owner_id": field['owner_id']}
    )
    
    # Notify owner
    notif = Notification(
        user_id=field['owner_id'],
        type="booking",
        message=f"Sahanız '{field['name']}' onaylandı ve yayına alındı!"
    )
    notif_dict = notif.model_dump()
    notif_dict['created_at'] = notif_dict['created_at'].isoformat()
    await db.notifications.insert_one(notif_dict)
    
    return {"status": "success", "message": "Saha onaylandı"}

@api_router.post("/admin/fields/{field_id}/reject")
async def admin_reject_field(field_id: str, reason: str, admin: Dict = Depends(get_admin_user)):
    """Reject a field"""
    field = await db.fields.find_one({"id": field_id}, {"_id": 0})
    if not field:
        raise HTTPException(status_code=404, detail="Saha bulunamadı")
    
    # Create audit log
    await create_audit_log(
        admin['id'],
        admin['email'],
        "reject_field",
        "field",
        field_id,
        {"field_name": field['name'], "owner_id": field['owner_id'], "reason": reason}
    )
    
    # Notify owner
    notif = Notification(
        user_id=field['owner_id'],
        type="booking",
        message=f"Sahanız '{field['name']}' reddedildi. Sebep: {reason}"
    )
    notif_dict = notif.model_dump()
    notif_dict['created_at'] = notif_dict['created_at'].isoformat()
    await db.notifications.insert_one(notif_dict)
    
    return {"status": "success", "message": "Saha reddedildi"}

@api_router.get("/admin/users")
async def admin_get_users(admin: Dict = Depends(get_admin_user), role: Optional[str] = None):
    """Get all users"""
    query = {}
    if role:
        query["role"] = role
    
    users = await db.users.find(query, {"_id": 0, "password": 0}).sort("created_at", -1).to_list(10000)
    
    return {"users": users}

@api_router.post("/admin/users/{user_id}/suspend")
async def admin_suspend_user(user_id: str, admin: Dict = Depends(get_admin_user)):
    """Suspend a user account"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    if user['role'] == 'admin':
        raise HTTPException(status_code=403, detail="Admin hesapları askıya alınamaz")
    
    # Add suspended flag
    await db.users.update_one({"id": user_id}, {"$set": {"suspended": True}})
    
    # Create audit log
    await create_audit_log(
        admin['id'],
        admin['email'],
        "suspend_user",
        "user",
        user_id,
        {"user_email": user['email'], "user_name": user['name']}
    )
    
    return {"status": "success", "message": "Kullanıcı askıya alındı"}

@api_router.post("/admin/users/{user_id}/unsuspend")
async def admin_unsuspend_user(user_id: str, admin: Dict = Depends(get_admin_user)):
    """Unsuspend a user account"""
    await db.users.update_one({"id": user_id}, {"$set": {"suspended": False}})
    
    # Create audit log
    await create_audit_log(
        admin['id'],
        admin['email'],
        "unsuspend_user",
        "user",
        user_id,
        {}
    )
    
    return {"status": "success", "message": "Kullanıcı aktif hale getirildi"}

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: str, admin: Dict = Depends(get_admin_user)):
    """Delete a user account"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    if user['role'] == 'admin':
        raise HTTPException(status_code=403, detail="Admin hesapları silinemez")
    
    # Delete user
    await db.users.delete_one({"id": user_id})
    
    # Create audit log
    await create_audit_log(
        admin['id'],
        admin['email'],
        "delete_user",
        "user",
        user_id,
        {"user_email": user['email'], "user_name": user['name']}
    )
    
    return {"status": "success", "message": "Kullanıcı silindi"}

@api_router.get("/admin/bookings")
async def admin_get_bookings(admin: Dict = Depends(get_admin_user)):
    """Get all bookings"""
    bookings = await db.bookings.find({}, {"_id": 0}).sort("created_at", -1).to_list(10000)
    
    # Enrich with user and field data
    for booking in bookings:
        user = await db.users.find_one({"id": booking['user_id']}, {"_id": 0})
        if user:
            booking['user_name'] = user['name']
            booking['user_email'] = user['email']
        
        field = await db.fields.find_one({"id": booking['field_id']}, {"_id": 0})
        if field:
            booking['field_name'] = field['name']
            booking['field_city'] = field['city']
    
    return {"bookings": bookings}

@api_router.get("/admin/analytics")
async def admin_analytics(admin: Dict = Depends(get_admin_user)):
    """Get analytics data"""
    # Get bookings by status
    confirmed_bookings = await db.bookings.count_documents({"status": {"$in": ["paid", "confirmed"]}})
    cancelled_bookings = await db.bookings.count_documents({"status": "cancelled"})
    
    # Revenue by month (last 12 months)
    from datetime import date
    monthly_revenue = []
    
    for month_offset in range(12):
        start_date = date.today().replace(day=1) - timedelta(days=30 * month_offset)
        end_date = (start_date + timedelta(days=32)).replace(day=1)
        
        bookings = await db.bookings.find({
            "status": {"$in": ["paid", "confirmed"]},
            "created_at": {
                "$gte": start_date.isoformat(),
                "$lt": end_date.isoformat()
            }
        }, {"_id": 0}).to_list(10000)
        
        revenue = sum(b.get('total_amount_user_paid', 0) for b in bookings)
        monthly_revenue.insert(0, {
            "month": start_date.strftime("%Y-%m"),
            "revenue": revenue,
            "booking_count": len(bookings)
        })
    
    # Top fields by bookings
    pipeline = [
        {"$match": {"status": {"$in": ["paid", "confirmed"]}}},
        {"$group": {"_id": "$field_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    top_fields_data = await db.bookings.aggregate(pipeline).to_list(10)
    top_fields = []
    for item in top_fields_data:
        field = await db.fields.find_one({"id": item['_id']}, {"_id": 0})
        if field:
            top_fields.append({
                "field_name": field['name'],
                "city": field['city'],
                "booking_count": item['count']
            })
    
    return {
        "booking_stats": {
            "confirmed": confirmed_bookings,
            "cancelled": cancelled_bookings
        },
        "monthly_revenue": monthly_revenue,
        "top_fields": top_fields
    }

@api_router.get("/admin/audit-logs")
async def admin_get_audit_logs(admin: Dict = Depends(get_admin_user), limit: int = 100):
    """Get audit logs"""
    logs = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"logs": logs}

@api_router.get("/admin/support-tickets")
async def admin_get_support_tickets(admin: Dict = Depends(get_admin_user)):
    """Get all support tickets"""
    tickets = await db.support_tickets.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return {"tickets": tickets}

@api_router.post("/support/ticket")
async def create_support_ticket(
    subject: str,
    message: str,
    user: Dict = Depends(get_current_user)
):
    """Create a support ticket"""
    ticket = SupportTicket(
        user_id=user['id'],
        user_email=user['email'],
        user_name=user['name'],
        subject=subject,
        message=message
    )
    
    ticket_dict = ticket.model_dump()
    ticket_dict['created_at'] = ticket_dict['created_at'].isoformat()
    ticket_dict['updated_at'] = ticket_dict['updated_at'].isoformat()
    
    await db.support_tickets.insert_one(ticket_dict)
    
    return {"status": "success", "message": "Destek talebiniz oluşturuldu", "ticket_id": ticket.id}

# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def create_default_admin():
    """Create default admin account if it doesn't exist"""
    admin_email = "cnrakbb070@hotmail.com"
    admin_password = "Canerak07"
    
    # Check if admin exists
    existing_admin = await db.users.find_one({"email": admin_email}, {"_id": 0})
    if existing_admin:
        logger.info("Default admin account already exists")
    else:
        # Create admin account
        admin_user = User(
            email=admin_email,
            password=hash_password(admin_password),
            name="E-Saha Admin",
            role="admin"
        )
        
        admin_dict = admin_user.model_dump()
        admin_dict['created_at'] = admin_dict['created_at'].isoformat()
        
        await db.users.insert_one(admin_dict)
        logger.info(f"Default admin account created: {admin_email}")
        
        # Create audit log for admin creation
        log = AuditLog(
            admin_id="system",
            admin_email="system",
            action="create_admin",
            target_type="user",
            target_id=admin_user.id,
            details={"email": admin_email}
        )
        log_dict = log.model_dump()
        log_dict['created_at'] = log_dict['created_at'].isoformat()
        await db.audit_logs.insert_one(log_dict)
    
    # Backfill: Create owner profiles for existing owners without profiles
    owners_without_profiles = []
    async for user in db.users.find({"role": "owner"}, {"_id": 0}):
        profile_exists = await db.owner_profiles.find_one({"user_id": user['id']}, {"_id": 0})
        if not profile_exists:
            owners_without_profiles.append(user)
    
    if owners_without_profiles:
        logger.info(f"Found {len(owners_without_profiles)} owners without profiles. Creating default profiles...")
        
        for owner in owners_without_profiles:
            # Create a basic profile for existing owners
            # They can update it later
            default_profile = OwnerProfile(
                user_id=owner['id'],
                tax_number="0000000000",  # Placeholder - user should update
                iban="TR000000000000000000000000",  # Placeholder - user should update
                phone=owner.get('phone', '0000000000'),
                address="Lütfen adresinizi güncelleyin",
                business_name=owner.get('name', 'Unknown'),
                status="active"  # Set active so they can create fields
            )
            
            profile_dict = default_profile.model_dump()
            profile_dict['created_at'] = profile_dict['created_at'].isoformat()
            profile_dict['updated_at'] = profile_dict['updated_at'].isoformat()
            
            await db.owner_profiles.insert_one(profile_dict)
            
            # Update user is_owner flag
            await db.users.update_one(
                {"id": owner['id']},
                {"$set": {"is_owner": True}}
            )
            
            logger.info(f"Created default owner profile for {owner['email']}")
        
        logger.info(f"Completed owner profile backfill for {len(owners_without_profiles)} users")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
