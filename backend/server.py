from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.responses import PlainTextResponse, HTMLResponse
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
    altin_tac: int = 0
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
    photos: List[str] = []
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
    # Check cookie first
    session_token = request.cookies.get('session_token')
    
    # Fallback to Authorization header
    if not session_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            session_token = auth_header.split(' ')[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(session_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload['user_id']}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(req: RegisterRequest):
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
            "role": user['role'],
            "altin_tac": user.get('altin_tac', 0)
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
                "role": user['role'],
                "altin_tac": user.get('altin_tac', 0)
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
        "role": user['role'],
        "altin_tac": user.get('altin_tac', 0)
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
    if user['role'] != 'owner':
        raise HTTPException(status_code=403, detail="Only owners can create fields")
    
    # Validate required fields
    if not field.tax_number or not field.iban:
        raise HTTPException(status_code=400, detail="Vergi numarası ve IBAN zorunludur")
    
    # Validate tax_number format (basic check)
    if len(field.tax_number.strip()) < 10:
        raise HTTPException(status_code=400, detail="Geçersiz vergi numarası formatı")
    
    # Validate IBAN format (basic check)
    if not field.iban.strip().startswith('TR') or len(field.iban.strip()) < 20:
        raise HTTPException(status_code=400, detail="Geçersiz IBAN formatı (TR ile başlamalı)")
    
    new_field = FieldModel(
        owner_id=user['id'],
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
    """Get weekly calendar view for a field"""
    from datetime import date, timedelta
    
    field = await db.fields.find_one({"id": field_id}, {"_id": 0})
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    
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
            "status": {"$in": ["confirmed", "pending"]}
        }, {"_id": 0}).to_list(100)
        
        # Create slots for each hour (09:00 - 23:00)
        slots = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        for hour in range(9, 24):
            start_time = f"{hour:02d}:00"
            end_time = f"{(hour + 1):02d}:00"
            
            # Check if this slot is booked
            is_booked = any(b['time'] == start_time for b in bookings)
            
            # Check if it's in the past
            slot_datetime = datetime.fromisoformat(f"{date_str}T{start_time}:00")
            is_past = slot_datetime < now
            
            # Determine status
            if is_past:
                status = "past"
                bookable = False
            elif is_booked:
                # Check if it's subscription
                booking = next((b for b in bookings if b['time'] == start_time), None)
                if booking and booking.get('is_subscription'):
                    status = "subscription_locked"
                else:
                    status = "reserved"
                bookable = False
            else:
                status = "available"
                bookable = True
            
            slots.append({
                "start": start_time,
                "end": end_time,
                "status": status,
                "bookable": bookable
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
        "days": days_data
    }

# ==================== BOOKINGS ROUTES ====================

@api_router.post("/bookings")
async def create_booking(booking: BookingCreate, user: Dict = Depends(get_current_user)):
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
    
    # Create booking
    new_booking = Booking(
        user_id=user['id'],
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
    
    # Update availability - mark slot as unavailable
    # Note: We'll need to add an availabilities collection for this
    # For now, the booking existence itself marks the slot as unavailable
    
    # Return clean booking data without _id
    return {"status": "success", "booking": {
        "id": booking_dict['id'],
        "field_id": booking_dict['field_id'],
        "start_datetime": booking_dict['start_datetime'],
        "end_datetime": booking_dict['end_datetime'],
        "status": booking_dict['status'],
        "total_amount_user_paid": booking_dict['total_amount_user_paid'],
        "owner_share_amount": booking_dict['owner_share_amount'],
        "platform_fee_amount": booking_dict['platform_fee_amount']
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
        
        # Update user's altin_tac
        await db.users.update_one({"id": booking['user_id']}, {"$inc": {"altin_tac": 1}})
        
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
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ödeme Başarılı</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
            .success {{ color: #2E7D32; }}
        </style>
    </head>
    <body>
        <div class="success">
            <h1>✓ Ödeme Başarılı</h1>
            <p>Rezervasyonunuz onaylandı.</p>
            <p>Tutar: {booking['amount']} TL</p>
            <a href="/">Ana Sayfaya Dön</a>
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
    new_team = TeamSearch(
        user_id=user['id'],
        **team.model_dump()
    )
    
    team_dict = new_team.model_dump()
    team_dict['created_at'] = team_dict['created_at'].isoformat()
    
    await db.team_searches.insert_one(team_dict)
    
    return {"status": "success", "team_search": team_dict}

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
