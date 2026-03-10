# BizCore - Business Management Application

## Product Requirements Document (PRD)

### Overview
BizCore is a comprehensive, mobile-first ERP-style business management application designed for SMEs in manufacturing, trading, or distribution. It provides real-time visibility into all critical business operations with role-based access control.

### Target Users
- Business Owners / Super Admins
- Department Managers
- Purchase Clerks
- Sales Executives
- Accountants
- Viewers (Read-only access)

### Core Modules

#### 1. Dashboard (Home Screen)
- KPI cards: Total Inventory Value, Low Stock Items, Today's Sales/Purchases, Cash Balance, Pending Invoices
- Charts: Sales vs Purchases (7/30 days), Top Products, Stock Trend
- Quick alerts: Low raw materials, Overdue payments
- Recent activity feed

#### 2. Admin Module
- User Management: Add/edit users, assign roles
- Role-based Access Control (RBAC)
- Company Profile settings
- Audit Logs

#### 3. Inventory Module
- Product Catalog (Raw Materials, Finished Goods, Packaging)
- Multi-warehouse stock management
- Stock movements tracking
- Low stock alerts
- Barcode support

#### 4. Suppliers Module
- Supplier Directory
- Performance tracking
- Contact integration

#### 5. Distributors Module
- Distributor/Customer Directory
- Territory/Region assignment
- Credit management

#### 6. Purchases Module
- Purchase Orders (PO)
- Status tracking (Draft → Ordered → Received → Paid)
- Goods Receipt Notes

#### 7. Sales Module
- Sales Orders (SO)
- Invoice generation
- Delivery tracking

#### 8. Finance Module
- Chart of Accounts
- Accounts Receivable/Payable
- Payment tracking
- Basic reports (P&L, Balance Sheet)

#### 9. Reports Module
- Stock Summary
- Purchase/Sales Analysis
- Supplier/Distributor performance
- Financial reports

### Technical Stack
- **Frontend**: Expo React Native (iOS/Android/Web)
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: Emergent Google OAuth

### Design Theme
- Dark professional theme
- Mobile-first responsive design
- Touch-friendly UI elements

### Database Collections
1. users
2. user_sessions
3. roles
4. companies
5. warehouses
6. products
7. inventory_stock
8. stock_transactions
9. suppliers
10. distributors
11. purchase_orders
12. purchase_order_items
13. sales_orders
14. sales_order_items
15. invoices
16. payments
17. chart_of_accounts
18. journal_entries
19. notifications
20. audit_logs
