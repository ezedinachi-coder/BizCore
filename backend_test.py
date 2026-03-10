#!/usr/bin/env python3
"""
BizCore Backend API Testing Suite
Tests all major API endpoints with authentication
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional, List

# Configuration
BASE_URL = "https://biz-command-23.preview.emergentagent.com/api"
SESSION_TOKEN = "test_session_1773136094446"

class BizCoreAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session_token = SESSION_TOKEN
        self.headers = {
            "Authorization": f"Bearer {SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
        self.test_results = []
        self.created_resources = {
            'products': [],
            'suppliers': [],
            'distributors': [],
            'warehouses': [],
            'purchase_orders': [],
            'sales_orders': []
        }
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            'test_name': test_name,
            'passed': passed,
            'details': details
        })
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> tuple[bool, Dict[str, Any], str]:
        """Make HTTP request and return success status, response data, and error message"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=30)
            else:
                return False, {}, f"Unsupported method: {method}"
            
            if response.status_code >= 200 and response.status_code < 300:
                try:
                    return True, response.json(), ""
                except json.JSONDecodeError:
                    return True, {"text": response.text}, ""
            else:
                return False, {}, f"HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.RequestException as e:
            return False, {}, f"Request failed: {str(e)}"
    
    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication...")
        
        # Test GET /auth/me
        success, data, error = self.make_request("GET", "/auth/me")
        if success and "user_id" in data:
            self.log_result("GET /auth/me", True, f"Authenticated as: {data.get('email', 'Unknown')}")
            return True
        else:
            self.log_result("GET /auth/me", False, error)
            return False
    
    def test_dashboard_endpoints(self):
        """Test dashboard endpoints"""
        print("\n📊 Testing Dashboard...")
        
        # Test dashboard stats
        success, data, error = self.make_request("GET", "/dashboard/stats")
        self.log_result("GET /dashboard/stats", success, 
                       f"Stats returned: {list(data.keys()) if success else error}")
        
        # Test recent activity
        success, data, error = self.make_request("GET", "/dashboard/recent-activity")
        self.log_result("GET /dashboard/recent-activity", success,
                       f"Activity items: {len(data) if success and isinstance(data, list) else error}")
        
        # Test sales chart
        success, data, error = self.make_request("GET", "/dashboard/sales-chart", params={"days": 7})
        self.log_result("GET /dashboard/sales-chart", success,
                       f"Chart data points: {len(data) if success and isinstance(data, list) else error}")
        
        # Test top products
        success, data, error = self.make_request("GET", "/dashboard/top-products")
        self.log_result("GET /dashboard/top-products", success,
                       f"Top products: {len(data) if success and isinstance(data, list) else error}")
    
    def test_warehouse_operations(self):
        """Test warehouse endpoints and create test warehouse"""
        print("\n🏭 Testing Warehouses...")
        
        # Get existing warehouses
        success, data, error = self.make_request("GET", "/warehouses")
        self.log_result("GET /warehouses", success,
                       f"Found warehouses: {len(data) if success and isinstance(data, list) else error}")
        
        # Create a test warehouse
        warehouse_data = {
            "name": "Test Warehouse Alpha",
            "address": "123 Industrial Blvd, Test City, TC 12345",
            "capacity": 10000.0
        }
        
        success, data, error = self.make_request("POST", "/warehouses", warehouse_data)
        if success and "warehouse_id" in data:
            warehouse_id = data["warehouse_id"]
            self.created_resources['warehouses'].append(warehouse_id)
            self.log_result("POST /warehouses", True, f"Created warehouse: {warehouse_id}")
            return warehouse_id
        else:
            self.log_result("POST /warehouses", False, error)
            return None
    
    def test_supplier_operations(self):
        """Test supplier endpoints"""
        print("\n🚛 Testing Suppliers...")
        
        # Get existing suppliers
        success, data, error = self.make_request("GET", "/suppliers")
        self.log_result("GET /suppliers", success,
                       f"Found suppliers: {len(data) if success and isinstance(data, list) else error}")
        
        # Create a test supplier
        supplier_data = {
            "name": "Acme Manufacturing Co.",
            "contact_person": "John Smith",
            "phone": "+1-555-0123",
            "email": "john.smith@acme-mfg.com",
            "address": "456 Factory Road, Manufacturing City, MC 67890",
            "payment_terms_days": 30,
            "tax_id": "TAX-123456789"
        }
        
        success, data, error = self.make_request("POST", "/suppliers", supplier_data)
        if success and "supplier_id" in data:
            supplier_id = data["supplier_id"]
            self.created_resources['suppliers'].append(supplier_id)
            self.log_result("POST /suppliers", True, f"Created supplier: {supplier_id}")
            
            # Test supplier update
            update_data = {"rating": 4.5}
            success, data, error = self.make_request("PUT", f"/suppliers/{supplier_id}", update_data)
            self.log_result("PUT /suppliers/{id}", success, error if not success else "Updated supplier rating")
            
            return supplier_id
        else:
            self.log_result("POST /suppliers", False, error)
            return None
    
    def test_distributor_operations(self):
        """Test distributor endpoints"""
        print("\n🚚 Testing Distributors...")
        
        # Get existing distributors
        success, data, error = self.make_request("GET", "/distributors")
        self.log_result("GET /distributors", success,
                       f"Found distributors: {len(data) if success and isinstance(data, list) else error}")
        
        # Create a test distributor
        distributor_data = {
            "name": "Global Distribution Partners",
            "contact_person": "Sarah Johnson",
            "phone": "+1-555-9876",
            "email": "sarah.j@globaldist.com",
            "address": "789 Commerce Street, Trade City, TC 54321",
            "territory": "North Region",
            "commission_percent": 5.0,
            "credit_limit": 50000.0
        }
        
        success, data, error = self.make_request("POST", "/distributors", distributor_data)
        if success and "distributor_id" in data:
            distributor_id = data["distributor_id"]
            self.created_resources['distributors'].append(distributor_id)
            self.log_result("POST /distributors", True, f"Created distributor: {distributor_id}")
            return distributor_id
        else:
            self.log_result("POST /distributors", False, error)
            return None
    
    def test_product_operations(self):
        """Test product endpoints"""
        print("\n📦 Testing Products...")
        
        # Get existing products
        success, data, error = self.make_request("GET", "/products")
        self.log_result("GET /products", success,
                       f"Found products: {len(data) if success and isinstance(data, list) else error}")
        
        # Create test products
        products_data = [
            {
                "sku": "WIDGET-001",
                "name": "Premium Widget Type A",
                "description": "High-quality industrial widget for manufacturing applications",
                "category": "raw",
                "unit": "pcs",
                "cost_price": 12.50,
                "selling_price": 25.00,
                "reorder_level": 50,
                "min_stock": 10,
                "max_stock": 500
            },
            {
                "sku": "GADGET-002",
                "name": "Multi-Purpose Gadget",
                "description": "Versatile gadget for various industrial uses",
                "category": "finished",
                "unit": "units",
                "cost_price": 35.75,
                "selling_price": 59.99,
                "reorder_level": 25,
                "min_stock": 5,
                "max_stock": 200
            }
        ]
        
        created_product_ids = []
        for product_data in products_data:
            success, data, error = self.make_request("POST", "/products", product_data)
            if success and "product_id" in data:
                product_id = data["product_id"]
                created_product_ids.append(product_id)
                self.created_resources['products'].append(product_id)
                self.log_result(f"POST /products ({product_data['sku']})", True, f"Created: {product_id}")
            else:
                self.log_result(f"POST /products ({product_data['sku']})", False, error)
        
        # Test individual product retrieval
        if created_product_ids:
            product_id = created_product_ids[0]
            success, data, error = self.make_request("GET", f"/products/{product_id}")
            self.log_result("GET /products/{id}", success, error if not success else f"Retrieved product: {data.get('name', 'Unknown')}")
            
            # Test product update
            update_data = {"selling_price": 29.99}
            success, data, error = self.make_request("PUT", f"/products/{product_id}", update_data)
            self.log_result("PUT /products/{id}", success, error if not success else "Updated product price")
        
        return created_product_ids
    
    def test_inventory_operations(self, product_ids: List[str], warehouse_id: str):
        """Test inventory endpoints"""
        print("\n📋 Testing Inventory...")
        
        if not product_ids or not warehouse_id:
            self.log_result("Inventory tests", False, "Missing products or warehouse for testing")
            return
        
        # Get current inventory
        success, data, error = self.make_request("GET", "/inventory")
        self.log_result("GET /inventory", success,
                       f"Inventory records: {len(data) if success and isinstance(data, list) else error}")
        
        # Test inventory adjustment
        for product_id in product_ids[:2]:  # Test first 2 products
            adjustment_data = {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "type": "adjustment",
                "quantity": 100,
                "notes": f"Initial stock for testing - Product {product_id}"
            }
            
            success, data, error = self.make_request("POST", "/inventory/adjust", adjustment_data)
            self.log_result(f"POST /inventory/adjust (Product {product_id})", success,
                           error if not success else f"Adjusted inventory: {data.get('transaction_id', 'Unknown')}")
        
        # Test low stock items
        success, data, error = self.make_request("GET", "/inventory/low-stock")
        self.log_result("GET /inventory/low-stock", success,
                       f"Low stock items: {len(data) if success and isinstance(data, list) else error}")
    
    def test_purchase_order_operations(self, supplier_id: str, warehouse_id: str, product_ids: List[str]):
        """Test purchase order endpoints"""
        print("\n🛒 Testing Purchase Orders...")
        
        if not supplier_id or not warehouse_id or not product_ids:
            self.log_result("Purchase Order tests", False, "Missing dependencies for testing")
            return
        
        # Get existing purchase orders
        success, data, error = self.make_request("GET", "/purchase-orders")
        self.log_result("GET /purchase-orders", success,
                       f"Found purchase orders: {len(data) if success and isinstance(data, list) else error}")
        
        # Create a purchase order
        po_data = {
            "supplier_id": supplier_id,
            "warehouse_id": warehouse_id,
            "items": [
                {
                    "product_id": product_ids[0],
                    "quantity": 50,
                    "unit_price": 12.00
                },
                {
                    "product_id": product_ids[1],
                    "quantity": 30,
                    "unit_price": 35.00
                }
            ],
            "tax_amount": 105.0,
            "notes": "Test purchase order for API validation"
        }
        
        success, data, error = self.make_request("POST", "/purchase-orders", po_data)
        if success and "po_id" in data:
            po_id = data["po_id"]
            self.created_resources['purchase_orders'].append(po_id)
            self.log_result("POST /purchase-orders", True, f"Created PO: {po_id}")
            
            # Test PO status update
            update_data = {"status": "ordered"}
            success, data, error = self.make_request("PUT", f"/purchase-orders/{po_id}", update_data)
            self.log_result("PUT /purchase-orders/{id}", success,
                           error if not success else "Updated PO status")
            
            return po_id
        else:
            self.log_result("POST /purchase-orders", False, error)
            return None
    
    def test_sales_order_operations(self, distributor_id: str, warehouse_id: str, product_ids: List[str]):
        """Test sales order endpoints"""
        print("\n💰 Testing Sales Orders...")
        
        if not distributor_id or not warehouse_id or not product_ids:
            self.log_result("Sales Order tests", False, "Missing dependencies for testing")
            return
        
        # Get existing sales orders
        success, data, error = self.make_request("GET", "/sales-orders")
        self.log_result("GET /sales-orders", success,
                       f"Found sales orders: {len(data) if success and isinstance(data, list) else error}")
        
        # Create a sales order
        so_data = {
            "distributor_id": distributor_id,
            "warehouse_id": warehouse_id,
            "items": [
                {
                    "product_id": product_ids[0],
                    "quantity": 10,
                    "unit_price": 25.00
                },
                {
                    "product_id": product_ids[1],
                    "quantity": 5,
                    "unit_price": 59.99
                }
            ],
            "tax_amount": 54.995,
            "notes": "Test sales order for API validation"
        }
        
        success, data, error = self.make_request("POST", "/sales-orders", so_data)
        if success and "so_id" in data:
            so_id = data["so_id"]
            self.created_resources['sales_orders'].append(so_id)
            self.log_result("POST /sales-orders", True, f"Created SO: {so_id}")
            return so_id
        else:
            self.log_result("POST /sales-orders", False, error)
            return None
    
    def test_reports_endpoints(self):
        """Test reports endpoints"""
        print("\n📈 Testing Reports...")
        
        # Test stock summary report
        success, data, error = self.make_request("GET", "/reports/stock-summary")
        self.log_result("GET /reports/stock-summary", success,
                       f"Stock summary records: {len(data) if success and isinstance(data, list) else error}")
    
    def test_auth_logout(self):
        """Test logout endpoint"""
        print("\n🚪 Testing Logout...")
        
        success, data, error = self.make_request("POST", "/auth/logout")
        self.log_result("POST /auth/logout", success,
                       error if not success else "Logout successful")
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created resources
        for resource_type, ids in self.created_resources.items():
            for resource_id in ids:
                if resource_type == 'products':
                    success, _, error = self.make_request("DELETE", f"/products/{resource_id}")
                elif resource_type == 'suppliers':
                    success, _, error = self.make_request("DELETE", f"/suppliers/{resource_id}")
                elif resource_type == 'distributors':
                    success, _, error = self.make_request("DELETE", f"/distributors/{resource_id}")
                elif resource_type == 'warehouses':
                    success, _, error = self.make_request("DELETE", f"/warehouses/{resource_id}")
                elif resource_type == 'purchase_orders':
                    # POs can only be cancelled if in draft status
                    continue
                elif resource_type == 'sales_orders':
                    # SOs can only be cancelled if in draft status
                    continue
                
                if success:
                    print(f"   ✅ Deleted {resource_type[:-1]}: {resource_id}")
                else:
                    print(f"   ⚠️  Failed to delete {resource_type[:-1]} {resource_id}: {error}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🎯 TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   - {result['test_name']}: {result['details']}")
        
        print("\n" + "="*60)
        
        return failed_tests == 0
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting BizCore Backend API Tests...")
        print(f"Base URL: {self.base_url}")
        print(f"Session Token: {self.session_token[:20]}...")
        
        # Test authentication first
        if not self.test_authentication():
            print("❌ Authentication failed - skipping remaining tests")
            return False
        
        try:
            # Test basic endpoints
            self.test_dashboard_endpoints()
            
            # Create test data and test CRUD operations
            warehouse_id = self.test_warehouse_operations()
            supplier_id = self.test_supplier_operations()
            distributor_id = self.test_distributor_operations()
            product_ids = self.test_product_operations()
            
            # Test dependent operations
            if product_ids and warehouse_id:
                self.test_inventory_operations(product_ids, warehouse_id)
            
            if supplier_id and warehouse_id and product_ids:
                self.test_purchase_order_operations(supplier_id, warehouse_id, product_ids)
            
            if distributor_id and warehouse_id and product_ids:
                self.test_sales_order_operations(distributor_id, warehouse_id, product_ids)
            
            # Test reports
            self.test_reports_endpoints()
            
            # Test logout
            self.test_auth_logout()
            
        except Exception as e:
            print(f"❌ Test execution error: {str(e)}")
            return False
        
        finally:
            # Clean up test data
            self.cleanup_test_data()
        
        # Print summary and return success status
        return self.print_summary()


def main():
    """Main test execution"""
    tester = BizCoreAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()