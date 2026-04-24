"""
FastAPI сервер для доступа к базе данных склада.
Поддерживает CORS для доступа с других ПК.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
from contextlib import contextmanager
import os

# Путь к базе данных
DB_PATH = os.path.join(os.path.dirname(__file__), "bd.db")


# ==================== Pydantic Models (CREATE/UPDATE) ====================
# Используем латинские имена полей для удобства работы с API

class StockItemCreate(BaseModel):
    product_name: str
    sku: str
    quantity: float
    unit: str
    price: float
    total: float


class StockItemResponse(BaseModel):
    id: int
    Товар: str
    Артикул: str
    Количество: float
    Ед_изм: str
    Цена: float
    Сумма: float

    class Config:
        from_attributes = True


class ReceiptItemCreate(BaseModel):
    date: str
    product_name: str
    sku: str
    quantity: float
    unit: str
    price: float
    total: float
    supplier: str


class ReceiptItemResponse(BaseModel):
    id: int
    Дата: str
    Товар: str
    Артикул: str
    Количество: float
    Ед_изм: str
    Цена: float
    Сумма: float
    Поставщик: str

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    client: str
    date: str
    amount: float
    status: str


class OrderResponse(BaseModel):
    id: int
    Клиент: str
    Дата: str
    Сумма: float
    Статус: str

    class Config:
        from_attributes = True


class InWorkOrderCreate(BaseModel):
    client: str
    date: str
    amount: float
    manager: str


class InWorkOrderResponse(BaseModel):
    id: int
    Клиент: str
    Дата: str
    Сумма: float
    Ответственный: str

    class Config:
        from_attributes = True


class ReadyOrderCreate(BaseModel):
    client: str
    date: str
    amount: float
    status: str


class ReadyOrderResponse(BaseModel):
    id: int
    Клиент: str
    Дата: str
    Сумма: float
    Статус: str

    class Config:
        from_attributes = True


class SaleCreate(BaseModel):
    invoice_number: str
    date: str
    buyer: str
    items_count: int
    amount: float


class SaleResponse(BaseModel):
    id: int
    Номер: str
    Дата: str
    Покупатель: str
    Кол_во_позиций: int
    Сумма: float

    class Config:
        from_attributes = True


class WriteoffCreate(BaseModel):
    date: str
    product_name: str
    sku: str
    quantity: float
    reason: str
    manager: str


class WriteoffResponse(BaseModel):
    id: int
    Дата: str
    Товар: str
    Артикул: str
    Количество: float
    Причина: str
    Ответственный: str

    class Config:
        from_attributes = True


class ReturnClientCreate(BaseModel):
    date: str
    product_name: str
    sku: str
    quantity: float
    reason: str
    client: str


class ReturnClientResponse(BaseModel):
    id: int
    Дата: str
    Товар: str
    Артикул: str
    Количество: float
    Причина: str
    Клиент: str

    class Config:
        from_attributes = True


class ReturnSupplierCreate(BaseModel):
    date: str
    product_name: str
    sku: str
    quantity: float
    reason: str
    supplier: str


class ReturnSupplierResponse(BaseModel):
    id: int
    Дата: str
    Товар: str
    Артикул: str
    Количество: float
    Причина: str
    Поставщик: str

    class Config:
        from_attributes = True


# ==================== Database Connection ====================

@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def dict_from_row(row):
    """Преобразует sqlite3.Row в словарь."""
    return dict(zip(row.keys(), row))


# ==================== FastAPI App ====================

app = FastAPI(
    title="Склад API",
    description="API для управления складом, заказами, продажами и прайсами",
    version="1.0.0"
)

# Настройка CORS для доступа с любых ПК
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы
    allow_headers=["*"],  # Разрешить все заголовки
)


# ==================== Health Check ====================

@app.get("/")
async def root():
    """Проверка работоспособности API."""
    return {"message": "Склад API работает", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Проверка подключения к базе данных."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
        return {"status": "ok", "database": "connected", "tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ==================== Stock Endpoints ====================

@app.get("/api/stock", response_model=List[StockItemResponse], tags=["Склад"])
async def get_stock():
    """Получить все остатки на складе."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stock_page")
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@app.get("/api/stock/{item_id}", response_model=StockItemResponse, tags=["Склад"])
async def get_stock_item(item_id: int):
    """Получить конкретный товар со склада."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stock_page WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Товар не найден")
        return dict_from_row(row)


@app.post("/api/stock", response_model=StockItemResponse, tags=["Склад"])
async def create_stock_item(item: StockItemCreate):
    """Добавить новый товар на склад."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO stock_page (Товар, Артикул, Количество, Ед_изм, Цена, Сумма)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (item.product_name, item.sku, item.quantity, item.unit, item.price, item.total))
        conn.commit()
        cursor.execute("SELECT * FROM stock_page WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()
        return dict_from_row(row)


@app.put("/api/stock/{item_id}", response_model=StockItemResponse, tags=["Склад"])
async def update_stock_item(item_id: int, item: StockItemCreate):
    """Обновить товар на складе."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE stock_page 
            SET Товар=?, Артикул=?, Количество=?, Ед_изм=?, Цена=?, Сумма=?
            WHERE id=?
        """, (item.product_name, item.sku, item.quantity, item.unit, item.price, item.total, item_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Товар не найден")
        cursor.execute("SELECT * FROM stock_page WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        return dict_from_row(row)


@app.delete("/api/stock/{item_id}", tags=["Склад"])
async def delete_stock_item(item_id: int):
    """Удалить товар со склада."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stock_page WHERE id = ?", (item_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Товар не найден")
        return {"message": "Товар удален"}


# ==================== Receipts Endpoints ====================

@app.get("/api/receipts", response_model=List[ReceiptItemResponse], tags=["Поступления"])
async def get_receipts():
    """Получить все поступления."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM receipts_page")
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@app.get("/api/receipts/{receipt_id}", response_model=ReceiptItemResponse, tags=["Поступления"])
async def get_receipt(receipt_id: int):
    """Получить конкретное поступление."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM receipts_page WHERE id = ?", (receipt_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Поступление не найдено")
        return dict_from_row(row)


@app.post("/api/receipts", response_model=ReceiptItemResponse, tags=["Поступления"])
async def create_receipt(receipt: ReceiptItemCreate):
    """Добавить новое поступление."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO receipts_page (Дата, Товар, Артикул, Количество, Ед_изм, Цена, Сумма, Поставщик)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (receipt.date, receipt.product_name, receipt.sku, receipt.quantity, 
              receipt.unit, receipt.price, receipt.total, receipt.supplier))
        conn.commit()
        cursor.execute("SELECT * FROM receipts_page WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()
        return dict_from_row(row)


@app.delete("/api/receipts/{receipt_id}", tags=["Поступления"])
async def delete_receipt(receipt_id: int):
    """Удалить поступление."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM receipts_page WHERE id = ?", (receipt_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Поступление не найдено")
        return {"message": "Поступление удалено"}


# ==================== Orders Endpoints ====================

@app.get("/api/orders", response_model=List[OrderResponse], tags=["Заказы"])
async def get_all_orders():
    """Получить все заказы."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM all_orders_page")
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@app.get("/api/orders/{order_id}", response_model=OrderResponse, tags=["Заказы"])
async def get_order(order_id: int):
    """Получить конкретный заказ."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM all_orders_page WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        return dict_from_row(row)


@app.post("/api/orders", response_model=OrderResponse, tags=["Заказы"])
async def create_order(order: OrderCreate):
    """Добавить новый заказ."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO all_orders_page (Клиент, Дата, Сумма, Статус)
            VALUES (?, ?, ?, ?)
        """, (order.client, order.date, order.amount, order.status))
        conn.commit()
        cursor.execute("SELECT * FROM all_orders_page WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()
        return dict_from_row(row)


@app.put("/api/orders/{order_id}", response_model=OrderResponse, tags=["Заказы"])
async def update_order(order_id: int, order: OrderCreate):
    """Обновить заказ."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE all_orders_page 
            SET Клиент=?, Дата=?, Сумма=?, Статус=?
            WHERE id=?
        """, (order.client, order.date, order.amount, order.status, order_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        cursor.execute("SELECT * FROM all_orders_page WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        return dict_from_row(row)


@app.delete("/api/orders/{order_id}", tags=["Заказы"])
async def delete_order(order_id: int):
    """Удалить заказ."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM all_orders_page WHERE id = ?", (order_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        return {"message": "Заказ удален"}


# ==================== In Work Orders Endpoints ====================

@app.get("/api/in-work", response_model=List[InWorkOrderResponse], tags=["В работе"])
async def get_in_work_orders():
    """Получить все заказы в работе."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM in_work_page")
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@app.get("/api/in-work/{order_id}", response_model=InWorkOrderResponse, tags=["В работе"])
async def get_in_work_order(order_id: int):
    """Получить заказ в работе."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM in_work_page WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        return dict_from_row(row)


@app.post("/api/in-work", response_model=InWorkOrderResponse, tags=["В работе"])
async def create_in_work_order(order: InWorkOrderCreate):
    """Добавить заказ в работу."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO in_work_page (Клиент, Дата, Сумма, Ответственный)
            VALUES (?, ?, ?, ?)
        """, (order.client, order.date, order.amount, order.manager))
        conn.commit()
        cursor.execute("SELECT * FROM in_work_page WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()
        return dict_from_row(row)


@app.delete("/api/in-work/{order_id}", tags=["В работе"])
async def delete_in_work_order(order_id: int):
    """Удалить заказ из работы."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM in_work_page WHERE id = ?", (order_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        return {"message": "Заказ удален"}


# ==================== Ready Orders Endpoints ====================

@app.get("/api/ready", response_model=List[ReadyOrderResponse], tags=["Готовые"])
async def get_ready_orders():
    """Получить все готовые заказы."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ready_page")
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@app.get("/api/ready/{order_id}", response_model=ReadyOrderResponse, tags=["Готовые"])
async def get_ready_order(order_id: int):
    """Получить готовый заказ."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ready_page WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        return dict_from_row(row)


@app.post("/api/ready", response_model=ReadyOrderResponse, tags=["Готовые"])
async def create_ready_order(order: ReadyOrderCreate):
    """Добавить готовый заказ."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ready_page (Клиент, Дата, Сумма, Статус)
            VALUES (?, ?, ?, ?)
        """, (order.client, order.date, order.amount, order.status))
        conn.commit()
        cursor.execute("SELECT * FROM ready_page WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()
        return dict_from_row(row)


@app.put("/api/ready/{order_id}", response_model=ReadyOrderResponse, tags=["Готовые"])
async def update_ready_order(order_id: int, order: ReadyOrderCreate):
    """Обновить готовый заказ."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ready_page 
            SET Клиент=?, Дата=?, Сумма=?, Статус=?
            WHERE id=?
        """, (order.client, order.date, order.amount, order.status, order_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        cursor.execute("SELECT * FROM ready_page WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        return dict_from_row(row)


@app.delete("/api/ready/{order_id}", tags=["Готовые"])
async def delete_ready_order(order_id: int):
    """Удалить готовый заказ."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ready_page WHERE id = ?", (order_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        return {"message": "Заказ удален"}


# ==================== Sales Endpoints ====================

@app.get("/api/sales", response_model=List[SaleResponse], tags=["Продажи"])
async def get_sales():
    """Получить все продажи."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sales_page")
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@app.get("/api/sales/{sale_id}", response_model=SaleResponse, tags=["Продажи"])
async def get_sale(sale_id: int):
    """Получить конкретную продажу."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sales_page WHERE id = ?", (sale_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Продажа не найдена")
        return dict_from_row(row)


@app.post("/api/sales", response_model=SaleResponse, tags=["Продажи"])
async def create_sale(sale: SaleCreate):
    """Добавить новую продажу."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sales_page (Номер, Дата, Покупатель, Кол_во_позиций, Сумма)
            VALUES (?, ?, ?, ?, ?)
        """, (sale.invoice_number, sale.date, sale.buyer, sale.items_count, sale.amount))
        conn.commit()
        cursor.execute("SELECT * FROM sales_page WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()
        return dict_from_row(row)


@app.delete("/api/sales/{sale_id}", tags=["Продажи"])
async def delete_sale(sale_id: int):
    """Удалить продажу."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sales_page WHERE id = ?", (sale_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Продажа не найдена")
        return {"message": "Продажа удалена"}


# ==================== Writeoffs Endpoints ====================

@app.get("/api/writeoffs", response_model=List[WriteoffResponse], tags=["Списания"])
async def get_writeoffs():
    """Получить все списания."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM writeoffs_page")
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@app.get("/api/writeoffs/{writeoff_id}", response_model=WriteoffResponse, tags=["Списания"])
async def get_writeoff(writeoff_id: int):
    """Получить конкретное списание."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM writeoffs_page WHERE id = ?", (writeoff_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Списание не найдено")
        return dict_from_row(row)


@app.post("/api/writeoffs", response_model=WriteoffResponse, tags=["Списания"])
async def create_writeoff(writeoff: WriteoffCreate):
    """Добавить новое списание."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO writeoffs_page (Дата, Товар, Артикул, Количество, Причина, Ответственный)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (writeoff.date, writeoff.product_name, writeoff.sku, writeoff.quantity, 
              writeoff.reason, writeoff.manager))
        conn.commit()
        cursor.execute("SELECT * FROM writeoffs_page WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()
        return dict_from_row(row)


@app.delete("/api/writeoffs/{writeoff_id}", tags=["Списания"])
async def delete_writeoff(writeoff_id: int):
    """Удалить списание."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM writeoffs_page WHERE id = ?", (writeoff_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Списание не найдено")
        return {"message": "Списание удалено"}


# ==================== Returns Clients Endpoints ====================

@app.get("/api/returns-clients", response_model=List[ReturnClientResponse], tags=["Возвраты клиентов"])
async def get_returns_clients():
    """Получить все возвраты от клиентов."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM returns_clients_page")
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@app.get("/api/returns-clients/{return_id}", response_model=ReturnClientResponse, tags=["Возвраты клиентов"])
async def get_return_client(return_id: int):
    """Получить возврат от клиента."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM returns_clients_page WHERE id = ?", (return_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Возврат не найден")
        return dict_from_row(row)


@app.post("/api/returns-clients", response_model=ReturnClientResponse, tags=["Возвраты клиентов"])
async def create_return_client(return_item: ReturnClientCreate):
    """Добавить возврат от клиента."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO returns_clients_page (Дата, Товар, Артикул, Количество, Причина, Клиент)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (return_item.date, return_item.product_name, return_item.sku, return_item.quantity, 
              return_item.reason, return_item.client))
        conn.commit()
        cursor.execute("SELECT * FROM returns_clients_page WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()
        return dict_from_row(row)


@app.delete("/api/returns-clients/{return_id}", tags=["Возвраты клиентов"])
async def delete_return_client(return_id: int):
    """Удалить возврат клиента."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM returns_clients_page WHERE id = ?", (return_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Возврат не найден")
        return {"message": "Возврат удален"}


# ==================== Returns Suppliers Endpoints ====================

@app.get("/api/returns-suppliers", response_model=List[ReturnSupplierResponse], tags=["Возвраты поставщикам"])
async def get_returns_suppliers():
    """Получить все возвраты поставщикам."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM returns_suppliers_page")
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@app.get("/api/returns-suppliers/{return_id}", response_model=ReturnSupplierResponse, tags=["Возвраты поставщикам"])
async def get_return_supplier(return_id: int):
    """Получить возврат поставщику."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM returns_suppliers_page WHERE id = ?", (return_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Возврат не найден")
        return dict_from_row(row)


@app.post("/api/returns-suppliers", response_model=ReturnSupplierResponse, tags=["Возвраты поставщикам"])
async def create_return_supplier(return_item: ReturnSupplierCreate):
    """Добавить возврат поставщику."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO returns_suppliers_page (Дата, Товар, Артикул, Количество, Причина, Поставщик)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (return_item.date, return_item.product_name, return_item.sku, return_item.quantity, 
              return_item.reason, return_item.supplier))
        conn.commit()
        cursor.execute("SELECT * FROM returns_suppliers_page WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()
        return dict_from_row(row)


@app.delete("/api/returns-suppliers/{return_id}", tags=["Возвраты поставщикам"])
async def delete_return_supplier(return_id: int):
    """Удалить возврат поставщику."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM returns_suppliers_page WHERE id = ?", (return_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Возврат не найден")
        return {"message": "Возврат удален"}


# ==================== Statistics Endpoints ====================

@app.get("/api/stats/dashboard", tags=["Статистика"])
async def get_dashboard_stats():
    """Получить статистику для главной панели."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Заказы сегодня
        cursor.execute("SELECT COUNT(*) FROM all_orders_page WHERE Дата LIKE ?", (f"{today}%",))
        today_orders = cursor.fetchone()[0]
        
        # В работе
        cursor.execute("SELECT COUNT(*) FROM in_work_page")
        in_work_count = cursor.fetchone()[0]
        
        # Готовые
        cursor.execute("SELECT COUNT(*) FROM ready_page WHERE Статус = 'Выполнен' OR Статус = 'Готов'")
        ready_count = cursor.fetchone()[0]
        
        # Сумма готовых
        cursor.execute("SELECT SUM(Сумма) FROM ready_page WHERE Статус = 'Выполнен' OR Статус = 'Готов'")
        ready_sum = cursor.fetchone()[0] or 0
        
        return {
            "today_orders": today_orders,
            "in_work": in_work_count,
            "ready_count": ready_count,
            "ready_sum": ready_sum
        }


if __name__ == "__main__":
    import uvicorn
    # Запуск на 0.0.0.0 для доступа с других ПК
    uvicorn.run(app, host="192.168.56.1", port=8055)
