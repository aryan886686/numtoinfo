# =============================================
# PHONE TO FULL INFO API - JSON DATABASE
# =============================================
# Creator: @notracearyan
# Version: 5.0.0 - JSON FILE SUPPORT
# =============================================

from flask import Flask, request, jsonify
import json
import re
import os
from datetime import datetime

app = Flask(__name__)

API_KEY = "Demo"

# Credit Info
CREDIT = {
    "name": "NoTraceAryan",
    "developer": "@NoTraceAryan",
    "contact": "https://t.me/osintxpro",
    "footer": "Powered by NoTraceAryan"
}

# ---- DATABASE FILES ----
DATABASE_FILES = [
    r"C:\Users\aryan\Downloads\users_data_part1.json",
    r"C:\Users\aryan\Downloads\users_data_part2.json",
    r"C:\Users\aryan\Downloads\users_data_part3.json"
]

# Column mappings for each field
COLUMN_MAP = {
    'name': ['name', 'fullName', 'FullName', 'Name', 'full_name', 'customerName', 'fullname'],
    'father_name': ['fatherName', 'FatherName', 'father', 'Father', 'fname', 'FName', 'guardian', 'father_name'],
    'mobile': ['mobile', 'phone', 'contact', 'phoneNumber', 'mobileNumber', 'phone_no', 'contact_no', 'mobilenumber'],
    'alt_mobile': ['alternateMobile', 'altMobile', 'phone2', 'mobile2', 'alt_phone', 'secondaryPhone', 'alternate_mobile'],
    'aadhaar': ['aadharNumber', 'aadhaarNumber', 'uid', 'aadhar', 'aadhaar', 'Aadhaar', 'aadhaar_number'],
    'address': ['address', 'fullAddress', 'Address', 'permanentAddress', 'currentAddress', 'full_address'],
    'email': ['email', 'Email', 'emailId', 'email_id', 'emailAddress', 'mail']
}

# ---- LOAD JSON DATABASES ----
ALL_DATA = []
FILE_SOURCES = {}

def load_databases():
    """Load all JSON files into memory"""
    global ALL_DATA, FILE_SOURCES
    ALL_DATA = []
    FILE_SOURCES = {}
    
    for file_path in DATABASE_FILES:
        if not os.path.exists(file_path):
            print(f"[-] {file_path} not found, skipping...")
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Handle different JSON structures
                if isinstance(data, list):
                    rows = data
                elif isinstance(data, dict):
                    # Check if data has a 'users' or 'data' key
                    if 'users' in data:
                        rows = data['users']
                    elif 'data' in data:
                        rows = data['data']
                    elif 'records' in data:
                        rows = data['records']
                    else:
                        # Assume the dict itself is a single record
                        rows = [data]
                else:
                    rows = []
                
                # Add source tracking
                for row in rows:
                    if isinstance(row, dict):
                        row['_source_file'] = os.path.basename(file_path)
                
                ALL_DATA.extend(rows)
                FILE_SOURCES[os.path.basename(file_path)] = len(rows)
                print(f"[+] Loaded {len(rows)} records from {os.path.basename(file_path)}")
                
        except json.JSONDecodeError as e:
            print(f"[-] JSON decode error in {file_path}: {e}")
        except Exception as e:
            print(f"[-] Error loading {file_path}: {e}")
    
    print(f"[+] Total records loaded: {len(ALL_DATA)}")

load_databases()

# ---- HELPER FUNCTIONS ----
def clean_phone(number):
    """Clean phone number to 10 digits"""
    if not number:
        return None
    cleaned = re.sub(r'[\s\-\(\)\+]', '', str(number))
    cleaned = cleaned.lstrip('0')
    if len(cleaned) > 10 and len(cleaned) <= 15:
        cleaned = cleaned[-10:]
    return cleaned if len(cleaned) == 10 and cleaned.isdigit() else None

def get_field_value(row, field_type):
    """Extract field value from row using column mapping"""
    for col in COLUMN_MAP.get(field_type, []):
        if col in row and row[col] and str(row[col]).strip():
            value = str(row[col]).strip()
            if field_type == 'mobile' or field_type == 'alt_mobile':
                return clean_phone(value)
            return value
    return None

def extract_info(row):
    """Extract all required fields from a row"""
    return {
        "name": get_field_value(row, 'name') or "N/A",
        "father_name": get_field_value(row, 'father_name') or "N/A",
        "mobile": get_field_value(row, 'mobile') or "N/A",
        "alt_mobile": get_field_value(row, 'alt_mobile') or "N/A",
        "aadhaar": get_field_value(row, 'aadhaar') or "N/A",
        "address": get_field_value(row, 'address') or "N/A",
        "email": get_field_value(row, 'email') or "N/A",
        "source": row.get('_source_file', 'Unknown')
    }

# ---- RESPONSE ----
def response(status, result=None, message=None, count=None):
    data = {
        "status": status,
        "credit": CREDIT,
        "timestamp": datetime.now().isoformat()
    }
    if result is not None:
        data["result"] = result
    if message is not None:
        data["message"] = message
    if count is not None:
        data["count"] = count
        data["total_records"] = len(ALL_DATA)
    return jsonify(data)

# ---- ROUTES ----
@app.route("/")
def home():
    return response(
        True, 
        message="Phone to Full Info API Online (JSON)",
        count=len(ALL_DATA)
    )

@app.route("/api")
def search():
    # API Key Check
    key = request.args.get("key")
    if key != API_KEY:
        return response(False, message="Invalid API Key"), 401
    
    # Phone number check
    phone = request.args.get("phone")
    if not phone:
        return response(False, message="phone parameter required"), 400
    
    clean_number = clean_phone(phone)
    if not clean_number:
        return response(False, message="Invalid phone number format"), 400
    
    # Search across all databases
    results = []
    for row in ALL_DATA:
        row_phone = get_field_value(row, 'mobile')
        if row_phone == clean_number:
            info = extract_info(row)
            results.append(info)
    
    if results:
        if len(results) == 1:
            return response(True, result=results[0])
        else:
            return response(True, result=results, count=len(results))
    
    return response(False, message="Record not found in any database"), 404

@app.route("/api/stats")
def stats():
    """Get database statistics"""
    key = request.args.get("key")
    if key != API_KEY:
        return response(False, message="Invalid API Key"), 401
    
    stats_data = {
        "total_records": len(ALL_DATA),
        "files": FILE_SOURCES,
        "fields_available": list(ALL_DATA[0].keys()) if ALL_DATA else [],
        "timestamp": datetime.now().isoformat()
    }
    return response(True, result=stats_data)

@app.route("/api/reload")
def reload_databases():
    """Reload all databases without restarting"""
    key = request.args.get("key")
    if key != API_KEY:
        return response(False, message="Invalid API Key"), 401
    
    load_databases()
    return response(True, message="Databases reloaded successfully", count=len(ALL_DATA))

@app.route("/api/search/all")
def search_all_fields():
    """Search by any field across all databases"""
    key = request.args.get("key")
    if key != API_KEY:
        return response(False, message="Invalid API Key"), 401
    
    query = request.args.get("q")
    if not query:
        return response(False, message="search query required"), 400
    
    query_lower = query.lower()
    results = []
    
    for row in ALL_DATA:
        row_str = " ".join(str(v).lower() for v in row.values() if v and isinstance(v, (str, int, float)))
        if query_lower in row_str:
            info = extract_info(row)
            results.append(info)
    
    if results:
        return response(True, result=results, count=len(results))
    return response(False, message="No results found"), 404

# ---- ERROR HANDLING ----
@app.errorhandler(404)
def not_found(e):
    return response(False, message="Route not found"), 404

@app.errorhandler(500)
def server_error(e):
    return response(False, message="Internal server error"), 500

# ---- MAIN ----
if __name__ == "__main__":
    print("\n" + "="*60)
    print(" PHONE TO FULL INFO API v5.0 - JSON")
    print(" Creator: @notracearyan")
    print("="*60)
    print(f"[+] Loaded {len(ALL_DATA)} total records")
    print("[+] Database files:")
    for file, count in FILE_SOURCES.items():
        print(f"    - {file}: {count} records")
    print("\n[+] Endpoints:")
    print("    GET /api?phone=9876543210&key=Demo")
    print("    GET /api/stats?key=Demo")
    print("    GET /api/reload?key=Demo")
    print("    GET /api/search/all?q=John&key=Demo")
    print("="*60 + "\n")
    
    app.run(host="0.0.0.0", port=8000, debug=False)
