"""Constants for VAIWA Cloud Home Assistant integration."""

DOMAIN = "vaiwa"
DATABASE_URL = "https://vaiwa-vaiwagroup-default-rtdb.europe-west1.firebasedatabase.app"
FIREBASE_API_KEY = "api_key"  # legacy field (previously saved in config entries)
# Public Firebase Web API key of the official VAIWA Firebase project.
# Developer: replace this ONE value before publishing the HACS repository.
# Do not put a service account JSON key here.
PUBLIC_FIREBASE_WEB_API_KEY = "AIzaSyCCsyEPnA24otBM2FepZEW8KxTIMet5X8w"
REFRESH_TOKEN = "refresh_token"
FIREBASE_UID = "uid"
SCAN_INTERVAL_SECONDS = 15

AUTH_SIGNIN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
AUTH_REFRESH_URL = "https://securetoken.googleapis.com/v1/token"
