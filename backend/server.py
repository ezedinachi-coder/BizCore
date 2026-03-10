from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import httpx
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'bizcore_db')]

# Create the main app
app = FastAPI(title="BizCore API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================
# ENUMS
# ========================

class ProductCategory(str, Enum):
    RAW = "raw"
    FINISHED = "finished"
    PACKAGING = "packaging"

class TransactionType(str, Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    PRODUCTION = "production"
    ADJUSTMENT = "adjustment"
    RETURN = "return"

class OrderStatus(str, Enum):
    DRAFT = "draft"
    ORDERED = "ordered"
    RECEIVED = "received"
    CANCELLED = "cancelled"
    PAID = "paid"
    PARTIAL = "partial"
    DELIVERED = "delivered"

class InvoiceType(str, Enum):
    PURCHASE = "purchase"
    SALE = "sale"

class InvoiceStatus(str, Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"

class PaymentMethod(str, Enum):
    CASH = "cash"
    BANK = "bank"
    UPI = "upi"
    CARD = "card"

class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    INCOME = "income"
    EXPENSE = "expense"
    EQUITY = "equity"

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    MANAGER = "manager"
    PURCHASE_CLERK = "purchase_clerk"
    SALES_EXECUTIVE = "sales_executive"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"

# ========================
# PYDANTIC MODELS
# ========================

# Auth Models
class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    company_id: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

# Company Model
class Company(BaseModel):
    company_id: str = Field(default_factory=lambda: f"comp_{uuid.uuid4().hex[:12]}")
    name: str
    address: Optional[str] = None
    tax_id: Optional[str] = None
    logo_url: Optional[str] = None
    currency: str = "USD"
    fiscal_year_start: int = 1  # Month (1-12)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompanyCreate(BaseModel):
    name: str
    address: Optional[str] = None
    tax_id: Optional[str] = None
    currency: str = "USD"

# Warehouse Model
class Warehouse(BaseModel):
    warehouse_id: str = Field(default_factory=lambda: f"wh_{uuid.uuid4().hex[:12]}")
    name: str
    address: Optional[str] = None
    capacity: Optional[float] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WarehouseCreate(BaseModel):
    name: str
    address: Optional[str] = None
    capacity: Optional[float] = None

# Product Model
class Product(BaseModel):
    product_id: str = Field(default_factory=lambda: f"prod_{uuid.uuid4().hex[:12]}")
    sku: str
    name: str
    description: Optional[str] = None
    category: ProductCategory = ProductCategory.RAW
    unit: str = "pcs"
    cost_price: float = 0.0
    selling_price: float = 0.0
    reorder_level: int = 10
    min_stock: int = 0
    max_stock: int = 1000
    expiry_days: Optional[int] = None
    barcode: Optional[str] = None
    image_url: Optional[str] = None
    default_supplier_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: ProductCategory = ProductCategory.RAW
    unit: str = "pcs"
    cost_price: float = 0.0
    selling_price: float = 0.0
    reorder_level: int = 10
    min_stock: int = 0
    max_stock: int = 1000
    expiry_days: Optional[int] = None
    barcode: Optional[str] = None
    image_url: Optional[str] = None
    default_supplier_id: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    unit: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    reorder_level: Optional[int] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None
    expiry_days: Optional[int] = None
    barcode: Optional[str] = None
    image_url: Optional[str] = None
    default_supplier_id: Optional[str] = None
    is_active: Optional[bool] = None

# Inventory Stock Model
class InventoryStock(BaseModel):
    stock_id: str = Field(default_factory=lambda: f"stock_{uuid.uuid4().hex[:12]}")
    product_id: str
    warehouse_id: str
    quantity: float = 0.0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Stock Transaction Model
class StockTransaction(BaseModel):
    transaction_id: str = Field(default_factory=lambda: f"txn_{uuid.uuid4().hex[:12]}")
    product_id: str
    warehouse_id: str
    type: TransactionType
    quantity: float
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StockTransactionCreate(BaseModel):
    product_id: str
    warehouse_id: str
    type: TransactionType
    quantity: float
    reference_id: Optional[str] = None
    notes: Optional[str] = None

# Supplier Model
class Supplier(BaseModel):
    supplier_id: str = Field(default_factory=lambda: f"sup_{uuid.uuid4().hex[:12]}")
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    payment_terms_days: int = 30
    tax_id: Optional[str] = None
    rating: float = 0.0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    payment_terms_days: int = 30
    tax_id: Optional[str] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    payment_terms_days: Optional[int] = None
    tax_id: Optional[str] = None
    rating: Optional[float] = None
    is_active: Optional[bool] = None

# Distributor Model
class Distributor(BaseModel):
    distributor_id: str = Field(default_factory=lambda: f"dist_{uuid.uuid4().hex[:12]}")
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    territory: Optional[str] = None
    commission_percent: float = 0.0
    credit_limit: float = 0.0
    outstanding: float = 0.0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DistributorCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    territory: Optional[str] = None
    commission_percent: float = 0.0
    credit_limit: float = 0.0

class DistributorUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    territory: Optional[str] = None
    commission_percent: Optional[float] = None
    credit_limit: Optional[float] = None
    is_active: Optional[bool] = None

# Purchase Order Models
class PurchaseOrderItem(BaseModel):
    item_id: str = Field(default_factory=lambda: f"poi_{uuid.uuid4().hex[:12]}")
    product_id: str
    product_name: Optional[str] = None
    quantity: float
    unit_price: float
    received_quantity: float = 0.0

class PurchaseOrder(BaseModel):
    po_id: str = Field(default_factory=lambda: f"po_{uuid.uuid4().hex[:12]}")
    po_number: str
    supplier_id: str
    supplier_name: Optional[str] = None
    warehouse_id: str
    order_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expected_date: Optional[datetime] = None
    status: OrderStatus = OrderStatus.DRAFT
    items: List[PurchaseOrderItem] = []
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PurchaseOrderItemCreate(BaseModel):
    product_id: str
    quantity: float
    unit_price: float

class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    warehouse_id: str
    expected_date: Optional[datetime] = None
    items: List[PurchaseOrderItemCreate] = []
    tax_amount: float = 0.0
    notes: Optional[str] = None

class PurchaseOrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    expected_date: Optional[datetime] = None
    notes: Optional[str] = None

# Sales Order Models
class SalesOrderItem(BaseModel):
    item_id: str = Field(default_factory=lambda: f"soi_{uuid.uuid4().hex[:12]}")
    product_id: str
    product_name: Optional[str] = None
    quantity: float
    unit_price: float
    delivered_quantity: float = 0.0

class SalesOrder(BaseModel):
    so_id: str = Field(default_factory=lambda: f"so_{uuid.uuid4().hex[:12]}")
    so_number: str
    distributor_id: str
    distributor_name: Optional[str] = None
    warehouse_id: str
    order_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivery_date: Optional[datetime] = None
    status: OrderStatus = OrderStatus.DRAFT
    items: List[SalesOrderItem] = []
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SalesOrderItemCreate(BaseModel):
    product_id: str
    quantity: float
    unit_price: float

class SalesOrderCreate(BaseModel):
    distributor_id: str
    warehouse_id: str
    delivery_date: Optional[datetime] = None
    items: List[SalesOrderItemCreate] = []
    tax_amount: float = 0.0
    notes: Optional[str] = None

class SalesOrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    delivery_date: Optional[datetime] = None
    notes: Optional[str] = None

# Invoice Model
class Invoice(BaseModel):
    invoice_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:12]}")
    invoice_number: str
    type: InvoiceType
    reference_id: str  # PO or SO id
    party_id: str  # Supplier or Distributor id
    party_name: Optional[str] = None
    issue_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: datetime
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    paid_amount: float = 0.0
    status: InvoiceStatus = InvoiceStatus.UNPAID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InvoiceCreate(BaseModel):
    type: InvoiceType
    reference_id: str
    party_id: str
    due_date: datetime
    subtotal: float
    tax_amount: float = 0.0

# Payment Model
class Payment(BaseModel):
    payment_id: str = Field(default_factory=lambda: f"pay_{uuid.uuid4().hex[:12]}")
    invoice_id: str
    amount: float
    payment_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    method: PaymentMethod = PaymentMethod.CASH
    transaction_ref: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PaymentCreate(BaseModel):
    invoice_id: str
    amount: float
    method: PaymentMethod = PaymentMethod.CASH
    transaction_ref: Optional[str] = None
    notes: Optional[str] = None

# Chart of Accounts Model
class ChartOfAccount(BaseModel):
    account_id: str = Field(default_factory=lambda: f"acc_{uuid.uuid4().hex[:12]}")
    code: str
    name: str
    type: AccountType
    parent_id: Optional[str] = None
    balance: float = 0.0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChartOfAccountCreate(BaseModel):
    code: str
    name: str
    type: AccountType
    parent_id: Optional[str] = None

# Notification Model
class Notification(BaseModel):
    notification_id: str = Field(default_factory=lambda: f"notif_{uuid.uuid4().hex[:12]}")
    user_id: str
    title: str
    message: str
    type: str = "info"
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Audit Log Model
class AuditLog(BaseModel):
    log_id: str = Field(default_factory=lambda: f"log_{uuid.uuid4().hex[:12]}")
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Dashboard Models
class DashboardStats(BaseModel):
    total_inventory_value: float = 0.0
    low_stock_count: int = 0
    today_sales: float = 0.0
    today_purchases: float = 0.0
    cash_balance: float = 0.0
    pending_invoices: int = 0
    total_products: int = 0
    total_suppliers: int = 0
    total_distributors: int = 0
    total_warehouses: int = 0

# ========================
# AUTHENTICATION HELPERS
# ========================

async def get_current_user(request: Request) -> User:
    """Get current user from session token"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user)

async def get_optional_user(request: Request) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None

# ========================
# AUTH ENDPOINTS
# ========================

@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Exchange session_id for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session_id")
        
        data = resp.json()
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    existing_user = await db.users.find_one({"email": data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "name": data["name"],
                "picture": data.get("picture"),
                "updated_at": datetime.now(timezone.utc)
            }}
        )
    else:
        user_doc = {
            "user_id": user_id,
            "email": data["email"],
            "name": data["name"],
            "picture": data.get("picture"),
            "role": UserRole.VIEWER.value,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(user_doc)
    
    session_token = data.get("session_token", f"sess_{uuid.uuid4().hex}")
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user

@api_router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current user info"""
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out successfully"}

# ========================
# USER MANAGEMENT ENDPOINTS
# ========================

@api_router.get("/users", response_model=List[User])
async def get_users(user: User = Depends(get_current_user)):
    """Get all users (admin only)"""
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    return [User(**u) for u in users]

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, update: UserUpdate, user: User = Depends(get_current_user)):
    """Update user (admin only)"""
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await db.users.update_one({"user_id": user_id}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return User(**updated_user)

# ========================
# COMPANY ENDPOINTS
# ========================

@api_router.get("/company")
async def get_company(user: User = Depends(get_current_user)):
    """Get company info"""
    company = await db.companies.find_one({}, {"_id": 0})
    if not company:
        default_company = Company(
            name="My Company",
            currency="USD"
        )
        await db.companies.insert_one(default_company.model_dump())
        return default_company
    return company

@api_router.put("/company")
async def update_company(company_data: CompanyCreate, user: User = Depends(get_current_user)):
    """Update company info (admin only)"""
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    existing = await db.companies.find_one({}, {"_id": 0})
    if existing:
        await db.companies.update_one({}, {"$set": company_data.model_dump()})
    else:
        company = Company(**company_data.model_dump())
        await db.companies.insert_one(company.model_dump())
    
    return await db.companies.find_one({}, {"_id": 0})

# ========================
# WAREHOUSE ENDPOINTS
# ========================

@api_router.get("/warehouses", response_model=List[Warehouse])
async def get_warehouses(user: User = Depends(get_current_user)):
    """Get all warehouses"""
    warehouses = await db.warehouses.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return [Warehouse(**w) for w in warehouses]

@api_router.post("/warehouses", response_model=Warehouse)
async def create_warehouse(warehouse: WarehouseCreate, user: User = Depends(get_current_user)):
    """Create a warehouse"""
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    new_warehouse = Warehouse(**warehouse.model_dump())
    await db.warehouses.insert_one(new_warehouse.model_dump())
    return new_warehouse

@api_router.put("/warehouses/{warehouse_id}", response_model=Warehouse)
async def update_warehouse(warehouse_id: str, warehouse: WarehouseCreate, user: User = Depends(get_current_user)):
    """Update a warehouse"""
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.warehouses.update_one(
        {"warehouse_id": warehouse_id},
        {"$set": warehouse.model_dump()}
    )
    updated = await db.warehouses.find_one({"warehouse_id": warehouse_id}, {"_id": 0})
    if not updated:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return Warehouse(**updated)

@api_router.delete("/warehouses/{warehouse_id}")
async def delete_warehouse(warehouse_id: str, user: User = Depends(get_current_user)):
    """Delete a warehouse (soft delete)"""
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.warehouses.update_one(
        {"warehouse_id": warehouse_id},
        {"$set": {"is_active": False}}
    )
    return {"message": "Warehouse deleted"}

# ========================
# PRODUCT ENDPOINTS
# ========================

@api_router.get("/products", response_model=List[Product])
async def get_products(
    category: Optional[ProductCategory] = None,
    supplier_id: Optional[str] = None,
    low_stock: bool = False,
    user: User = Depends(get_current_user)
):
    """Get all products with optional filters"""
    query = {"is_active": True}
    if category:
        query["category"] = category.value
    if supplier_id:
        query["default_supplier_id"] = supplier_id
    
    products = await db.products.find(query, {"_id": 0}).to_list(1000)
    result = [Product(**p) for p in products]
    
    if low_stock:
        result = [p for p in result if await is_low_stock(p.product_id, p.reorder_level)]
    
    return result

async def is_low_stock(product_id: str, reorder_level: int) -> bool:
    """Check if product is low on stock"""
    stocks = await db.inventory_stock.find({"product_id": product_id}, {"_id": 0}).to_list(100)
    total_qty = sum(s.get("quantity", 0) for s in stocks)
    return total_qty <= reorder_level

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str, user: User = Depends(get_current_user)):
    """Get a single product"""
    product = await db.products.find_one({"product_id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.post("/products", response_model=Product)
async def create_product(product: ProductCreate, user: User = Depends(get_current_user)):
    """Create a product"""
    existing = await db.products.find_one({"sku": product.sku}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    new_product = Product(**product.model_dump())
    await db.products.insert_one(new_product.model_dump())
    return new_product

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, update: ProductUpdate, user: User = Depends(get_current_user)):
    """Update a product"""
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await db.products.update_one({"product_id": product_id}, {"$set": update_data})
    
    product = await db.products.find_one({"product_id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, user: User = Depends(get_current_user)):
    """Delete a product (soft delete)"""
    await db.products.update_one(
        {"product_id": product_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
    )
    return {"message": "Product deleted"}

# ========================
# INVENTORY ENDPOINTS
# ========================

@api_router.get("/inventory")
async def get_inventory(
    warehouse_id: Optional[str] = None,
    product_id: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Get inventory stock levels"""
    query = {}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if product_id:
        query["product_id"] = product_id
    
    stocks = await db.inventory_stock.find(query, {"_id": 0}).to_list(1000)
    
    # Enrich with product info
    result = []
    for stock in stocks:
        product = await db.products.find_one({"product_id": stock["product_id"]}, {"_id": 0})
        warehouse = await db.warehouses.find_one({"warehouse_id": stock["warehouse_id"]}, {"_id": 0})
        stock["product_name"] = product["name"] if product else "Unknown"
        stock["product_sku"] = product["sku"] if product else "Unknown"
        stock["warehouse_name"] = warehouse["name"] if warehouse else "Unknown"
        stock["cost_price"] = product["cost_price"] if product else 0
        stock["reorder_level"] = product["reorder_level"] if product else 0
        result.append(stock)
    
    return result

@api_router.post("/inventory/adjust")
async def adjust_inventory(adjustment: StockTransactionCreate, user: User = Depends(get_current_user)):
    """Adjust inventory (damage, return, conversion)"""
    # Find or create stock record
    stock = await db.inventory_stock.find_one({
        "product_id": adjustment.product_id,
        "warehouse_id": adjustment.warehouse_id
    }, {"_id": 0})
    
    if stock:
        new_qty = stock["quantity"] + adjustment.quantity
        await db.inventory_stock.update_one(
            {"stock_id": stock["stock_id"]},
            {"$set": {"quantity": new_qty, "last_updated": datetime.now(timezone.utc)}}
        )
    else:
        new_stock = InventoryStock(
            product_id=adjustment.product_id,
            warehouse_id=adjustment.warehouse_id,
            quantity=adjustment.quantity
        )
        await db.inventory_stock.insert_one(new_stock.model_dump())
    
    # Record transaction
    transaction = StockTransaction(
        **adjustment.model_dump(),
        created_by=user.user_id
    )
    await db.stock_transactions.insert_one(transaction.model_dump())
    
    return {"message": "Inventory adjusted", "transaction_id": transaction.transaction_id}

@api_router.get("/inventory/transactions")
async def get_stock_transactions(
    product_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    limit: int = 100,
    user: User = Depends(get_current_user)
):
    """Get stock transaction history"""
    query = {}
    if product_id:
        query["product_id"] = product_id
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    
    transactions = await db.stock_transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return transactions

@api_router.get("/inventory/low-stock")
async def get_low_stock_items(user: User = Depends(get_current_user)):
    """Get products that are low on stock"""
    products = await db.products.find({"is_active": True}, {"_id": 0}).to_list(1000)
    low_stock_items = []
    
    for product in products:
        stocks = await db.inventory_stock.find({"product_id": product["product_id"]}, {"_id": 0}).to_list(100)
        total_qty = sum(s.get("quantity", 0) for s in stocks)
        if total_qty <= product.get("reorder_level", 10):
            low_stock_items.append({
                "product_id": product["product_id"],
                "name": product["name"],
                "sku": product["sku"],
                "current_stock": total_qty,
                "reorder_level": product.get("reorder_level", 10)
            })
    
    return low_stock_items

# ========================
# SUPPLIER ENDPOINTS
# ========================

@api_router.get("/suppliers", response_model=List[Supplier])
async def get_suppliers(user: User = Depends(get_current_user)):
    """Get all suppliers"""
    suppliers = await db.suppliers.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return [Supplier(**s) for s in suppliers]

@api_router.get("/suppliers/{supplier_id}", response_model=Supplier)
async def get_supplier(supplier_id: str, user: User = Depends(get_current_user)):
    """Get a single supplier"""
    supplier = await db.suppliers.find_one({"supplier_id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return Supplier(**supplier)

@api_router.post("/suppliers", response_model=Supplier)
async def create_supplier(supplier: SupplierCreate, user: User = Depends(get_current_user)):
    """Create a supplier"""
    new_supplier = Supplier(**supplier.model_dump())
    await db.suppliers.insert_one(new_supplier.model_dump())
    return new_supplier

@api_router.put("/suppliers/{supplier_id}", response_model=Supplier)
async def update_supplier(supplier_id: str, update: SupplierUpdate, user: User = Depends(get_current_user)):
    """Update a supplier"""
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await db.suppliers.update_one({"supplier_id": supplier_id}, {"$set": update_data})
    
    supplier = await db.suppliers.find_one({"supplier_id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return Supplier(**supplier)

@api_router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, user: User = Depends(get_current_user)):
    """Delete a supplier (soft delete)"""
    await db.suppliers.update_one(
        {"supplier_id": supplier_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
    )
    return {"message": "Supplier deleted"}

# ========================
# DISTRIBUTOR ENDPOINTS
# ========================

@api_router.get("/distributors", response_model=List[Distributor])
async def get_distributors(user: User = Depends(get_current_user)):
    """Get all distributors"""
    distributors = await db.distributors.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return [Distributor(**d) for d in distributors]

@api_router.get("/distributors/{distributor_id}", response_model=Distributor)
async def get_distributor(distributor_id: str, user: User = Depends(get_current_user)):
    """Get a single distributor"""
    distributor = await db.distributors.find_one({"distributor_id": distributor_id}, {"_id": 0})
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
    return Distributor(**distributor)

@api_router.post("/distributors", response_model=Distributor)
async def create_distributor(distributor: DistributorCreate, user: User = Depends(get_current_user)):
    """Create a distributor"""
    new_distributor = Distributor(**distributor.model_dump())
    await db.distributors.insert_one(new_distributor.model_dump())
    return new_distributor

@api_router.put("/distributors/{distributor_id}", response_model=Distributor)
async def update_distributor(distributor_id: str, update: DistributorUpdate, user: User = Depends(get_current_user)):
    """Update a distributor"""
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await db.distributors.update_one({"distributor_id": distributor_id}, {"$set": update_data})
    
    distributor = await db.distributors.find_one({"distributor_id": distributor_id}, {"_id": 0})
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
    return Distributor(**distributor)

@api_router.delete("/distributors/{distributor_id}")
async def delete_distributor(distributor_id: str, user: User = Depends(get_current_user)):
    """Delete a distributor (soft delete)"""
    await db.distributors.update_one(
        {"distributor_id": distributor_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
    )
    return {"message": "Distributor deleted"}

# ========================
# PURCHASE ORDER ENDPOINTS
# ========================

async def generate_po_number():
    """Generate unique PO number"""
    count = await db.purchase_orders.count_documents({})
    return f"PO-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"

@api_router.get("/purchase-orders")
async def get_purchase_orders(
    status: Optional[OrderStatus] = None,
    supplier_id: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Get all purchase orders"""
    query = {}
    if status:
        query["status"] = status.value
    if supplier_id:
        query["supplier_id"] = supplier_id
    
    orders = await db.purchase_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return orders

@api_router.get("/purchase-orders/{po_id}")
async def get_purchase_order(po_id: str, user: User = Depends(get_current_user)):
    """Get a single purchase order"""
    po = await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@api_router.post("/purchase-orders")
async def create_purchase_order(po_data: PurchaseOrderCreate, user: User = Depends(get_current_user)):
    """Create a purchase order"""
    supplier = await db.suppliers.find_one({"supplier_id": po_data.supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Build items with product names
    items = []
    subtotal = 0.0
    for item in po_data.items:
        product = await db.products.find_one({"product_id": item.product_id}, {"_id": 0})
        po_item = PurchaseOrderItem(
            product_id=item.product_id,
            product_name=product["name"] if product else "Unknown",
            quantity=item.quantity,
            unit_price=item.unit_price
        )
        items.append(po_item.model_dump())
        subtotal += item.quantity * item.unit_price
    
    po = PurchaseOrder(
        po_number=await generate_po_number(),
        supplier_id=po_data.supplier_id,
        supplier_name=supplier["name"],
        warehouse_id=po_data.warehouse_id,
        expected_date=po_data.expected_date,
        items=items,
        subtotal=subtotal,
        tax_amount=po_data.tax_amount,
        total_amount=subtotal + po_data.tax_amount,
        notes=po_data.notes,
        created_by=user.user_id
    )
    
    await db.purchase_orders.insert_one(po.model_dump())
    return po.model_dump()

@api_router.put("/purchase-orders/{po_id}")
async def update_purchase_order(po_id: str, update: PurchaseOrderUpdate, user: User = Depends(get_current_user)):
    """Update a purchase order"""
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Handle status change to "received"
        if update.status == OrderStatus.RECEIVED:
            po = await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})
            if po:
                for item in po.get("items", []):
                    # Update inventory
                    stock = await db.inventory_stock.find_one({
                        "product_id": item["product_id"],
                        "warehouse_id": po["warehouse_id"]
                    }, {"_id": 0})
                    
                    if stock:
                        new_qty = stock["quantity"] + item["quantity"]
                        await db.inventory_stock.update_one(
                            {"stock_id": stock["stock_id"]},
                            {"$set": {"quantity": new_qty, "last_updated": datetime.now(timezone.utc)}}
                        )
                    else:
                        new_stock = InventoryStock(
                            product_id=item["product_id"],
                            warehouse_id=po["warehouse_id"],
                            quantity=item["quantity"]
                        )
                        await db.inventory_stock.insert_one(new_stock.model_dump())
                    
                    # Record transaction
                    transaction = StockTransaction(
                        product_id=item["product_id"],
                        warehouse_id=po["warehouse_id"],
                        type=TransactionType.PURCHASE,
                        quantity=item["quantity"],
                        reference_id=po_id,
                        created_by=user.user_id
                    )
                    await db.stock_transactions.insert_one(transaction.model_dump())
        
        await db.purchase_orders.update_one({"po_id": po_id}, {"$set": update_data})
    
    return await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})

@api_router.delete("/purchase-orders/{po_id}")
async def delete_purchase_order(po_id: str, user: User = Depends(get_current_user)):
    """Cancel a purchase order"""
    po = await db.purchase_orders.find_one({"po_id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po["status"] != OrderStatus.DRAFT.value:
        raise HTTPException(status_code=400, detail="Can only cancel draft orders")
    
    await db.purchase_orders.update_one(
        {"po_id": po_id},
        {"$set": {"status": OrderStatus.CANCELLED.value, "updated_at": datetime.now(timezone.utc)}}
    )
    return {"message": "Purchase order cancelled"}

# ========================
# SALES ORDER ENDPOINTS
# ========================

async def generate_so_number():
    """Generate unique SO number"""
    count = await db.sales_orders.count_documents({})
    return f"SO-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"

@api_router.get("/sales-orders")
async def get_sales_orders(
    status: Optional[OrderStatus] = None,
    distributor_id: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Get all sales orders"""
    query = {}
    if status:
        query["status"] = status.value
    if distributor_id:
        query["distributor_id"] = distributor_id
    
    orders = await db.sales_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return orders

@api_router.get("/sales-orders/{so_id}")
async def get_sales_order(so_id: str, user: User = Depends(get_current_user)):
    """Get a single sales order"""
    so = await db.sales_orders.find_one({"so_id": so_id}, {"_id": 0})
    if not so:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return so

@api_router.post("/sales-orders")
async def create_sales_order(so_data: SalesOrderCreate, user: User = Depends(get_current_user)):
    """Create a sales order"""
    distributor = await db.distributors.find_one({"distributor_id": so_data.distributor_id}, {"_id": 0})
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
    
    # Build items with product names
    items = []
    subtotal = 0.0
    for item in so_data.items:
        product = await db.products.find_one({"product_id": item.product_id}, {"_id": 0})
        so_item = SalesOrderItem(
            product_id=item.product_id,
            product_name=product["name"] if product else "Unknown",
            quantity=item.quantity,
            unit_price=item.unit_price
        )
        items.append(so_item.model_dump())
        subtotal += item.quantity * item.unit_price
    
    so = SalesOrder(
        so_number=await generate_so_number(),
        distributor_id=so_data.distributor_id,
        distributor_name=distributor["name"],
        warehouse_id=so_data.warehouse_id,
        delivery_date=so_data.delivery_date,
        items=items,
        subtotal=subtotal,
        tax_amount=so_data.tax_amount,
        total_amount=subtotal + so_data.tax_amount,
        notes=so_data.notes,
        created_by=user.user_id
    )
    
    await db.sales_orders.insert_one(so.model_dump())
    return so.model_dump()

@api_router.put("/sales-orders/{so_id}")
async def update_sales_order(so_id: str, update: SalesOrderUpdate, user: User = Depends(get_current_user)):
    """Update a sales order"""
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Handle status change to "delivered"
        if update.status == OrderStatus.DELIVERED:
            so = await db.sales_orders.find_one({"so_id": so_id}, {"_id": 0})
            if so:
                for item in so.get("items", []):
                    # Update inventory (reduce stock)
                    stock = await db.inventory_stock.find_one({
                        "product_id": item["product_id"],
                        "warehouse_id": so["warehouse_id"]
                    }, {"_id": 0})
                    
                    if stock:
                        new_qty = stock["quantity"] - item["quantity"]
                        await db.inventory_stock.update_one(
                            {"stock_id": stock["stock_id"]},
                            {"$set": {"quantity": max(0, new_qty), "last_updated": datetime.now(timezone.utc)}}
                        )
                    
                    # Record transaction
                    transaction = StockTransaction(
                        product_id=item["product_id"],
                        warehouse_id=so["warehouse_id"],
                        type=TransactionType.SALE,
                        quantity=-item["quantity"],
                        reference_id=so_id,
                        created_by=user.user_id
                    )
                    await db.stock_transactions.insert_one(transaction.model_dump())
        
        await db.sales_orders.update_one({"so_id": so_id}, {"$set": update_data})
    
    return await db.sales_orders.find_one({"so_id": so_id}, {"_id": 0})

@api_router.delete("/sales-orders/{so_id}")
async def delete_sales_order(so_id: str, user: User = Depends(get_current_user)):
    """Cancel a sales order"""
    so = await db.sales_orders.find_one({"so_id": so_id}, {"_id": 0})
    if not so:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    if so["status"] != OrderStatus.DRAFT.value:
        raise HTTPException(status_code=400, detail="Can only cancel draft orders")
    
    await db.sales_orders.update_one(
        {"so_id": so_id},
        {"$set": {"status": OrderStatus.CANCELLED.value, "updated_at": datetime.now(timezone.utc)}}
    )
    return {"message": "Sales order cancelled"}

# ========================
# INVOICE ENDPOINTS
# ========================

async def generate_invoice_number(inv_type: InvoiceType):
    """Generate unique invoice number"""
    prefix = "PI" if inv_type == InvoiceType.PURCHASE else "SI"
    count = await db.invoices.count_documents({"type": inv_type.value})
    return f"{prefix}-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"

@api_router.get("/invoices")
async def get_invoices(
    type: Optional[InvoiceType] = None,
    status: Optional[InvoiceStatus] = None,
    user: User = Depends(get_current_user)
):
    """Get all invoices"""
    query = {}
    if type:
        query["type"] = type.value
    if status:
        query["status"] = status.value
    
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return invoices

@api_router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, user: User = Depends(get_current_user)):
    """Get a single invoice"""
    invoice = await db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@api_router.post("/invoices")
async def create_invoice(invoice_data: InvoiceCreate, user: User = Depends(get_current_user)):
    """Create an invoice"""
    # Get party name
    party_name = "Unknown"
    if invoice_data.type == InvoiceType.PURCHASE:
        supplier = await db.suppliers.find_one({"supplier_id": invoice_data.party_id}, {"_id": 0})
        party_name = supplier["name"] if supplier else "Unknown"
    else:
        distributor = await db.distributors.find_one({"distributor_id": invoice_data.party_id}, {"_id": 0})
        party_name = distributor["name"] if distributor else "Unknown"
    
    invoice = Invoice(
        invoice_number=await generate_invoice_number(invoice_data.type),
        type=invoice_data.type,
        reference_id=invoice_data.reference_id,
        party_id=invoice_data.party_id,
        party_name=party_name,
        due_date=invoice_data.due_date,
        subtotal=invoice_data.subtotal,
        tax_amount=invoice_data.tax_amount,
        total=invoice_data.subtotal + invoice_data.tax_amount
    )
    
    await db.invoices.insert_one(invoice.model_dump())
    return invoice.model_dump()

# ========================
# PAYMENT ENDPOINTS
# ========================

@api_router.get("/payments")
async def get_payments(invoice_id: Optional[str] = None, user: User = Depends(get_current_user)):
    """Get all payments"""
    query = {}
    if invoice_id:
        query["invoice_id"] = invoice_id
    
    payments = await db.payments.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return payments

@api_router.post("/payments")
async def create_payment(payment_data: PaymentCreate, user: User = Depends(get_current_user)):
    """Record a payment"""
    invoice = await db.invoices.find_one({"invoice_id": payment_data.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    payment = Payment(
        **payment_data.model_dump(),
        created_by=user.user_id
    )
    await db.payments.insert_one(payment.model_dump())
    
    # Update invoice paid amount
    new_paid = invoice.get("paid_amount", 0) + payment_data.amount
    new_status = InvoiceStatus.PAID if new_paid >= invoice["total"] else InvoiceStatus.PARTIAL
    
    await db.invoices.update_one(
        {"invoice_id": payment_data.invoice_id},
        {"$set": {"paid_amount": new_paid, "status": new_status.value}}
    )
    
    return payment.model_dump()

# ========================
# CHART OF ACCOUNTS ENDPOINTS
# ========================

@api_router.get("/accounts")
async def get_accounts(type: Optional[AccountType] = None, user: User = Depends(get_current_user)):
    """Get chart of accounts"""
    query = {"is_active": True}
    if type:
        query["type"] = type.value
    
    accounts = await db.chart_of_accounts.find(query, {"_id": 0}).to_list(1000)
    return accounts

@api_router.post("/accounts")
async def create_account(account_data: ChartOfAccountCreate, user: User = Depends(get_current_user)):
    """Create an account"""
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.MANAGER, UserRole.ACCOUNTANT]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    existing = await db.chart_of_accounts.find_one({"code": account_data.code}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Account code already exists")
    
    account = ChartOfAccount(**account_data.model_dump())
    await db.chart_of_accounts.insert_one(account.model_dump())
    return account.model_dump()

# ========================
# DASHBOARD ENDPOINTS
# ========================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: User = Depends(get_current_user)):
    """Get dashboard statistics"""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Count totals
    total_products = await db.products.count_documents({"is_active": True})
    total_suppliers = await db.suppliers.count_documents({"is_active": True})
    total_distributors = await db.distributors.count_documents({"is_active": True})
    total_warehouses = await db.warehouses.count_documents({"is_active": True})
    
    # Calculate inventory value
    inventory = await db.inventory_stock.find({}, {"_id": 0}).to_list(10000)
    total_inventory_value = 0.0
    for stock in inventory:
        product = await db.products.find_one({"product_id": stock["product_id"]}, {"_id": 0})
        if product:
            total_inventory_value += stock.get("quantity", 0) * product.get("cost_price", 0)
    
    # Count low stock items
    low_stock_items = await get_low_stock_items(user)
    low_stock_count = len(low_stock_items)
    
    # Today's sales
    today_sales_orders = await db.sales_orders.find({
        "order_date": {"$gte": today}
    }, {"_id": 0}).to_list(1000)
    today_sales = sum(so.get("total_amount", 0) for so in today_sales_orders)
    
    # Today's purchases
    today_purchase_orders = await db.purchase_orders.find({
        "order_date": {"$gte": today}
    }, {"_id": 0}).to_list(1000)
    today_purchases = sum(po.get("total_amount", 0) for po in today_purchase_orders)
    
    # Pending invoices
    pending_invoices = await db.invoices.count_documents({
        "status": {"$in": [InvoiceStatus.UNPAID.value, InvoiceStatus.PARTIAL.value]}
    })
    
    # Cash balance (simplified - sum of all payments minus purchase payments)
    all_payments = await db.payments.find({}, {"_id": 0}).to_list(10000)
    cash_balance = 0.0
    for payment in all_payments:
        invoice = await db.invoices.find_one({"invoice_id": payment["invoice_id"]}, {"_id": 0})
        if invoice:
            if invoice["type"] == InvoiceType.SALE.value:
                cash_balance += payment["amount"]
            else:
                cash_balance -= payment["amount"]
    
    return DashboardStats(
        total_inventory_value=round(total_inventory_value, 2),
        low_stock_count=low_stock_count,
        today_sales=round(today_sales, 2),
        today_purchases=round(today_purchases, 2),
        cash_balance=round(cash_balance, 2),
        pending_invoices=pending_invoices,
        total_products=total_products,
        total_suppliers=total_suppliers,
        total_distributors=total_distributors,
        total_warehouses=total_warehouses
    )

@api_router.get("/dashboard/recent-activity")
async def get_recent_activity(limit: int = 10, user: User = Depends(get_current_user)):
    """Get recent activity feed"""
    activities = []
    
    # Recent purchase orders
    recent_pos = await db.purchase_orders.find({}, {"_id": 0}).sort("created_at", -1).to_list(5)
    for po in recent_pos:
        activities.append({
            "type": "purchase_order",
            "title": f"PO {po['po_number']}",
            "description": f"Created for {po.get('supplier_name', 'Unknown')}",
            "amount": po.get("total_amount", 0),
            "status": po.get("status"),
            "timestamp": po.get("created_at")
        })
    
    # Recent sales orders
    recent_sos = await db.sales_orders.find({}, {"_id": 0}).sort("created_at", -1).to_list(5)
    for so in recent_sos:
        activities.append({
            "type": "sales_order",
            "title": f"SO {so['so_number']}",
            "description": f"Created for {so.get('distributor_name', 'Unknown')}",
            "amount": so.get("total_amount", 0),
            "status": so.get("status"),
            "timestamp": so.get("created_at")
        })
    
    # Recent stock transactions
    recent_txns = await db.stock_transactions.find({}, {"_id": 0}).sort("created_at", -1).to_list(5)
    for txn in recent_txns:
        product = await db.products.find_one({"product_id": txn["product_id"]}, {"_id": 0})
        activities.append({
            "type": "stock_transaction",
            "title": f"Stock {txn['type']}",
            "description": f"{product['name'] if product else 'Unknown'}: {txn['quantity']} units",
            "amount": None,
            "status": txn.get("type"),
            "timestamp": txn.get("created_at")
        })
    
    # Sort by timestamp and return top N
    activities.sort(key=lambda x: x.get("timestamp") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return activities[:limit]

@api_router.get("/dashboard/sales-chart")
async def get_sales_chart(days: int = 7, user: User = Depends(get_current_user)):
    """Get sales vs purchases chart data"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    chart_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        next_date = date + timedelta(days=1)
        
        # Sales for the day
        day_sales = await db.sales_orders.find({
            "order_date": {"$gte": date, "$lt": next_date}
        }, {"_id": 0}).to_list(1000)
        total_sales = sum(so.get("total_amount", 0) for so in day_sales)
        
        # Purchases for the day
        day_purchases = await db.purchase_orders.find({
            "order_date": {"$gte": date, "$lt": next_date}
        }, {"_id": 0}).to_list(1000)
        total_purchases = sum(po.get("total_amount", 0) for po in day_purchases)
        
        chart_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "sales": round(total_sales, 2),
            "purchases": round(total_purchases, 2)
        })
    
    return chart_data

@api_router.get("/dashboard/top-products")
async def get_top_products(limit: int = 5, user: User = Depends(get_current_user)):
    """Get top selling products"""
    # Aggregate sales by product
    product_sales = {}
    
    sales_orders = await db.sales_orders.find({}, {"_id": 0}).to_list(1000)
    for so in sales_orders:
        for item in so.get("items", []):
            pid = item["product_id"]
            if pid not in product_sales:
                product_sales[pid] = {"quantity": 0, "revenue": 0}
            product_sales[pid]["quantity"] += item.get("quantity", 0)
            product_sales[pid]["revenue"] += item.get("quantity", 0) * item.get("unit_price", 0)
    
    # Sort and get top products
    sorted_products = sorted(product_sales.items(), key=lambda x: x[1]["revenue"], reverse=True)[:limit]
    
    result = []
    for pid, data in sorted_products:
        product = await db.products.find_one({"product_id": pid}, {"_id": 0})
        if product:
            result.append({
                "product_id": pid,
                "name": product["name"],
                "sku": product["sku"],
                "quantity_sold": data["quantity"],
                "revenue": round(data["revenue"], 2)
            })
    
    return result

# ========================
# NOTIFICATIONS ENDPOINTS
# ========================

@api_router.get("/notifications")
async def get_notifications(unread_only: bool = False, user: User = Depends(get_current_user)):
    """Get user notifications"""
    query = {"user_id": user.user_id}
    if unread_only:
        query["is_read"] = False
    
    notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return notifications

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: User = Depends(get_current_user)):
    """Mark notification as read"""
    await db.notifications.update_one(
        {"notification_id": notification_id, "user_id": user.user_id},
        {"$set": {"is_read": True}}
    )
    return {"message": "Notification marked as read"}

@api_router.put("/notifications/read-all")
async def mark_all_notifications_read(user: User = Depends(get_current_user)):
    """Mark all notifications as read"""
    await db.notifications.update_many(
        {"user_id": user.user_id},
        {"$set": {"is_read": True}}
    )
    return {"message": "All notifications marked as read"}

# ========================
# REPORTS ENDPOINTS
# ========================

@api_router.get("/reports/stock-summary")
async def get_stock_summary_report(warehouse_id: Optional[str] = None, user: User = Depends(get_current_user)):
    """Get stock summary report"""
    query = {}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    
    stocks = await db.inventory_stock.find(query, {"_id": 0}).to_list(10000)
    
    report = []
    for stock in stocks:
        product = await db.products.find_one({"product_id": stock["product_id"]}, {"_id": 0})
        warehouse = await db.warehouses.find_one({"warehouse_id": stock["warehouse_id"]}, {"_id": 0})
        
        if product:
            report.append({
                "product_id": stock["product_id"],
                "product_name": product["name"],
                "sku": product["sku"],
                "category": product.get("category"),
                "warehouse_id": stock["warehouse_id"],
                "warehouse_name": warehouse["name"] if warehouse else "Unknown",
                "quantity": stock.get("quantity", 0),
                "unit": product.get("unit", "pcs"),
                "cost_price": product.get("cost_price", 0),
                "value": round(stock.get("quantity", 0) * product.get("cost_price", 0), 2),
                "reorder_level": product.get("reorder_level", 0),
                "is_low_stock": stock.get("quantity", 0) <= product.get("reorder_level", 0)
            })
    
    return report

@api_router.get("/reports/purchase-analysis")
async def get_purchase_analysis_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Get purchase analysis report"""
    query = {}
    if start_date:
        query["order_date"] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        if "order_date" in query:
            query["order_date"]["$lte"] = datetime.fromisoformat(end_date)
        else:
            query["order_date"] = {"$lte": datetime.fromisoformat(end_date)}
    
    orders = await db.purchase_orders.find(query, {"_id": 0}).to_list(10000)
    
    # Aggregate by supplier
    by_supplier = {}
    for order in orders:
        sid = order["supplier_id"]
        if sid not in by_supplier:
            by_supplier[sid] = {
                "supplier_name": order.get("supplier_name", "Unknown"),
                "order_count": 0,
                "total_amount": 0
            }
        by_supplier[sid]["order_count"] += 1
        by_supplier[sid]["total_amount"] += order.get("total_amount", 0)
    
    return {
        "total_orders": len(orders),
        "total_amount": round(sum(o.get("total_amount", 0) for o in orders), 2),
        "by_supplier": list(by_supplier.values())
    }

@api_router.get("/reports/sales-analysis")
async def get_sales_analysis_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Get sales analysis report"""
    query = {}
    if start_date:
        query["order_date"] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        if "order_date" in query:
            query["order_date"]["$lte"] = datetime.fromisoformat(end_date)
        else:
            query["order_date"] = {"$lte": datetime.fromisoformat(end_date)}
    
    orders = await db.sales_orders.find(query, {"_id": 0}).to_list(10000)
    
    # Aggregate by distributor
    by_distributor = {}
    for order in orders:
        did = order["distributor_id"]
        if did not in by_distributor:
            by_distributor[did] = {
                "distributor_name": order.get("distributor_name", "Unknown"),
                "order_count": 0,
                "total_amount": 0
            }
        by_distributor[did]["order_count"] += 1
        by_distributor[did]["total_amount"] += order.get("total_amount", 0)
    
    return {
        "total_orders": len(orders),
        "total_amount": round(sum(o.get("total_amount", 0) for o in orders), 2),
        "by_distributor": list(by_distributor.values())
    }

# ========================
# AUDIT LOG ENDPOINTS
# ========================

@api_router.get("/audit-logs")
async def get_audit_logs(
    entity_type: Optional[str] = None,
    limit: int = 100,
    user: User = Depends(get_current_user)
):
    """Get audit logs (admin only)"""
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return logs

# ========================
# HEALTH CHECK
# ========================

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    """Initialize database indexes"""
    # Create indexes for better performance
    await db.products.create_index("sku", unique=True)
    await db.products.create_index("barcode")
    await db.products.create_index("category")
    await db.inventory_stock.create_index([("product_id", 1), ("warehouse_id", 1)])
    await db.purchase_orders.create_index("po_number", unique=True)
    await db.sales_orders.create_index("so_number", unique=True)
    await db.invoices.create_index("invoice_number", unique=True)
    await db.users.create_index("email", unique=True)
    await db.user_sessions.create_index("session_token")
    logger.info("Database indexes created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
