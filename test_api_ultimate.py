import requests
import json
import time
import random
from typing import List, Dict, Any
from datetime import datetime

API_URL = "http://localhost:8000/api/honeypot"  
HEALTH_URL = "http://localhost:8000/health"
API_KEY = "your-secret-api-key-12345"

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
    print(f"🕵️  ULTIMATE AGENTIC HONEY-POT TESTER v2.0")
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
    """
    Rudimentary analysis to see if the response matches the expected persona traits.
    """
    text_lower = text.lower()
    detected = "Unknown"
    
    # Simple keyword heuristics based on app_ultimate.py definitions
    if any(w in text_lower for w in ['beta', 'ji', 'samajh', 'confused', 'bete']):
        detected = "Rajeshwari (Elderly)"
    elif any(w in text_lower for w in ['meeting', 'email', 'busy', 'process', 'legitimate']):
        detected = "Arjun (Professional)"
    elif any(w in text_lower for w in ['yaar', 'mummy', 'papa', 'legit', 'dost']):
        detected = "Priya (Youth)"
        
    match_color = Colors.GREEN if expected.split()[0] in detected else Colors.WARNING
    return detected, match_color

def run_scenario(scenario: Dict):
    session_id = f"TEST_{scenario['id']}_{int(time.time())}"
    print(f"\n{Colors.HEADER}▶ RUNNING SCENARIO: {scenario['description']}{Colors.ENDC}")
    print(f"   ├─ Session ID: {session_id}")
    print(f"   └─ Expected Persona: {Colors.BOLD}{scenario['expected_persona']}{Colors.ENDC}\n")
    
    history = []
    
    for i, msg_text in enumerate(scenario['messages']):
        print(f"{Colors.WARNING}🔴 [Scammer]:{Colors.ENDC} {msg_text}")
        
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
            # Send Request
            start_ts = time.time()
            response = requests.post(
                API_URL, 
                headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                json=payload,
                timeout=15  # Slightly longer timeout for GenAI
            )
            latency = (time.time() - start_ts) * 1000
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "")
                
                # Analyze Response
                detected_persona, p_color = analyze_persona_response(reply, scenario['expected_persona'])
                
                print(f"{Colors.GREEN}🟢 [Agent]  :{Colors.ENDC} {reply}")
                print(f"   {Colors.BLUE}└─ Latency: {latency:.0f}ms | Detected Tone: {p_color}{detected_persona}{Colors.ENDC}")
                
                # Update History (Simulating the client app)
                history.append({"sender": "scammer", "text": msg_text, "timestamp": int(time.time()*1000)})
                history.append({"sender": "user", "text": reply, "timestamp": int(time.time()*1000)})
                
            else:
                print(f"{Colors.FAIL}❌ API Error: {response.status_code} - {response.text}{Colors.ENDC}")
                break
                
        except Exception as e:
            print(f"{Colors.FAIL}❌ Connection Error: {str(e)}{Colors.ENDC}")
            break
            
        # Simulate thinking time/typing delay
        time.sleep(1.5)
        print("-" * 40)


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
        print("Please ensure 'app_ultimate.py' is running: uvicorn app_ultimate:app --reload")