import requests
import json
import time
import random
from typing import List, Dict, Any
from datetime import datetime

API_URL = "https://honey-pot-buildathon.onrender.com"  
HEALTH_URL = "https://honey-pot-buildathon.onrender.com/health"
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

SCENARIOS = [
    {
        "id": "SCAM_BANKING_01",
        "expected_persona": "Rajeshwari (Elderly)",
        "description": "Traditional Bank Account Block Threat",
        "messages": [
            "Dear customer, your SBI account XXXXX6789 will be blocked today due to pending KYC.",
            "If you do not update immediately, your balance will be frozen.",
            "Click here to verify: http://sbi-kyc-update-fast.com/login",
            "Please enter your account number to proceed.",
            "You also need to provide your Debit Card number for verification."
        ]
    },
    {
        "id": "SCAM_LOTTERY_02",
        "expected_persona": "Priya (Youth)",
        "description": "WhatsApp Lottery/Prize Scam",
        "messages": [
            "Congratulations! You have won Rs. 25 Lakhs in KBC Lucky Draw!",
            "To claim your prize, contact Rana Pratap at +91-9988776655.",
            "You need to pay a small registration fee of Rs. 5000 via UPI.",
            "Send money to upi id: winner@paytm",
            "This is a limited time offer. Hurry up!"
        ]
    },
    {
        "id": "SCAM_CORPORATE_03",
        "expected_persona": "Arjun (Professional)",
        "description": "Urgent Corporate/Refund Scam",
        "messages": [
            "Refund Approved: Rs. 12,400 has been initiated to your account.",
            "However, the transaction failed due to server error.",
            "Please verify your details immediately to process the refund.",
            "Click: http://refund-support-portal.com/verify",
            "Failure to verify will result in cancellation of refund."
        ]
    }
]


def print_banner():
    print(f"{Colors.HEADER}{'='*80}")
    print(f"🕵️  ULTIMATE AGENTIC HONEY-POT TESTER v2.1 (ENHANCED)")
    print(f"Target: {API_URL}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}{Colors.ENDC}\n")

def check_health():
    print(f"{Colors.CYAN}🔍 Checking System Health...{Colors.ENDC}", end=" ")
    try:
        start = time.time()
        resp = requests.get(HEALTH_URL, timeout=5)
        latency = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"{Colors.GREEN}ONLINE ✅ ({latency:.0f}ms){Colors.ENDC}")
            print(f"   └─ Active Sessions: {data.get('active_sessions', 0)}")
            print(f"   └─ Personas Loaded: {data.get('personas_loaded', 0)}")
            print(f"   └─ Gemini Configured: {data.get('gemini_configured', False)}")
            return True
        else:
            print(f"{Colors.FAIL}FAILED ❌ (Status: {resp.status_code}){Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.FAIL}ERROR ❌ ({str(e)}){Colors.ENDC}")
        return False

def analyze_persona_response(text: str, expected: str):
    """Analyze if response matches expected persona"""
    text_lower = text.lower()
    detected = "Unknown"
    
    # Keyword heuristics
    if any(w in text_lower for w in ['beta', 'ji', 'samajh', 'confused', 'bete']):
        detected = "Rajeshwari (Elderly)"
    elif any(w in text_lower for w in ['meeting', 'email', 'busy', 'process', 'legitimate']):
        detected = "Arjun (Professional)"
    elif any(w in text_lower for w in ['yaar', 'mummy', 'papa', 'legit', 'dost']):
        detected = "Priya (Youth)"
        
    match_color = Colors.GREEN if expected.split()[0] in detected else Colors.WARNING
    return detected, match_color

def extract_intelligence_from_message(msg: str) -> Dict:
    """Extract intelligence from scammer message"""
    import re
    intel = {
        'urls': [],
        'phones': [],
        'amounts': [],
        'upi_ids': []
    }
    
    # Extract URLs
    urls = re.findall(r'https?://[^\s]+', msg)
    intel['urls'] = urls
    
    # Extract phone numbers
    phones = re.findall(r'\+91[\s-]?\d{10}|\b[6-9]\d{9}\b', msg)
    intel['phones'] = phones
    
    # Extract amounts
    amounts = re.findall(r'Rs\.?\s*[\d,]+|₹\s*[\d,]+|\d+\s*(?:lakh|crore)', msg, re.IGNORECASE)
    intel['amounts'] = amounts
    
    # Extract UPI IDs
    upi = re.findall(r'[\w\.-]+@(?:paytm|oksbi|okicici|okaxis|okhdfcbank|ybl|ibl)', msg, re.IGNORECASE)
    intel['upi_ids'] = upi
    
    return intel

def run_scenario(scenario: Dict):
    session_id = f"TEST_{scenario['id']}_{int(time.time())}"
    print(f"\n{Colors.HEADER}▶ RUNNING SCENARIO: {scenario['description']}{Colors.ENDC}")
    print(f"   ├─ Session ID: {session_id}")
    print(f"   └─ Expected Persona: {Colors.BOLD}{scenario['expected_persona']}{Colors.ENDC}\n")
    
    history = []
    total_intel = {
        'urls': [],
        'phones': [],
        'amounts': [],
        'upi_ids': []
    }
    
    for i, msg_text in enumerate(scenario['messages']):
        print(f"{Colors.WARNING}🔴 [Scammer]:{Colors.ENDC} {msg_text}")
        
        # Extract intelligence from scammer message
        msg_intel = extract_intelligence_from_message(msg_text)
        for key in total_intel:
            total_intel[key].extend(msg_intel[key])
        
        # Show extracted intelligence
        if any(msg_intel.values()):
            print(f"   {Colors.MAGENTA}📊 Intelligence in message:{Colors.ENDC}")
            if msg_intel['urls']:
                print(f"      └─ URLs: {', '.join(msg_intel['urls'])}")
            if msg_intel['phones']:
                print(f"      └─ Phones: {', '.join(msg_intel['phones'])}")
            if msg_intel['amounts']:
                print(f"      └─ Amounts: {', '.join(msg_intel['amounts'])}")
            if msg_intel['upi_ids']:
                print(f"      └─ UPI IDs: {', '.join(msg_intel['upi_ids'])}")
        
        # Construct Payload
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": msg_text,
                "timestamp": int(time.time() * 1000)
            },
            "conversationHistory": history,
            "metadata": {
                "channel": "WhatsApp",
                "language": "English",
                "locale": "IN"
            }
        }
        
        try:
            start_ts = time.time()
            response = requests.post(
                API_URL, 
                headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                json=payload,
                timeout=15
            )
            latency = (time.time() - start_ts) * 1000
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "")
                
                # Analyze Response
                detected_persona, p_color = analyze_persona_response(reply, scenario['expected_persona'])
                
                print(f"{Colors.GREEN}🟢 [Agent]  :{Colors.ENDC} {reply}")
                print(f"   {Colors.BLUE}└─ Latency: {latency:.0f}ms | Detected Tone: {p_color}{detected_persona}{Colors.ENDC}")
                
                # Update History
                history.append({"sender": "scammer", "text": msg_text, "timestamp": int(time.time()*1000)})
                history.append({"sender": "user", "text": reply, "timestamp": int(time.time()*1000)})
                
            else:
                print(f"{Colors.FAIL}❌ API Error: {response.status_code} - {response.text}{Colors.ENDC}")
                break
                
        except Exception as e:
            print(f"{Colors.FAIL}❌ Connection Error: {str(e)}{Colors.ENDC}")
            break
            
        time.sleep(1.5)
        print("-" * 80)
    
    # Show total intelligence gathered
    print(f"\n{Colors.MAGENTA}📈 TOTAL INTELLIGENCE GATHERED:{Colors.ENDC}")
    total_items = sum(len(v) for v in total_intel.values())
    if total_items > 0:
        if total_intel['urls']:
            print(f"   ├─ URLs: {len(total_intel['urls'])} ({', '.join(set(total_intel['urls']))})")
        if total_intel['phones']:
            print(f"   ├─ Phone Numbers: {len(total_intel['phones'])} ({', '.join(set(total_intel['phones']))})")
        if total_intel['amounts']:
            print(f"   ├─ Amounts: {len(total_intel['amounts'])} ({', '.join(set(total_intel['amounts']))})")
        if total_intel['upi_ids']:
            print(f"   └─ UPI IDs: {len(total_intel['upi_ids'])} ({', '.join(set(total_intel['upi_ids']))})")
    else:
        print(f"   └─ {Colors.WARNING}No intelligence extracted{Colors.ENDC}")
    print()


if __name__ == "__main__":
    print_banner()
    
    if check_health():
        print(f"\n{Colors.BOLD}🚀 Starting {len(SCENARIOS)} Test Scenarios...{Colors.ENDC}")
        time.sleep(1)
        
        for scenario in SCENARIOS:
            run_scenario(scenario)
            time.sleep(2)
            
        print(f"\n{Colors.HEADER}{'='*80}")
        print(f"✅ TEST SUITE COMPLETED")
        print(f"{'='*80}{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}🛑 Aborting tests due to health check failure.{Colors.ENDC}")
        print("Please ensure 'app_ultimate_fixed.py' is running: uvicorn app_ultimate_fixed:app --reload")