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
            except:
                cleaned += ' '
    
    # Only clean up excessive whitespace (3+ spaces), preserve normal spacing
    cleaned = re.sub(r' {3,}', ' ', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned

def save_to_json(data, filename="output.json"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print_success(f"Saved extracted data to {filename}")
    except Exception as e:
        print_error(f"Failed to save JSON: {e}")
