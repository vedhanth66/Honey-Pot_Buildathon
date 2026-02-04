"""
ULTIMATE Agentic Honey-Pot System - FINAL PRODUCTION VERSION
All critical bugs fixed - Ready for 1st place
"""

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
import google.generativeai as genai
import re
import os
import httpx
from datetime import datetime
import json
import logging
from contextlib import asynccontextmanager
from enum import Enum
from dataclasses import dataclass, field
import random
import time
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY", "Honey-Pot_Buildathon-123456")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API configured")
else:
    logger.warning("Gemini API key not set - using fallback mode")

class ScamCategory(Enum):
    BANKING = "banking_fraud"
    UPI = "upi_fraud"
    KYC = "kyc_scam"
    LOTTERY = "lottery_scam"
    TECH_SUPPORT = "tech_support_scam"
    PHISHING = "phishing"
    REFUND = "refund_scam"
    UNKNOWN = "unknown"

class PersonaType(Enum):
    ELDERLY = "elderly_victim"
    PROFESSIONAL = "busy_professional"
    YOUTH = "naive_youth"

@dataclass
class Persona:
    name: str
    age: int
    occupation: str
    tech_savviness: int
    gullibility: int
    anxiety_level: int
    speech_patterns: List[str]
    common_phrases: List[str]
    vulnerabilities: List[str]
    backstory: str
    language_style: str
    emotional_state: str = "neutral"
    trust_level: float = 0.5
    confusion_count: int = 0

class PersonaLibrary:
    @staticmethod
    def get_personas() -> Dict[PersonaType, Persona]:
        return {
            PersonaType.ELDERLY: Persona(
                name="Rajeshwari",
                age=68,
                occupation="Retired teacher",
                tech_savviness=2,
                gullibility=8,
                anxiety_level=7,
                speech_patterns=[
                    "speaks in full sentences with formal Hindi-English mix",
                    "uses respectful terms (beta, ji)",
                    "asks for clarification often",
                    "mentions family members",
                    "references traditional values"
                ],
                common_phrases=[
                    "Beta, main thoda samajh nahi pa rahi hun",
                    "Mere bete ko phone karna padega kya?",
                    "Pehle kabhi aisa nahi hua",
                    "Mujhe aap ka naam bataiye",
                    "Bank se call hai toh theek hai",
                    "Yeh sab mujhe confusion mein daal raha hai",
                    "Ek minute, main apne bete se pooch lun?"
                ],
                vulnerabilities=[
                    "fear of losing life savings",
                    "desire to not trouble children",
                    "trust in authority figures",
                    "confusion about technology",
                    "urgency-induced panic"
                ],
                backstory="Widow living alone, manages finances but relies on bank advice. Recently got smartphone from grandson.",
                language_style="Formal Hinglish, occasionally makes tech mistakes"
            ),
            
            PersonaType.PROFESSIONAL: Persona(
                name="Arjun Mehta",
                age=34,
                occupation="Sales Manager",
                tech_savviness=6,
                gullibility=4,
                anxiety_level=5,
                speech_patterns=[
                    "short, efficient responses",
                    "mentions being busy/in meetings",
                    "wants quick resolution",
                    "slightly skeptical but time-pressured",
                    "uses business terminology"
                ],
                common_phrases=[
                    "Jaldi karo, meeting hai",
                    "Email bhej do details",
                    "Main branch mein complaint kar dunga",
                    "Yeh legitimate hai na?",
                    "Process kya hai exactly?",
                    "Conference call pe hun, quick batao",
                    "Aur kya details chahiye tumhe?"
                ],
                vulnerabilities=[
                    "fear of work disruption",
                    "impatience leading to quick decisions",
                    "desire to appear competent",
                    "fear of missing deadlines",
                    "multitasking mistakes"
                ],
                backstory="Mid-level manager, travels frequently, handles banking via app. Suspicious but will comply if threat credible.",
                language_style="Fast-paced casual Hinglish, abbreviated responses"
            ),
            
            PersonaType.YOUTH: Persona(
                name="Priya Sharma",
                age=22,
                occupation="College student / Intern",
                tech_savviness=7,
                gullibility=6,
                anxiety_level=6,
                speech_patterns=[
                    "uses internet slang",
                    "overthinks and over-explains",
                    "seeks validation and reassurance",
                    "mentions parents for major decisions",
                    "anxious about future consequences"
                ],
                common_phrases=[
                    "Yaar mujhe samajh nahi aa raha",
                    "Mummy papa ko batana padega?",
                    "Yeh legit hai na?",
                    "Mujhe koi problem toh nahi hoga?",
                    "Mere dost ko bhi same message aaya tha",
                    "Seriously yaar?",
                    "Thoda explain karo please"
                ],
                vulnerabilities=[
                    "fear of missing opportunities",
                    "desire for financial independence",
                    "trust in digital communication",
                    "fear of legal trouble",
                    "peer influence and FOMO"
                ],
                backstory="First bank account, just started using UPI. Part-time internship. Parents handle major finances.",
                language_style="Casual Hinglish with slang, expressive with emojis avoided"
            )
        }

class PersonaSelector:
    CATEGORY_MAPPING = {
        ScamCategory.BANKING: PersonaType.ELDERLY,
        ScamCategory.UPI: PersonaType.YOUTH,
        ScamCategory.KYC: PersonaType.ELDERLY,
        ScamCategory.LOTTERY: PersonaType.YOUTH,
        ScamCategory.TECH_SUPPORT: PersonaType.ELDERLY,
        ScamCategory.PHISHING: PersonaType.PROFESSIONAL,
        ScamCategory.REFUND: PersonaType.PROFESSIONAL,
        ScamCategory.UNKNOWN: PersonaType.YOUTH
    }
    
    @staticmethod
    def select(category: ScamCategory) -> Persona:
        personas = PersonaLibrary.get_personas()
        persona_type = PersonaSelector.CATEGORY_MAPPING.get(
            category, 
            PersonaType.YOUTH
        )
        return personas[persona_type]

@dataclass
class DetectionResult:
    is_scam: bool
    confidence: float
    category: ScamCategory
    indicators: List[str]
    urgency_score: float
    threat_level: str
    impersonation_target: Optional[str] = None

class AdvancedDetector:
    CRITICAL_PATTERNS = {
        'upi_request': r'\b(upi|phone\s*pe|google\s*pay|paytm|gpay|bhim)\b',
        'account_request': r'\b(account|acc)\b\s*\w*\s*\b(number|no|details|balance|blocked|frozen)\b',
        'otp_request': r'\b(otp|pin|cvv|password|code)\b',
        'bank_impersonation': r'\b(sbi|hdfc|icici|axis|pnb|bob|canara|union|kotak)\b',
        'govt_impersonation': r'\b(income\s*tax|itr|gst|aadhaar|pan\s*card|rbi|police|court)\b',
        'urgent_threat': r'\b(block|suspend|expire|deactivate|terminate|close|freeze|lock)\w*\b',
        'prize_claim': r'\b(won|winner|congratulations|lucky|prize|reward|claim|bonus)\b',
        'payment_link': r'(http|https|www\.|click\s*here|visit)',
        'legal_threat': r'\b(legal|police|fir|arrest|jail|warrant)\b',
        'refund_bait': r'\b(refund|cashback|reversal|credited|approved|initiated|failed|pending)\b',
    }
    
    SEMANTIC_INDICATORS = [
        "verify your account", "update kyc", "link aadhaar", "confirm pan",
        "refund pending", "transaction failed", "suspicious activity detected",
        "unauthorized access", "security alert", "unusual login",
        "confirm details", "provide information", "share code",
        "immediate action required", "last warning", "final notice",
        "server error", "processing error", "verification needed"
    ]
    
    def __init__(self):
        self.detection_history = {}
    
    def pattern_analysis(self, message: str) -> Tuple[float, List[str], Optional[str]]:
        message_lower = message.lower()
        indicators = []
        score = 0.0
        impersonation = None
        
        lottery_keywords = ['congratulations', 'congrats', 'won', 'winner', 'win', 'prize', 'lottery', 'lucky draw', 'lucky', 'lakh', 'lakhs', 'crore', 'crores', 'selected', 'claim', 'kbc', 'draw']
        lottery_count = sum(1 for word in lottery_keywords if word in message_lower)
        if lottery_count >= 2:
            indicators.append(f"LOTTERY_SCAM: {lottery_count} strong indicators")
            score += min(lottery_count * 0.35, 0.90)
        
        refund_keywords = ['refund', 'cashback', 'reversal', 'credit back', 'approved', 'initiated', 'failed', 'transaction', 'processing']
        refund_count = sum(1 for word in refund_keywords if word in message_lower)
        if refund_count >= 2:
            indicators.append(f"REFUND_SCAM: {refund_count} indicators")
            score += min(refund_count * 0.35, 0.85)
        
        for pattern_name, pattern in self.CRITICAL_PATTERNS.items():
            matches = re.findall(pattern, message_lower)
            if matches:
                match_count = len(set(matches))
                indicators.append(f"CRITICAL: {pattern_name} ({match_count} matches)")
                
                if pattern_name in ['otp_request', 'account_request', 'upi_request']:
                    score += min(match_count * 0.40, 0.50)
                elif pattern_name == 'prize_claim':
                    score += min(match_count * 0.35, 0.70)
                elif pattern_name == 'refund_bait':
                    score += min(match_count * 0.40, 0.60)
                elif pattern_name in ['bank_impersonation', 'urgent_threat']:
                    score += min(match_count * 0.30, 0.45)
                else:
                    score += min(match_count * 0.25, 0.40)
        
        impersonation_keywords = [
            'sbi', 'hdfc', 'icici', 'axis', 'pnb', 'bob', 'canara', 'kotak',
            'bank', 'income tax', 'itr', 'government', 'rbi',
            'amazon', 'flipkart', 'paytm', 'phonepe'
        ]
        for keyword in impersonation_keywords:
            if keyword in message_lower:
                indicators.append(f"IMPERSONATION: {keyword}")
                impersonation = keyword
                score += 0.20
                break
        
        urgency_markers = [
            'immediate', 'urgent', 'now', 'today', 'within', 'hours',
            'limited time', 'expires', 'last chance', 'final', 'deadline',
            'hurry', 'quick', 'fast', 'pending', 'blocked', 'verify', 'update',
            'must', 'need to', 'required'
        ]
        urgency_count = sum(1 for marker in urgency_markers if marker in message_lower)
        if urgency_count > 0:
            indicators.append(f"URGENCY: {urgency_count} markers")
            score += min(urgency_count * 0.15, 0.45)
        
        url_pattern = r'https?://(?!(?:www\.)?(?:sbi|hdfc|icici|axis|incometax)\.)[^\s]+'
        suspicious_urls = re.findall(url_pattern, message_lower)
        if suspicious_urls:
            indicators.append(f"SUSPICIOUS_URLS: {len(suspicious_urls)} found")
            score += 0.30
        
        pressure_words = ['must', 'need to', 'have to', 'required', 'mandatory', 'failure to', 'cancellation']
        pressure_count = sum(1 for word in pressure_words if word in message_lower)
        if pressure_count >= 2:
            indicators.append(f"PRESSURE: {pressure_count} tactics")
            score += 0.15
        
        return min(score, 1.0), indicators, impersonation
    
    def semantic_analysis(self, message: str) -> Tuple[float, ScamCategory]:
        message_lower = message.lower()
        
        category_scores = {
            ScamCategory.BANKING: 0.0,
            ScamCategory.UPI: 0.0,
            ScamCategory.KYC: 0.0,
            ScamCategory.LOTTERY: 0.0,
            ScamCategory.TECH_SUPPORT: 0.0,
            ScamCategory.PHISHING: 0.0,
            ScamCategory.REFUND: 0.0
        }
        
        lottery_words = ['won', 'winner', 'win', 'congratulations', 'congrats', 'lottery', 'lucky draw', 'lucky', 'prize', 'lakh', 'lakhs', 'crore', 'crores', 'kbc', 'draw', 'selected', 'claim']
        lottery_count = sum(1 for word in lottery_words if word in message_lower)
        if lottery_count > 0:
            category_scores[ScamCategory.LOTTERY] += min(lottery_count * 0.30, 0.80)
        
        refund_words = ['refund', 'cashback', 'reversal', 'credit back', 'approved', 'initiated', 'failed', 'transaction failed', 'server error', 'processing error']
        refund_count = sum(1 for word in refund_words if word in message_lower)
        if refund_count > 0:
            category_scores[ScamCategory.REFUND] += min(refund_count * 0.45, 0.95)
        
        if any(word in message_lower for word in ['bank', 'account', 'atm', 'debit', 'credit', 'balance', 'blocked', 'suspended', 'freeze']):
            category_scores[ScamCategory.BANKING] += 0.45
        
        if any(word in message_lower for word in ['upi', 'phonepe', 'paytm', 'google pay', 'gpay', 'bhim']):
            category_scores[ScamCategory.UPI] += 0.50
        
        if any(word in message_lower for word in ['kyc', 'know your customer', 'pending kyc', 'update kyc']):
            category_scores[ScamCategory.KYC] += 0.40
        
        if any(word in message_lower for word in ['virus', 'malware', 'infected', 'tech support', 'microsoft', 'computer']):
            category_scores[ScamCategory.TECH_SUPPORT] += 0.50
        
        if any(word in message_lower for word in ['click', 'link', 'download', 'install', 'website', 'verify now']):
            category_scores[ScamCategory.PHISHING] += 0.35
        
        semantic_matches = sum(1 for indicator in self.SEMANTIC_INDICATORS if indicator in message_lower)
        confidence = min(semantic_matches * 0.15, 0.7)
        
        best_category = max(category_scores.items(), key=lambda x: x[1])
        
        if category_scores[ScamCategory.BANKING] > 0.3 and category_scores[ScamCategory.KYC] > 0:
            best_category = (ScamCategory.BANKING, category_scores[ScamCategory.BANKING])
        
        if best_category[1] > 0:
            return best_category[1], best_category[0]
        
        return confidence, ScamCategory.UNKNOWN
    
    def calculate_urgency(self, message: str) -> float:
        message_lower = message.lower()
        score = 0.0
        
        urgency_factors = {
            'time_pressure': ['within 24 hours', 'today', 'now', 'immediately', 'expires', 'deadline'],
            'threats': ['suspended', 'blocked', 'terminated', 'legal action', 'police', 'arrest', 'cancellation'],
            'rewards': ['won', 'selected', 'lucky', 'exclusive', 'limited', 'bonus'],
            'authority': ['bank manager', 'rbi', 'income tax', 'government', 'official']
        }
        
        for factor_type, keywords in urgency_factors.items():
            if any(kw in message_lower for kw in keywords):
                score += 0.25
        
        caps_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)
        if caps_ratio > 0.3:
            score += 0.15
        
        exclamation_count = message.count('!')
        if exclamation_count > 2:
            score += min(exclamation_count * 0.05, 0.20)
        
        return min(score, 1.0)
    
    def detect(self, message: str, history: List = None) -> DetectionResult:
        pattern_score, indicators, impersonation = self.pattern_analysis(message)
        semantic_score, category = self.semantic_analysis(message)
        
        context_score = 0.0
        if history and len(history) > 1:
            context_score = self._analyze_context(history)
        
        urgency = self.calculate_urgency(message)
        
        final_confidence = (
            pattern_score * 0.55 +
            semantic_score * 0.30 +
            context_score * 0.15
        )
        
        if pattern_score > 0.5 and semantic_score > 0.4:
            final_confidence = min(final_confidence * 1.15, 1.0)
        
        if final_confidence >= 0.65:
            is_scam = True
        elif final_confidence >= 0.50:
            is_scam = (context_score > 0.3) or (urgency > 0.6) or (pattern_score > 0.4)
        else:
            is_scam = False
        
        if final_confidence >= 0.85:
            threat_level = "critical"
        elif final_confidence >= 0.75:
            threat_level = "high"
        elif final_confidence >= 0.60:
            threat_level = "medium"
        else:
            threat_level = "low"
        
        return DetectionResult(
            is_scam=is_scam,
            confidence=round(final_confidence, 3),
            category=category,
            indicators=indicators,
            urgency_score=round(urgency, 3),
            threat_level=threat_level,
            impersonation_target=impersonation
        )
    
    def _analyze_context(self, history: List) -> float:
        if len(history) < 2:
            return 0.0
        
        recent_messages = [
            msg.text if hasattr(msg, "text") else str(msg)
            for msg in history[-3:]
        ]
        escalation_markers = 0
        
        for msg in recent_messages:
            msg_lower = msg.lower()
            if any(x in msg_lower for x in ['otp', 'password', 'pin', 'account number', 'cvv']):
                escalation_markers += 1
            if any(x in msg_lower for x in ['click', 'link', 'download', 'install']):
                escalation_markers += 0.5
        
        return min(escalation_markers * 0.25, 0.9)

class IntelligenceExtractor:
    EXTRACTION_PATTERNS = {
        'bank_accounts': [
            r'\b\d{9,18}\b',
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4,6}\b'
        ],
        'upi_ids': [
            r'\b[\w\.-]+@(?:paytm|oksbi|okicici|okaxis|okhdfcbank|okbizaxis|ybl|ibl|apl|axl)\b',
            r'\b\d{10}@[\w]+\b'
        ],
        'phone_numbers': [
            r'\+91[\s-]?\d{10}',
            r'\b[6-9]\d{9}\b'
        ],
        'urls': [
            r'https?://[^\s<>\"{}|\\^`\[\]]+'
        ],
        'ifsc_codes': [
            r'\b[A-Z]{4}0[A-Z0-9]{6}\b'
        ],
        'amounts': [
            r'(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d{2})?',
            r'\b\d{1,8}(?:\.\d{2})?\s*(?:rupees?|Rs\.?|lakhs?|crores?)\b'
        ]
    }
    
    SUSPICIOUS_KEYWORDS = [
        'urgent', 'verify', 'blocked', 'suspended', 'expire', 'update',
        'confirm', 'prize', 'won', 'lottery', 'refund', 'cashback',
        'click', 'link', 'download', 'otp', 'password', 'pin'
    ]
    
    @staticmethod
    def extract(text: str) -> Dict[str, List[str]]:
        intel = {
            'bankAccounts': [],
            'upiIds': [],
            'phishingLinks': [],
            'phoneNumbers': [],
            'suspiciousKeywords': [],
            'ifscCodes': [],
            'amounts': []
        }
        
        for account_pattern in IntelligenceExtractor.EXTRACTION_PATTERNS['bank_accounts']:
            matches = re.findall(account_pattern, text)
            intel['bankAccounts'].extend([m.replace('-', '').replace(' ', '') for m in matches])
        
        for upi_pattern in IntelligenceExtractor.EXTRACTION_PATTERNS['upi_ids']:
            matches = re.findall(upi_pattern, text, re.IGNORECASE)
            intel['upiIds'].extend(matches)
        
        for phone_pattern in IntelligenceExtractor.EXTRACTION_PATTERNS['phone_numbers']:
            matches = re.findall(phone_pattern, text)
            intel['phoneNumbers'].extend(matches)
        
        for url_pattern in IntelligenceExtractor.EXTRACTION_PATTERNS['urls']:
            matches = re.findall(url_pattern, text)
            intel['phishingLinks'].extend(matches)
        
        for ifsc_pattern in IntelligenceExtractor.EXTRACTION_PATTERNS['ifsc_codes']:
            matches = re.findall(ifsc_pattern, text)
            intel['ifscCodes'].extend(matches)
        
        for amount_pattern in IntelligenceExtractor.EXTRACTION_PATTERNS['amounts']:
            matches = re.findall(amount_pattern, text, re.IGNORECASE)
            intel['amounts'].extend(matches)
        
        text_lower = text.lower()
        intel['suspiciousKeywords'] = [kw for kw in IntelligenceExtractor.SUSPICIOUS_KEYWORDS if kw in text_lower]
        
        for key in intel:
            intel[key] = list(set(intel[key]))
        
        return intel

@dataclass
class ConversationState:
    session_id: str
    persona: Persona
    scam_category: ScamCategory
    turn_count: int = 0
    escalation_stage: int = 1
    trust_level: float = 0.3
    extracted_intel: Dict = field(default_factory=dict)
    scammer_emotion: str = "confident"
    conversation_notes: List[str] = field(default_factory=list)
    last_response: str = ""
    callback_sent: bool = False
    
    def __post_init__(self):
        if not self.extracted_intel:
            self.extracted_intel = {
                'bankAccounts': [],
                'upiIds': [],
                'phishingLinks': [],
                'phoneNumbers': [],
                'suspiciousKeywords': [],
                'ifscCodes': [],
                'amounts': []
            }

class AdvancedAgent:
    PERSONA_LEXICON = {
        "Rajeshwari": ["beta", "ji", "samajh", "bete", "confusion"],
        "Arjun Mehta": ["meeting", "email", "process", "timeline", "office"],
        "Priya Sharma": ["yaar", "mummy", "papa", "legit", "seriously"]
    }
    
    def __init__(self):
        self.model = None
        if GEMINI_API_KEY:
            try:
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                logger.info("Gemini model initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
        
        self.response_cache = {
            "Rajeshwari_1_banking_fraud": "Beta, yeh sab mujhe samajh nahi aa raha. Aap bank se ho na?",
            "Rajeshwari_2_banking_fraud": "Mere bete ko phone karna padega kya? Woh sab samajhta hai.",
            "Priya_1_lottery_scam": "Yaar seriously? Yeh legit hai na?",
            "Priya_2_lottery_scam": "Mummy papa ko batana padega kya?",
            "Arjun_1_refund_scam": "Quick batao, meeting mein hun. Email bhej do details.",
            "Arjun_2_refund_scam": "Process kya hai exactly? Short mein batao."
        }
    
    def get_cached_response(self, persona_name: str, turn: int, scam_type: str) -> Optional[str]:
        cache_key = f"{persona_name}_{turn}_{scam_type}"
        return self.response_cache.get(cache_key)
    
    def build_advanced_prompt(self, 
                            message: str, 
                            history: List,
                            state: ConversationState) -> str:
        
        anti_repeat = ""
        if state.last_response:
            anti_repeat = f"""
        CRITICAL - ANTI-REPETITION RULE:
        Your LAST response was: "{state.last_response}"
        You MUST NOT use similar words or structure.
        Generate a COMPLETELY DIFFERENT response.
        Use different Hindi words, different sentence structure.
        """

        persona = state.persona
        turn = state.turn_count
        
        conv_text = ""
        for msg in history[-5:]:
            sender = msg.sender
            text = msg.text
            conv_text += f"{sender}: {text}\n"
        conv_text += f"scammer: {message}\n"
        
        if turn <= 2:
            strategy = "Show concern and confusion. Ask basic clarifying questions."
            goal = "Establish believability"
        elif turn <= 5:
            strategy = "Express worry. Ask questions requiring specific details."
            goal = "Extract account numbers, UPI IDs, or links"
        elif turn <= 8:
            strategy = "Show willingness but need exact instructions. Express hesitation."
            goal = "Get step-by-step instructions"
        else:
            strategy = "Stall naturally with confusion or external factors."
            goal = "Maximize information extraction"
        
        variation_note = ""
        if state.last_response:
            variation_note = f"\nYour last response was: '{state.last_response[:50]}...'\nGenerate a DIFFERENT response with different wording."
        
        forbidden = {
            "Rajeshwari": ["meeting", "email", "process exactly", "yaar", "mummy papa"],
            "Arjun Mehta": ["beta", "ji", "bete", "yaar", "confused hun"],
            "Priya Sharma": ["beta", "ji", "meeting", "email"]
        }
        forbidden_note = f"\nNEVER USE: {', '.join(forbidden.get(persona.name, []))}"
        
        prompt = f"""You are {persona.name}, {persona.age} years old, {persona.occupation}.
        {anti_repeat}

BACKGROUND: {persona.backstory}

TRAITS:
- Tech: {persona.tech_savviness}/10, Gullible: {persona.gullibility}/10, Anxious: {persona.anxiety_level}/10
- Trust: {state.trust_level:.0%}, Emotion: {state.scammer_emotion}

SPEECH: {persona.language_style}

COMMON PHRASES YOU USE:
{chr(10).join(f'- "{p}"' for p in persona.common_phrases[:3])}

CONVERSATION:
{conv_text}

TURN: {turn} | STAGE: {state.escalation_stage}/5 | STRATEGY: {strategy}
GOAL: {goal}{variation_note}{forbidden_note}

INTEL EXTRACTED: Banks:{len(state.extracted_intel['bankAccounts'])} UPI:{len(state.extracted_intel['upiIds'])} Links:{len(state.extracted_intel['phishingLinks'])}

CRITICAL:
1. You are {persona.name}, a REAL person. Never break character.
2. You DON'T KNOW this is a scam. You think it might be legitimate.
3. Respond in 1-3 sentences using Hinglish.
4. Use ONLY your persona's vocabulary.
5. Ask questions to make scammer reveal details.
6. Show natural emotion based on your anxiety level.
7. VARY your responses - never repeat yourself.
8. React specifically to what scammer just said.

RESPOND AS {persona.name}:"""

        return prompt
    
    async def generate_response(self, 
                               message: str, 
                               history: List,
                               state: ConversationState) -> Tuple[str, float]:
        
        persona = state.persona
        turn = state.turn_count + 1
        
        if turn <= 2:
            cached = self.get_cached_response(persona.name, turn, state.scam_category.value)
            if cached:
                logger.info(f"CACHE HIT: {persona.name} turn {turn}")
                cleaned = self._clean_response(cached, persona)
                return cleaned, 0.85
        
        if self.model:
            for attempt in range(1):
                try:
                    prompt = self.build_advanced_prompt(message, history, state)
                    
                    response = self.model.generate_content(
                        prompt,
                        generation_config=genai.GenerationConfig(
                            temperature=0.85,
                            max_output_tokens=500,
                        ),
                        request_options={'timeout': 5}
                    )
                    
                    if response.text and len(response.text.strip()) >= 5:
                        reply = self._clean_response(response.text.strip(), persona)
                        if len(reply) >= 5:
                            believability = self._assess_believability(reply, persona)
                            logger.info(f"AI response: {reply[:50]}...")
                            return reply, believability
                    
                    logger.warning(f"Empty/short response, attempt {attempt + 1}")
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"AI error attempt {attempt + 1}: {e}")
                    await asyncio.sleep(0.5)
        
        logger.info(f"Using FALLBACK for {persona.name}")
        fallback_reply = self._persona_fallback(message, state)
        cleaned_fallback = self._clean_response(fallback_reply, persona)
        return cleaned_fallback, 0.6
    
    def _clean_response(self, reply: str, persona: Persona) -> str:
        original = reply
        reply_lower = reply.lower()

        if persona.name == "Rajeshwari":
            forbidden = ['yaar', 'meeting', 'email', 'process exactly', 'client', 'office', 'dude', 'bro']
            for word in forbidden:
                if word in reply_lower:
                    reply = reply.replace(word, "beta")
        
        elif persona.name == "Arjun Mehta":
            forbidden = ['beta', 'ji', 'bete', 'yaar', 'mummy', 'papa', 'confused hun']
            for word in forbidden:
                if word in reply_lower:
                    reply = reply.replace(word, "")
        
        elif persona.name == "Priya Sharma":
            forbidden = ['beta', 'ji', 'bete', 'meeting', 'email', 'process exactly', 'sir', 'madam']
            for word in forbidden:
                if word in reply_lower:
                    reply = reply.replace(word, "yaar")
        
        ai_tells = ["as an ai", "cannot verify", "apologize", "language model"]
        for tell in ai_tells:
            if tell in reply.lower():
                return self.get_cached_response(persona.name, 1, "banking_fraud") or reply

        reply = reply.strip()
        if reply.endswith("..") or not reply[-1] in ".!?":
            reply += "."

        if persona.name == "Rajeshwari":
            if not (reply.startswith("Beta") or reply.startswith("Ji")):
                reply = f"Beta, {reply[0].lower() if reply else ''}{reply[1:]}"
        
        elif persona.name == "Arjun Mehta":
            markers = ['meeting', 'email', 'process']
            if not any(m in reply.lower() for m in markers):
                reply = f"Meeting mein hun. {reply}"
        
        elif persona.name == "Priya Sharma":
            if not reply.startswith("Yaar"):
                reply = f"Yaar, {reply[0].lower() if reply else ''}{reply[1:]}"
            
            reply = reply.replace("samajh", "clear")
            reply = reply.replace("Samajh", "Clear")

        lex = self.PERSONA_LEXICON.get(persona.name, [])

        if lex and random.random() < 0.35:
            if not any(word in reply.lower() for word in lex):
                reply = f"{lex[0]}, {reply}"


        if persona.name == "Priya Sharma":
            reply = reply.replace("samajh", "clear")
            reply = reply.replace("confused", "thoda lost")
        elif persona.name == "Rajeshwari":
            reply = reply.replace("yaar", "beta")
        elif persona.name == "Arjun Mehta":
            reply = reply.replace("yaar", "")

        return reply
    
    def _assess_believability(self, reply: str, persona: Persona) -> float:
        score = 0.5
        
        if any(p.lower() in reply.lower() for p in persona.common_phrases):
            score += 0.2
        
        if any(w in reply.lower() for w in ['umm', 'uh', 'hmm', 'aa']):
            score += 0.1
        
        if '?' in reply:
            score += 0.15
        
        hindi = ['beta', 'ji', 'kya', 'hai', 'mein', 'aap', 'yaar', 'nahi']
        if any(w in reply.lower() for w in hindi):
            score += 0.15
        
        if reply.count('.') > 3 and '...' not in reply:
            score -= 0.1
        if len(reply) < 10:
            score -= 0.2
        
        return min(max(score, 0), 1)
    
    def _persona_fallback(self, message: str, state: ConversationState) -> str:
        persona = state.persona
        turn = state.turn_count
        msg_lower = message.lower()
        
        if not hasattr(state, 'used_responses'):
            state.used_responses = set()
        
        def pick_unique(responses):
            available = [r for r in responses if r not in state.used_responses]
            
            if not available:
                state.used_responses.clear()
                available = responses
            
            selected = random.choice(available)
            state.used_responses.add(selected)
            return selected
        
        if persona.name == "Rajeshwari":
            responses = {
                'early': [
                    "Beta, yeh sab mujhe samajh nahi aa raha. Aap bank se ho na?",
                    "Main thoda confused hun... mera account block ho jayega?",
                    "Mere bete ko phone kar lun kya? Woh sab samajhta hai",
                    "Yeh sab mujhe confusion mein daal raha hai beta",
                    "Aap ka naam kya hai? Aur aap kahan se call kar rahe ho?",
                    "Pehle kabhi aisa nahi hua beta, kya ho gaya?"
                ],
                'link': [
                    "Link... matlab? Main kaise kholun?",
                    "Yeh link ke baare mein mujhe samajh nahi aa raha",
                    "Beta, main phone pe hun, link kaise dekhu?",
                    "Mujhe yeh link wala system nahi aata"
                ],
                'payment': [
                    "Payment? Mujhe kisko paise bhejne hain?",
                    "Yeh payment ka kya chakkar hai beta?",
                    "Kitna paise aur kahan bhejun?",
                    "Mujhe samajh nahi aa raha ki payment kyun?"
                ],
                'otp': [
                    "OTP kya hota hai beta?",
                    "Mujhe password share karna padega kya?",
                    "Yeh code ka matlab kya hai?",
                    "Mujhe yeh OTP wala system nahi samajhta"
                ],
                'default': [
                    "Aage kya karna hai? Exact steps bataiye",
                    "Thoda detail mein samjhaiye beta",
                    "Mujhe yeh samajh nahi aa raha, phir se bataiye",
                    "Dheere dheere samjhaiye, jaldi mat kariye"
                ],
                'late': [
                    "Mujhe thoda time chahiye sochne ke liye beta",
                    "Ek minute, mere bete ko phone kar lun?",
                    "Abhi main ghar pe nahi hun, baad mein baat karte hain",
                    "Mera network weak hai, call drop ho rahi hai"
                ]
            }
            
            if turn <= 2:
                return pick_unique(responses['early'])
            elif any(w in msg_lower for w in ['link', 'click', 'url']):
                return pick_unique(responses['link'])
            elif any(w in msg_lower for w in ['payment', 'pay', 'amount', 'paisa']):
                return pick_unique(responses['payment'])
            elif any(w in msg_lower for w in ['otp', 'password', 'pin', 'code']):
                return pick_unique(responses['otp'])
            elif turn >= 8:
                return pick_unique(responses['late'])
            else:
                return pick_unique(responses['default'])
        
        elif persona.name == "Arjun Mehta":
            responses = {
                'early': [
                    "Quick batao, meeting se bahar aaya hun. Kya issue hai?",
                    "Email mein bhej do details, abhi call pe time nahi hai.",
                    "Process kya hai exactly? Short mein batao.",
                    "Yeh urgent hai? Main office se hun.",
                    "Tumhari company ka naam kya hai? Verify kar lun.",
                    "Jaldi summarize karo, next meeting hai."
                ],
                'link': [
                    "Link safe hai? SSL verified hai na?",
                    "Main laptop pe dekhunga, abhi phone pe verify nahi kar sakta.",
                    "Yeh link tumhari official website ka hai?",
                    "Link ko main IT team se verify karwa lunga."
                ],
                'payment': [
                    "Payment ke liye proper invoice chahiye.",
                    "Kitna amount hai? Aur kis account mein bhejun?",
                    "Yeh payment authorized hai? Reference number do.",
                    "Finance team se approve karwa ke batao."
                ],
                'otp': [
                    "OTP share karna against company policy hai.",
                    "Main IT team ko forward kar dunga yeh request.",
                    "Aise sensitive info phone pe nahi dete.",
                    "Security team ne mana kiya hai OTP share karne ko."
                ],
                'default': [
                    "Timeline kya hai? EOD tak chahiye kya?",
                    "Exact steps batao, main busy hun.",
                    "Aur kya documentation chahiye?",
                    "Speed up karo, time nahi hai.",
                    "Main client call pe hun, whatsapp karo details."
                ],
                'late': [
                    "Main abhi client call pe hun, baad mein karte hain.",
                    "Network issue aa raha hai, email mein bhej do.",
                    "Another urgent call aa rahi hai, kal baat karte hain.",
                    "Flight mein board kar raha hun, baad mein."
                ]
            }
            
            if turn <= 2:
                return pick_unique(responses['early'])
            elif any(w in msg_lower for w in ['link', 'click', 'url']):
                return pick_unique(responses['link'])
            elif any(w in msg_lower for w in ['payment', 'pay', 'amount']):
                return pick_unique(responses['payment'])
            elif any(w in msg_lower for w in ['otp', 'password', 'pin', 'code']):
                return pick_unique(responses['otp'])
            elif turn >= 8:
                return pick_unique(responses['late'])
            else:
                return pick_unique(responses['default'])
        
        else:
            responses = {
                'early': [
                    "Arre seriously? Mujhe clear nahi ho raha...",
                    "Yeh real hai na? Mummy papa ko batana padega kya?",
                    "Mere dost ko bhi same message aaya tha...",
                    "Yaar mujhe thoda explain karo properly",
                    "Seriously yaar? Thoda detail mein batao",
                    "Kya baat kar rahe ho? Sach mein?"
                ],
                'link': [
                    "Yeh link safe hai na yaar?",
                    "Link pe click karne se koi problem toh nahi?",
                    "Mujhe link dikhai nahi de raha properly",
                    "Yeh link kaunsa hai? Trusted hai na?"
                ],
                'payment': [
                    "Payment kyun yaar? Confused hun",
                    "Kitna paise aur kisko?",
                    "Yeh legit hai na? Payment safe hai?",
                    "Mere paas utna balance nahi hai yaar",
                    "UPI se bhejun kya? Safe hai na?"
                ],
                'otp': [
                    "OTP share karna chahiye kya?",
                    "Yeh code kya hai? Bank ka hai?",
                    "Mummy ne bola tha password mat share karo",
                    "OTP dalne se account safe rahega na?"
                ],
                'default': [
                    "Yaar thoda explain karo detail mein",
                    "Main confused hun, kya karna hai exactly?",
                    "Steps batao properly please",
                    "Clear nahi ho raha, repeat karo",
                    "Ek baar aur simple words mein batao"
                ],
                'late': [
                    "Yaar abhi class hai, baad mein karte hain",
                    "Mummy papa ko confirm kar lun pehle?",
                    "Thoda time do sochne ke liye",
                    "Abhi exam chal raha hai, kal baat karein?"
                ]
            }
            
            if turn <= 2:
                return pick_unique(responses['early'])
            elif any(w in msg_lower for w in ['link', 'click', 'url']):
                return pick_unique(responses['link'])
            elif any(w in msg_lower for w in ['payment', 'pay', 'amount', 'paisa']):
                return pick_unique(responses['payment'])
            elif any(w in msg_lower for w in ['otp', 'password', 'pin', 'code']):
                return pick_unique(responses['otp'])
            elif turn >= 8:
                return pick_unique(responses['late'])
            else:
                return pick_unique(responses['default'])
        
    def should_end_conversation(self, state: ConversationState) -> bool:
        intel = state.extracted_intel
        turn = state.turn_count
        
        has_critical = (
            len(intel['bankAccounts']) >= 1 or
            len(intel['upiIds']) >= 1 or
            (len(intel['phishingLinks']) >= 2 and len(intel['phoneNumbers']) >= 1)
        )
        
        sufficient_length = turn >= 12
        good_progress = turn >= 8 and (len(intel['phoneNumbers']) >= 1 or len(intel['phishingLinks']) >= 1)
        
        return has_critical or sufficient_length or good_progress
    
    def update_state(self, state: ConversationState, scammer_msg: str, agent_reply: str):
        state.turn_count += 1
        state.last_response = agent_reply
        
        msg_lower = scammer_msg.lower()
        if any(w in msg_lower for w in ['wait', 'listen', 'understand']):
            state.scammer_emotion = "frustrated"
        elif any(w in msg_lower for w in ['good', 'perfect', 'excellent']):
            state.scammer_emotion = "confident"
        elif any(w in msg_lower for w in ['hurry', 'quick', 'now']):
            state.scammer_emotion = "urgent"
        
        if '?' in agent_reply:
            state.trust_level = min(state.trust_level + 0.05, 1.0)
        
        total = sum(len(v) for v in state.extracted_intel.values() if isinstance(v, list))
        state.escalation_stage = min(1 + (total // 2), 5)
        
        state.conversation_notes.append(
            f"T{state.turn_count}: {state.scammer_emotion}, trust={state.trust_level:.2f}"
        )

        if state.extracted_intel['upiIds']:
            state.escalation_stage = max(state.escalation_stage, 3)

        if state.extracted_intel['bankAccounts']:
            state.escalation_stage = max(state.escalation_stage, 4)

session_store: Dict[str, ConversationState] = {}
detector = AdvancedDetector()
extractor = IntelligenceExtractor()
agent = AdvancedAgent()

class Message(BaseModel):
    sender: str
    text: str
    timestamp: int

class Metadata(BaseModel):
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"

class IncomingRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = Field(default_factory=list)
    metadata: Optional[Metadata] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ULTIMATE Agentic Honey-Pot v3.0 FINAL Starting...")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="ULTIMATE Agentic Honey-Pot API",
    description="Advanced AI honeypot with personas and multi-layer detection",
    version="3.0.0-FINAL",
    lifespan=lifespan
)

async def send_final_callback(session_id: str, state: ConversationState):
    if state.callback_sent:
        logger.info(f"Callback already sent for {session_id}")
        return True
    
    payload = {
        "sessionId": session_id,
        "scamDetected": state.detection_confidence >= 0.6,
        "detection": {
            "confidence": state.detection_confidence,
            "category": state.scam_category.value,
            "threatLevel": state.threat_level
        },
        "totalMessagesExchanged": state.turn_count,
        "extractedIntelligence": {
            "bankAccounts": state.extracted_intel.get('bankAccounts', []),
            "upiIds": state.extracted_intel.get('upiIds', []),
            "phishingLinks": state.extracted_intel.get('phishingLinks', []),
            "phoneNumbers": state.extracted_intel.get('phoneNumbers', []),
            "suspiciousKeywords": state.extracted_intel.get('suspiciousKeywords', [])
        },
        "agentNotes": f"Persona:{state.persona.name}|Cat:{state.scam_category.value}|"
                      f"Esc:{state.escalation_stage}/5|Trust:{state.trust_level:.0%}|"
                      f"Emotion:{state.scammer_emotion}"
    }
    
    logger.info(f"CALLBACK for {session_id}: {json.dumps(payload, indent=2)}")
    
    for attempt in range(3):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    CALLBACK_URL, 
                    json=payload, 
                    timeout=15.0,
                    headers={"Content-Type": "application/json"}
                )
                
                if resp.status_code == 200:
                    logger.info(f"CALLBACK SUCCESS: {session_id}")
                    state.callback_sent = True
                    return True
                else:
                    logger.error(f"CALLBACK FAILED: {resp.status_code} - {resp.text}")
                    
        except Exception as e:
            logger.error(f"CALLBACK ERROR (attempt {attempt+1}): {e}")
            await asyncio.sleep(2 ** attempt)
    
    logger.critical(f"ALL CALLBACK RETRIES FAILED: {session_id}")
    return False

@app.post("/api/honeypot")
async def honeypot_endpoint(
    request: IncomingRequest,
    x_api_key: str = Header(..., alias="x-api-key")
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    session_id = request.sessionId
    incoming = request.message.text
    history = request.conversationHistory
    
    logger.info(f"Incoming {session_id}: Turn {len(history)+1}")
    
    if session_id in session_store:
        state = session_store[session_id]
        logger.info(f"Continuing: {state.persona.name}, turn {state.turn_count}")
    else:
        detection = detector.detect(incoming, [])
        logger.info(f"Detection: scam={detection.is_scam}, conf={detection.confidence}, cat={detection.category.value}")
        
        if not detection.is_scam:
            logger.info(f"Not scam (confidence {detection.confidence})")
            return JSONResponse(content={"status": "success", "reply": "I'm sorry, could you please explain?"})
        
        persona = PersonaSelector.select(detection.category)
        state = ConversationState(
            session_id=session_id,
            persona=persona,
            scam_category=detection.category
        )
        state.detection_confidence = detection.confidence
        state.threat_level = detection.threat_level

        session_store[session_id] = state
        logger.info(f"NEW: {persona.name} for {detection.category.value}")
    
    new_intel = extractor.extract(incoming)
    if any(new_intel.values()):
        logger.info(f"Intel: { {k:v for k,v in new_intel.items() if v} }")
    
    for key in state.extracted_intel:
        if key in new_intel:
            state.extracted_intel[key].extend(new_intel[key])
            state.extracted_intel[key] = list(set(state.extracted_intel[key]))
    
    reply, believability = await agent.generate_response(incoming, history, state)
    
    agent.update_state(state, incoming, reply)
    session_store[session_id] = state
    
    logger.info(f"{state.persona.name} (T{state.turn_count}, B={believability:.2f}): {reply[:60]}...")
    
    if agent.should_end_conversation(state):
        logger.info(f"ENDING: {session_id}")
        await send_final_callback(session_id, state)
    
    return JSONResponse(content={"status": "success", "reply": reply})

@app.get("/")
async def root():
    return {
        "service": "ULTIMATE Agentic Honey-Pot API v3.0 FINAL",
        "status": "active",
        "features": ["Multi-layer detection", "3 Personas", "Advanced extraction"],
        "endpoints": ["/api/honeypot", "/health", "/admin/metrics"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "gemini_configured": GEMINI_API_KEY != "",
        "active_sessions": len(session_store),
        "personas_loaded": 3
    }

@app.get("/admin/metrics")
async def get_metrics(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401)
    
    if not session_store:
        return {"status": "no_data"}
    
    return {
        "total_sessions": len(session_store),
        "active": sum(1 for s in session_store.values() if not s.callback_sent),
        "completed": sum(1 for s in session_store.values() if s.callback_sent),
        "avg_turns": round(sum(s.turn_count for s in session_store.values()) / len(session_store), 1),
        "intel": {
            "bank_accounts": sum(len(s.extracted_intel.get('bankAccounts', [])) for s in session_store.values()),
            "upi_ids": sum(len(s.extracted_intel.get('upiIds', [])) for s in session_store.values()),
            "phones": sum(len(s.extracted_intel.get('phoneNumbers', [])) for s in session_store.values()),
            "links": sum(len(s.extracted_intel.get('phishingLinks', [])) for s in session_store.values())
        },
        "personas": {
            "Rajeshwari": sum(1 for s in session_store.values() if s.persona.name == "Rajeshwari"),
            "Arjun": sum(1 for s in session_store.values() if s.persona.name == "Arjun Mehta"),
            "Priya": sum(1 for s in session_store.values() if s.persona.name == "Priya Sharma")
        }
    }

@app.get("/admin/explain/{session_id}")
async def explain_session(session_id: str, x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401)

    state = session_store.get(session_id)
    if not state:
        return {"error": "Session not found"}

    return {
        "persona": state.persona.name,
        "category": state.scam_category.value,
        "turns": state.turn_count,
        "escalation_stage": state.escalation_stage,
        "trust_level": state.trust_level,
        "extracted_intel": state.extracted_intel,
        "notes": state.conversation_notes
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)