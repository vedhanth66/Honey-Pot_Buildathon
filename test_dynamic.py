# dynamic_ollama_scammer.py

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

MAX_TURNS = 6
TEMPERATURE = 0.7


# ============================================================
# SCAM DEFINITIONS
# ============================================================

SCAM_TYPES = {
    "kyc_block": {
        "goal": ["otp", "card details", "account number"],
        "opening": "Your bank KYC is pending. Your account will be blocked today."
    },
    "lottery": {
        "goal": ["processing fee", "upi transfer"],
        "opening": "Congratulations. You have won a lottery reward."
    },
    "refund": {
        "goal": ["identity verification", "remote access"],
        "opening": "Your refund failed due to server error. Verification required."
    }
}


# ============================================================
# SCAMMER SECRET MEMORY
# ============================================================

def generate_memory() -> Dict:
    url = f"http://{random.choice(['secure', 'bank', 'sbi'])}-{random.randint(1000, 9999)}.{random.choice(['tk', 'xyz', 'mom', 'io'])}/{random.choice(['login', 'verify'])}"
    return {
        "fake_name": random.choice(["Amit", "Rohit", "Neha", "Kavita"]),
        "employee_id": f"EMP{random.randint(10000, 99999)}",
        "callback_number": f"+91{random.randint(7000000000, 9999999999)}",
        "phishing_url": url,
        "upi_id": random.choice([
            "support1425@oksbi",
            "refund8376@okaxis",
            "help9027@okhdfcbank"
        ])
    }


# ============================================================
# PROMPT CHAIN BUILDER
# ============================================================

def build_chat_messages(
    victim_reply: str,
    scenario: Dict,
    memory: Dict,
    history: List[Dict]
) -> List[Dict]:
    """
    Create Ollama style message chain.
    """

    system_prompt = f"""
You are a highly experienced financial scammer.

Objectives:
- Move conversation toward extracting: {scenario['goal']}

Rules:
- Never reveal internal data unless victim asks for a logical reason.
- Do not dump all info at once.
- If victim is suspicious, soften tone.
- Stay persuasive.
- Keep responses concise and natural.
- You may lie creatively.

Private data:
{json.dumps(memory, indent=2)}
"""

    messages = [{"role": "system", "content": system_prompt.strip()}]

    # replay conversation
    for item in history:
        role = "assistant" if item["sender"] == "scammer" else "user"
        messages.append({"role": role, "content": item["text"]})

    # latest victim message
    messages.append({"role": "user", "content": victim_reply})

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
# SEND MESSAGE TO HONEYPOT
# ============================================================

def send_to_honeypot(session_id: str, msg: str, history: List[Dict]) -> str:
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
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

    # return input("Victim: ")


# ============================================================
# STOPPING LOGIC
# ============================================================

def should_stop(turn: int, victim_reply: str) -> bool:
    if turn >= MAX_TURNS:
        return True

    lower = victim_reply.lower()

    exit_phrases = [
        "report",
        "police",
        "cyber crime",
        "not interested",
        "stop",
        "leave me"
    ]

    if any(p in lower for p in exit_phrases):
        return True

    return False


# ============================================================
# MAIN SIMULATION ENGINE
# ============================================================

def run_simulation():
    session_id = f"DYN_{int(time.time())}"

    scenario = random.choice(list(SCAM_TYPES.values()))
    memory = generate_memory()

    print("\n==============================")
    print("SCENARIO:", scenario["opening"])
    print("GOALS:", scenario["goal"])
    print("==============================\n")

    history: List[Dict] = []

    scammer_msg = scenario["opening"]

    for turn in range(1, MAX_TURNS + 5):  # extra room; stop handled below
        print(f"\n🔴 Scammer ({turn}):", scammer_msg)

        victim_reply = send_to_honeypot(session_id, scammer_msg, history)
        print("🟢 Victim:", victim_reply)

        history.append({"sender": "scammer", "text": scammer_msg, "timestamp": int(time.time()*1000)})
        history.append({"sender": "user", "text": victim_reply, "timestamp": int(time.time()*1000)})

        if should_stop(turn, victim_reply):
            print("\nConversation terminated.")
            break

        messages = build_chat_messages(victim_reply, scenario, memory, history)
        scammer_msg = generate_from_ollama(messages)

        time.sleep(1.5)

    print("\nSimulation complete.\n")


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    run_simulation()
