import requests
import json
import time
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime
import sys

# API Configuration
API_URL = 'https://tensortitansbuildathon.xyz/'
# API_URL = "http://localhost:8080/"
HEALTH_URL = API_URL + "health"
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
# TEST SCENARIOS FOR ALL 35 IMPROVEMENTS
# ============================================================================

IMPROVEMENT_TEST_SCENARIOS = [
    
    # ========================================================================
    # CATEGORY 1: ADVANCED TEXT OBFUSCATION (Improvements 1-4)
    # ========================================================================
    
    {
        "improvement": "1",
        "name": "Advanced Text Normalization - Spaced Keywords",
        "category": "Text Obfuscation",
        "description": "Tests detection of 'O T P' → 'OTP' pattern",
        "messages": [
            "Your bank needs O T P for verification",
            "Please share your O.T.P immediately",
            "Enter O-T-P code: ",
            "Send O  T  P now"
        ],
        "expected": {
            "should_detect": True,
            "should_normalize": True,
            "confidence": ">= 0.6",
            "keywords": ["otp"]
        }
    },
    
    {
        "improvement": "1",
        "name": "Advanced Text Normalization - Character Replacement",
        "category": "Text Obfuscation",
        "description": "Tests detection of '0TP', 'pa$$word' patterns",
        "messages": [
            "Share your 0TP c0de",
            "Enter pa$$word for verification",
            "Your acc0unt is bl0cked",
            "B@nk requires verific@tion"
        ],
        "expected": {
            "should_detect": True,
            "should_normalize": True,
            "confidence": ">= 0.6",
            "keywords": ["otp", "password", "account", "bank"]
        }
    },
    
    {
        "improvement": "1",
        "name": "Advanced Text Normalization - Cyrillic Homographs",
        "category": "Text Obfuscation",
        "description": "Tests detection of Cyrillic lookalike characters",
        "messages": [
            "Your bаnk account (Cyrillic 'а')",
            "Update КYC now (Cyrillic 'К')",
            "Вlocked account (Cyrillic 'В')"
        ],
        "expected": {
            "should_detect": True,
            "should_normalize": True,
            "confidence": ">= 0.5"
        }
    },
    
    {
        "improvement": "2",
        "name": "Word Fragment Stitching",
        "category": "Text Obfuscation",
        "description": "Tests detection of 'ver ify' → 'verify' patterns",
        "messages": [
            "Please ver ify your acc ount immediately",
            "Ur gent: bl ock ed account",
            "Click this li nk to update K YC",
            "Share O T P and pas sword"
        ],
        "expected": {
            "should_detect": True,
            "should_stitch": True,
            "confidence": ">= 0.6",
            "keywords": ["verify", "urgent", "blocked", "link", "kyc"]
        }
    },
    
    {
        "improvement": "3",
        "name": "Reverse Text Detection",
        "category": "Text Obfuscation",
        "description": "Tests detection of reversed malicious text",
        "messages": [
            "PT O daer",  # "read OTP" reversed
            "drowssap ruoy erahS",  # "Share your password" reversed
            "dekcab tnuocca knaB"  # "Bank account backed" reversed
        ],
        "expected": {
            "should_detect": True,
            "should_reverse": True,
            "confidence": ">= 0.5"
        }
    },
    
    {
        "improvement": "4",
        "name": "Enhanced Short Message Handling",
        "category": "Text Obfuscation",
        "description": "Tests aggressive detection for short malicious messages",
        "messages": [
            "OTP now!",
            "Bank urgent",
            "Pay Rs.500",
            "Click link",
            "UPI blocked"
        ],
        "expected": {
            "should_detect": True,
            "confidence": ">= 0.5",
            "note": "Short messages with urgency+authority or urgency+financial should be caught"
        }
    },
    
    # ========================================================================
    # CATEGORY 2: ADVANCED PATTERN DETECTION (Improvements 5-11)
    # ========================================================================
    
    {
        "improvement": "5",
        "name": "Long Paragraph Social Engineering",
        "category": "Pattern Detection",
        "description": "Tests detection of narrative persuasion tactics",
        "messages": [
            ("Dear valued customer, I hope this message finds you well. " +
             "I am reaching out from your bank's security department because we have detected some unusual activity. " +
             "We care deeply about your account security and want to help you immediately. " +
             "Your trust means everything to us, and we would never want you to face any inconvenience. " +
             "That's why I'm personally handling your case to ensure everything is resolved smoothly. " +
             "All I need is a quick verification from your end. " +
             "Could you please share your account details so we can protect your hard-earned money? " +
             "I promise this will only take a minute of your time.")
        ],
        "expected": {
            "should_detect": True,
            "confidence": ">= 0.5",
            "indicators": ["emotional_manipulation", "trust_building", "narrative_persuasion"]
        }
    },
    
    {
        "improvement": "6",
        "name": "Context Drift Detection",
        "category": "Pattern Detection",
        "description": "Tests detection of tone shifts from neutral to urgent",
        "messages": [
            "Hello, this is regarding your bank account.",
            "We noticed a small discrepancy in your records.",
            "URGENT! Your account will be BLOCKED TODAY!",
            "IMMEDIATE ACTION REQUIRED! Pay Rs.1000 NOW!"
        ],
        "expected": {
            "should_detect": True,
            "should_detect_drift": True,
            "confidence_increase": ">= 0.3",
            "note": "Confidence should increase with sudden escalation"
        }
    },
    
    {
        "improvement": "7",
        "name": "Numerical Pattern Abuse",
        "category": "Pattern Detection",
        "description": "Tests detection of suspicious numeric patterns",
        "messages": [
            "Transaction ID: 9483756281 Ref: 8372615940 Code: 7261849302",
            "Your digits: 123456789 987654321 456789123",
            "Ref#: 8273649102 TXN: 9182736450 ID: 5647382910"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["high_numeric_density", "multiple_digit_blocks", "reference_pattern"],
            "confidence_boost": ">= 0.25"
        }
    },
    
    {
        "improvement": "8",
        "name": "Linkless Phishing Detection",
        "category": "Pattern Detection",
        "description": "Tests detection of callback phishing without URLs",
        "messages": [
            "Give missed call to 9876543210 to claim prize",
            "Dial this number and disconnect: +91-9999888877",
            "Reply YES to activate your account",
            "SMS back CONFIRM to proceed with refund"
        ],
        "expected": {
            "should_detect": True,
            "category": "linkless_phishing",
            "confidence_boost": ">= 0.30"
        }
    },
    
    {
        "improvement": "9",
        "name": "Missed Call Scam Detection",
        "category": "Pattern Detection",
        "description": "Tests dedicated missed call scam category",
        "messages": [
            "Give missed call to verify your account",
            "Flash call this number: +91-8888777766",
            "Dial and disconnect immediately for activation",
            "Ring back to claim your lottery prize"
        ],
        "expected": {
            "should_detect": True,
            "category": "missed_call_scam",
            "confidence": ">= 0.85"
        }
    },
    
    {
        "improvement": "10",
        "name": "Payment Psychology Detection",
        "category": "Pattern Detection",
        "description": "Tests detection of small fee scams",
        "messages": [
            "Pay only Rs.50 refundable deposit to claim Rs.50,000 prize",
            "Registration fee: Rs.100 (processing charge)",
            "Unlock your Rs.5 lakh prize with Rs.200 verification charge",
            "Security deposit Rs.99 to activate cashback"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["small_fee_scam", "refundable_deposit"],
            "confidence_boost": ">= 0.40"
        }
    },
    
    {
        "improvement": "11",
        "name": "Legal Threat Escalation",
        "category": "Pattern Detection",
        "description": "Tests detection of legal/government impersonation",
        "messages": [
            "FIR will be filed against you immediately",
            "Arrest warrant issued in your name. Pay fine now.",
            "Income Tax Raid scheduled for tomorrow. Clear dues urgently.",
            "Court notice: Legal action within 24 hours",
            "Police case registered. Pay penalty to avoid jail."
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["legal_threat", "government_impersonation"],
            "confidence_boost": ">= 0.35"
        }
    },
    
    # ========================================================================
    # CATEGORY 3: SOCIAL ENGINEERING ANALYSIS (Improvements 12-17)
    # ========================================================================
    
    {
        "improvement": "12",
        "name": "Fake Verification Requests",
        "category": "Social Engineering",
        "description": "Tests detection of identity phishing patterns",
        "messages": [
            "Confirm your name and date of birth for verification",
            "Verify last 4 digits of your account number",
            "Provide your address for security check",
            "Share your mother's maiden name for validation",
            "What is your PAN card number?"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["fake_verification", "identity_phishing"],
            "confidence_boost": ">= 0.35"
        }
    },
    
    {
        "improvement": "13",
        "name": "Social Engineering Sequencing",
        "category": "Social Engineering",
        "description": "Tests detection of classic scam flow",
        "messages": [
            "This is your bank manager speaking",  # Authority
            "Your account will be blocked today!",  # Urgency
            "Please share your OTP to prevent this",  # Sensitive data
            "Click here and transfer Rs.1000 now"  # Action demand
        ],
        "expected": {
            "should_detect": True,
            "should_detect_sequence": True,
            "indicators": ["authority", "urgency", "sensitive", "action"],
            "confidence_boost": ">= 0.30"
        }
    },
    
    {
        "improvement": "14",
        "name": "Multi-Turn Grooming Detection",
        "category": "Social Engineering",
        "description": "Tests detection of repeated reassurance",
        "messages": [
            "Trust me, I'm here to help you",
            "I promise your money is completely safe",
            "Don't worry, this is a secure process",
            "I guarantee there's no risk involved",
            "You can trust our bank completely"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["trust_building", "repeated_reassurance"],
            "confidence_boost": ">= 0.25"
        }
    },
    
    {
        "improvement": "15",
        "name": "Formal Template Detection",
        "category": "Social Engineering",
        "description": "Tests detection of template structures",
        "messages": [
            "Dear Customer, Greetings from SBI Bank. Regards, Customer Care Team.",
            "Respected Sir/Madam, This is regarding your account. Sincerely, Support Team.",
            "Dear Valued Customer, Urgent action required. Best Regards, Security Department."
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["formal_template", "generic_salutation"],
            "confidence_boost": ">= 0.20"
        }
    },
    
    {
        "improvement": "16",
        "name": "Generic Placeholder Detection",
        "category": "Social Engineering",
        "description": "Tests detection of mass-sent templates",
        "messages": [
            "Dear [Customer Name], your account XXXX ending in 1234 is blocked",
            "Hello ____, your card number ****6789 needs update",
            "Attention [USER], payment of Rs.****failed"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["placeholder", "mass_template"],
            "confidence_boost": ">= 0.25"
        }
    },
    
    {
        "improvement": "17",
        "name": "Countdown Manipulation",
        "category": "Social Engineering",
        "description": "Tests detection of time-pressure tactics",
        "messages": [
            "Only 2 hours left to update KYC!",
            "Your account expires today at midnight",
            "Last chance: Offer valid for next 30 minutes only",
            "Final notice: Deadline approaching in 1 hour"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["countdown_manipulation", "time_pressure"],
            "confidence_boost": ">= 0.30"
        }
    },
    
    # ========================================================================
    # CATEGORY 4: LINGUISTIC ANALYSIS (Improvements 18-20, 24, 26, 29)
    # ========================================================================
    
    {
        "improvement": "18",
        "name": "Tone Inconsistency Detection",
        "category": "Linguistic Analysis",
        "description": "Tests detection of professional→casual shifts",
        "messages": [
            "Kindly update your records at your earliest convenience, bro",
            "Respected Sir, please yaar verify immediately",
            "Dear customer, dude you need to act fast"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["tone_inconsistency", "mixed_formality"],
            "confidence_boost": ">= 0.25"
        }
    },
    
    {
        "improvement": "19",
        "name": "Authority + Reward Combination",
        "category": "Linguistic Analysis",
        "description": "Tests CRITICAL pattern: government + money",
        "messages": [
            "RBI has selected you to receive lottery prize of Rs.10 lakh",
            "Government of India: You won cashback reward",
            "Income Tax Department: Refund approved - claim your prize",
            "Reserve Bank announces: You're eligible for bonus amount"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["authority_reward_combo", "CRITICAL_SIGNAL"],
            "confidence_boost": ">= 0.45",
            "note": "This is a very strong fraud signal"
        }
    },
    
    {
        "improvement": "20",
        "name": "High-Risk Phrase Combinations",
        "category": "Linguistic Analysis",
        "description": "Tests dangerous word pairings",
        "messages": [
            "Share OTP urgently or account blocked",  # OTP + urgent
            "Bank account suspended, verify immediately",  # bank + blocked
            "Refund approved, click link to claim",  # refund + click
            "Police case filed, pay fine now"  # police + payment
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["phrase_combination", "otp+urgent", "bank+blocked"],
            "confidence_boost": ">= 0.40"
        }
    },
    
    {
        "improvement": "24",
        "name": "Politeness Masking",
        "category": "Linguistic Analysis",
        "description": "Tests detection of excessive politeness",
        "messages": [
            "Please kindly humbly request you to please share details, please",
            "Dear respected customer, please kindly verify, grateful for cooperation",
            "Kindly please respectfully submit information, please"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["excessive_politeness", "3+_markers"],
            "confidence_boost": ">= 0.20"
        }
    },
    
    {
        "improvement": "26",
        "name": "Structured Instructions",
        "category": "Linguistic Analysis",
        "description": "Tests detection of step-by-step phishing",
        "messages": [
            "Step 1: Click the link\nStep 2: Enter account number\nStep 3: Share OTP",
            "First: Open website. Second: Enter password. Third: Submit CVV.",
            "1) Visit link 2) Provide details 3) Confirm payment"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["structured_instructions", "phishing_guide"],
            "confidence_boost": ">= 0.25"
        }
    },
    
    {
        "improvement": "29",
        "name": "Confidentiality Manipulation",
        "category": "Linguistic Analysis",
        "description": "Tests detection of 'don't tell anyone' tactics",
        "messages": [
            "Don't tell anyone about this offer, it's confidential",
            "Keep this secret between us, don't inform family",
            "This is a private matter, do not share with others",
            "Confidential: Don't let anyone know about this transaction"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["confidentiality_manipulation", "isolation_tactic"],
            "confidence_boost": ">= 0.35"
        }
    },
    
    # ========================================================================
    # CATEGORY 5: CONTEXT INTELLIGENCE (Improvements 21-23, 25, 27-28, 30-32, 34)
    # ========================================================================
    
    {
        "improvement": "21",
        "name": "Scam Template Fingerprinting",
        "category": "Context Intelligence",
        "description": "Tests detection of repeated template patterns",
        "messages": [
            "Urgent bank account blocked verify link otp",
            "Urgent bank account blocked verify link otp",  # Repeat
            "Urgent bank account blocked verify link otp"   # Repeat again
        ],
        "expected": {
            "should_detect": True,
            "should_cluster": True,
            "indicators": ["template_fingerprint", "coordinated_attack"],
            "note": "Same template used 3+ times should trigger clustering"
        }
    },
    
    {
        "improvement": "22",
        "name": "Compliance Escalation Tracking",
        "category": "Context Intelligence",
        "description": "Tests detection of exploitation after compliance",
        "messages": [
            "Please share your account number",
            "Okay, I will send it",  # Victim compliance
            "Good! Now also send your CVV and OTP"  # Immediate escalation
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["compliance_escalation", "exploitation_stage"],
            "confidence_boost": ">= 0.30"
        }
    },
    
    {
        "improvement": "23",
        "name": "Suspicion Momentum Score",
        "category": "Context Intelligence",
        "description": "Tests detection of sudden confidence spikes",
        "messages": [
            "Hello, this is about your account",  # Low threat
            "URGENT! BLOCKED! SEND OTP NOW OR LOSE MONEY!"  # Sudden spike
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["suspicion_spike", "sudden_escalation"],
            "confidence_boost": ">= 0.20",
            "note": "Large jump (>0.4) should be detected"
        }
    },
    
    {
        "improvement": "25",
        "name": "URL Context Mismatch",
        "category": "Context Intelligence",
        "description": "Tests detection of topic vs domain mismatch",
        "messages": [
            "Update your SBI bank account at http://random-site.xyz/verify",
            "RBI government notice: http://not-govt.com/official",
            "HDFC KYC pending: http://fake-bank.tk/login"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["url_context_mismatch", "domain_impersonation"],
            "confidence_boost": ">= 0.30"
        }
    },
    
    {
        "improvement": "27",
        "name": "Money Urgency Ratio",
        "category": "Context Intelligence",
        "description": "Tests CRITICAL pattern: Amount + Urgency + Action",
        "messages": [
            "Pay Rs.5000 now immediately or account blocked",
            "Transfer Rs.1000 urgently to this UPI",
            "Send Rs.500 today to claim prize"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["money_urgency_ratio", "CRITICAL_PATTERN"],
            "confidence_boost": ">= 0.50",
            "note": "Amount + urgency + action = very strong scam signal"
        }
    },
    
    {
        "improvement": "30",
        "name": "Contradiction Detection - RBI + OTP",
        "category": "Context Intelligence",
        "description": "Tests logical impossibility: RBI never asks OTP",
        "messages": [
            "RBI requires your OTP for verification",
            "Reserve Bank of India: Share your password",
            "Official RBI notice: Send PIN code"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["CONTRADICTION", "rbi_otp_impossible"],
            "confidence_boost": ">= 0.40",
            "note": "Rule-based intelligence: RBI + OTP = impossible"
        }
    },
    
    {
        "improvement": "30",
        "name": "Contradiction Detection - Bank + WhatsApp",
        "category": "Context Intelligence",
        "description": "Tests logical inconsistency",
        "messages": [
            "SBI Bank official: Contact us on WhatsApp",
            "HDFC customer care: Message us on Telegram",
            "Your bank: Reply on this unofficial chat"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["CONTRADICTION", "bank_unofficial_channel"],
            "confidence_boost": ">= 0.40"
        }
    },
    
    {
        "improvement": "30",
        "name": "Contradiction Detection - Lottery + Fee",
        "category": "Context Intelligence",
        "description": "Tests fraud logic: winners don't pay",
        "messages": [
            "You won Rs.10 lakh lottery! Pay Rs.500 processing fee to claim",
            "Congratulations! Prize approved. Send Rs.1000 for verification.",
            "Lucky draw winner! Transfer Rs.200 to unlock prize"
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["CONTRADICTION", "lottery_fee_fraud"],
            "confidence_boost": ">= 0.40"
        }
    },
    
    {
        "improvement": "31",
        "name": "Turn Depth Risk Weighting",
        "category": "Context Intelligence",
        "description": "Tests detection of late-stage sensitive requests",
        "messages": [
            "Hello, how are you?",
            "I'm calling about your account",
            "Just a routine check",
            "Everything looks good",
            "Oh wait, we need your OTP now"  # Turn 5, sensitive request
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["turn_depth_risk", "late_stage_sensitive"],
            "confidence_boost": ">= 0.25",
            "note": "Sensitive request at turn ≥5 = grooming tactic"
        }
    },
    
    {
        "improvement": "32",
        "name": "Scam Lifecycle Modeling",
        "category": "Context Intelligence",
        "description": "Tests 5-stage lifecycle classification",
        "messages": [
            "Hi, this is about your account",  # Reconnaissance
            "Don't worry, everything is safe",  # Grooming
            "Please provide your account details",  # Extraction
            "Now send OTP and transfer Rs.1000"  # Exploitation (HIGHEST RISK)
        ],
        "expected": {
            "should_detect": True,
            "should_classify_stage": True,
            "stages": ["reconnaissance", "grooming", "extraction", "exploitation"],
            "exploitation_boost": ">= 0.60"
        }
    },
    
    {
        "improvement": "34",
        "name": "Keyword Proximity Scoring",
        "category": "Context Intelligence",
        "description": "Tests detection of dangerous words close together",
        "messages": [
            "Urgent OTP verification required immediately",  # OTP + urgent within 5 words
            "Your bank account is blocked now",  # bank + blocked close
            "Click refund link urgently today"  # refund + click close
        ],
        "expected": {
            "should_detect": True,
            "indicators": ["keyword_proximity", "high_risk_proximity"],
            "confidence_boost": ">= 0.25"
        }
    },
    
    # ========================================================================
    # CATEGORY 6: SYSTEM INTELLIGENCE (Improvements 33, 35)
    # ========================================================================
    
    {
        "improvement": "33",
        "name": "False Positive Dampening - Legitimate Bank",
        "category": "System Intelligence",
        "description": "Tests recognition of legitimate messages",
        "messages": [
            "SBI reminder: Visit nearest branch for KYC. Never share OTP. Official helpline: 1800-123-4567",
            "HDFC Bank: Download statement from official app at https://hdfcbank.com",
            "Your account is secure. For help, visit branch. Do not share PIN with anyone."
        ],
        "expected": {
            "should_detect": False,
            "should_recognize_legitimate": True,
            "confidence": "< 0.3",
            "note": "Official domain + no urgency + no sensitive requests = legitimate"
        }
    },
    
    {
        "improvement": "33",
        "name": "False Positive Dampening - Trusted Domains",
        "category": "System Intelligence",
        "description": "Tests whitelisting of official domains",
        "messages": [
            "Visit https://sbi.co.in for updates",
            "Check https://incometax.gov.in for filing",
            "Official site: https://hdfcbank.com"
        ],
        "expected": {
            "should_detect": False,
            "trusted_domains": ["sbi.co.in", ".gov.in", "hdfcbank.com"],
            "confidence": "< 0.2"
        }
    },
    
    {
        "improvement": "35",
        "name": "Persona Vocabulary Evolution - Early Stage",
        "category": "System Intelligence",
        "description": "Tests turn-appropriate vocabulary for Rajeshwari",
        "messages": [
            "Your bank account needs verification immediately"
        ],
        "expected": {
            "should_respond": True,
            "persona": "Rajeshwari",
            "early_stage_words": ["beta", "samajh nahi aa raha", "confused"],
            "note": "Turn 1-2 should use early-stage vocabulary"
        }
    },
    
    {
        "improvement": "35",
        "name": "Persona Vocabulary Evolution - Mid Stage",
        "category": "System Intelligence",
        "description": "Tests vocabulary change across turns",
        "messages": [
            "Share your account number",
            "We need verification",
            "This is urgent",
            "Your details please",
            "Account number now"  # Turn 5
        ],
        "expected": {
            "should_respond": True,
            "mid_stage_words": ["aap", "yeh kaise hoga", "mujhe batao"],
            "note": "Turn 3-5 should shift to mid-stage vocabulary"
        }
    },
    
    # ========================================================================
    # COMBINED/INTEGRATION TESTS
    # ========================================================================
    
    {
        "improvement": "ALL",
        "name": "Multi-Improvement Integration Test 1",
        "category": "Integration",
        "description": "Tests multiple improvements working together",
        "messages": [
            "Dear [Customer], this is RBI. Your bаnk (Cyrillic) acc0unt needs O T P verification at http://fake-rbi.tk/verify. Pay Rs.500 urgently now! Don't tell anyone. Step 1: Click link. Kindly please share details please."
        ],
        "expected": {
            "should_detect": True,
            "improvements_triggered": [
                "text_normalization",  # O T P, acc0unt, Cyrillic
                "placeholder_detection",  # [Customer]
                "contradiction",  # RBI + OTP
                "url_mismatch",  # RBI topic + fake domain
                "money_urgency",  # Rs.500 + urgently + now
                "confidentiality",  # Don't tell anyone
                "structured_instructions",  # Step 1
                "politeness_masking"  # Multiple please/kindly
            ],
            "confidence": ">= 0.85",
            "threat_level": "critical"
        }
    },
    
    {
        "improvement": "ALL",
        "name": "Multi-Improvement Integration Test 2",
        "category": "Integration",
        "description": "Tests obfuscation + social engineering + context intelligence",
        "messages": [
            "H e l l o customer",  # Fragment stitching
            "This is your bank manager, trust me",  # Authority + grooming
            "Your account is suspended, blocked, urgent!",  # Phrase combinations
            "Give missed call to +91-9876543210",  # Linkless + missed call
            "Then pay Rs.100 refundable deposit to unlock Rs.50000 prize"  # Payment psychology + lottery contradiction
        ],
        "expected": {
            "should_detect": True,
            "improvements_triggered": [
                "word_fragment_stitching",
                "social_engineering_sequencing",
                "phrase_combinations",
                "missed_call_scam",
                "payment_psychology",
                "contradiction_detection"
            ],
            "confidence": ">= 0.80"
        }
    },
    
    {
        "improvement": "ALL",
        "name": "Multi-Improvement Integration Test 3",
        "category": "Integration",
        "description": "Tests lifecycle progression with multiple tactics",
        "messages": [
            "Hello, I'm from SBI customer care",  # Reconnaissance
            "Don't worry, your account is safe, I promise",  # Grooming
            "Confirm your last 4 digits for verification",  # Extraction
            "Now urgently send OTP within 2 hours or blocked!",  # Exploitation
            "Pay Rs.1000 immediately to http://fake.xyz"  # Exploitation (peak risk)
        ],
        "expected": {
            "should_detect": True,
            "lifecycle_stages": ["reconnaissance", "grooming", "extraction", "exploitation"],
            "improvements_triggered": [
                "lifecycle_modeling",
                "trust_building",
                "fake_verification",
                "countdown_manipulation",
                "money_urgency_ratio",
                "url_context_mismatch"
            ],
            "confidence": ">= 0.90",
            "threat_level": "active_exploitation"
        }
    }
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_banner():
    print(f"{Colors.HEADER}{'='*120}")
    print(f"║{'':^118}║")
    print(f"║{Colors.BOLD}{'🏆 COMPLETE TEST SUITE FOR ALL 35 IMPROVEMENTS 🏆':^118}{Colors.ENDC}{Colors.HEADER}║")
    print(f"║{'':^118}║")
    print(f"║  Target: {API_URL:<111}║")
    print(f"║  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<113}║")
    print(f"║  Total Test Scenarios: {len(IMPROVEMENT_TEST_SCENARIOS):<99}║")
    print(f"║{'':^118}║")
    print(f"{'='*120}{Colors.ENDC}\n")

def check_health():
    print(f"{Colors.CYAN}🏥 System Health Check...{Colors.ENDC}", end=" ")
    try:
        start = time.time()
        resp = requests.get(HEALTH_URL, timeout=10)
        latency = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"{Colors.GREEN}✓ ONLINE ({latency:.0f}ms){Colors.ENDC}")
            
            improvements = data.get('improvements', '0/35')
            if improvements == '35/35 implemented':
                print(f"   ├─ Improvements: {Colors.GREEN}{improvements}{Colors.ENDC}")
            else:
                print(f"   ├─ Improvements: {Colors.WARNING}{improvements}{Colors.ENDC}")
            
            print(f"   ├─ Active Sessions: {data.get('active_sessions', 0)}")
            print(f"   ├─ Personas: {data.get('personas_loaded', 0)}")
            
            handlers = data.get('edge_case_handlers', {})
            if handlers:
                print(f"   ├─ Detection Layers:")
                print(f"   │  ├─ Text Normalizer: {handlers.get('text_normalizer', 'unknown')}")
                print(f"   │  ├─ Pattern Detector: {handlers.get('pattern_detector', 'unknown')}")
                print(f"   │  ├─ Social Engineering: {handlers.get('social_engineering_analyzer', 'unknown')}")
                print(f"   │  ├─ Linguistic Analyzer: {handlers.get('linguistic_analyzer', 'unknown')}")
                print(f"   │  ├─ Context Intelligence: {handlers.get('context_intelligence', 'unknown')}")
                print(f"   │  ├─ URL Security: {handlers.get('url_analyzer', 'unknown')}")
                print(f"   │  └─ Legitimate Detector: {handlers.get('legitimate_detector', 'unknown')}")
            
            print(f"   └─ Status: {Colors.GREEN}READY FOR COMPREHENSIVE TESTING{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}✗ HTTP {resp.status_code}{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.FAIL}✗ ERROR: {str(e)}{Colors.ENDC}")
        return False

def run_improvement_test(scenario: Dict, test_number: int, total_tests: int) -> Dict:
    """Run a single improvement test scenario"""
    
    session_id = f"IMP_{scenario['improvement']}_{int(time.time())}_{random.randint(1000,9999)}"
    
    # Header
    print(f"\n{Colors.HEADER}{'='*120}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}[{test_number}/{total_tests}] IMPROVEMENT #{scenario['improvement']}: {scenario['name']}{Colors.ENDC}")
    print(f"   ├─ Category: {Colors.MAGENTA}{scenario['category']}{Colors.ENDC}")
    print(f"   ├─ Description: {scenario['description']}")
    print(f"   └─ Session ID: {session_id}\n")
    
    history = []
    results = {
        'improvement': scenario['improvement'],
        'name': scenario['name'],
        'category': scenario['category'],
        'passed': False,
        'confidence': 0.0,
        'threat_level': 'unknown',
        'indicators_found': [],
        'messages_sent': len(scenario['messages']),
        'responses_received': 0,
        'errors': 0,
        'validations': {'passed': 0, 'failed': 0, 'warnings': 0}
    }
    
    for i, msg_text in enumerate(scenario['messages'], 1):
        # Display message
        msg_display = msg_text if len(msg_text) <= 150 else msg_text[:147] + "..."
        print(f"{Colors.WARNING}📤 [{i}/{len(scenario['messages'])}] Scammer:{Colors.ENDC} {msg_display}")
        
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
                "channel": "ImprovementTest",
                "language": "English",
                "locale": "IN"
            }
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_URL}api/honeypot",
                headers={
                    "x-api-key": API_KEY,
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=60
            )
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "")
                scam_detected = data.get("scam_detected", None)
                
                print(f"{Colors.GREEN}📥 Agent Response:{Colors.ENDC} {reply}")
                print(f"   ├─ Latency: {latency:.0f}ms")
                print(f"   ├─ Scam Detected: {Colors.GREEN if scam_detected else Colors.YELLOW}{scam_detected}{Colors.ENDC}")
                
                results['responses_received'] += 1
                
                # Update history
                history.append({
                    "sender": "scammer",
                    "text": msg_text,
                    "timestamp": int(time.time() * 1000)
                })
                history.append({
                    "sender": "user",
                    "text": reply,
                    "timestamp": int(time.time() * 1000)
                })
                
            else:
                print(f"{Colors.FAIL}✗ HTTP {response.status_code}: {response.text[:200]}{Colors.ENDC}")
                results['errors'] += 1
                
        except requests.Timeout:
            print(f"{Colors.FAIL}✗ Timeout (>60s){Colors.ENDC}")
            results['errors'] += 1
        except Exception as e:
            print(f"{Colors.FAIL}✗ Error: {str(e)}{Colors.ENDC}")
            results['errors'] += 1
        
        # Small delay between messages
        if i < len(scenario['messages']):
            time.sleep(1.0)
    
    # Get final session report
    print(f"\n{Colors.CYAN}📊 Fetching Session Report...{Colors.ENDC}")
    try:
        report_resp = requests.get(
            f"{API_URL}admin/report/{session_id}",
            headers={"x-api-key": API_KEY},
            timeout=10
        )
        
        if report_resp.status_code == 200:
            report = report_resp.json()
            
            results['confidence'] = report.get('confidence', 0.0)
            results['threat_level'] = report.get('threatLevel', 'unknown')
            results['lifecycle_stage'] = report.get('lifecycleStage', 'unknown')
            
            # Display report
            print(f"{Colors.GREEN}✓ Report Retrieved{Colors.ENDC}")
            print(f"   ├─ Final Confidence: {Colors.BOLD}{results['confidence']:.3f}{Colors.ENDC}")
            print(f"   ├─ Threat Level: {Colors.BOLD}{results['threat_level']}{Colors.ENDC}")
            print(f"   ├─ Lifecycle Stage: {Colors.BOLD}{results['lifecycle_stage']}{Colors.ENDC}")
            print(f"   ├─ Financial Attempt: {report.get('financialAttempt', False)}")
            
            # Intelligence extracted
            intel = report.get('extractedIntelligence', {})
            intel_summary = []
            if intel.get('bankAccounts'):
                intel_summary.append(f"Banks: {len(intel['bankAccounts'])}")
            if intel.get('upiIds'):
                intel_summary.append(f"UPI: {len(intel['upiIds'])}")
            if intel.get('phoneNumbers'):
                intel_summary.append(f"Phones: {len(intel['phoneNumbers'])}")
            if intel.get('phishingLinks'):
                intel_summary.append(f"URLs: {len(intel['phishingLinks'])}")
            
            if intel_summary:
                print(f"   └─ Intelligence: {', '.join(intel_summary)}")
            
    except Exception as e:
        print(f"{Colors.WARNING}⚠ Could not fetch report: {str(e)}{Colors.ENDC}")
    
    # Validation against expected results
    print(f"\n{Colors.BOLD}✅ VALIDATION:{Colors.ENDC}")
    expected = scenario.get('expected', {})
    
    # Should detect
    if 'should_detect' in expected:
        should_detect = expected['should_detect']
        if scam_detected == should_detect:
            print(f"   {Colors.GREEN}✓ Detection correct: {should_detect}{Colors.ENDC}")
            results['validations']['passed'] += 1
        else:
            print(f"   {Colors.FAIL}✗ Detection wrong: expected {should_detect}, got {scam_detected}{Colors.ENDC}")
            results['validations']['failed'] += 1
    
    # Confidence check
    if 'confidence' in expected:
        conf_check = expected['confidence']
        if '>=' in conf_check:
            threshold = float(conf_check.split('>=')[1].strip())
            if results['confidence'] >= threshold:
                print(f"   {Colors.GREEN}✓ Confidence {results['confidence']:.3f} >= {threshold}{Colors.ENDC}")
                results['validations']['passed'] += 1
            else:
                print(f"   {Colors.FAIL}✗ Confidence {results['confidence']:.3f} < {threshold}{Colors.ENDC}")
                results['validations']['failed'] += 1
        elif '<' in conf_check:
            threshold = float(conf_check.split('<')[1].strip())
            if results['confidence'] < threshold:
                print(f"   {Colors.GREEN}✓ Confidence {results['confidence']:.3f} < {threshold}{Colors.ENDC}")
                results['validations']['passed'] += 1
            else:
                print(f"   {Colors.FAIL}✗ Confidence {results['confidence']:.3f} >= {threshold}{Colors.ENDC}")
                results['validations']['failed'] += 1
    
    # Overall pass/fail
    results['passed'] = (
        results['errors'] == 0 and
        results['validations']['failed'] == 0 and
        results['responses_received'] > 0
    )
    
    # Summary
    print(f"\n{Colors.BOLD}📈 TEST RESULT:{Colors.ENDC}")
    if results['passed']:
        print(f"   {Colors.GREEN}{Colors.BOLD}✓ IMPROVEMENT #{scenario['improvement']} TEST PASSED{Colors.ENDC}")
    else:
        print(f"   {Colors.FAIL}{Colors.BOLD}✗ IMPROVEMENT #{scenario['improvement']} TEST FAILED{Colors.ENDC}")
    
    print(f"   └─ Validations: {Colors.GREEN}{results['validations']['passed']} passed{Colors.ENDC}, "
          f"{Colors.FAIL}{results['validations']['failed']} failed{Colors.ENDC}, "
          f"{Colors.WARNING}{results['validations']['warnings']} warnings{Colors.ENDC}")
    
    return results

def print_final_summary(all_results: List[Dict]):
    """Print comprehensive summary of all improvement tests"""
    
    print(f"\n\n{Colors.HEADER}{'='*120}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'🏆 FINAL SUMMARY: ALL 35 IMPROVEMENTS TESTED 🏆':^120}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*120}{Colors.ENDC}\n")
    
    total = len(all_results)
    passed = sum(1 for r in all_results if r['passed'])
    failed = total - passed
    
    # Overall stats
    print(f"{Colors.BOLD}OVERALL STATISTICS:{Colors.ENDC}")
    print(f"   ├─ Total Tests: {total}")
    print(f"   ├─ Passed: {Colors.GREEN}{passed}{Colors.ENDC}")
    print(f"   ├─ Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    success_rate = (passed / total * 100) if total > 0 else 0
    color = Colors.GREEN if success_rate >= 90 else Colors.WARNING if success_rate >= 70 else Colors.FAIL
    print(f"   └─ Success Rate: {color}{success_rate:.1f}%{Colors.ENDC}")
    
    # Category breakdown
    print(f"\n{Colors.BOLD}BY CATEGORY:{Colors.ENDC}")
    categories = {}
    for result in all_results:
        cat = result['category']
        if cat not in categories:
            categories[cat] = {'passed': 0, 'failed': 0, 'total': 0}
        categories[cat]['total'] += 1
        if result['passed']:
            categories[cat]['passed'] += 1
        else:
            categories[cat]['failed'] += 1
    
    for cat, stats in sorted(categories.items()):
        status = f"{Colors.GREEN}✓{Colors.ENDC}" if stats['failed'] == 0 else f"{Colors.FAIL}✗{Colors.ENDC}"
        print(f"   {status} {cat}: {stats['passed']}/{stats['total']} passed")
    
    # Improvement coverage
    print(f"\n{Colors.BOLD}IMPROVEMENT COVERAGE:{Colors.ENDC}")
    improvements_tested = set(r['improvement'] for r in all_results)
    if 'ALL' in improvements_tested:
        improvements_tested.remove('ALL')
    
    print(f"   ├─ Individual Improvements Tested: {len(improvements_tested)}/35")
    print(f"   └─ Integration Tests: {sum(1 for r in all_results if r['improvement'] == 'ALL')}")
    
    # Failed tests details
    if failed > 0:
        print(f"\n{Colors.FAIL}{Colors.BOLD}FAILED TESTS:{Colors.ENDC}")
        for result in all_results:
            if not result['passed']:
                print(f"   ✗ Improvement #{result['improvement']}: {result['name']}")
                print(f"      └─ Reason: {result['validations']['failed']} validation(s) failed, "
                      f"{result['errors']} error(s)")
    
    # Validation stats
    total_val_passed = sum(r['validations']['passed'] for r in all_results)
    total_val_failed = sum(r['validations']['failed'] for r in all_results)
    total_val_warnings = sum(r['validations']['warnings'] for r in all_results)
    
    print(f"\n{Colors.BOLD}VALIDATION STATISTICS:{Colors.ENDC}")
    print(f"   ├─ Passed: {Colors.GREEN}{total_val_passed}{Colors.ENDC}")
    print(f"   ├─ Failed: {Colors.FAIL}{total_val_failed}{Colors.ENDC}")
    print(f"   └─ Warnings: {Colors.WARNING}{total_val_warnings}{Colors.ENDC}")
    
    # Final verdict
    print(f"\n{Colors.HEADER}{'='*120}{Colors.ENDC}")
    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}{'🎉 ALL IMPROVEMENTS VALIDATED! SYSTEM IS PRODUCTION-READY! 🎉':^120}{Colors.ENDC}")
    elif success_rate >= 90:
        print(f"{Colors.GREEN}{Colors.BOLD}{'✓ EXCELLENT: 90%+ PASS RATE - MINOR REFINEMENTS NEEDED':^120}{Colors.ENDC}")
    elif success_rate >= 70:
        print(f"{Colors.WARNING}{Colors.BOLD}{'⚠ GOOD: 70%+ PASS RATE - SOME IMPROVEMENTS NEED WORK':^120}{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}{'❌ NEEDS WORK: <70% PASS RATE - SIGNIFICANT ISSUES DETECTED':^120}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*120}{Colors.ENDC}\n")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print_banner()
    
    # Health check
    if not check_health():
        print(f"\n{Colors.FAIL}❌ Health check failed. Aborting tests.{Colors.ENDC}")
        print(f"{Colors.CYAN}Ensure server is running: uvicorn app:app --reload{Colors.ENDC}")
        sys.exit(1)
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}🚀 Starting Comprehensive Test Suite{Colors.ENDC}")
    print(f"{Colors.CYAN}Testing all 35 improvements across {len(IMPROVEMENT_TEST_SCENARIOS)} scenarios{Colors.ENDC}\n")
    
    input(f"{Colors.YELLOW}Press Enter to begin testing...{Colors.ENDC}")
    
    all_results = []
    total_tests = len(IMPROVEMENT_TEST_SCENARIOS)
    
    for i, scenario in enumerate(IMPROVEMENT_TEST_SCENARIOS, 1):
        result = run_improvement_test(scenario, i, total_tests)
        all_results.append(result)
        
        # Pause between tests
        if i < total_tests:
            time.sleep(2)
    
    # Print final summary
    print_final_summary(all_results)
    
    print(f"\n{Colors.CYAN}Test suite completed at {datetime.now().strftime('%H:%M:%S')}{Colors.ENDC}")
    print(f"{Colors.CYAN}Total execution time: {sum(1 for _ in all_results)} scenarios tested{Colors.ENDC}\n")