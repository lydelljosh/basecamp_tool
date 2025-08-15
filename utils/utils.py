import json
import os
import re
import unicodedata

CONFIG_FILE = "config.json"
BASE_URL = "https://3.basecampapi.com"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def validate_config(config):
    """Validate configuration has required fields"""
    required_fields = ['client_id', 'client_secret']
    missing = [field for field in required_fields if not config.get(field)]
    
    if missing:
        raise ValueError(f"Missing required config fields: {missing}")
    
    # Check for session auth fields if needed
    if config.get('username') and not config.get('password'):
        print_error("Warning: username provided but password missing - session auth may fail")
    elif config.get('password') and not config.get('username'):
        print_error("Warning: password provided but username missing - session auth may fail")
    
    return True

def get_account_id():
    config = load_config()
    return config.get("account_id")

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def print_success(msg):
    print(f"[SUCCESS] {msg}")

def print_error(msg):
    print(f"[ERROR] {msg}")

def clean_special_characters(text):
    """Clean special characters from text while preserving proper spacing"""
    if not text:
        return text
    
    # Replace em dashes and en dashes with regular hyphens
    text = text.replace('–', '-')
    text = text.replace('—', '-')
    
    # Replace curly quotes with straight quotes
    text = text.replace('"', '"')
    text = text.replace('"', '"')
    text = text.replace(''', "'")
    text = text.replace(''', "'")
    
    # Replace other common special characters
    text = text.replace('…', '...')
    text = text.replace('•', '*')
    
    # Keep only ASCII characters that make sense in English
    cleaned = ''
    for char in text:
        if ord(char) <= 127:  # ASCII characters
            cleaned += char  # Keep all ASCII as-is
        else:
            # For non-ASCII, try to normalize to ASCII equivalent
            try:
                normalized = unicodedata.normalize('NFKD', char)
                ascii_equivalent = ''.join([c for c in normalized if ord(c) <= 127])
                if ascii_equivalent:
                    cleaned += ascii_equivalent
                else:
                    cleaned += ' '
            except Exception:
                # If Unicode normalization fails, replace with space
                cleaned += ' '
    
    # Only clean up excessive whitespace (3+ spaces), preserve normal spacing
    cleaned = re.sub(r' {3,}', ' ', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned

def sanitize_csv_field(text):
    """Clean text for CSV compatibility across platforms (Windows/macOS)"""
    if not text:
        return text
    
    # Remove base64 encoded data (common in embedded images)
    # Pattern matches base64 strings that are typically very long
    cleaned = re.sub(r'[A-Za-z0-9+/]{100,}={0,2}', '[base64 data removed]', text)
    
    # Replace any newlines (both \n and \r\n) with spaces for CSV compatibility
    # This prevents Windows CSV readers from breaking rows on internal newlines
    cleaned = re.sub(r'\r?\n', ' ', cleaned)
    
    # Clean up multiple consecutive spaces
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    
    # Trim leading/trailing spaces
    cleaned = cleaned.strip()
    
    # Limit field length to prevent extremely long text from breaking CSV readers
    if len(cleaned) > 5000:
        cleaned = cleaned[:4997] + "..."
    
    return cleaned

def save_to_json(data, filename="output.json"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print_success(f"Saved extracted data to {filename}")
    except Exception as e:
        print_error(f"Failed to save JSON: {e}")
