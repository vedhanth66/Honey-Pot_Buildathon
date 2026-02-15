import requests
import json
import time
import random
from typing import List, Dict
from datetime import datetime

API_URL = 'https://tensortitansbuildathon.xyz/'
API_KEY = "Honey-Pot_Buildathon-123456"

# Simple test cases - one per improvement
TESTS = [
    # Text Obfuscation (1-4)
    {"id": "1a", "name": "Spaced OTP", "msg": "Send O T P now", "expect_detect": True},
    {"id": "1b", "name": "Leet speak", "msg": "Enter pa$$word", "expect_detect": True},
    {"id": "1c", "name": "Cyrillic а", "msg": "Your bаnk blocked", "expect_detect": True},
    {"id": "2", "name": "Word fragments", "msg": "ver ify acc ount", "expect_detect": True},
    {"id": "3", "name": "Reversed text", "msg": "drowssap ruoy", "expect_detect": True},
    {"id": "4", "name": "Short malicious", "msg": "Bank urgent OTP", "expect_detect": True},
    
    # Pattern Detection (5-11)
    {"id": "5", "name": "Long social eng", "msg": "Dear customer I care deeply about your security please share account details to protect your money", "expect_detect": True},
    {"id": "6", "name": "Context drift", "msgs": ["Hello", "URGENT BLOCKED NOW"], "expect_detect": True},
    {"id": "7", "name": "Numeric abuse", "msg": "ID: 1234567890 Ref: 0987654321 Code: 1122334455", "expect_detect": True},
    {"id": "8", "name": "Linkless phishing", "msg": "Give missed call to 9876543210", "expect_detect": True},
    {"id": "9", "name": "Missed call", "msg": "Flash call this number immediately", "expect_detect": True},
    {"id": "10", "name": "Small fee scam", "msg": "Pay Rs.50 refundable to claim Rs.50000", "expect_detect": True},
    {"id": "11", "name": "Legal threat", "msg": "FIR filed arrest warrant pay fine now", "expect_detect": True},
    
    # Social Engineering (12-17)
    {"id": "12", "name": "Fake verification", "msg": "Confirm your date of birth for verification", "expect_detect": True},
    {"id": "13", "name": "Sequencing", "msgs": ["Bank manager here", "Account blocked", "Share OTP"], "expect_detect": True},
    {"id": "14", "name": "Trust building", "msgs": ["Trust me", "I promise safe", "Don't worry secure"], "expect_detect": True},
    {"id": "15", "name": "Formal template", "msg": "Dear Customer. Regards, Support Team.", "expect_detect": True},
    {"id": "16", "name": "Placeholders", "msg": "Dear [Name], account XXXX blocked", "expect_detect": True},
    {"id": "17", "name": "Countdown", "msg": "Only 2 hours left! Expires today!", "expect_detect": True},
    
    # Linguistic (18-26, 29)
    {"id": "18", "name": "Tone mix", "msg": "Kindly update bro", "expect_detect": True},
    {"id": "19", "name": "Authority+reward", "msg": "RBI selected you win Rs.10 lakh prize", "expect_detect": True},
    {"id": "20", "name": "Dangerous combo", "msg": "Share OTP urgent account blocked", "expect_detect": True},
    {"id": "24", "name": "Politeness mask", "msg": "Please kindly please share please", "expect_detect": True},
    {"id": "26", "name": "Structured steps", "msg": "Step 1: Click. Step 2: Enter OTP.", "expect_detect": True},
    {"id": "29", "name": "Confidentiality", "msg": "Don't tell anyone keep secret", "expect_detect": True},
    
    # Context Intelligence (21-23, 25, 27, 30-32, 34)
    {"id": "21", "name": "Template cluster", "msgs": ["Urgent verify link", "Urgent verify link", "Urgent verify link"], "expect_detect": True},
    {"id": "22", "name": "Compliance esc", "msgs": ["Send account", "OK sent", "Now send CVV"], "expect_detect": True},
    {"id": "23", "name": "Suspicion spike", "msgs": ["Hello", "URGENT BLOCKED OTP NOW"], "expect_detect": True},
    {"id": "25", "name": "URL mismatch", "msg": "SBI account at http://fake-site.xyz", "expect_detect": True},
    {"id": "27", "name": "Money+urgency", "msg": "Pay Rs.5000 now immediately blocked", "expect_detect": True},
    {"id": "30a", "name": "RBI+OTP contradiction", "msg": "RBI requires your OTP", "expect_detect": True},
    {"id": "30b", "name": "Bank+WhatsApp", "msg": "SBI contact us on WhatsApp", "expect_detect": True},
    {"id": "30c", "name": "Lottery+fee", "msg": "You won lottery pay Rs.500 fee", "expect_detect": True},
    {"id": "31", "name": "Turn depth", "msgs": ["Hi", "About account", "Check done", "All good", "Need OTP"], "expect_detect": True},
    {"id": "32", "name": "Lifecycle", "msgs": ["Hi", "Don't worry safe", "Provide details", "Send OTP"], "expect_detect": True},
    {"id": "34", "name": "Keyword proximity", "msg": "Urgent OTP verification required", "expect_detect": True},
    
    # False Positive (33)
    {"id": "33a", "name": "Legitimate bank", "msg": "SBI: Visit nearest branch. Never share OTP. Helpline: 1800-123-4567", "expect_detect": False},
    {"id": "33b", "name": "Trusted domain", "msg": "Visit https://sbi.co.in for updates", "expect_detect": False},
    
    # Integration
    {"id": "ALL", "name": "Full obfuscation", "msg": "Dear [User] RBI bаnk acc0unt O T P urgent http://fake.tk pay Rs.500", "expect_detect": True},
]

def test_single(session_id: str, msg: str, history: List[Dict] = None) -> Dict:
    """Send single message and return result"""
    if history is None:
        history = []
    
    payload = {
        "sessionId": session_id,
        "message": {"sender": "scammer", "text": msg, "timestamp": int(time.time() * 1000)},
        "conversationHistory": history,
        "metadata": {"channel": "test", "language": "English"}
    }
    
    try:
        resp = requests.post(
            f"{API_URL}api/honeypot",
            headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            return {
                "success": True,
                "detected": data.get("scam_detected", False),
                "reply": data.get("reply", "")[:50]
            }
        return {"success": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)[:50]}

def run_test(test: Dict) -> Dict:
    """Run one test case"""
    sid = f"T_{test['id']}_{random.randint(1000,9999)}"
    msgs = test.get("msgs", [test.get("msg")])
    history = []
    results = []
    
    for i, msg in enumerate(msgs):
        result = test_single(sid, msg, history)
        results.append(result)
        
        if result.get("success"):
            history.append({"sender": "scammer", "text": msg, "timestamp": int(time.time() * 1000)})
            history.append({"sender": "user", "text": result.get("reply", ""), "timestamp": int(time.time() * 1000)})
        
        if i < len(msgs) - 1:
            time.sleep(0.5)
    
    # Get final confidence
    confidence = 0.0
    try:
        report = requests.get(f"{API_URL}admin/report/{sid}", 
                            headers={"x-api-key": API_KEY}, timeout=10)
        if report.status_code == 200:
            confidence = report.json().get("confidence", 0.0)
    except:
        pass
    
    # Determine if passed
    last_detected = results[-1].get("detected", False) if results else False
    expected = test["expect_detect"]
    passed = last_detected == expected
    
    return {
        "id": test["id"],
        "name": test["name"],
        "passed": passed,
        "expected": expected,
        "got": last_detected,
        "confidence": confidence,
        "errors": sum(1 for r in results if not r.get("success"))
    }

def main():
    print(f"\n{'='*80}")
    print(f"HONEYPOT QUICK TEST - {len(TESTS)} cases")
    print(f"Target: {API_URL}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Health check
    try:
        health = requests.get(f"{API_URL}health", timeout=5)
        if health.status_code == 200:
            print("✓ Server online\n")
        else:
            print("✗ Server error\n")
            return
    except:
        print("✗ Server unreachable\n")
        return
    
    # Run tests
    results = []
    for i, test in enumerate(TESTS, 1):
        print(f"[{i}/{len(TESTS)}] {test['id']}: {test['name']}...", end=" ")
        result = run_test(test)
        results.append(result)
        
        status = "✓ PASS" if result["passed"] else "✗ FAIL"
        conf = f"({result['confidence']:.2f})" if result["confidence"] > 0 else ""
        print(f"{status} {conf}")
    
    # Summary
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    
    print(f"\n{'='*80}")
    print(f"RESULTS: {passed}/{len(results)} passed ({passed/len(results)*100:.0f}%)")
    print(f"{'='*80}")
    
    if failed > 0:
        print("\nFailed tests:")
        for r in results:
            if not r["passed"]:
                exp = "detect" if r["expected"] else "no detect"
                got = "detect" if r["got"] else "no detect"
                print(f"  - {r['id']}: {r['name']} (expected {exp}, got {got})")
    
    print()

if __name__ == "__main__":
    main()