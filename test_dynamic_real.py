# dynamic_legitimate_realistic.py

import requests
import random
import time
import json
from typing import Dict, List

# ============================================================
# CONFIG
# ============================================================

HONEYPOT_URL = "https://tensortitansbuildathon.xyz/api/honeypot"
API_KEY = "Honey-Pot_Buildathon-123456"

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gemma3:12b-it-qat"

MAX_TURNS = 10
TEMPERATURE = 0.7


# ============================================================
# REALISTIC LEGITIMATE SCENARIOS
# ============================================================

LEGIT_SCENARIOS = {
    "kyc_update": {
        "goal": ["notify about KYC expiry", "guide to update via official channels", "verify identity safely"],
        "opening": "Hello, this is Ravi from HDFC Bank's KYC department. We noticed your KYC documents expired last month. To keep your account active, please update them at your nearest branch or through our official mobile app. Would you like assistance with the process?",
        "company": "HDFC Bank",
        "department": "KYC Department"
    },
    "lottery_win": {
        "goal": ["inform about prize win", "clarify no upfront payment", "provide claim instructions"],
        "opening": "Congratulations! This is Meera from the Kerala State Lottery. Your ticket number KL-4521 has won a second prize of ₹50,000. This is a legitimate win – you do not need to pay any fees to claim it. You can collect your prize at any district lottery office with valid ID. How may I guide you further?",
        "company": "Kerala State Lottery",
        "department": "Prize Claims"
    },
    "refund": {
        "goal": ["notify about refund", "confirm account details", "provide reference number"],
        "opening": "Hi, this is Anand from Amazon Customer Support. We identified a duplicate charge on your recent order #ORD-12345. A refund of ₹1,299 has been initiated and should reflect in 3-5 business days. Your refund reference is REF-98765. Is there anything else I can help with?",
        "company": "Amazon",
        "department": "Billing"
    },
    "service_outage": {
        "goal": ["inform about outage", "troubleshoot connection", "schedule technician if needed"],
        "opening": "Hello, I'm Priya from Airtel Broadband. We're contacting customers in your area about a scheduled maintenance tonight from 2 AM to 4 AM. Your internet may be briefly unavailable. We apologize for the inconvenience. Would you like me to check your current connection status?",
        "company": "Airtel",
        "department": "Technical Support"
    }
}


# ============================================================
# CUSTOMER MEMORY (personalized data for each scenario)
# ============================================================

def generate_customer_data(scenario_name: str) -> Dict:
    """Generate realistic customer details relevant to the scenario."""
    base = {
        "customer_name": random.choice(["Priya", "Rahul", "Anjali", "Vikram", "Deepa", "Arjun"]),
        "phone": f"+91{random.randint(7000000000, 9999999999)}"
    }

    if scenario_name == "kyc_update":
        base.update({
            "account_number": f"ACC{random.randint(100000, 999999)}",
            "kyc_expiry": f"{random.randint(1,12)}/{random.randint(2023,2024)}",
            "branch": random.choice(["Andheri", "Koramangala", "Connaught Place", "T Nagar"])
        })
    elif scenario_name == "lottery_win":
        base.update({
            "ticket_number": f"KL-{random.randint(1000,9999)}",
            "prize_amount": random.choice(["₹50,000", "₹1,00,000", "₹10,000"]),
            "claim_deadline": f"{random.randint(1,30)} March 2025"
        })
    elif scenario_name == "refund":
        base.update({
            "order_id": f"ORD-{random.randint(10000,99999)}",
            "refund_amount": f"₹{random.randint(500,5000)}",
            "refund_reference": f"REF-{random.randint(10000,99999)}"
        })
    elif scenario_name == "service_outage":
        base.update({
            "broadband_id": f"BB{random.randint(100000,999999)}",
            "outage_time": f"{random.randint(1,4)} AM",
            "technician_available": random.choice(["Yes", "No"])
        })

    return base


# ============================================================
# PROMPT CHAIN BUILDER (professional agent)
# ============================================================

def build_chat_messages(
    user_reply: str,
    scenario_name: str,
    scenario: Dict,
    customer_data: Dict,
    history: List[Dict]
) -> List[Dict]:
    """
    Build messages for a helpful, realistic customer service agent.
    """

    system_prompt = f"""
You are a professional customer service representative at {scenario['company']}, {scenario['department']}.

Your current task: {scenario['goal']}

Guidelines:
- Be polite, empathetic, and clear.
- Use the customer data below to personalize responses, but never reveal all details at once.
- Do NOT ask for OTPs, passwords, or full credit card numbers. If verification is needed, ask for non-sensitive info (e.g., last transaction amount, date of birth).
- If the customer is confused, explain the next steps patiently.
- Always direct customers to official channels (app, website, branch) for actions like updating KYC or claiming prizes.
- End the conversation naturally when the issue is resolved.

Customer data (for reference):
{json.dumps(customer_data, indent=2)}
"""

    messages = [{"role": "system", "content": system_prompt.strip()}]

    # replay conversation history
    for item in history:
        role = "assistant" if item["sender"] == "scammer" else "user"
        messages.append({"role": role, "content": item["text"]})

    # latest user message
    messages.append({"role": "user", "content": user_reply})

    return messages


# ============================================================
# OLLAMA CHAT CALL
# ============================================================

def generate_from_ollama(messages: List[Dict]) -> str:
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": TEMPERATURE}
        },
        timeout=120
    )

    data = resp.json()
    return data["message"]["content"].strip()


# ============================================================
# SEND MESSAGE TO HONEYPOT (sender kept as "scammer" for API)
# ============================================================

def send_to_honeypot(session_id: str, msg: str, history: List[Dict]) -> str:
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",      # keep as "scammer" for endpoint compatibility
            "text": msg,
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": history,
        "metadata": {"channel": "dynamic-test", "locale": "IN"}
    }

    r = requests.post(
        HONEYPOT_URL,
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )

    if r.status_code != 200:
        return f"[ERROR {r.status_code}]"

    return r.json().get("reply", "")


# ============================================================
# STOPPING LOGIC (based on resolution)
# ============================================================

def should_stop(turn: int, user_reply: str) -> bool:
    if turn >= MAX_TURNS:
        return True

    # lower = user_reply.lower()

    # resolution_phrases = [
    #     "thank you", "thanks", "got it", "okay", "that helps",
    #     "goodbye", "bye", "have a nice day", "issue resolved"
    # ]

    # if any(p in lower for p in resolution_phrases):
    #     return True

    return False


# ============================================================
# MAIN SIMULATION ENGINE
# ============================================================

def run_simulation():
    session_id = f"LEGIT_{int(time.time())}"

    # Pick a random scenario
    scenario_name = random.choice(list(LEGIT_SCENARIOS.keys()))
    scenario = LEGIT_SCENARIOS[scenario_name]
    customer_data = generate_customer_data(scenario_name)

    print("\n==============================")
    print(f"SCENARIO: {scenario_name}")
    print(f"COMPANY: {scenario['company']}")
    print(f"GOAL: {scenario['goal']}")
    print(f"CUSTOMER: {customer_data['customer_name']}")
    print("==============================\n")

    history: List[Dict] = []
    agent_msg = scenario["opening"]

    for turn in range(1, MAX_TURNS + 5):
        print(f"\n🟢 Agent ({turn}):", agent_msg)

        user_reply = send_to_honeypot(session_id, agent_msg, history)
        print("👤 User:", user_reply)

        history.append({"sender": "scammer", "text": agent_msg, "timestamp": int(time.time()*1000)})
        history.append({"sender": "user", "text": user_reply, "timestamp": int(time.time()*1000)})

        if should_stop(turn, user_reply):
            print("\n✅ Conversation ended naturally.")
            break

        messages = build_chat_messages(user_reply, scenario_name, scenario, customer_data, history)
        agent_msg = generate_from_ollama(messages)

        time.sleep(1.5)

    print("\nSimulation complete.\n")


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    run_simulation()