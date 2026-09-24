import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR / "db"
DASHBOARD_DIR = BASE_DIR / "dashboard"

DATABASE_URL = f"sqlite:///{DB_DIR / 'foxflow.db'}"

HOST = "127.0.0.1"
PORT = 8000

EYE_TRACK_INTERVAL_MS = 500          
EYE_TRACK_SAVE_INTERVAL_S = 300      
EYE_FOCUS_THRESHOLD = 0.25         

APP_TRACK_INTERVAL_S = 2            

WEB_TRACK_INTERVAL_S = 30           
CHROME_HISTORY_PATH = os.path.expanduser(
    r"~\AppData\Local\Google\Chrome\User Data\Default\History"
)
EDGE_HISTORY_PATH = os.path.expanduser(
    r"~\AppData\Local\Microsoft\Edge\User Data\Default\History"
)


INPUT_AGGREGATE_INTERVAL_S = 300    

FOCUS_WEIGHTS = {
    "eye_focus": 0.40,
    "input_activity": 0.30,
    "app_consistency": 0.20,
    "no_distractions": 0.10,
}

POMODORO_WORK_MINUTES = 25
POMODORO_BREAK_MINUTES = 5
POMODORO_LONG_BREAK_MINUTES = 15
POMODORO_SESSIONS_BEFORE_LONG_BREAK = 4

HOSTS_FILE_PATH = r"C:\Windows\System32\drivers\etc\hosts"
BLOCK_REDIRECT_IP = "127.0.0.1"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
AI_MODEL = "gemini-2.5-flash"

DEFAULT_DISTRACTING_DOMAINS = [
    "instagram.com", "facebook.com", "twitter.com", "x.com",
    "tiktok.com", "reddit.com", "youtube.com", "netflix.com",
]
