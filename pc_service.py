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
import signal
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional
import logging

SERVER_URL = "http://localhost:5000"
VERSION = "PackUnic"
CODE_LIFETIME = 120
CHECK_INTERVAL = 1
AUTHORIZED_FLAG_FILE = "authorized.flag"

TEMP_DIR = os.path.join(tempfile.gettempdir(), "SessionLogger")
SESSION_FILE = os.path.join(TEMP_DIR, "current_session.json")
PHOTOS_DIR = os.path.join(TEMP_DIR, "photos")
QR_CODES_DIR = os.path.join(TEMP_DIR, "qr_codes")
LOG_FILE = os.path.join(TEMP_DIR, "service.log")
PID_FILE = os.path.join(TEMP_DIR, "service.pid")
SESSIONS_DIR = os.path.join(TEMP_DIR, "sessions")
AUTHORIZED_FILE = os.path.join(TEMP_DIR, AUTHORIZED_FLAG_FILE)

for dir_path in [TEMP_DIR, PHOTOS_DIR, QR_CODES_DIR, SESSIONS_DIR]:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def to_safe_filename(value: str, fallback: str = "unknown") -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in str(value))
    safe = safe.strip("._")
    return safe or fallback


def get_computer_serial():
    invalid_serials = {
        "to be filled by o.e.m.",
        "to be filled by o.e.m",
        "default string",
        "none",
        "system serial number",
        "",
    }

    def _is_valid(serial_value: str) -> bool:
        return bool(serial_value) and serial_value.strip().lower() not in invalid_serials

    try:
        result = subprocess.run(
            [
                'powershell',
                '-NoProfile',
                '-Command',
                '(Get-CimInstance -ClassName Win32_BIOS).SerialNumber'
            ],
            capture_output=True,
            timeout=7
        )
        serial = result.stdout.decode('utf-8', errors='ignore').strip()
        if _is_valid(serial):
            logger.info(f"Получен серийный номер через PowerShell CIM: {serial}")
            return serial
    except Exception as e:
        logger.error(f"Ошибка получения serial через CIM: {e}")

    try:
        result = subprocess.run(
            [
                'powershell',
                '-NoProfile',
                '-Command',
                'Get-WmiObject Win32_BIOS | Select-Object -ExpandProperty SerialNumber'
            ],
            capture_output=True,
            timeout=7
        )
        serial = result.stdout.decode('utf-8', errors='ignore').strip()
        if _is_valid(serial):
            logger.info(f"Получен серийный номер через PowerShell: {serial}")
            return serial
    except Exception as e:
        logger.error(f"Ошибка PowerShell: {e}")

    try:
        machine_uuid = str(uuid.getnode())
        if _is_valid(machine_uuid):
            logger.warning(f"Использую machine id (uuid.getnode): {machine_uuid}")
            return machine_uuid
    except Exception as e:
        logger.error(f"Ошибка получения machine id: {e}")

    computer_name = socket.gethostname()
    logger.warning(f"Использую имя компьютера: {computer_name}")
    return computer_name


def is_authorized():
    return os.path.exists(AUTHORIZED_FILE)


def mark_authorized():
    try:
        with open(AUTHORIZED_FILE, 'w') as f:
            f.write(f"Authorized at: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Computer: {COMPUTER_SERIAL}\n")
        logger.info(f"Компьютер {COMPUTER_SERIAL} отмечен как авторизованный")
        return True
    except Exception as e:
        logger.error(f"Ошибка отметки авторизации: {e}")
        return False


def reset_authorization():
    try:
        if os.path.exists(AUTHORIZED_FILE):
            os.remove(AUTHORIZED_FILE)
            logger.info(f"🔄 Авторизация сброшена для {COMPUTER_SERIAL}")

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
    try:
        import cv2

        for camera_id in [0, 1]:
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            if cap.isOpened():
                time.sleep(0.5)
                ret, frame = cap.read()
                if ret and frame is not None:
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    photo_base64 = base64.b64encode(buffer).decode('utf-8')
                    cap.release()

                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_serial = to_safe_filename(COMPUTER_SERIAL)
                    local_path = os.path.join(PHOTOS_DIR, f"photo_{safe_serial}_{timestamp}.jpg")
                    with open(local_path, 'wb') as f:
                        f.write(base64.b64decode(photo_base64))

                    logger.info(f"📸 Фото сохранено: {local_path}")
                    return photo_base64
                cap.release()

        logger.warning("Не удалось сделать фото")
        return None
    except Exception as e:
        logger.error(f"Ошибка камеры: {e}")
        return None


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


class WebAPIClient:

    def __init__(self, server_url=SERVER_URL):
        self.server_url = server_url
        logger.info(f"🌐 WebAPI клиент: {server_url}")

    def create_session(self, computer_serial):
        try:
            response = requests.post(
                f"{self.server_url}/api/create_session",
                json={"computer_serial": computer_serial},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Сессия создана: {data}")
                return data
        except Exception as e:
            logger.error(f"Ошибка создания сессии: {e}")
        return None

    def check_verification(self, computer_serial):
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
            logger.info(f"Сессия: {computer_serial} - {code}")
            return session

    def _generate_qr(self, url: str, computer_serial: str, code: str):
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            safe_serial = to_safe_filename(computer_serial)
            filename = f"QR_{safe_serial}_{code}.png"
            filepath = os.path.join(QR_CODES_DIR, filename)
            img.save(filepath)

            return filepath
        except Exception as e:
            logger.error(f"Ошибка создания QR: {e}")
            return None


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


class SystemMonitor:
    def __init__(self, api_client: WebAPIClient, computer_serial: str):
        self.api_client = api_client
        self.computer_serial = computer_serial
        self.running = True
        self.session_active = False

    def start_monitoring(self):
        self.session_active = True
        self.api_client.start_work_session(self.computer_serial)
        logger.info("📊 Мониторинг сессии запущен")

    def stop_monitoring(self):
        if self.session_active:
            result = self.api_client.end_work_session(self.computer_serial)
            if result.get('success'):
                logger.info(f"📊 Сессия завершена, длительность: {result.get('duration', 0)} мин")
            self.session_active = False

    def run(self):
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        while self.running:
            time.sleep(5)

            if not is_authorized():
                if self.session_active:
                    logger.info("💤 Авторизация сброшена, завершаем сессию")
                    self.stop_monitoring()
                continue

            hwnd = user32.GetForegroundWindow()

            try:
                last_check = time.time()
            except:
                pass


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
        try:
            with open(PID_FILE, 'w') as f:
                f.write(str(os.getpid()))

            monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            monitor_thread.start()

            while self.running:
                if is_authorized():
                    if not self.work_session_started:
                        logger.info(f"✅ Компьютер авторизован")
                        self._start_work_session()
                else:
                    logger.info(f"🔒 Компьютер не авторизован")
                    if self.work_session_started:
                        self._end_work_session()

                    while self.running and not is_authorized():
                        session = self.session_manager.create_session(self.computer_serial)

                        if session:
                            display = ComputerDisplay(session, self.computer_serial)
                            display_thread = threading.Thread(target=display.show, daemon=True)
                            display_thread.start()

                            wait_time = 0
                            while wait_time < CODE_LIFETIME and not is_authorized() and self.running:
                                verification_data = self.api_client.check_verification(self.computer_serial)

                                if verification_data.get('verified'):
                                    mark_authorized()
                                    session.unlock_event.set()
                                    logger.info(f"✅ КОМПЬЮТЕР РАЗБЛОКИРОВАН!")

                                    photo = take_photo()
                                    if photo:
                                        self.api_client.upload_photo(self.computer_serial, photo)

                                    self._start_work_session()
                                    break

                                time.sleep(2)
                                wait_time += 2

                            if not is_authorized():
                                continue
                            else:
                                break
                        else:
                            time.sleep(10)

                time.sleep(5)

        except KeyboardInterrupt:
            logger.info("👋 Завершение работы по сигналу")
        except Exception as e:
            logger.error(f"❌ Ошибка в службе: {e}")
        finally:
            self.running = False
            self._end_work_session()
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            try:
                import shutil
                if os.path.exists(TEMP_DIR):
                    shutil.rmtree(TEMP_DIR)
                    logger.info("🗑 Временные файлы очищены")
            except Exception as e:
                logger.error(f"Ошибка очистки временных файлов: {e}")

    def _start_work_session(self):
        if not self.work_session_started:
            result = self.api_client.start_work_session(self.computer_serial)
            if result.get('success'):
                self.work_session_started = True
                logger.info("📊 Рабочая сессия начата")

    def _end_work_session(self):
        if self.work_session_started:
            result = self.api_client.end_work_session(self.computer_serial)
            if result.get('success'):
                self.work_session_started = False
                logger.info(f"📊 Рабочая сессия завершена, длительность: {result.get('duration', 0)} мин")

    def _monitor_loop(self):
        import ctypes

        while self.running:
            time.sleep(30)

            if not is_authorized():
                if self.work_session_started:
                    logger.info("💤 Обнаружен сброс авторизации, завершаем сессию")
                    self._end_work_session()
                continue

            try:
                last_input = ctypes.windll.user32.GetLastInputInfo()

                if not os.path.exists(AUTHORIZED_FILE):
                    logger.info("💤 Файл авторизации исчез, возможно система была в сне")
                    self._end_work_session()

                    try:
                        import shutil
                        shutil.rmtree(TEMP_DIR)
                        logger.info("🗑 Папка SessionLogger очищена")
                    except:
                        pass
            except:
                pass


COMPUTER_SERIAL = get_computer_serial()


def signal_handler(signum, frame):
    logger.info(f"Получен сигнал {signum}, завершение работы...")
    if 'service' in globals():
        service.running = False


def main():
    print(f"💻 Серийный номер: {COMPUTER_SERIAL}")
    print(f"🌐 Сервер: {SERVER_URL}")

    if os.path.exists(PID_FILE):
        print("⚠️ Программа уже запущена!")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        import win32api
        win32api.SetConsoleCtrlHandler(lambda event: signal_handler(event, None), True)
    except ImportError:
        pass

    global service
    service = SessionService()
    try:
        service.run()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Программа завершена")
        sys.exit(0)


if __name__ == "__main__":
    main()