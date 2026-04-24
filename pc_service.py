import os
import sys
import json
import socket
import datetime
import time
import tempfile
import threading
import random
import string
import requests
import subprocess
import uuid
import base64
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional
import logging

# ==================== КОНФИГУРАЦИЯ ====================
SERVER_URL = "http://localhost:5000"
VERSION = "25.4"
CODE_LIFETIME = 120
CHECK_INTERVAL = 1
AUTHORIZED_FLAG_FILE = "authorized.flag"

# ==================== ПУТИ ====================
TEMP_DIR = os.path.join(tempfile.gettempdir(), "SessionLogger")
SESSION_FILE = os.path.join(TEMP_DIR, "current_session.json")
PHOTOS_DIR = os.path.join(TEMP_DIR, "photos")
QR_CODES_DIR = os.path.join(TEMP_DIR, "qr_codes")
LOG_FILE = os.path.join(TEMP_DIR, "service.log")
PID_FILE = os.path.join(TEMP_DIR, "service.pid")
SESSIONS_DIR = os.path.join(TEMP_DIR, "sessions")
AUTHORIZED_FILE = os.path.join(TEMP_DIR, AUTHORIZED_FLAG_FILE)

# Создаем все папки
for dir_path in [TEMP_DIR, PHOTOS_DIR, QR_CODES_DIR, SESSIONS_DIR]:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

# ==================== НАСТРОЙКА ЛОГГИРОВАНИЯ ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С СИСТЕМОЙ ====================
def get_computer_serial():
    """Получить серийный номер компьютера"""

    try:
        result = subprocess.run(
            ['wmic', 'bios', 'get', 'serialnumber'],
            capture_output=True,
            timeout=5
        )

        output = result.stdout.decode('utf-8', errors='ignore')
        lines = output.strip().split('\n')

        if len(lines) >= 2:
            serial = lines[1].strip()
            if serial and serial not in [
                "To be filled by O.E.M.",
                "To be filled by O.E.M",
                "Default string",
                "None",
                "System Serial Number",
                ""
            ]:
                logger.info(f"✅ Получен серийный номер через wmic: {serial}")
                return serial
    except Exception as e:
        logger.error(f"❌ Ошибка wmic: {e}")

    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-WmiObject win32_bios | Select-Object -ExpandProperty SerialNumber'],
            capture_output=True,
            timeout=5
        )

        serial = result.stdout.decode('utf-8', errors='ignore').strip()
        if serial and serial not in ["To be filled by O.E.M.", "Default string", ""]:
            logger.info(f"✅ Получен серийный номер через PowerShell: {serial}")
            return serial
    except Exception as e:
        logger.error(f"❌ Ошибка PowerShell: {e}")

    computer_name = socket.gethostname()
    logger.warning(f"⚠️ Использую имя компьютера: {computer_name}")
    return computer_name


def is_authorized():
    """Проверить, авторизован ли компьютер"""
    return os.path.exists(AUTHORIZED_FILE)


def mark_authorized():
    """Отметить компьютер как авторизованный"""
    try:
        with open(AUTHORIZED_FILE, 'w') as f:
            f.write(f"Authorized at: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Computer: {COMPUTER_SERIAL}\n")
        logger.info(f"✅ Компьютер {COMPUTER_SERIAL} отмечен как авторизованный")
        return True
    except Exception as e:
        logger.error(f"Ошибка отметки авторизации: {e}")
        return False


def reset_authorization():
    """Сбросить авторизацию"""
    try:
        if os.path.exists(AUTHORIZED_FILE):
            os.remove(AUTHORIZED_FILE)
            logger.info(f"🔄 Авторизация сброшена для {COMPUTER_SERIAL}")

            # Уведомляем сервер о завершении сессии
            try:
                requests.post(f"{SERVER_URL}/api/session/end",
                              json={"computer_serial": COMPUTER_SERIAL}, timeout=5)
            except:
                pass

            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка сброса авторизации: {e}")
        return False


def take_photo():
    """Сделать фото с веб-камеры"""
    try:
        import cv2

        for camera_id in [0, 1]:
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            if cap.isOpened():
                time.sleep(0.5)  # Прогрев камеры
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Конвертируем в base64
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    photo_base64 = base64.b64encode(buffer).decode('utf-8')
                    cap.release()

                    # Сохраняем локально
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    local_path = os.path.join(PHOTOS_DIR, f"photo_{COMPUTER_SERIAL}_{timestamp}.jpg")
                    with open(local_path, 'wb') as f:
                        f.write(base64.b64decode(photo_base64))

                    logger.info(f"📸 Фото сохранено: {local_path}")
                    return photo_base64
                cap.release()

        logger.warning("⚠️ Не удалось сделать фото")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка камеры: {e}")
        return None


# ==================== ДАТАКЛАССЫ ====================
@dataclass
class Session:
    session_id: str
    computer_serial: str
    code: str
    qr_path: str
    unlock_url: str
    created_at: float
    expires_at: float
    verified: bool = False
    unlock_event: Optional[threading.Event] = None

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


# ==================== WEB API КЛИЕНТ ====================
class WebAPIClient:
    """Клиент для работы с веб-сервером"""

    def __init__(self, server_url=SERVER_URL):
        self.server_url = server_url
        logger.info(f"🌐 WebAPI клиент: {server_url}")

    def create_session(self, computer_serial):
        """Создать сессию на сервере"""
        try:
            response = requests.post(
                f"{self.server_url}/api/create_session",
                json={"computer_serial": computer_serial},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Сессия создана: {data}")
                return data
        except Exception as e:
            logger.error(f"❌ Ошибка создания сессии: {e}")
        return None

    def check_verification(self, computer_serial):
        """Проверить статус верификации"""
        try:
            response = requests.get(
                f"{self.server_url}/api/check_session/{computer_serial}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data
        except:
            pass
        return {'verified': False}

    def start_work_session(self, computer_serial):
        """Начать рабочую сессию"""
        try:
            response = requests.post(
                f"{self.server_url}/api/session/start",
                json={"computer_serial": computer_serial},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {'success': False}

    def end_work_session(self, computer_serial):
        """Завершить рабочую сессию"""
        try:
            response = requests.post(
                f"{self.server_url}/api/session/end",
                json={"computer_serial": computer_serial},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {'success': False}

    def upload_photo(self, computer_serial, photo_base64):
        """Загрузить фото на сервер"""
        try:
            response = requests.post(
                f"{self.server_url}/api/session/photo",
                json={"computer_serial": computer_serial, "photo": photo_base64},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {'success': False}


# ==================== МЕНЕДЖЕР СЕССИЙ ====================
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.lock = threading.Lock()
        self.api_client = WebAPIClient()
        logger.info("SessionManager инициализирован")

    def create_session(self, computer_serial: str) -> Optional[Session]:
        if is_authorized():
            return None

        with self.lock:
            session_data = self.api_client.create_session(computer_serial)
            if not session_data:
                return None

            code = session_data['code']
            unlock_url = session_data['unlock_url']
            session_id = str(uuid.uuid4())

            qr_path = self._generate_qr(unlock_url, computer_serial, code)
            if not qr_path:
                return None

            session = Session(
                session_id=session_id,
                computer_serial=computer_serial,
                code=code,
                qr_path=qr_path,
                unlock_url=unlock_url,
                created_at=time.time(),
                expires_at=time.time() + CODE_LIFETIME,
                unlock_event=threading.Event()
            )

            self.sessions[session_id] = session
            logger.info(f"✅ Сессия: {computer_serial} - {code}")
            return session

    def _generate_qr(self, url: str, computer_serial: str, code: str):
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            filename = f"QR_{computer_serial}_{code}.png"
            filepath = os.path.join(QR_CODES_DIR, filename)
            img.save(filepath)

            return filepath
        except Exception as e:
            logger.error(f"❌ Ошибка создания QR: {e}")
            return None


# ==================== ДИСПЛЕЙ ====================
class ComputerDisplay:
    def __init__(self, session: Session, computer_serial: str):
        self.session = session
        self.computer_serial = computer_serial
        self.unlock_event = session.unlock_event

    def show(self) -> bool:
        try:
            import tkinter as tk
            from PIL import Image, ImageTk

            root = tk.Tk()
            root.title(f"АВТОРИЗАЦИЯ - {self.computer_serial}")
            root.attributes('-fullscreen', True)
            root.attributes('-topmost', True)
            root.configure(bg='#2c3e50')

            tk.Label(
                root, text="🔐 АВТОРИЗАЦИЯ", font=('Arial', 32, 'bold'),
                bg='#2c3e50', fg='white', pady=20
            ).pack()

            if os.path.exists(self.session.qr_path):
                pil_image = Image.open(self.session.qr_path)
                screen_width = root.winfo_screenwidth()
                max_size = min(screen_width - 200, 400)
                pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(pil_image)

                tk.Label(root, image=photo, bg='white').pack(pady=10)
                root.image = photo

            tk.Label(
                root, text=f"СЕРИЙНЫЙ НОМЕР: {self.computer_serial}",
                font=('Arial', 14), bg='#2c3e50', fg='#3498db'
            ).pack(pady=10)

            tk.Label(
                root, text=f"КОД: {self.session.code}",
                font=('Courier', 48, 'bold'), bg='#2c3e50', fg='#e74c3c'
            ).pack(pady=10)

            status_label = tk.Label(
                root, text="⏳ ОЖИДАНИЕ АВТОРИЗАЦИИ...",
                font=('Arial', 16, 'bold'), bg='#2c3e50', fg='#f1c40f'
            )
            status_label.pack(pady=20)

            def check_unlock():
                if self.unlock_event.is_set():
                    status_label.config(text="✅ АВТОРИЗАЦИЯ ПОДТВЕРЖДЕНА!", fg='#2ecc71')
                    root.after(2000, root.destroy)
                else:
                    root.after(500, check_unlock)

            root.after(500, check_unlock)
            root.mainloop()

            return self.unlock_event.is_set()

        except Exception as e:
            logger.error(f"❌ Ошибка отображения: {e}")
            return False


# ==================== МОНИТОР СИСТЕМЫ ====================
class SystemMonitor:
    """Мониторинг состояния системы (сон/блокировка)"""

    def __init__(self, api_client: WebAPIClient, computer_serial: str):
        self.api_client = api_client
        self.computer_serial = computer_serial
        self.running = True
        self.session_active = False

    def start_monitoring(self):
        """Запустить мониторинг"""
        self.session_active = True
        self.api_client.start_work_session(self.computer_serial)
        logger.info("📊 Мониторинг сессии запущен")

    def stop_monitoring(self):
        """Остановить мониторинг"""
        if self.session_active:
            result = self.api_client.end_work_session(self.computer_serial)
            if result.get('success'):
                logger.info(f"📊 Сессия завершена, длительность: {result.get('duration', 0)} мин")
            self.session_active = False

    def run(self):
        """Основной цикл мониторинга"""
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        while self.running:
            time.sleep(5)  # Проверяем каждые 5 секунд

            if not is_authorized():
                if self.session_active:
                    logger.info("💤 Авторизация сброшена, завершаем сессию")
                    self.stop_monitoring()
                continue

            # Проверяем, не заблокирован ли экран
            # GetForegroundWindow и проверка на Secure Desktop
            hwnd = user32.GetForegroundWindow()

            # Проверяем, не в спящем ли режиме система
            # Для этого проверяем время последнего ответа
            try:
                # Пингуем себя чтобы проверить что система не спит
                last_check = time.time()
            except:
                pass


# ==================== ОСНОВНАЯ СЛУЖБА ====================
class SessionService:
    def __init__(self):
        self.computer_serial = COMPUTER_SERIAL
        self.running = True
        self.session_manager = SessionManager()
        self.api_client = WebAPIClient()
        self.monitor = SystemMonitor(self.api_client, self.computer_serial)
        self.work_session_started = False
        logger.info(f"Служба запущена для: {self.computer_serial}")

    def run(self):
        """Запуск службы"""
        try:
            with open(PID_FILE, 'w') as f:
                f.write(str(os.getpid()))

            # Запускаем мониторинг в отдельном потоке
            monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            monitor_thread.start()

            if is_authorized():
                logger.info(f"✅ Компьютер уже авторизован")
                self._start_work_session()

                while self.running:
                    time.sleep(10)
                    if not is_authorized():
                        logger.info("🔄 Авторизация сброшена")
                        self._end_work_session()
                        break
            else:
                logger.info(f"🔒 Компьютер не авторизован")

                while self.running and not is_authorized():
                    session = self.session_manager.create_session(self.computer_serial)

                    if session:
                        display = ComputerDisplay(session, self.computer_serial)
                        display_thread = threading.Thread(target=display.show, daemon=True)
                        display_thread.start()

                        wait_time = 0
                        while wait_time < CODE_LIFETIME and not is_authorized():
                            verification_data = self.api_client.check_verification(self.computer_serial)

                            if verification_data.get('verified'):
                                mark_authorized()
                                session.unlock_event.set()
                                logger.info(f"✅ КОМПЬЮТЕР РАЗБЛОКИРОВАН!")

                                # Делаем фото
                                photo = take_photo()
                                if photo:
                                    self.api_client.upload_photo(self.computer_serial, photo)

                                # Начинаем рабочую сессию
                                self._start_work_session()
                                break

                            time.sleep(2)
                            wait_time += 2
                    else:
                        time.sleep(10)

        except KeyboardInterrupt:
            logger.info("👋 Завершение работы")
            self._end_work_session()
        except Exception as e:
            logger.error(f"❌ Ошибка в службе: {e}")
            self._end_work_session()
        finally:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)

    def _start_work_session(self):
        """Начать рабочую сессию"""
        if not self.work_session_started:
            result = self.api_client.start_work_session(self.computer_serial)
            if result.get('success'):
                self.work_session_started = True
                logger.info("📊 Рабочая сессия начата")

    def _end_work_session(self):
        """Завершить рабочую сессию"""
        if self.work_session_started:
            result = self.api_client.end_work_session(self.computer_serial)
            if result.get('success'):
                self.work_session_started = False
                logger.info(f"📊 Рабочая сессия завершена, длительность: {result.get('duration', 0)} мин")

    def _monitor_loop(self):
        """Цикл мониторинга состояния системы"""
        import ctypes

        while self.running:
            time.sleep(30)  # Проверяем каждые 30 секунд

            if not is_authorized():
                if self.work_session_started:
                    logger.info("💤 Обнаружен сброс авторизации, завершаем сессию")
                    self._end_work_session()
                continue

            # Проверяем, не в спящем ли режиме система
            try:
                # Проверяем активность системы
                last_input = ctypes.windll.user32.GetLastInputInfo()

                # Если система была в сне, авторизация могла сброситься
                # Проверяем файл авторизации
                if not os.path.exists(AUTHORIZED_FILE):
                    logger.info("💤 Файл авторизации исчез, возможно система была в сне")
                    self._end_work_session()

                    # Очищаем Temp папку
                    try:
                        import shutil
                        shutil.rmtree(TEMP_DIR)
                        logger.info("🗑 Папка SessionLogger очищена")
                    except:
                        pass
            except:
                pass


# ==================== ТОЧКА ВХОДА ====================
COMPUTER_SERIAL = get_computer_serial()


def main():
    print("=" * 70)
    print(f"🚀 UNLOCK SYSTEM v{VERSION}")
    print("=" * 70)
    print(f"💻 Серийный номер: {COMPUTER_SERIAL}")
    print(f"🌐 Сервер: {SERVER_URL}")
    print("=" * 70)

    if os.path.exists(PID_FILE):
        print("⚠️ Программа уже запущена!")
        sys.exit(0)

    service = SessionService()
    try:
        service.run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()