import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import datetime

# Импортируем ваш API клиент
try:
    from api_client import WarehouseAPI
except ImportError:
    print("Ошибка: Файл api_client.py не найден!")
    WarehouseAPI = None

# ==================== НАСТРОЙКИ ПОДКЛЮЧЕНИЯ ====================
SERVER_IP = "192.168.3.189"
SERVER_PORT = 8055
UI_CONFIG = {
    'window_width': 1600,      # Базовая ширина для 16:10
    'window_height': 1000,     # Базовая высота для 16:10
    'sidebar_width': 300,      # Ширина бокового меню (18.75% от ширины)
    'table_font_size': 14,     # Размер шрифта в таблицах
    'card_value_font_size': 42, # Размер цифр в карточках
    'button_font_size': 15,    # Размер шрифта кнопок
    'header_font_size': 14,    # Размер шрифта заголовков
    'menu_font_size': 16,      # Размер шрифта меню
    'dialog_font_size': 20,    # Размер шрифта в диалогах
    'title_font_size': 32,     # Размер главного заголовка
    'subtitle_font_size': 20,  # Размер подзаголовков
    'min_column_width': 120,   # Минимальная ширина колонки
    'card_padding': 25,        # Отступы в карточках
    'table_row_padding': 10,   # Отступы в строках таблицы
    'button_padding_v': 14,    # Вертикальные отступы кнопок
    'button_padding_h': 28,    # Горизонтальные отступы кнопок
}
# Стили для приложения
STYLE_SHEET = """
QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #333333;
}

QLabel {
    color: #333333;
}

/* Стиль для заголовков */
QLabel#title {
    font-size: 28px;
    font-weight: bold;
    color: #2c3e50;
    padding: 20px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border-radius: 10px;
    margin: 10px;
}

QLabel#subtitle {
    font-size: 18px;
    font-weight: bold;
    color: #34495e;
    padding: 10px;
    margin: 5px;
}

/* Стиль для кнопок */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: bold;
    min-width: 100px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #764ba2, stop:1 #667eea);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #5a67d8, stop:1 #6b46a0);
}

QPushButton#danger {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f56565, stop:1 #c53030);
}

QPushButton#danger:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #fc8181, stop:1 #e53e3e);
}

QPushButton#success {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #48bb78, stop:1 #2f855a);
}

QPushButton#success:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #68d391, stop:1 #38a169);
}

/* Стиль для бокового меню */
QWidget#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a202c, stop:1 #2d3748);
    border-right: 1px solid #4a5568;
}

/* Стиль для кнопок меню */
QPushButton#menu-button {
    background: transparent;
    color: #e2e8f0;
    text-align: left;
    padding: 15px 20px;
    font-size: 15px;
    font-weight: 600;
    border: none;
    border-radius: 0;
    margin: 2px 5px;
}

QPushButton#menu-button:hover {
    background: rgba(102, 126, 234, 0.2);
    color: white;
}

QPushButton#menu-button:checked {
    background: rgba(102, 126, 234, 0.3);
    color: white;
    border-left: 4px solid #667eea;
}

/* Стиль для выпадающего списка в меню */
QListWidget#dropdown-menu {
    background: #1a202c;
    color: #cbd5e0;
    border: none;
    border-radius: 5px;
    margin: 5px 15px;
    padding: 5px;
}

QListWidget#dropdown-menu::item {
    padding: 10px 15px;
    border-radius: 5px;
    margin: 2px;
    color: #cbd5e0;
}

QListWidget#dropdown-menu::item:hover {
    background: rgba(102, 126, 234, 0.3);
    color: white;
}

QListWidget#dropdown-menu::item:selected {
    background: rgba(102, 126, 234, 0.5);
    color: white;
}

/* Стиль для таблиц */
QTableWidget {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    gridline-color: #e2e8f0;
    selection-background-color: rgba(102, 126, 234, 0.2);
    font-size: 15px;
    color: #2d3748;
}

QTableWidget::item {
    padding: 15px;
    border-bottom: 1px solid #e2e8f0;
    color: #2d3748;
}

QTableWidget::item:selected {
    background-color: rgba(102, 126, 234, 0.2);
    color: #2d3748;
}

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f7fafc, stop:1 #edf2f7);
    padding: 12px 8px;
    border: none;
    border-bottom: 2px solid #cbd5e0;
    border-right: 1px solid #e2e8f0;
    font-weight: bold;
    color: #2d3748;
    font-size: 13px;
}

/* Стиль для полей ввода */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    border: 2px solid #e2e8f0;
    border-radius: 6px;
    padding: 10px;
    font-size: 14px;
    background: white;
    color: #2d3748;
    selection-background-color: #667eea;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 2px solid #667eea;
}

QComboBox {
    color: #2d3748;
}

QComboBox QAbstractItemView {
    background: white;
    color: #2d3748;
    selection-background-color: #667eea;
}

/* Стиль для диалогов */
QDialog {
    background: #f7fafc;
}

QDialog QLabel {
    color: #2d3748;
    font-weight: 600;
    padding: 5px 0;
}

/* Стиль для статус бара */
QStatusBar {
    background: #2d3748;
    color: white;
    padding: 5px;
}

QStatusBar::item {
    border: none;
    color: white;
}

QStatusBar QLabel {
    color: white;
}

/* Карточки для дашборда */
QFrame#card {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin: 10px;
    border: 1px solid #e2e8f0;
}

QLabel#card-title {
    font-size: 16px;
    color: #718096;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}

QLabel#card-value {
    font-size: 36px;
    font-weight: bold;
    color: #2d3748;
    padding: 10px 0;
}

QLabel#card-icon {
    font-size: 48px;
    padding: 10px;
}

/* Для темной темы ОС */
@media (prefers-color-scheme: dark) {
    QMainWindow {
        background-color: #1a1a1a;
    }

    QWidget {
        color: #e0e0e0;
    }

    QLabel {
        color: #e0e0e0;
    }

    QTableWidget {
        background: #2d2d2d;
        border: 1px solid #404040;
        gridline-color: #404040;
        color: #e0e0e0;
    }

    QTableWidget::item {
        border-bottom: 1px solid #404040;
        color: #e0e0e0;
    }

    QHeaderView::section {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #3d3d3d, stop:1 #353535);
        border-bottom: 2px solid #505050;
        border-right: 1px solid #404040;
        color: #e0e0e0;
    }

    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
        background: #2d2d2d;
        color: #e0e0e0;
        border: 2px solid #404040;
    }

    QDialog {
        background: #2d2d2d;
    }

    QDialog QLabel {
        color: #e0e0e0;
    }

    QComboBox QAbstractItemView {
        background: #2d2d2d;
        color: #e0e0e0;
    }
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PackHouse - Клиентская версия")

        # Применяем стили
        self.setStyleSheet(STYLE_SHEET)

        if WarehouseAPI:
            try:
                self.api = WarehouseAPI(server_ip=SERVER_IP, port=SERVER_PORT)
                self.is_connected = self.api.check_connection()
            except Exception as e:
                print(f"Ошибка инициализации API: {e}")
                self.api = None
                self.is_connected = False
        else:
            self.api = None
            self.is_connected = False

        self.setup_ui()

        if not self.is_connected:
            QTimer.singleShot(500, self.show_connection_warning)

    def show_connection_warning(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Ошибка сети")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(f"Не удалось подключиться к серверу {SERVER_IP}")
        msg.setInformativeText("Проверьте работу сервера и API клиента.")
        msg.exec()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = self.create_sidebar()
        self.content_area = QStackedWidget()

        main_layout.addWidget(self.sidebar, 2)  # 22.2% ширины
        main_layout.addWidget(self.content_area, 7)

        self.setup_content_pages()
        self.update_status_bar()

    def update_status_bar(self):
        status = "🟢 В сети" if self.is_connected else "🔴 Оффлайн"
        server_info = f"{SERVER_IP}:{SERVER_PORT}"

        status_widget = QLabel(f"  Статус сервера: {status} | {server_info}  ")

        self.statusBar().addPermanentWidget(status_widget)

        # Добавляем время
        time_label = QLabel(datetime.now().strftime("  %d.%m.%Y %H:%M:%S  "))
        self.statusBar().addPermanentWidget(time_label)

        # Обновляем время каждую секунду
        timer = QTimer(self)
        timer.timeout.connect(lambda: time_label.setText(datetime.now().strftime("  %d.%m.%Y %H:%M:%S  ")))
        timer.start(1000)

    def setup_content_pages(self):
        # Создаем страницы
        self.main_page = self.create_main_dashboard()
        self.stock_page = self.create_stock_page()
        self.receipts_page = self.create_receipts_page()
        self.writeoffs_page = self.create_writeoffs_page()
        self.users_page = self.create_users_page()
        self.sessions_page = self.create_sessions_page()

        # Добавляем в стек
        self.content_area.addWidget(self.main_page)
        self.content_area.addWidget(self.stock_page)
        self.content_area.addWidget(self.receipts_page)
        self.content_area.addWidget(self.writeoffs_page)
        self.content_area.addWidget(self.users_page)
        self.content_area.addWidget(self.sessions_page)

        self.individual_pages = {
            "Главная-Главная": self.main_page,
            "Склад-Остатки": self.stock_page,
            "Склад-Поступления": self.receipts_page,
            "Склад-Списания": self.writeoffs_page,
            "Админ-Пользователи": self.users_page,
            "Админ-Сессии": self.sessions_page,
        }

    def load_table_to_qtablewidget(self, table_type, qtable_widget):

        if not self.is_connected or not self.api:
            qtable_widget.setRowCount(0)
            return

        try:
            api_methods = {
                "stock_page": self.api.get_stock,
                "receipts_page": self.api.get_receipts,
                "writeoffs_page": self.api.get_writeoffs,
                "users_page": self.api.get_users,
                "sessions_page": self.api.get_work_sessions,
            }

            if table_type not in api_methods:
                print(f"Неизвестный тип таблицы: {table_type}")
                return

            data = api_methods[table_type]()

            if not data:
                qtable_widget.setRowCount(0)
                qtable_widget.setColumnCount(0)
                return
            qtable_widget.setAlternatingRowColors(False)
            if isinstance(data, list) and len(data) > 0:
                headers = list(data[0].keys())
                header_labels = []
                for header in headers:
                    translations = {
                        'id': 'ID',
                        'product_name': 'Название',
                        'sku': 'Артикул',
                        'quantity': 'Количество',
                        'unit': 'Ед.',
                        'price': 'Цена',
                        'total': 'Сумма',
                        'supplier': 'Поставщик',
                        'date': 'Дата',
                        'reason': 'Причина',
                        'manager': 'Менеджер',
                        'client': 'Клиент',
                        'username': 'Логин',
                        'name': 'Имя',
                        'surname': 'Фамилия',
                        'is_admin': 'Админ',
                        'created_at': 'Создан',
                        'user_id': 'ID пользователя',
                        'computer_serial': 'Серийник ПК',
                        'session_start': 'Начало сессии',
                        'session_end': 'Конец сессии',
                        'duration_minutes': 'Длительность (мин)',
                        'photo_path': 'Фото'
                    }
                    header_labels.append(translations.get(header, header))

                qtable_widget.setColumnCount(len(headers))
                qtable_widget.setHorizontalHeaderLabels(header_labels)
                qtable_widget.setRowCount(len(data))

                for row_idx, row_data in enumerate(data):
                    for col_idx, key in enumerate(headers):
                        val = row_data.get(key, "")
                        if key in ['price', 'total', 'amount'] and val:
                            try:
                                val = f"{float(val):.2f}"
                            except:
                                pass
                        item = QTableWidgetItem(str(val))
                        item.setBackground(QColor("#ffffff"))
                        qtable_widget.setItem(row_idx, col_idx, item)

                # ===== ДОБАВЛЕННЫЙ КОД ДЛЯ НУМЕРАЦИИ =====
                # Включаем вертикальные заголовки
                qtable_widget.verticalHeader().setVisible(True)

                # Устанавливаем номера строк
                for row_idx in range(qtable_widget.rowCount()):
                    qtable_widget.setVerticalHeaderItem(row_idx, QTableWidgetItem(str(row_idx + 1)))

                # Настраиваем размеры
                qtable_widget.verticalHeader().setDefaultSectionSize(40)
                qtable_widget.verticalHeader().setMinimumWidth(50)
                # ========================================

                qtable_widget.resizeColumnsToContents()

                for i in range(qtable_widget.columnCount()):
                    current_width = qtable_widget.columnWidth(i)
                    qtable_widget.setColumnWidth(i, max(current_width, 100))

            else:
                qtable_widget.setRowCount(0)
                qtable_widget.setColumnCount(0)

        except Exception as e:
            print(f"Ошибка загрузки {table_type}: {e}")
            qtable_widget.setRowCount(0)
            qtable_widget.setColumnCount(0)

    # --- МЕТОДЫ ГЛАВНОЙ ПАНЕЛИ ---
    def create_main_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок
        title = QLabel("Панель управления")
        title.setObjectName("title")
        layout.addWidget(title)

        # СНАЧАЛА СОЗДАЕМ КАРТОЧКИ
        # Карточка 1 - Всего товаров
        self.total_products_card = self.create_stat_card("📦", "Всего товаров", "0")

        # Карточка 2 - Общая стоимость
        self.total_value_card = self.create_stat_card("💰", "Общая стоимость", "0")

        # Карточка 3 - Количество сессий
        self.orders_card = self.create_stat_card("🧩", "Количество сессий", "0")

        # Карточка 4 - Среднее время сессии
        self.sales_card = self.create_stat_card("⏱️", "Среднее время сессии", "0 мин")

        # ТЕПЕРЬ ДОБАВЛЯЕМ ИХ В СЕТКУ
        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        cards_layout.setSpacing(15)

        cards_layout.addWidget(self.total_products_card, 0, 0)
        cards_layout.addWidget(self.total_value_card, 0, 1)
        cards_layout.addWidget(self.orders_card, 1, 0)
        cards_layout.addWidget(self.sales_card, 1, 1)

        layout.addWidget(cards_widget)

        # Кнопка обновления
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addStretch()

        refresh_btn = QPushButton("🔄 Обновить статистику")
        refresh_btn.setObjectName("success")
        refresh_btn.clicked.connect(self.update_dashboard_stats)
        refresh_btn.setMinimumWidth(200)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()

        layout.addWidget(btn_container)
        layout.addStretch()

        # Загружаем начальные данные
        QTimer.singleShot(100, self.update_dashboard_stats)

        return page

    def create_stat_card(self, icon, title, value):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)

        # Иконка и заголовок
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setObjectName("card-icon")
        header_layout.addWidget(icon_label)
        header_layout.addStretch()

        title_label = QLabel(title)
        title_label.setObjectName("card-title")
        header_layout.addWidget(title_label)

        layout.addLayout(header_layout)

        # Значение
        self.value_label = QLabel(value)
        self.value_label.setObjectName("card-value")
        layout.addWidget(self.value_label)

        # Сохраняем ссылку на лейбл значения
        card.value_label = self.value_label
        card.title_label = title_label

        return card

    def update_dashboard_stats(self):
        if not self.is_connected or not self.api:
            QMessageBox.warning(self, "Нет подключения", "Отсутствует подключение к серверу")
            return

        try:
            stats = self.api.get_dashboard_stats()

            if stats:
                # Обновляем значения в карточках
                for card, key in [(self.total_products_card, 'total_products'),
                                  (self.total_value_card, 'total_value'),
                                  (self.orders_card, 'session_count'),
                                  (self.sales_card, 'avg_session_minutes')]:
                    value = stats.get(key, 0)
                    if key == 'total_value':
                        card.value_label.setText(f"{float(value):.2f} ₽")
                    elif key == 'avg_session_minutes':
                        card.value_label.setText(f"{float(value):.1f} мин")
                    else:
                        card.value_label.setText(str(value))
            else:
                # Базовая статистика
                stock_data = self.api.get_stock()
                receipts_data = self.api.get_receipts()

                total_quantity = sum(item.get('quantity', 0) for item in stock_data)
                total_sum = sum(item.get('total', 0) for item in receipts_data)

                self.total_products_card.value_label.setText(str(total_quantity))
                self.total_value_card.value_label.setText(f"{total_sum:.2f} ₽")
                self.orders_card.value_label.setText("0")
                self.sales_card.value_label.setText("0.0 мин")

            QMessageBox.information(self, "✅ Обновлено", "Данные успешно получены с сервера")

        except Exception as e:
            QMessageBox.critical(self, "❌ Ошибка", f"Нет связи с API: {e}")

    # --- РАБОТА С ПОСТУПЛЕНИЯМИ ---
    def create_receipts_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("📥 Поступления")
        title.setObjectName("subtitle")
        layout.addWidget(title)

        # Таблица
        self.receipts_table = QTableWidget()
        self.receipts_table.setAlternatingRowColors(True)
        layout.addWidget(self.receipts_table)

        # Кнопки
        btns_widget = QWidget()
        btns = QHBoxLayout(btns_widget)
        btns.setSpacing(10)

        add_btn = QPushButton("➕ Добавить поступление")
        add_btn.setObjectName("success")
        add_btn.clicked.connect(self.add_receipt)

        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(lambda: self.load_table_to_qtablewidget("receipts_page", self.receipts_table))

        delete_btn = QPushButton("🗑️ Удалить")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self.delete_receipt)

        btns.addWidget(add_btn)
        btns.addWidget(refresh_btn)
        btns.addWidget(delete_btn)
        btns.addStretch()
        layout.addWidget(btns_widget)

        QTimer.singleShot(100, lambda: self.load_table_to_qtablewidget("receipts_page", self.receipts_table))

        return page

    def add_receipt(self):
        if not self.is_connected or not self.api:
            QMessageBox.warning(self, "Нет подключения", "Отсутствует подключение к серверу")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("📦 Новое поступление")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)

        main_layout = QVBoxLayout(dialog)

        # Заголовок
        header = QLabel("📋 Заполните данные о поступлении")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding: 15px;
            background: white;
            border-radius: 10px;
            margin-bottom: 20px;
        """)
        main_layout.addWidget(header)

        form_widget = QWidget()
        l = QFormLayout(form_widget)
        l.setSpacing(15)
        l.setContentsMargins(20, 20, 20, 20)

        name_in = QLineEdit()
        name_in.setPlaceholderText("Введите название товара")
        sku_in = QLineEdit()
        sku_in.setPlaceholderText("Введите артикул")
        qty_in = QDoubleSpinBox()
        qty_in.setRange(0.001, 1000000)
        qty_in.setDecimals(3)
        qty_in.setSuffix(" шт")
        prc_in = QDoubleSpinBox()
        prc_in.setRange(0.01, 10000000)
        prc_in.setDecimals(2)
        prc_in.setPrefix("₽ ")
        sup_in = QLineEdit()
        sup_in.setPlaceholderText("Введите название поставщика")

        total_label = QLabel("₽ 0.00")
        total_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #48bb78;
            padding: 5px;
            background: white;
            border-radius: 5px;
        """)

        def update_total():
            total = qty_in.value() * prc_in.value()
            total_label.setText(f"₽ {total:.2f}")

        qty_in.valueChanged.connect(update_total)
        prc_in.valueChanged.connect(update_total)

        l.addRow("🏷️ Название товара:", name_in)
        l.addRow("🔖 Артикул (SKU):", sku_in)
        l.addRow("📊 Количество:", qty_in)
        l.addRow("💵 Цена за единицу:", prc_in)
        l.addRow("💰 Общая сумма:", total_label)
        l.addRow("🏢 Поставщик:", sup_in)

        main_layout.addWidget(form_widget)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Ok).setText("✅ Добавить")
        bb.button(QDialogButtonBox.StandardButton.Cancel).setText("❌ Отмена")
        bb.accepted.connect(dialog.accept)
        bb.rejected.connect(dialog.reject)
        main_layout.addWidget(bb)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not name_in.text() or not sku_in.text():
                QMessageBox.warning(self, "⚠️ Ошибка", "Название и артикул обязательны!")
                return

            try:
                result = self.api.add_receipt(
                    product_name=name_in.text(),
                    sku=sku_in.text(),
                    quantity=qty_in.value(),
                    unit="шт",
                    price=prc_in.value(),
                    total=qty_in.value() * prc_in.value(),
                    supplier=sup_in.text() or "Не указан"
                )

                if result:
                    QMessageBox.information(self, "✅ Успех", "Поступление успешно добавлено!")
                    self.load_table_to_qtablewidget("receipts_page", self.receipts_table)
                    self.load_table_to_qtablewidget("stock_page", self.stock_table)
                    self.update_dashboard_stats()
                else:
                    QMessageBox.warning(self, "❌ Ошибка", "Сервер не принял данные")

            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка", f"Не удалось добавить поступление: {e}")

    def delete_receipt(self):
        if not self.is_connected or not self.api:
            QMessageBox.warning(self, "Нет подключения", "Отсутствует подключение к серверу")
            return

        current_row = self.receipts_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "⚠️ Предупреждение", "Выберите запись для удаления")
            return

        item_id = self.receipts_table.item(current_row, 0)
        if not item_id:
            return

        receipt_id = item_id.text()

        reply = QMessageBox.question(self, "🗑️ Подтверждение",
                                     f"Вы уверены, что хотите удалить поступление ID: {receipt_id}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.api.delete_receipt(int(receipt_id)):
                    QMessageBox.information(self, "✅ Успех", "Поступление удалено")
                    self.load_table_to_qtablewidget("receipts_page", self.receipts_table)
                else:
                    QMessageBox.warning(self, "❌ Ошибка", "Не удалось удалить поступление")
            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка", f"Ошибка при удалении: {e}")

    # --- РАБОТА СО СПИСАНИЯМИ ---
    def create_writeoffs_page(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setSpacing(15)
        l.setContentsMargins(20, 20, 20, 20)

        title = QLabel("📤 Списания")
        title.setObjectName("subtitle")
        l.addWidget(title)

        self.writeoffs_table = QTableWidget()
        l.addWidget(self.writeoffs_table)

        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setSpacing(10)

        add_btn = QPushButton("➕ Добавить списание")
        add_btn.setObjectName("danger")
        add_btn.clicked.connect(self.add_writeoff)

        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(lambda: self.load_table_to_qtablewidget("writeoffs_page", self.writeoffs_table))

        delete_btn = QPushButton("🗑️ Удалить")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self.delete_writeoff)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        l.addWidget(btn_widget)

        QTimer.singleShot(100, lambda: self.load_table_to_qtablewidget("writeoffs_page", self.writeoffs_table))

        return p

    def add_writeoff(self):
        if not self.is_connected or not self.api:
            QMessageBox.warning(self, "Нет подключения", "Отсутствует подключение к серверу")
            return

        stock_items = self.api.get_stock() or []
        if not stock_items:
            QMessageBox.warning(self, "⚠️ Нет остатков", "Сначала добавьте поступление, чтобы создать остатки для списания.")
            return

        product_options = []
        for item in stock_items:
            name = item.get("Товар") or item.get("product_name") or ""
            sku = item.get("Артикул") or item.get("sku") or ""
            qty = float(item.get("Количество") or item.get("quantity") or 0)
            unit = item.get("Ед_изм") or item.get("unit") or "шт"
            if sku:
                product_options.append({
                    "name": name,
                    "sku": sku,
                    "qty": qty,
                    "unit": unit,
                    "display": f"{name} ({sku}) - доступно: {qty:g} {unit}",
                })

        if not product_options:
            QMessageBox.warning(self, "⚠️ Нет остатков", "Нет валидных позиций на складе для списания.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("📤 Новое списание")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)

        main_layout = QVBoxLayout(dialog)

        header = QLabel("📝 Заполните данные о списании")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding: 15px;
            background: white;
            border-radius: 10px;
            margin-bottom: 20px;
        """)
        main_layout.addWidget(header)

        form_widget = QWidget()
        l = QFormLayout(form_widget)
        l.setSpacing(15)
        l.setContentsMargins(20, 20, 20, 20)

        product_in = QComboBox()
        product_in.addItems([opt["display"] for opt in product_options])
        sku_in = QLineEdit()
        sku_in.setReadOnly(True)
        sku_in.setPlaceholderText("Артикул будет подставлен автоматически")
        qty_in = QDoubleSpinBox()
        qty_in.setRange(0.001, max(product_options[0]["qty"], 0.001))
        qty_in.setDecimals(3)
        qty_in.setSuffix(" шт")
        reason_in = QComboBox()
        reason_in.addItems(["🔧 Брак", "⏰ Истек срок годности", "💔 Повреждение", "📉 Недостача", "📌 Другое"])
        manager_in = QLineEdit()
        manager_in.setPlaceholderText("Введите имя менеджера")

        available_label = QLabel()

        def sync_selected_product():
            selected = product_options[product_in.currentIndex()]
            sku_in.setText(selected["sku"])
            qty_in.setSuffix(f" {selected['unit']}")
            qty_in.setMaximum(max(selected["qty"], 0.001))
            if qty_in.value() > selected["qty"]:
                qty_in.setValue(selected["qty"])
            available_label.setText(f"Доступно на складе: {selected['qty']:g} {selected['unit']}")

        product_in.currentIndexChanged.connect(sync_selected_product)
        sync_selected_product()

        l.addRow("🏷️ Товар со склада:", product_in)
        l.addRow("🔖 Артикул (SKU):", sku_in)
        l.addRow("📦 Остаток:", available_label)
        l.addRow("📊 Количество:", qty_in)
        l.addRow("📋 Причина:", reason_in)
        l.addRow("👤 Менеджер:", manager_in)

        main_layout.addWidget(form_widget)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Ok).setText("✅ Добавить")
        bb.button(QDialogButtonBox.StandardButton.Cancel).setText("❌ Отмена")
        bb.accepted.connect(dialog.accept)
        bb.rejected.connect(dialog.reject)
        main_layout.addWidget(bb)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = product_options[product_in.currentIndex()]
            if not selected["name"] or not selected["sku"]:
                QMessageBox.warning(self, "⚠️ Ошибка", "Не удалось определить товар для списания.")
                return

            try:
                reason_text = reason_in.currentText()
                # Убираем эмодзи из причины
                for emoji in ["🔧 ", "⏰ ", "💔 ", "📉 ", "📌 "]:
                    reason_text = reason_text.replace(emoji, "")

                result = self.api.add_writeoff(
                    product_name=selected["name"],
                    sku=selected["sku"],
                    quantity=qty_in.value(),
                    reason=reason_text,
                    manager=manager_in.text() or "Не указан"
                )

                if result:
                    QMessageBox.information(self, "✅ Успех", "Списание добавлено!")
                    self.load_table_to_qtablewidget("writeoffs_page", self.writeoffs_table)
                    self.load_table_to_qtablewidget("stock_page", self.stock_table)
                    self.update_dashboard_stats()
                else:
                    QMessageBox.warning(self, "❌ Ошибка", "Сервер не принял данные")

            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка", f"Не удалось добавить списание: {e}")

    def delete_writeoff(self):
        if not self.is_connected or not self.api:
            QMessageBox.warning(self, "Нет подключения", "Отсутствует подключение к серверу")
            return

        current_row = self.writeoffs_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "⚠️ Предупреждение", "Выберите запись для удаления")
            return

        item_id = self.writeoffs_table.item(current_row, 0)
        if not item_id:
            return

        writeoff_id = item_id.text()

        reply = QMessageBox.question(self, "🗑️ Подтверждение",
                                     f"Вы уверены, что хотите удалить списание ID: {writeoff_id}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.api.delete_writeoff(int(writeoff_id)):
                    QMessageBox.information(self, "✅ Успех", "Списание удалено")
                    self.load_table_to_qtablewidget("writeoffs_page", self.writeoffs_table)
                else:
                    QMessageBox.warning(self, "❌ Ошибка", "Не удалось удалить списание")
            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка", f"Ошибка при удалении: {e}")

    # --- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ МЕНЮ ---
    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(320)

        layout = QVBoxLayout(sidebar)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Логотип
        logo_widget = QWidget()
        logo_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #667eea, stop:1 #764ba2);
            padding: 20px;
            margin: 0px;
        """)
        logo_layout = QVBoxLayout(logo_widget)

        logo = QLabel("🏠 PackHouse")
        logo.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo)

        subtitle = QLabel("Клиентская версия")
        subtitle.setStyleSheet("""
            color: #cbd5e0;
            font-size: 12px;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(subtitle)

        layout.addWidget(logo_widget)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: #4a5568; max-height: 1px; margin: 0px;")
        layout.addWidget(separator)

        layout.addSpacing(20)

        # Меню
        self.create_main_dropdown(layout)
        self.create_stock_dropdown(layout)
        self.create_admin_dropdown(layout)

        layout.addStretch()

        # Информация о сервере внизу
        info_widget = QWidget()
        info_widget.setStyleSheet("""
            background: #1a202c;
            padding: 15px;
            margin: 0px;
        """)
        info_layout = QVBoxLayout(info_widget)

        server_label = QLabel(f"🖥️ Сервер: {SERVER_IP}")
        server_label.setStyleSheet("color: #cbd5e0; font-size: 12px;")
        info_layout.addWidget(server_label)

        port_label = QLabel(f"🔌 Порт: {SERVER_PORT}")
        port_label.setStyleSheet("color: #cbd5e0; font-size: 12px;")
        info_layout.addWidget(port_label)

        status_label = QLabel("🟢 Онлайн" if self.is_connected else "🔴 Оффлайн")
        status_label.setStyleSheet("color: #cbd5e0; font-size: 12px; font-weight: bold;")
        info_layout.addWidget(status_label)

        layout.addWidget(info_widget)

        return sidebar

    def create_main_dropdown(self, layout):
        btn = QPushButton("🏠 Главная")
        btn.setObjectName("menu-button")
        btn.setCheckable(True)

        lw = QListWidget()
        lw.setObjectName("dropdown-menu")
        lw.setVisible(False)
        lw.addItem("📊 Главная")

        btn.toggled.connect(lambda ch: self.toggle_dropdown(lw, btn, ch))
        lw.itemClicked.connect(lambda i: self.on_list_item_clicked(i, "Главная"))

        layout.addWidget(btn)
        layout.addWidget(lw)

    def create_stock_dropdown(self, layout):
        btn = QPushButton("📦 Склад")
        btn.setObjectName("menu-button")
        btn.setCheckable(True)

        lw = QListWidget()
        lw.setObjectName("dropdown-menu")
        lw.setVisible(False)
        lw.addItems(["📋 Остатки", "📥 Поступления", "📤 Списания"])

        btn.toggled.connect(lambda ch: self.toggle_dropdown(lw, btn, ch))
        lw.itemClicked.connect(lambda i: self.on_list_item_clicked(i, "Склад"))

        layout.addWidget(btn)
        layout.addWidget(lw)

    def create_admin_dropdown(self, layout):
        btn = QPushButton("👥 Админ")
        btn.setObjectName("menu-button")
        btn.setCheckable(True)

        lw = QListWidget()
        lw.setObjectName("dropdown-menu")
        lw.setVisible(False)
        lw.addItems(["👤 Пользователи", "🔌 Сессии"])

        btn.toggled.connect(lambda ch: self.toggle_dropdown(lw, btn, ch))
        lw.itemClicked.connect(lambda i: self.on_list_item_clicked(i, "Админ"))

        layout.addWidget(btn)
        layout.addWidget(lw)

    def toggle_dropdown(self, lw, btn, show):
        lw.setVisible(show)
        text = btn.text()
        # Убираем эмодзи стрелки, чтобы не дублировались
        if text.startswith("▼ "):
            text = text[2:]
        elif text.startswith("▶ "):
            text = text[2:]

        btn.setText(f"{'▼' if show else '▶'} {text}")
        if show:
            lw.setMaximumHeight(lw.count() * 45)

    def on_list_item_clicked(self, item, category):
        item_text = item.text()
        # Убираем эмодзи из текста
        for emoji in ["📊 ", "📋 ", "📥 ", "📤 ", "👤 ", "🔌 "]:
            item_text = item_text.replace(emoji, "")

        key = f"{category}-{item_text}"
        if key in self.individual_pages:
            self.content_area.setCurrentWidget(self.individual_pages[key])

            page_map = {
                "Склад-Остатки": ("stock_page", self.stock_table),
                "Склад-Поступления": ("receipts_page", self.receipts_table),
                "Склад-Списания": ("writeoffs_page", self.writeoffs_table),
                "Админ-Пользователи": ("users_page", self.users_table),
                "Админ-Сессии": ("sessions_page", self.sessions_table),
            }
            if key in page_map:
                table_type, table_widget = page_map[key]
                self.load_table_to_qtablewidget(table_type, table_widget)

    def create_stock_page(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setSpacing(15)
        l.setContentsMargins(20, 20, 20, 20)

        title = QLabel("📋 Остатки на складе")
        title.setObjectName("subtitle")
        l.addWidget(title)

        self.stock_table = QTableWidget()
        l.addWidget(self.stock_table)

        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)

        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(lambda: self.load_table_to_qtablewidget("stock_page", self.stock_table))

        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        l.addWidget(btn_widget)

        QTimer.singleShot(100, lambda: self.load_table_to_qtablewidget("stock_page", self.stock_table))

        return p

    def create_users_page(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setSpacing(15)
        l.setContentsMargins(20, 20, 20, 20)

        title = QLabel("👤 Пользователи")
        title.setObjectName("subtitle")
        l.addWidget(title)

        self.users_table = QTableWidget()
        l.addWidget(self.users_table)

        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(lambda: self.load_table_to_qtablewidget("users_page", self.users_table))
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        l.addWidget(btn_widget)

        QTimer.singleShot(100, lambda: self.load_table_to_qtablewidget("users_page", self.users_table))
        return p

    def create_sessions_page(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setSpacing(15)
        l.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🔌 Сессии подключений")
        title.setObjectName("subtitle")
        l.addWidget(title)

        self.sessions_table = QTableWidget()
        l.addWidget(self.sessions_table)

        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(lambda: self.load_table_to_qtablewidget("sessions_page", self.sessions_table))
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        l.addWidget(btn_widget)

        QTimer.singleShot(100, lambda: self.load_table_to_qtablewidget("sessions_page", self.sessions_table))
        return p


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())