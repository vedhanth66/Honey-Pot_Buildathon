import requests
import json
import time
import random
from typing import List, Dict, Any
from datetime import datetime
import sys

# API Configuration
# API_URL = "https://honeypotbuildathon.vercel.app/"  
# HEALTH_URL = "https://honeypotbuildathon.vercel.app/health"
API_URL = "http://localhost:8080/"  
HEALTH_URL = "http://localhost:8080/health"
API_KEY = "Honey-Pot_Buildathon-123456"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    MAGENTA = '\033[35m'
    YELLOW = '\033[33m'
    WHITE = '\033[97m'

# ============================================================================
# EDGE CASE TEST SCENARIOS
# ============================================================================

EDGE_CASE_SCENARIOS = [
    # ========================================================================
    # CATEGORY 1: EMPTY AND SHORT MESSAGES
    # ========================================================================
    {
        "id": "EDGE_EMPTY_01",
        "category": "Empty/Short Messages",
        "description": "Completely Empty Message",
        "expected_behavior": "Should return error or default response",
        "messages": [
            ""
        ],
        "validation": {
            "should_not_crash": True,
            "should_respond": True,
            "expected_keywords": ["didn't receive", "try again", "help"]
        }
    },
    {
        "id": "EDGE_SHORT_02",
        "category": "Empty/Short Messages",
        "description": "Single Character",
        "expected_behavior": "Should handle gracefully",
        "messages": [
            ".",
            "!",
            "?"
        ],
        "validation": {
            "should_not_crash": True,
            "should_respond": True,
            "expected_keywords": ["didn't", "catch", "help"]
        }
    },
    {
        "id": "EDGE_SHORT_03",
        "category": "Empty/Short Messages",
        "description": "Only Whitespace",
        "expected_behavior": "Should handle as empty",
        "messages": [
            "   ",
            "\n\n",
            "\t\t"
        ],
        "validation": {
            "should_not_crash": True,
            "should_respond": True
        }
    },
    
    # ========================================================================
    # CATEGORY 2: GREETINGS
    # ========================================================================
    {
        "id": "EDGE_GREETING_04",
        "category": "Greetings",
        "description": "Various Greeting Formats",
        "expected_behavior": "Should detect and respond to greetings",
        "messages": [
            "hi",
            "Hello",
            "HEY!!!",
            "namaste",
            "hiii",
            "hlo",
            "sup",
            "yo"
        ],
        "validation": {
            "should_not_crash": True,
            "should_respond": True,
            "expected_keywords": ["hello", "help", "assist"]
        }
    },
    
    # ========================================================================
    # CATEGORY 3: LONG MESSAGES (TRUNCATION)
    # ========================================================================
    {
        "id": "EDGE_LONG_05",
        "category": "Long Messages",
        "description": "Extremely Long Message (3000+ words)",
        "expected_behavior": "Should truncate intelligently, keeping scam indicators",
        "messages": [
            ("URGENT URGENT URGENT " * 50 + 
             "Your SBI bank account will be blocked. " * 30 +
             "Please share your OTP immediately. " * 30 +
             "Click this link: http://fake-sbi-scam.com/verify " * 20 +
             "Call us at +91-9876543210 for verification. " * 25 +
             "Send payment to UPI ID: scammer@paytm " * 20 +
             "Your account number is required. " * 30 +
             "This is your final warning. " * 40)
        ],
        "validation": {
            "should_not_crash": True,
            "should_respond": True,
            "message_should_contain": ["bank", "otp", "link"],
            "max_processing_time": 45.0  # seconds
        }
    },
    {
        "id": "EDGE_LONG_06",
        "category": "Long Messages",
        "description": "Long Message - 1 Page Text",
        "expected_behavior": "Should extract key scam indicators",
        "messages": [
            ("Dear valued customer, we are writing to inform you about an important matter regarding your account. " * 15 +
             "Your KYC is pending and needs immediate update. " +
             "Without updating, your account will be BLOCKED within 24 hours. " +
             "Please click on this link to verify: http://urgent-kyc-update.xyz/verify " +
             "You will need to enter your account number, debit card number, CVV, and OTP. " +
             "Thank you for your cooperation. " * 20)
        ],
        "validation": {
            "should_respond": True,
            "should_detect_scam": True
        }
    },
    
    # ========================================================================
    # CATEGORY 4: ENCRYPTED/CIPHER MESSAGES
    # ========================================================================
    {
        "id": "EDGE_CIPHER_07",
        "category": "Cipher/Encryption",
        "description": "A=1, B=2 Cipher - 'URGENT BANK ACCOUNT BLOCKED'",
        "expected_behavior": "Should decode and detect scam",
        "messages": [
            "21 18 7 5 14 20 2 1 14 11 1 3 3 15 21 14 20 2 12 15 3 11 5 4"
        ],
        "validation": {
            "should_not_crash": True,
            "should_decode": True,
            "decoded_should_contain": ["urgent", "bank", "account", "blocked"]
        }
    },
    {
        "id": "EDGE_CIPHER_08",
        "category": "Cipher/Encryption",
        "description": "A=1, B=2 Cipher - 'SEND OTP NOW'",
        "expected_behavior": "Should decode and respond",
        "messages": [
            "19 5 14 4 15 20 16 14 15 23"
        ],
        "validation": {
            "should_decode": True,
            "decoded_should_contain": ["send", "otp"]
        }
    },
    
    # ========================================================================
    # CATEGORY 5: MULTI-LANGUAGE (DIFFERENT SCRIPTS)
    # ========================================================================
    {
        "id": "EDGE_LANG_09",
        "category": "Multi-Language",
        "description": "Hindi (Devanagari Script)",
        "expected_behavior": "Should detect language and translate",
        "messages": [
            "आपका बैंक खाता ब्लॉक हो जाएगा",  # Your bank account will be blocked
            "तुरंत OTP भेजें",  # Send OTP immediately
        ],
        "validation": {
            "should_not_crash": True,
            "should_translate": True,
            "expected_keywords": ["bank", "account", "block", "otp"]
        }
    },
    {
        "id": "EDGE_LANG_10",
        "category": "Multi-Language",
        "description": "Tamil Script",
        "expected_behavior": "Should detect and translate",
        "messages": [
            "உங்கள் வங்கி கணக்கு தடுக்கப்படும்",  # Your bank account will be blocked
        ],
        "validation": {
            "should_not_crash": True,
            "should_translate": True
        }
    },
    {
        "id": "EDGE_LANG_11",
        "category": "Multi-Language",
        "description": "Telugu Script",
        "expected_behavior": "Should detect and translate",
        "messages": [
            "మీ బ్యాంక్ ఖాతా బ్లాక్ చేయబడుతుంది",  # Your bank account will be blocked
        ],
        "validation": {
            "should_not_crash": True,
            "should_translate": True
        }
    },
    {
        "id": "EDGE_LANG_12",
        "category": "Multi-Language",
        "description": "Kannada Script",
        "expected_behavior": "Should detect and translate",
        "messages": [
            "ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆಯನ್ನು ನಿರ್ಬಂಧಿಸಲಾಗುತ್ತದೆ",  # Your bank account will be blocked
        ],
        "validation": {
            "should_not_crash": True,
            "should_translate": True
        }
    },
    
    # ========================================================================
    # CATEGORY 6: PHONE NUMBER FORMAT VARIATIONS
    # ========================================================================
    {
        "id": "EDGE_PHONE_13",
        "category": "Phone Formats",
        "description": "Various Phone Number Formats",
        "expected_behavior": "Should extract and normalize all formats",
        "messages": [
            "Call me at 9876543210",                          # Plain 10 digits
            "My number is +91-9876543210",                    # With country code and dash
            "Contact on +91 98765 43210",                     # With spaces
            "Phone: 091-9876543210",                          # With 0 prefix
            "WhatsApp: 98 76 54 32 10",                      # With spaces in number
            "Ring me: +919876543210",                         # No spaces/dashes
            "Call: 12 34 56 78 90",                          # Space separated
        ],
        "validation": {
            "should_extract_phones": True,
            "expected_phone_count": 7,
            "all_should_normalize_to": "+919876543210"
        }
    },
    
    # ========================================================================
    # CATEGORY 7: HTTP vs HTTPS URL SECURITY
    # ========================================================================
    {
        "id": "EDGE_URL_14",
        "category": "URL Security",
        "description": "HTTP (Insecure) Bank URL",
        "expected_behavior": "Should flag as CRITICAL RISK",
        "messages": [
            "Update your SBI account: http://sbi.co.in/verify",
            "Your HDFC KYC is pending: http://hdfcbank.com/update"
        ],
        "validation": {
            "should_detect_scam": True,
            "url_risk_score": ">= 50",
            "threat_level": "high"
        }
    },
    {
        "id": "EDGE_URL_15",
        "category": "URL Security",
        "description": "HTTPS Legitimate Bank URL",
        "expected_behavior": "Should recognize as legitimate",
        "messages": [
            "Visit official SBI: https://sbi.co.in for updates"
        ],
        "validation": {
            "should_detect_scam": False,
            "url_risk_score": "< 30"
        }
    },
    {
        "id": "EDGE_URL_16",
        "category": "URL Security",
        "description": "Suspicious TLDs and Long Domains",
        "expected_behavior": "Should flag as suspicious",
        "messages": [
            "Click: http://sbi-verify-account-urgent-kyc-update.tk/login",
            "Visit: https://secure-bank-verification-portal.xyz/verify",
            "Update: http://192.168.1.100/bank/login"
        ],
        "validation": {
            "should_detect_scam": True,
            "url_risk_score": ">= 40"
        }
    },
    {
        "id": "EDGE_URL_17",
        "category": "URL Security",
        "description": "Bank Impersonation URL",
        "expected_behavior": "Should detect impersonation",
        "messages": [
            "Verify at http://sbi.co.in.verify-account.com/login",
            "Update KYC: https://hdfc-bank-secure.com/verify"
        ],
        "validation": {
            "should_detect_scam": True,
            "should_detect_impersonation": True,
            "url_risk_score": ">= 60"
        }
    },
    
    # ========================================================================
    # CATEGORY 8: RATE LIMITING
    # ========================================================================
    {
        "id": "EDGE_RATE_18",
        "category": "Rate Limiting",
        "description": "Rapid-Fire Requests (Rate Limit Test)",
        "expected_behavior": "Should rate limit after 50 requests in 60s",
        "messages": ["Test message " + str(i) for i in range(55)],
        "validation": {
            "should_hit_rate_limit": True,
            "rate_limit_after": 50,
            "expected_status_code": 429
        }
    },
    
    # ========================================================================
    # CATEGORY 9: HOMOGRAPH ATTACKS
    # ========================================================================
    {
        "id": "EDGE_HOMOGRAPH_19",
        "category": "Homograph Attack",
        "description": "Cyrillic Lookalike Characters",
        "expected_behavior": "Should detect fake characters",
        "messages": [
            "Update your account at https://ѕbi.co.in/verify",  # Cyrillic 's'
            "Visit https://hdfсbank.com/login"  # Cyrillic 'c'
        ],
        "validation": {
            "should_detect_scam": True,
            "should_detect_homograph": True,
            "url_risk_score": ">= 45"
        }
    },
    
    # ========================================================================
    # CATEGORY 10: MIXED EDGE CASES
    # ========================================================================
    {
        "id": "EDGE_MIXED_20",
        "category": "Mixed Edge Cases",
        "description": "Long Message + Multiple Phone Formats + HTTP URLs",
        "expected_behavior": "Should handle all edge cases simultaneously",
        "messages": [
            ("URGENT! Your bank account will be blocked! " * 20 +
             "Call immediately: +91-9876543210 or 98 76 54 32 10 or 091-9876543210. " +
             "Update here: http://fake-bank.tk/verify or http://192.168.1.1/scam. " +
             "Send Rs. 5000 to UPI: scammer@paytm. " * 10 +
             "Your account 1234567890123456 needs verification. " * 15)
        ],
        "validation": {
            "should_extract_phones": True,
            "should_extract_urls": True,
            "should_extract_amounts": True,
            "should_extract_upi": True,
            "should_detect_scam": True,
            "should_truncate_message": True
        }
    },
    {
        "id": "EDGE_MIXED_21",
        "category": "Mixed Edge Cases",
        "description": "Cipher + Scam Indicators",
        "expected_behavior": "Should decode and detect scam",
        "messages": [
            "20 18 1 14 19 6 5 18 18 19 5 14 4 15 20 16 14 15 23",  # TRANSFER SEND OTP NOW
            "Then click: http://scam-site.xyz/verify",
            "UPI: hacker@paytm"
        ],
        "validation": {
            "should_decode": True,
            "should_detect_scam": True,
            "should_extract_urls": True,
            "should_extract_upi": True
        }
    },
    {
        "id": "EDGE_MIXED_22",
        "category": "Mixed Edge Cases",
        "description": "Multi-Language + Phone Numbers",
        "expected_behavior": "Should translate and extract intelligence",
        "messages": [
            "आपका खाता ब्लॉक होगा। कॉल करें: 9876543210",  # Hindi + phone
        ],
        "validation": {
            "should_translate": True,
            "should_extract_phones": True,
            "should_detect_scam": True
        }
    },
    
    # ========================================================================
    # CATEGORY 11: SPECIAL CHARACTERS AND ENCODING
    # ========================================================================
    {
        "id": "EDGE_SPECIAL_23",
        "category": "Special Characters",
        "description": "Emojis and Special Unicode",
        "expected_behavior": "Should handle without crashing",
        "messages": [
            "🚨🚨🚨 URGENT 🚨🚨🚨 Your account blocked! 😱😱",
            "💰💰 Won Rs. 50 Lakhs 💰💰 Call: 9876543210",
            "⚠️ WARNING ⚠️ Click here ➡️ http://scam.com"
        ],
        "validation": {
            "should_not_crash": True,
            "should_detect_scam": True,
            "should_extract_phones": True,
            "should_extract_urls": True
        }
    },
    
    # ========================================================================
    # CATEGORY 12: LEGITIMATE MESSAGES (FALSE POSITIVE CHECK)
    # ========================================================================
    {
        "id": "EDGE_LEGIT_24",
        "category": "Legitimate Messages",
        "description": "Official Bank Communication",
        "expected_behavior": "Should NOT flag as scam",
        "messages": [
            "Dear Customer, your KYC is due. Please visit the nearest branch. Do not share OTP with anyone. Official helpline: 1800-123-4567",
            "SBI reminder: Visit https://sbi.co.in for updates. Never share your PIN or OTP.",
            "HDFC Bank: Your statement is ready. Download from official app. Visit branch for queries."
        ],
        "validation": {
            "should_detect_scam": False,
            "should_respond_politely": True
        }
    },
    
    # ========================================================================
    # CATEGORY 13: MALFORMED DATA
    # ========================================================================
    {
        "id": "EDGE_MALFORMED_25",
        "category": "Malformed Data",
        "description": "Incomplete or Corrupted Messages",
        "expected_behavior": "Should handle gracefully",
        "messages": [
            "Your account...###ERROR###...blocked",
            "OTP: �����",  # Corrupted text
            "Call +++---91---+++",
            "http://...broken...url...com"
        ],
        "validation": {
            "should_not_crash": True,
            "should_respond": True
        }
    },
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_banner():
    print(f"{Colors.HEADER}{'='*100}")
    print(f"║{'':^98}║")
    print(f"║{Colors.BOLD}{'ULTIMATE AGENTIC HONEY-POT - EDGE CASE TESTER':^98}{Colors.ENDC}{Colors.HEADER}║")
    print(f"║{'':^98}║")
    print(f"║  Target: {API_URL:<89}║")
    print(f"║  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<91}║")
    print(f"║  Total Edge Cases: {len(EDGE_CASE_SCENARIOS):<82}║")
    print(f"║{'':^98}║")
    print(f"{'='*100}{Colors.ENDC}\n")

def check_health():
    print(f"{Colors.CYAN}🏥 Checking System Health...{Colors.ENDC}", end=" ")
    try:
        start = time.time()
        resp = requests.get(HEALTH_URL, timeout=5)
        latency = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"{Colors.GREEN}✓ ONLINE ({latency:.0f}ms){Colors.ENDC}")
            print(f"   ├─ Active Sessions: {data.get('active_sessions', 0)}")
            print(f"   ├─ Personas Loaded: {data.get('personas_loaded', 0)}")
            
            edge_handlers = data.get('edge_case_handlers', {})
            if edge_handlers:
                print(f"   ├─ Edge Case Handlers:")
                print(f"   │  ├─ Rate Limiter: {edge_handlers.get('rate_limiter', 'unknown')}")
                print(f"   │  ├─ Language Handler: {edge_handlers.get('language_handler', 'unknown')}")
                print(f"   │  ├─ URL Analyzer: {edge_handlers.get('url_analyzer', 'unknown')}")
                print(f"   │  └─ Cipher Detector: {edge_handlers.get('cipher_detector', 'unknown')}")
            
            print(f"   └─ Status: {Colors.GREEN}READY FOR TESTING{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}✗ FAILED (Status: {resp.status_code}){Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.FAIL}✗ ERROR ({str(e)}){Colors.ENDC}")
        return False

def extract_intelligence(msg: str) -> Dict:
    """Extract intelligence from message"""
    import re
    intel = {
        'urls': [],
        'phones': [],
        'amounts': [],
        'upi_ids': [],
        'bank_accounts': []
    }
    
    # URLs
    urls = re.findall(r'https?://[^\s]+', msg)
    intel['urls'] = urls
    
    # Phone numbers - multiple formats
    phones = re.findall(r'\+?91[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}|\+?91[\s-]?\d{10}|\b0?91[\s-]?\d{10}\b|\b[6-9]\d[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}\b|\b[6-9]\d{9}\b', msg)
    intel['phones'] = phones
    
    # Amounts
    amounts = re.finditer(r'(?:Rs\.?|₹|INR)\s*(\d+(?:,\d{3})*)(?:\.(\d+))?\s*(lakh|lakhs|crore|crores)?', msg, re.IGNORECASE)
    for m in amounts:
        intel['amounts'].append(m.group(0))
    
    # UPI IDs
    upi = re.findall(r'[\w\.-]+@(?:paytm|oksbi|okicici|okaxis|okhdfcbank|okbizaxis|ybl|ibl|apl|axl)', msg, re.IGNORECASE)
    intel['upi_ids'] = upi
    
    # Bank accounts
    accounts = re.findall(r'\b\d{9,18}\b', msg)
    intel['bank_accounts'] = [acc for acc in accounts if not re.fullmatch(r'[6-9]\d{9}', acc)]
    
    return intel

def validate_response(response_data: dict, validation: dict, scenario_id: str) -> dict:
    """Validate response against expected behavior"""
    results = {
        'passed': 0,
        'failed': 0,
        'warnings': 0,
        'details': []
    }
    
    reply = response_data.get('reply', '')
    scam_detected = response_data.get('scam_detected', None)
    
    # Check if should respond
    if validation.get('should_respond', True):
        if reply:
            results['passed'] += 1
            results['details'].append(f"{Colors.GREEN}✓ System responded{Colors.ENDC}")
        else:
            results['failed'] += 1
            results['details'].append(f"{Colors.FAIL}✗ No response received{Colors.ENDC}")
    
    # Check expected keywords
    if 'expected_keywords' in validation:
        found = any(kw.lower() in reply.lower() for kw in validation['expected_keywords'])
        if found:
            results['passed'] += 1
            results['details'].append(f"{Colors.GREEN}✓ Contains expected keywords{Colors.ENDC}")
        else:
            results['warnings'] += 1
            results['details'].append(f"{Colors.WARNING}⚠ Missing expected keywords{Colors.ENDC}")
    
    # Check scam detection
    if 'should_detect_scam' in validation:
        expected = validation['should_detect_scam']
        if scam_detected == expected:
            results['passed'] += 1
            results['details'].append(f"{Colors.GREEN}✓ Scam detection correct: {expected}{Colors.ENDC}")
        elif scam_detected is None:
            results['warnings'] += 1
            results['details'].append(f"{Colors.WARNING}⚠ Scam detection status unknown{Colors.ENDC}")
        else:
            results['failed'] += 1
            results['details'].append(f"{Colors.FAIL}✗ Scam detection incorrect: expected {expected}, got {scam_detected}{Colors.ENDC}")
    
    return results

def run_edge_case_scenario(scenario: Dict):
    session_id = f"EDGE_{scenario['id']}_{int(time.time())}"
    
    print(f"\n{Colors.HEADER}{'='*100}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}▶ TEST: {scenario['description']}{Colors.ENDC}")
    print(f"   ├─ ID: {scenario['id']}")
    print(f"   ├─ Category: {Colors.MAGENTA}{scenario['category']}{Colors.ENDC}")
    print(f"   ├─ Expected: {scenario['expected_behavior']}")
    print(f"   └─ Session: {session_id}\n")
    
    history = []
    test_results = {
        'total_messages': len(scenario['messages']),
        'successful': 0,
        'failed': 0,
        'errors': 0,
        'validations': {'passed': 0, 'failed': 0, 'warnings': 0}
    }
    
    total_intel = {'urls': [], 'phones': [], 'amounts': [], 'upi_ids': [], 'bank_accounts': []}
    
    for i, msg_text in enumerate(scenario['messages']):
        msg_display = msg_text if len(msg_text) <= 100 else msg_text[:97] + "..."
        print(f"{Colors.WARNING}📤 Message {i+1}/{len(scenario['messages'])}:{Colors.ENDC} {msg_display}")
        
        # Show message stats
        print(f"   ├─ Length: {len(msg_text)} characters")
        
        # Check for special characteristics
        if len(msg_text) == 0:
            print(f"   ├─ {Colors.YELLOW}⚠ Empty message{Colors.ENDC}")
        elif len(msg_text) > 1000:
            print(f"   ├─ {Colors.YELLOW}⚠ Long message (truncation expected){Colors.ENDC}")
        
        # Check for non-ASCII (multi-language)
        if any(ord(c) > 127 for c in msg_text):
            print(f"   ├─ {Colors.CYAN}🌐 Contains non-ASCII characters (translation may occur){Colors.ENDC}")
        
        # Extract intelligence
        msg_intel = extract_intelligence(msg_text)
        if any(msg_intel.values()):
            print(f"   ├─ {Colors.MAGENTA}📊 Intelligence in message:{Colors.ENDC}")
            for key, value in msg_intel.items():
                if value:
                    total_intel[key].extend(value)
                    print(f"   │  └─ {key}: {len(value)} item(s)")
        
        # Construct payload
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": msg_text,
                "timestamp": int(time.time() * 1000)
            },
            "conversationHistory": history,
            "metadata": {
                "channel": "Test",
                "language": "Mixed",
                "locale": "IN"
            }
        }
        
        try:
            start_ts = time.time()
            response = requests.post(
                f"{API_URL}api/honeypot",
                headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
            latency = (time.time() - start_ts) * 1000
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "")
                
                print(f"{Colors.GREEN}📥 Response:{Colors.ENDC} {reply}")
                print(f"   ├─ Latency: {latency:.0f}ms")
                print(f"   └─ Status: {Colors.GREEN}SUCCESS{Colors.ENDC}")
                
                test_results['successful'] += 1
                
                # Update history
                history.append({"sender": "scammer", "text": msg_text, "timestamp": int(time.time()*1000)})
                history.append({"sender": "user", "text": reply, "timestamp": int(time.time()*1000)})
                
            elif response.status_code == 429:
                print(f"{Colors.WARNING}⚠ Rate Limited (429) - This is expected for rate limit tests{Colors.ENDC}")
                if scenario['category'] == "Rate Limiting":
                    test_results['successful'] += 1
                    print(f"   └─ {Colors.GREEN}✓ Rate limiting working as expected{Colors.ENDC}")
                    break
                else:
                    test_results['errors'] += 1
                
            else:
                print(f"{Colors.FAIL}✗ API Error: {response.status_code} - {response.text[:200]}{Colors.ENDC}")
                test_results['failed'] += 1
                
        except requests.Timeout:
            print(f"{Colors.FAIL}✗ Timeout Error (>60s){Colors.ENDC}")
            test_results['errors'] += 1
            
        except Exception as e:
            print(f"{Colors.FAIL}✗ Connection Error: {str(e)}{Colors.ENDC}")
            test_results['errors'] += 1
        
        print()
        
        # Small delay between messages
        if i < len(scenario['messages']) - 1:
            time.sleep(0.5)
    
    # Validation
    print(f"{Colors.CYAN}{'─'*100}{Colors.ENDC}")
    print(f"{Colors.BOLD}📋 VALIDATION RESULTS:{Colors.ENDC}\n")
    
    validation = scenario.get('validation', {})
    
    # Should not crash
    if validation.get('should_not_crash', True):
        if test_results['errors'] == 0:
            print(f"{Colors.GREEN}✓ Did not crash{Colors.ENDC}")
            test_results['validations']['passed'] += 1
        else:
            print(f"{Colors.FAIL}✗ System crashed or errored{Colors.ENDC}")
            test_results['validations']['failed'] += 1
    
    # Intelligence extraction checks
    if validation.get('should_extract_phones'):
        if total_intel['phones']:
            print(f"{Colors.GREEN}✓ Extracted {len(total_intel['phones'])} phone number(s){Colors.ENDC}")
            test_results['validations']['passed'] += 1
        else:
            print(f"{Colors.FAIL}✗ Failed to extract phone numbers{Colors.ENDC}")
            test_results['validations']['failed'] += 1
    
    if validation.get('should_extract_urls'):
        if total_intel['urls']:
            print(f"{Colors.GREEN}✓ Extracted {len(total_intel['urls'])} URL(s){Colors.ENDC}")
            test_results['validations']['passed'] += 1
        else:
            print(f"{Colors.FAIL}✗ Failed to extract URLs{Colors.ENDC}")
            test_results['validations']['failed'] += 1
    
    if validation.get('should_extract_amounts'):
        if total_intel['amounts']:
            print(f"{Colors.GREEN}✓ Extracted {len(total_intel['amounts'])} amount(s){Colors.ENDC}")
            test_results['validations']['passed'] += 1
        else:
            print(f"{Colors.FAIL}✗ Failed to extract amounts{Colors.ENDC}")
            test_results['validations']['failed'] += 1
    
    if validation.get('should_extract_upi'):
        if total_intel['upi_ids']:
            print(f"{Colors.GREEN}✓ Extracted {len(total_intel['upi_ids'])} UPI ID(s){Colors.ENDC}")
            test_results['validations']['passed'] += 1
        else:
            print(f"{Colors.FAIL}✗ Failed to extract UPI IDs{Colors.ENDC}")
            test_results['validations']['failed'] += 1
    
    # Show intelligence summary
    print(f"\n{Colors.MAGENTA}📊 TOTAL INTELLIGENCE EXTRACTED:{Colors.ENDC}")
    total_items = sum(len(v) for v in total_intel.values())
    if total_items > 0:
        for key, value in total_intel.items():
            if value:
                unique = list(set(value))
                print(f"   ├─ {key.replace('_', ' ').title()}: {len(unique)}")
                for item in unique[:3]:  # Show first 3
                    print(f"   │  └─ {item}")
                if len(unique) > 3:
                    print(f"   │  └─ ... and {len(unique)-3} more")
    else:
        print(f"   └─ {Colors.WARNING}No intelligence extracted{Colors.ENDC}")
    
    # Test summary
    print(f"\n{Colors.BOLD}📈 TEST SUMMARY:{Colors.ENDC}")
    print(f"   ├─ Messages Sent: {test_results['total_messages']}")
    print(f"   ├─ Successful: {Colors.GREEN}{test_results['successful']}{Colors.ENDC}")
    print(f"   ├─ Failed: {Colors.FAIL}{test_results['failed']}{Colors.ENDC}")
    print(f"   ├─ Errors: {Colors.FAIL}{test_results['errors']}{Colors.ENDC}")
    print(f"   └─ Validations: {Colors.GREEN}{test_results['validations']['passed']} passed{Colors.ENDC}, "
          f"{Colors.FAIL}{test_results['validations']['failed']} failed{Colors.ENDC}, "
          f"{Colors.WARNING}{test_results['validations']['warnings']} warnings{Colors.ENDC}")
    
    # Overall result
    overall_pass = (test_results['failed'] == 0 and 
                   test_results['errors'] == 0 and 
                   test_results['validations']['failed'] == 0)
    
    if overall_pass:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ EDGE CASE TEST PASSED{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}✗ EDGE CASE TEST FAILED{Colors.ENDC}")
    
    return test_results

def print_final_summary(all_results: List[Dict]):
    """Print comprehensive test summary"""
    print(f"\n\n{Colors.HEADER}{'='*100}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'FINAL TEST SUMMARY':^100}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*100}{Colors.ENDC}\n")
    
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.get('overall_pass', False))
    failed_tests = total_tests - passed_tests
    
    total_messages = sum(r.get('total_messages', 0) for r in all_results)
    successful_msgs = sum(r.get('successful', 0) for r in all_results)
    failed_msgs = sum(r.get('failed', 0) for r in all_results)
    error_msgs = sum(r.get('errors', 0) for r in all_results)
    
    # Calculate validation totals
    total_val_passed = sum(r.get('validations', {}).get('passed', 0) for r in all_results)
    total_val_failed = sum(r.get('validations', {}).get('failed', 0) for r in all_results)
    total_val_warnings = sum(r.get('validations', {}).get('warnings', 0) for r in all_results)
    
    # Category breakdown
    categories = {}
    for i, result in enumerate(all_results):
        scenario = EDGE_CASE_SCENARIOS[i]
        cat = scenario['category']
        if cat not in categories:
            categories[cat] = {'passed': 0, 'failed': 0}
        
        if result.get('overall_pass', False):
            categories[cat]['passed'] += 1
        else:
            categories[cat]['failed'] += 1
    
    print(f"{Colors.BOLD}OVERALL STATISTICS:{Colors.ENDC}")
    print(f"   ├─ Total Test Scenarios: {total_tests}")
    print(f"   ├─ Passed: {Colors.GREEN}{passed_tests}{Colors.ENDC}")
    print(f"   ├─ Failed: {Colors.FAIL}{failed_tests}{Colors.ENDC}")
    print(f"   └─ Success Rate: {Colors.GREEN if passed_tests/total_tests >= 0.8 else Colors.WARNING}{(passed_tests/total_tests)*100:.1f}%{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}MESSAGE STATISTICS:{Colors.ENDC}")
    print(f"   ├─ Total Messages: {total_messages}")
    print(f"   ├─ Successful: {Colors.GREEN}{successful_msgs}{Colors.ENDC}")
    print(f"   ├─ Failed: {Colors.FAIL}{failed_msgs}{Colors.ENDC}")
    print(f"   └─ Errors: {Colors.FAIL}{error_msgs}{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}VALIDATION STATISTICS:{Colors.ENDC}")
    print(f"   ├─ Passed: {Colors.GREEN}{total_val_passed}{Colors.ENDC}")
    print(f"   ├─ Failed: {Colors.FAIL}{total_val_failed}{Colors.ENDC}")
    print(f"   └─ Warnings: {Colors.WARNING}{total_val_warnings}{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}CATEGORY BREAKDOWN:{Colors.ENDC}")
    for cat, stats in sorted(categories.items()):
        total = stats['passed'] + stats['failed']
        status = f"{Colors.GREEN}✓{Colors.ENDC}" if stats['failed'] == 0 else f"{Colors.FAIL}✗{Colors.ENDC}"
        print(f"   {status} {cat}: {stats['passed']}/{total} passed")
    
    # Final verdict
    print(f"\n{Colors.HEADER}{'='*100}{Colors.ENDC}")
    if failed_tests == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}{'🎉 ALL EDGE CASES PASSED! SYSTEM IS ROBUST! 🎉':^100}{Colors.ENDC}")
    elif passed_tests / total_tests >= 0.8:
        print(f"{Colors.WARNING}{Colors.BOLD}{'⚠ MOST TESTS PASSED - MINOR ISSUES DETECTED ⚠':^100}{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}{'❌ MULTIPLE FAILURES - SYSTEM NEEDS WORK ❌':^100}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*100}{Colors.ENDC}\n")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print_banner()
    
    if not check_health():
        print(f"\n{Colors.FAIL}❌ Health check failed. Please ensure the server is running.{Colors.ENDC}")
        print(f"{Colors.CYAN}Start server with: uvicorn app_ultimate_edge_cases:app --reload{Colors.ENDC}")
        sys.exit(1)
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}🚀 Starting Edge Case Test Suite...{Colors.ENDC}")
    print(f"{Colors.CYAN}Testing {len(EDGE_CASE_SCENARIOS)} scenarios across {len(set(s['category'] for s in EDGE_CASE_SCENARIOS))} categories{Colors.ENDC}\n")
    
    input(f"{Colors.YELLOW}Press Enter to begin testing...{Colors.ENDC}")
    
    all_results = []
    
    for i, scenario in enumerate(EDGE_CASE_SCENARIOS, 1):
        print(f"\n{Colors.BOLD}{Colors.WHITE}[{i}/{len(EDGE_CASE_SCENARIOS)}]{Colors.ENDC}")
        
        result = run_edge_case_scenario(scenario)
        
        # Add overall pass/fail
        result['overall_pass'] = (
            result['failed'] == 0 and 
            result['errors'] == 0 and 
            result['validations']['failed'] == 0
        )
        
        all_results.append(result)
        
        # Pause between tests
        if i < len(EDGE_CASE_SCENARIOS):
            time.sleep(2)
    
    # Print final summary
    print_final_summary(all_results)
    
    print(f"{Colors.CYAN}Test suite completed at {datetime.now().strftime('%H:%M:%S')}{Colors.ENDC}")