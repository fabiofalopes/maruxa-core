from dotenv import load_dotenv, find_dotenv
import os
import json
#import litellm

#litellm.set_verbose(True)

# Debug prints
print(f"Looking for .env file at: {find_dotenv()}")
print(f"Current working directory: {os.getcwd()}")

load_dotenv()

# Debug prints for GROQ_API_KEY
#print("\nEnvironment Variables Debug:")
#print(f"GROQ_API_KEY present: {'GROQ_API_KEY' in os.environ}")
#print(f"GROQ_API_KEY length: {len(os.getenv('GROQ_API_KEY', ''))} characters")
#print(f"GROQ_API_KEY value: {os.getenv('GROQ_API_KEY', '')}")  # Be careful with this in production!
#print(f"All .env files in current directory: {[f for f in os.listdir('.') if '.env' in f]}")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Define the path for the config file
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'audio_config.json')

def load_config():
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, 'r') as f:
            return json.load(f)
    return {}

# Load the audio configuration
AUDIO_CONFIG = load_config()

# Define paths for recordings and voice outputs
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Go up one more level
RECORDINGS_DIR = os.path.join(PROJECT_ROOT, '.recordings')
VOICE_OUTPUTS_DIR = os.path.join(PROJECT_ROOT, '.voice_outputs')

# Ensure directories exist
os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(VOICE_OUTPUTS_DIR, exist_ok=True)

LOCAL_LLM_BASE_URL = "http://192.168.108.80:4000/v1"
LOCAL_LLM_API_KEY = "sk-1234"
