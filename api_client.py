"""
Клиент для работы с сервером склада через REST API.
Используется в PyQt приложении для удалённого доступа к базе данных.
"""
import requests
from datetime import datetime


class WarehouseAPI:
    """Клиент для работы с сервером склада через API"""
    
    def __init__(self, server_ip="192.168.56.1", port=8055):
        """
        Инициализация клиента API.

        Args:
            server_ip: IP-адрес сервера с базой данных
            port: Порт сервера (по умолчанию 8000)
        """
        self.base_url = f"http://{server_ip}:{port}"
        self.server_ip = server_ip
        self.port = port
    
    def check_connection(self):
        """Проверить подключение к серверу"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_server_info(self):
        """Получить информацию о сервере"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    # ==================== СКЛАД ====================
    
    def get_stock(self):
        """Получить все остатки на складе"""
        try:
            response = requests.get(f"{self.base_url}/api/stock", timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []
    
    def get_stock_item(self, item_id):
        """Получить конкретный товар со склада"""
        try:
            response = requests.get(f"{self.base_url}/api/stock/{item_id}", timeout=10)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def add_stock_item(self, product_name, sku, quantity, unit, price, total):
        """Добавить товар на склад"""
        try:
            data = {
                "product_name": product_name,
                "sku": sku,
                "quantity": quantity,
                "unit": unit,
                "price": price,
                "total": total
            }
            response = requests.post(f"{self.base_url}/api/stock", json=data, timeout=10)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def update_stock_item(self, item_id, product_name, sku, quantity, unit, price, total):
        """Обновить товар на складе"""
        try:
            data = {
                "product_name": product_name,
                "sku": sku,
                "quantity": quantity,
                "unit": unit,
                "price": price,
                "total": total
            }
            response = requests.put(f"{self.base_url}/api/stock/{item_id}", json=data, timeout=10)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def delete_stock_item(self, item_id):
        """Удалить товар со склада"""
        try:
            response = requests.delete(f"{self.base_url}/api/stock/{item_id}", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    # ==================== ЗАКАЗЫ ====================
    
    def get_all_orders(self):
        """Получить все заказы"""
        try:
            response = requests.get(f"{self.base_url}/api/orders", timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []
    
    def get_order(self, order_id):
        """Получить конкретный заказ"""
        try:
            response = requests.get(f"{self.base_url}/api/orders/{order_id}", timeout=10)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def add_order(self, client, amount, status="В работе", date=None):
        """Добавить новый заказ"""
        try:
            data = {
                "client": client,
                "date": date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "amount": amount,
                "status": status
            }
            response = requests.post(f"{self.base_url}/api/orders", json=data, timeout=10)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def update_order(self, order_id, client, amount, status, date=None):
        """Обновить заказ"""
        try:
            data = {
                "client": client,
                "date": date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "amount": amount,
                "status": status
            }
            response = requests.put(f"{self.base_url}/api/orders/{order_id}", json=data, timeout=10)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def delete_order(self, order_id):
        """Удалить заказ"""
        try:
            response = requests.delete(f"{self.base_url}/api/orders/{order_id}", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    # ==================== В РАБОТЕ ====================
    
    def get_in_work_orders(self):
        """Получить все заказы в работе"""
        try:
            response = requests.get(f"{self.base_url}/api/in-work", timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []
    
    def add_in_work_order(self, client, amount, manager, date=None):
        """Добавить заказ в работу"""
        try:
            data = {
                "client": client,
                "date": date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "amount": amount,
                "manager": manager
            }
            response = requests.post(f"{self.base_url}/api/in-work", json=data, timeout=10)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def delete_in_work_order(self, order_id):
        """Удалить заказ из работы"""
        try:
            response = requests.delete(f"{self.base_url}/api/in-work/{order_id}", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    # ==================== ГОТОВЫЕ ЗАКАЗЫ ====================
    
    def get_ready_orders(self):
        """Получить все готовые заказы"""
        try:
            response = requests.get(f"{self.base_url}/api/ready", timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []
    
    def add_ready_order(self, client, amount, status="Готов", date=None):
        """Добавить готовый заказ"""
        try:
            data = {
                "client": client,
                "date": date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "amount": amount,
                "status": status
            }
            response = requests.post(f"{self.base_url}/api/ready", json=data, timeout=10)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def update_ready_order(self, order_id, client, amount, status, date=None):
        """Обновить готовый заказ"""
        try:
            data = {
                "client": client,
                "date": date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "amount": amount,
                "status": status
            }
            response = requests.put(f"{self.base_url}/api/ready/{order_id}", json=data, timeout=10)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def delete_ready_order(self, order_id):
        """Удалить готовый заказ"""
        try:
            response = requests.delete(f"{self.base_url}/api/ready/{order_id}", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    # ==================== ПРОДАЖИ ====================
    
    def get_sales(self):
        """Получить все продажи"""
        try:
            response = requests.get(f"{self.base_url}/api/sales", timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []
    
    def add_sale(self, invoice_number, buyer, items_count, amount, date=None):
        """Добавить новую продажу"""
        try:
            data = {
                "invoice_number": invoice_number,
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "buyer": buyer,
                "items_count": items_count,
                "amount": amount
            }
            response = requests.post(f"{self.base_url}/api/sales", json=data, timeout=10)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def delete_sale(self, sale_id):
        """Удалить продажу"""
        try:
            response = requests.delete(f"{self.base_url}/api/sales/{sale_id}", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    # ==================== ПОСТУПЛЕНИЯ ====================
    
    def get_receipts(self):
        """Получить все поступления"""
        try:
            response = requests.get(f"{self.base_url}/api/receipts", timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []
    
    def add_receipt(self, product_name, sku, quantity, unit, price, total, supplier, date=None):
        """Добавить новое поступление"""
        try:
            data = {
                "date": date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "product_name": product_name,
                "sku": sku,
                "quantity": quantity,
                "unit": unit,
                "price": price,
                "total": total,
                "supplier": supplier
            }
            response = requests.post(f"{self.base_url}/api/receipts", json=data, timeout=10)
            if response.ok:
                return response.json()
            error_text = response.text[:500]
            raise RuntimeError(f"HTTP {response.status_code}: {error_text}")
        except requests.exceptions.RequestException:
            return None
    
    def delete_receipt(self, receipt_id):
        """Удалить поступление"""
        try:
            response = requests.delete(f"{self.base_url}/api/receipts/{receipt_id}", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    # ==================== СПИСАНИЯ ====================
    
    def get_writeoffs(self):
        """Получить все списания"""
        try:
            response = requests.get(f"{self.base_url}/api/writeoffs", timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []
    
    def add_writeoff(self, product_name, sku, quantity, reason, manager, date=None):
        """Добавить новое списание"""
        try:
            data = {
                "date": date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "product_name": product_name,
                "sku": sku,
                "quantity": quantity,
                "reason": reason,
                "manager": manager
            }
            response = requests.post(f"{self.base_url}/api/writeoffs", json=data, timeout=10)
            if response.ok:
                return response.json()
            error_text = response.text[:500]
            raise RuntimeError(f"HTTP {response.status_code}: {error_text}")
        except requests.exceptions.RequestException:
            return None
    
    def delete_writeoff(self, writeoff_id):
        """Удалить списание"""
        try:
            response = requests.delete(f"{self.base_url}/api/writeoffs/{writeoff_id}", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    # ==================== ВОЗВРАТЫ КЛИЕНТОВ ====================
    
    def get_returns_clients(self):
        """Получить все возвраты от клиентов"""
        try:
            response = requests.get(f"{self.base_url}/api/returns-clients", timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []
    
    def add_return_client(self, product_name, sku, quantity, reason, client, date=None):
        """Добавить возврат от клиента"""
        try:
            data = {
                "date": date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "product_name": product_name,
                "sku": sku,
                "quantity": quantity,
                "reason": reason,
                "client": client
            }
            response = requests.post(f"{self.base_url}/api/returns-clients", json=data, timeout=10)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def delete_return_client(self, return_id):
        """Удалить возврат клиента"""
        try:
            response = requests.delete(f"{self.base_url}/api/returns-clients/{return_id}", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    # ==================== ВОЗВРАТЫ ПОСТАВЩИКАМ ====================
    
    def get_returns_suppliers(self):
        """Получить все возвраты поставщикам"""
        try:
            response = requests.get(f"{self.base_url}/api/returns-suppliers", timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []
    
    def add_return_supplier(self, product_name, sku, quantity, reason, supplier, date=None):
        """Добавить возврат поставщику"""
        try:
            data = {
                "date": date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "product_name": product_name,
                "sku": sku,
                "quantity": quantity,
                "reason": reason,
                "supplier": supplier
            }
            response = requests.post(f"{self.base_url}/api/returns-suppliers", json=data, timeout=10)
            return response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            return None
    
    def delete_return_supplier(self, return_id):
        """Удалить возврат поставщику"""
        try:
            response = requests.delete(f"{self.base_url}/api/returns-suppliers/{return_id}", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    # ==================== СТАТИСТИКА ====================
    
    def get_dashboard_stats(self):
        """Получить статистику для главной панели"""
        try:
            response = requests.get(f"{self.base_url}/api/stats/dashboard", timeout=10)
            return response.json() if response.status_code == 200 else {}
        except requests.exceptions.RequestException:
            return {}

    # ==================== USERS / SESSIONS ====================

    def get_users(self):
        """Получить список пользователей"""
        try:
            response = requests.get(f"{self.base_url}/api/users", timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []

    def get_work_sessions(self):
        """Получить список рабочих сессий"""
        try:
            response = requests.get(f"{self.base_url}/api/work-sessions", timeout=10)
            return response.json() if response.status_code == 200 else []
        except requests.exceptions.RequestException:
            return []
