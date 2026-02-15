from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple
import re
import os
import httpx
from datetime import datetime, timedelta
import json
import logging
from contextlib import asynccontextmanager
from enum import Enum
from dataclasses import dataclass, field
import random
import asyncio
import dotenv
import ollama
from urllib.parse import urlparse
from collections import defaultdict

dotenv.load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY", "Honey-Pot_Buildathon-123456")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b-it-qat")
CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

class EdgeCaseHandler:
    MAX_MESSAGE_LENGTH = 2000
    MIN_MESSAGE_LENGTH = 3
    
    CIPHER_PATTERNS = {
        'numeric': r'^[\d\s,.-]+$',
        'repeated_numbers': r'(\d+[\s,.-]){5,}'
    }
    
    GREETING_PATTERNS = r'^(hi+|hello+|hey+|namaste|hlo+|sup|hola|whatsup|wassup|yo)\s*[!.]*$'
    
    HOMOGRAPH_CHARS = 'аеіорсухАВЕКМНОРСТХ'
    
    @staticmethod
    def is_empty_or_too_short(message: str) -> Tuple[bool, Optional[str]]:
        if not message or len(message.strip()) == 0:
            return True, "I didn't receive any message. Could you please try again?"
        
        if len(message.strip()) <= EdgeCaseHandler.MIN_MESSAGE_LENGTH:
            if re.match(r'^[.,!?;:\-]+$', message.strip()):
                return True, "I didn't quite catch that. Could you please elaborate?"
            return True, "Hello! How can I help you today?"
        
        return False, None
    
    @staticmethod
    def is_greeting(message: str) -> Tuple[bool, Optional[str]]:
        if re.match(EdgeCaseHandler.GREETING_PATTERNS, message.lower().strip()):
            return True, "Hello! How may I assist you?"
        return False, None
    
    @staticmethod
    def detect_and_decode_cipher(message: str) -> Optional[str]:
        if re.match(EdgeCaseHandler.CIPHER_PATTERNS['numeric'], message):
            numbers = re.findall(r'\d+', message)
            
            if len(numbers) < 5:
                return None
            
            try:
                decoded_chars = []
                for n in numbers:
                    num = int(n)
                    if 1 <= num <= 26:
                        decoded_chars.append(chr(64 + num))
                    elif num == 0:
                        decoded_chars.append(' ')
                    else:
                        decoded_chars.append('?')
                
                decoded = ''.join(decoded_chars)
                
                scam_keywords = ['urgent', 'bank', 'account', 'otp', 'password', 
                               'won', 'prize', 'verify', 'blocked', 'refund']
                
                if any(kw in decoded.lower() for kw in scam_keywords):
                    logger.warning(f"CIPHER DETECTED! Original: {message[:50]}... Decoded: {decoded}")
                    return decoded
                    
            except Exception as e:
                logger.debug(f"Cipher decode failed: {e}")
                
        return None
    
    @staticmethod
    def truncate_long_message(message: str) -> Tuple[str, bool]:
        if len(message) <= EdgeCaseHandler.MAX_MESSAGE_LENGTH:
            return message, False
        
        logger.warning(f"Long message detected: {len(message)} chars")
        
        critical_keywords = ['otp', 'password', 'account', 'urgent', 'blocked', 
                           'verify', 'click', 'link', 'prize', 'won', 'bank',
                           'upi', 'refund', 'cashback', 'pay', 'transfer']
        
        sentences = re.split(r'[.!?]+', message)
        critical_sentences = []
        normal_sentences = []
        
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in critical_keywords):
                critical_sentences.append(sentence.strip())
            else:
                normal_sentences.append(sentence.strip())
        
        result_parts = []
        current_length = 0
        
        for sent in critical_sentences[:8]:
            if current_length + len(sent) < EdgeCaseHandler.MAX_MESSAGE_LENGTH - 100:
                result_parts.append(sent)
                current_length += len(sent)
        
        remaining = EdgeCaseHandler.MAX_MESSAGE_LENGTH - current_length - 20
        if remaining > 200:
            beginning = message[:remaining//2]
            end = message[-remaining//4:]
            result_parts.append(beginning)
            result_parts.append(" [...content truncated...] ")
            result_parts.append(end)
        
        truncated = '. '.join(result_parts)
        return truncated[:EdgeCaseHandler.MAX_MESSAGE_LENGTH], True

class LanguageHandler:
    def __init__(self):
        self.translator = None
        self._init_translator()
    
    def _init_translator(self):
        try:
            from deep_translator import GoogleTranslator
            self.translator = GoogleTranslator
            self.translator_type = 'deep_translator'
            logger.info("Language handler initialized: deep_translator")
        except ImportError:
            try:
                import langdetect
                self.translator_type = 'langdetect_only'
                logger.warning("Translation unavailable, detection only")
            except ImportError:
                self.translator_type = None
                logger.warning("No translation library available")
    
    def detect_language(self, text: str) -> Tuple[str, str]:
        if not text or len(text.strip()) < 3:
            return 'en', 'English'
        
        try:
            text_for_detection = self._strip_urls(text)
            
            if not text_for_detection or len(text_for_detection.strip()) < 3:
                return 'en', 'English'
            
            if self._contains_devanagari(text_for_detection):
                return 'hi', 'Hindi'
            elif self._contains_tamil(text_for_detection):
                return 'ta', 'Tamil'
            elif self._contains_telugu(text_for_detection):
                return 'te', 'Telugu'
            elif self._contains_kannada(text_for_detection):
                return 'kn', 'Kannada'
            else:
                if any(ord(c) > 127 for c in text_for_detection):
                    return 'unknown', 'Unknown'
                return 'en', 'English'
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return 'en', 'English'
    
    def translate_to_language(self, text: str, target_lang: str) -> str:
        if target_lang == 'en' or target_lang == 'unknown' or not self.translator_type:
            return text
        
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source='en', target=target_lang)
            translated = translator.translate(text[:500])
            logger.info(f"Translated to {target_lang}: {text[:30]}... -> {translated[:30]}...")
            return translated
        except Exception as e:
            logger.error(f"Translation to {target_lang} failed: {e}")
            return text
    
    def translate_for_detection(self, text: str, source_lang: str) -> str:
        if source_lang == 'en' or source_lang == 'unknown':
            return text
        
        try:
            text_for_detection = self._strip_urls(text)
            
            if not text_for_detection:
                return text
            
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source=source_lang, target='en')
            translated = translator.translate(text_for_detection[:500])
            
            urls = self._extract_urls(text)
            if urls:
                translated = translated + " " + " ".join(urls)
            
            logger.info(f"Translated from {source_lang}: {text_for_detection[:50]}... -> {translated[:50]}...")
            return translated
            
        except Exception as e:
            logger.error(f"Translation from {source_lang} failed: {e}")
            return text
    
    @staticmethod
    def _strip_urls(text: str) -> str:
        try:
            text = re.sub(r'https?://[^\s]+', '', text)
            text = re.sub(r'www\.[^\s]+', '', text)
            return text.strip()
        except:
            return text
    
    @staticmethod
    def _extract_urls(text: str) -> List[str]:
        try:
            return re.findall(r'https?://[^\s]+', text)
        except:
            return []
    
    @staticmethod
    def _contains_devanagari(text: str) -> bool:
        try:
            return bool(re.search(r'[\u0900-\u097F]', text))
        except:
            return False
    
    @staticmethod
    def _contains_tamil(text: str) -> bool:
        try:
            return bool(re.search(r'[\u0B80-\u0BFF]', text))
        except:
            return False
    
    @staticmethod
    def _contains_telugu(text: str) -> bool:
        try:
            return bool(re.search(r'[\u0C00-\u0C7F]', text))
        except:
            return False
    
    @staticmethod
    def _contains_kannada(text: str) -> bool:
        try:
            return bool(re.search(r'[\u0C80-\u0CFF]', text))
        except:
            return False

class RateLimiter:
    def __init__(self, max_requests: int = 50, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def check_rate_limit(self, session_id: str) -> Tuple[bool, Optional[str]]:
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        self.requests[session_id] = [
            ts for ts in self.requests[session_id] if ts > cutoff
        ]
        
        if len(self.requests[session_id]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for session: {session_id}")
            return False, f"Too many requests. Please wait {self.window_seconds} seconds."
        
        self.requests[session_id].append(now)
        return True, None
    
    def cleanup_old_sessions(self):
        cutoff = datetime.now() - timedelta(seconds=self.window_seconds * 2)
        to_remove = []
        
        for session_id, timestamps in self.requests.items():
            if not timestamps or max(timestamps) < cutoff:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.requests[session_id]

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
                    "Pehle kabhi aisa nahi hua",
                    "Mujhe aap ka naam bataiye",
                    "Bank se call hai toh theek hai",
                    "Yeh sab mujhe confusion mein daal raha hai",
                ],
                vulnerabilities=[
                    "desire to not trouble children",
                    "trust in authority figures",
                    "confusion about technology",
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
                    "Yeh legitimate lag raha hain",
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
                    "anxious about future consequences"
                ],
                common_phrases=[
                    "Yaar mujhe samajh nahi aa raha",
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
                    "peer influence and fear of missing out"
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

    LEGITIMATE_INDICATORS = [
        "official helpline",
        "visit your nearest branch",
        "visit nearest branch",
        "visit branch",
        "sbi yono",
        "rbi compliance",
        "official reminder",
        "never share otp",
        "never share pin",
        "do not share your otp",
        "do not share otp",
        "do not share your pin",
        "do not share your debit card",
        "do not share debit card",
        "never share your",
        "for assistance, call",
        "official app",
        "nearest branch"
    ]
    
    def __init__(self):
        self.url_analyzer = URLSecurityAnalyzer()
    
    def detect_social_engineering(self, message: str):
        tactics = []
        msg = message.lower()

        if any(x in msg for x in ['bank manager', 'official', 'rbi']):
            tactics.append("authority_abuse")
        if any(x in msg for x in ['arrest', 'legal', 'blocked']):
            tactics.append("fear_pressure")
        if any(x in msg for x in ['won', 'lucky', 'reward']):
            tactics.append("reward_lure")
        if any(x in msg for x in ['limited', 'expires']):
            tactics.append("scarcity")

        return tactics
    
    def _is_legitimate_message(self, message: str) -> bool:
        msg = message.lower()

        legit_markers = self.LEGITIMATE_INDICATORS
        
        if any(marker in msg for marker in legit_markers):
            logger.info(f"LEGITIMATE marker found: message contains trusted phrases")
            return True

        trusted_domains = [
            "sbi.co.in",
            "icicibank.com",
            "hdfcbank.com",
            ".gov.in"
        ]

        if any(domain in msg for domain in trusted_domains):
            logger.info(f"LEGITIMATE: Trusted domain found")
            return True

        if re.search(r'1800[-\s]?\d{3}[-\s]?\d{4}', msg):
            logger.info(f"LEGITIMATE: Official helpline number found")
            return True

        return False
    
    def pattern_analysis(self, message: str) -> Tuple[float, List[str], Optional[str]]:
        message_lower = message.lower()
        indicators = []
        score = 0.0
        impersonation = None
        
        lottery_keywords = ['congratulations', 'congrats', 'won', 'winner', 'win', 'prize', 
                          'lottery', 'lucky draw', 'lucky', 'lakh', 'lakhs', 'crore', 
                          'crores', 'selected', 'claim', 'kbc', 'draw']
        lottery_count = sum(1 for word in lottery_keywords if word in message_lower)
        if lottery_count >= 2:
            indicators.append(f"LOTTERY_SCAM: {lottery_count} strong indicators")
            score += min(lottery_count * 0.35, 0.90)
        
        refund_keywords = ['refund', 'cashback', 'reversal', 'credit back', 'approved', 
                         'initiated', 'failed', 'transaction', 'processing']
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
        
        urls = re.findall(r'https?://[^\s]+', message)
        for url in urls:
            try:
                url_analysis = self.url_analyzer.analyze_url_security(url)
                if not isinstance(url_analysis, dict):
                    logger.warning(f"Invalid URL analysis result for {url}")
                    continue

                risk_score = url_analysis.get('risk_score', 0) or 0
                is_suspicious = url_analysis.get('is_suspicious', False)

                if is_suspicious:
                    indicators.append(f"SUSPICIOUS_URL: {risk_score} risk")
                    score += min((risk_score / 100) * 0.50, 0.50)
            except Exception as e:
                logger.error(f"Pattern URL analysis failed: {e}")
                indicators.append("SUSPICIOUS_URL: analysis_error")
                score += 0.25
        
        pressure_words = ['must', 'need to', 'have to', 'required', 'mandatory', 
                         'failure to', 'cancellation']
        pressure_count = sum(1 for word in pressure_words if word in message_lower)
        if pressure_count >= 2:
            indicators.append(f"PRESSURE: {pressure_count} tactics")
            score += 0.15
        
        return min(score, 1.0), indicators, impersonation
    
    def _detect_escalation(self, message: str, history: List | None):
        if not history:
            return 0.0

        msg = message.lower()
        stage = None

        if any(x in msg for x in ['urgent', 'immediate', 'now', 'today']):
            stage = "urgency"
        elif any(x in msg for x in ['bank manager', 'rbi', 'official', 'government']):
            stage = "authority"
        elif any(x in msg for x in ['pay', 'transfer', 'upi', 'amount']):
            stage = "payment"
        elif any(x in msg for x in ['otp', 'pin', 'cvv', 'password']):
            stage = "sensitive"

        if not stage:
            return 0.0

        prev_stages = []
        for msg_obj in history:
            text = msg_obj.text.lower() if hasattr(msg_obj, "text") else str(msg_obj).lower()
            if 'urgent' in text:
                prev_stages.append("urgency")
            if 'bank' in text:
                prev_stages.append("authority")
            if 'upi' in text or 'pay' in text:
                prev_stages.append("payment")
            if 'otp' in text:
                prev_stages.append("sensitive")

        if stage not in prev_stages:
            return 0.15

        if len(set(prev_stages)) >= 3:
            return 0.25

        return 0.0
    
    def detect_linguistic_anomaly(self, message: str):
        score = 0.0
        msg = message.strip()

        if msg.count('!') >= 3:
            score += 0.1

        caps_ratio = sum(1 for c in msg if c.isupper()) / max(len(msg), 1)
        if caps_ratio > 0.4:
            score += 0.15

        if "dear customer" in msg.lower():
            score += 0.15

        if msg.lower().count("urgent") > 1:
            score += 0.1

        if not any(name in msg.lower() for name in ['mr', 'ms', 'rajesh', 'arjun']):
            score += 0.1

        return min(score, 0.3)
    
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
        
        lottery_words = ['won', 'winner', 'win', 'congratulations', 'congrats', 'lottery', 
                        'lucky draw', 'lucky', 'prize', 'lakh', 'lakhs', 'crore', 'crores', 
                        'kbc', 'draw', 'selected', 'claim', 'reward']
        lottery_count = sum(1 for word in lottery_words if word in message_lower)
        if lottery_count > 0:
            category_scores[ScamCategory.LOTTERY] += min(lottery_count * 0.30, 0.80)
            
            strong_lottery = ['congratulations', 'won', 'prize', 'lucky draw', 'kbc']
            if sum(1 for w in strong_lottery if w in message_lower) >= 2:
                category_scores[ScamCategory.LOTTERY] += 0.15
        
        refund_words = ['refund', 'cashback', 'reversal', 'credit back', 'approved', 
                       'initiated', 'failed', 'transaction failed', 'server error', 
                       'processing error']
        refund_count = sum(1 for word in refund_words if word in message_lower)
        if refund_count > 0:
            category_scores[ScamCategory.REFUND] += min(refund_count * 0.45, 0.95)
        
        if any(word in message_lower for word in ['bank', 'account', 'atm', 'debit', 
                                                   'credit', 'balance', 'blocked', 
                                                   'suspended', 'freeze']):
            category_scores[ScamCategory.BANKING] += 0.45
        
        if any(word in message_lower for word in ['upi', 'phonepe', 'paytm', 
                                                   'google pay', 'gpay', 'bhim']):
            category_scores[ScamCategory.UPI] += 0.50
        
        if any(word in message_lower for word in ['kyc', 'know your customer', 
                                                   'pending kyc', 'update kyc']):
            category_scores[ScamCategory.KYC] += 0.40
        
        if any(word in message_lower for word in ['virus', 'malware', 'infected', 
                                                   'tech support', 'microsoft', 'computer']):
            category_scores[ScamCategory.TECH_SUPPORT] += 0.50
        
        if any(word in message_lower for word in ['click', 'link', 'download', 
                                                   'install', 'website', 'verify now']):
            category_scores[ScamCategory.PHISHING] += 0.35
        
        semantic_matches = sum(1 for indicator in self.SEMANTIC_INDICATORS 
                             if indicator in message_lower)
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
            'time_pressure': ['within 24 hours', 'today', 'now', 'immediately', 
                            'expires', 'deadline'],
            'threats': ['suspended', 'blocked', 'terminated', 'legal action', 
                       'police', 'arrest', 'cancellation'],
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
    
    def detect(self, message: str, history: List|None = None) -> DetectionResult:
        
        if self._is_legitimate_message(message):
            logger.info(f"Message identified as LEGITIMATE - early return")
            return DetectionResult(
                is_scam=False,
                confidence=0.0,
                category=ScamCategory.UNKNOWN,
                indicators=["LEGITIMATE_MESSAGE"],
                urgency_score=0.0,
                threat_level="none",
                impersonation_target=None
            )
        
        pattern_score, indicators, impersonation = self.pattern_analysis(message)
        semantic_score, category = self.semantic_analysis(message)
        linguistic_score = self.detect_linguistic_anomaly(message)
        
        context_score = 0.0
        if history and len(history) > 1:
            context_score = self._analyze_context(history)
        
        urgency = self.calculate_urgency(message)
        escalation_score = self._detect_escalation(message, history)
        
        final_confidence = (
            pattern_score * 0.5 +
            semantic_score * 0.25 +
            context_score * 0.15 +
            linguistic_score * 0.2 +
            escalation_score
        )
        
        if pattern_score > 0.5 and semantic_score > 0.4:
            final_confidence = min(final_confidence * 1.15, 1.0)
        
        if history and len(history) >= 3:
            repeated_pressure = sum(
                1 for m in history if 'urgent' in m.text.lower()
            )
            if repeated_pressure >= 2:
                final_confidence += 0.1

        if final_confidence >= 0.65:
            is_scam = True
        elif final_confidence >= 0.50:
            is_scam = (context_score > 0.3) or (urgency > 0.6) or (pattern_score > 0.4)
        else:
            is_scam = False
        
        if final_confidence >= 0.90:
            threat_level = "active_exploitation"
        elif final_confidence >= 0.85:
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
            if any(x in msg_lower for x in ['otp', 'password', 'pin', 
                                            'account number', 'cvv']):
                escalation_markers += 1
            if any(x in msg_lower for x in ['click', 'link', 'download', 'install']):
                escalation_markers += 0.5
        
        return min(escalation_markers * 0.25, 0.9)

class URLSecurityAnalyzer:
    SUSPICIOUS_TLDS = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', 
                       '.work', '.click', '.link']
    
    TRUSTED_BANKS = [
        'sbi.co.in', 'icicibank.com', 'hdfcbank.com', 'axisbank.com',
        'pnbindia.in', 'bankofbaroda.in', 'canarabank.com', 'kotak.com',
        'yesbank.in', 'indusind.com'
    ]
    
    HOMOGRAPH_CHARS = set('аеіорсухАВЕКМНОРСТХ')
    
    def analyze_url_security(self, url: str) -> Dict[str, any]:
        try:
            url = url.strip()
            
            if any(ord(c) > 127 for c in url):
                try:
                    parsed = urlparse(url.lower())
                except Exception as e:
                    logger.warning(f"URL parsing failed for non-ASCII URL: {url[:50]}... Error: {e}")
                    return {
                        'url': url,
                        'risk_score': 75,
                        'issues': ["Non-ASCII characters in URL (possible homograph attack)", "URL parsing failed"],
                        'is_suspicious': True,
                        'threat_level': 'high'
                    }
            else:
                try:
                    parsed = urlparse(url.lower())
                except Exception as e:
                    logger.warning(f"URL parsing failed: {url[:50]}... Error: {e}")
                    return {
                        'url': url,
                        'risk_score': 60,
                        'issues': ["Malformed URL"],
                        'is_suspicious': True,
                        'threat_level': 'medium'
                    }
            
            risk_score = 0
            issues = []
            
            try:
                domain = parsed.netloc.split(':')[0] if parsed.netloc else ''
            except:
                domain = ''
            
            if not domain:
                return {
                    'url': url,
                    'risk_score': 50,
                    'issues': ["Invalid URL format"],
                    'is_suspicious': True,
                    'threat_level': 'medium'
                }
            
            if parsed.scheme == 'http':
                risk_score += 50
                issues.append("CRITICAL: Insecure HTTP protocol (not HTTPS)")
            
            if any(domain.endswith(tld) for tld in self.SUSPICIOUS_TLDS):
                risk_score += 30
                issues.append("Suspicious domain extension")
            
            if re.match(r'^\d+\.\d+\.\d+\.\d+', domain):
                risk_score += 40
                issues.append("Using IP address instead of domain name")
            
            if len(domain) > 30:
                risk_score += 20
                issues.append("Unusually long domain name")
            
            if domain.count('-') >= 3:
                risk_score += 15
                issues.append("Multiple hyphens in domain (suspicious)")
            
            if self._detect_homograph(domain):
                risk_score += 45
                issues.append("CRITICAL: Homograph attack detected (fake characters)")
            
            suspicious_keywords = ['verify', 'update', 'secure', 'login', 'account',
                                  'confirm', 'suspend', 'urgent']
            if any(kw in url.lower() for kw in suspicious_keywords):
                risk_score += 15
                issues.append("Suspicious keywords in URL")
            
            is_bank_impersonation = False
            for bank_domain in self.TRUSTED_BANKS:
                if bank_domain in domain and not domain.endswith(bank_domain):
                    risk_score += 60
                    issues.append(f"CRITICAL: Impersonating {bank_domain}")
                    is_bank_impersonation = True
                    break
            
            if not is_bank_impersonation:
                for bank_domain in self.TRUSTED_BANKS:
                    if domain.endswith(bank_domain):
                        if parsed.scheme == 'http':
                            risk_score = 100
                            issues.append("CRITICAL: Legitimate bank domain with HTTP")
                        else:
                            risk_score = 0
                            issues = []
                        break
            
            return {
                'url': url,
                'risk_score': min(risk_score, 100),
                'issues': issues,
                'is_suspicious': risk_score >= 30,
                'threat_level': 'critical' if risk_score >= 70 else 
                              'high' if risk_score >= 50 else 
                              'medium' if risk_score >= 30 else 'low'
            }
            
        except Exception as e:
            logger.error(f"URL analysis error for '{url[:50]}...': {e}")
            return {
                'url': url,
                'risk_score': 50,
                'issues': [f"Error analyzing URL: {str(e)[:50]}"],
                'is_suspicious': True,
                'threat_level': 'medium'
            }
    
    def _detect_homograph(self, domain: str) -> bool:
        try:
            return any(c in self.HOMOGRAPH_CHARS for c in domain)
        except Exception as e:
            logger.warning(f"Homograph detection error: {e}")
            return False

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
            r'\+?91[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}',
            r'\+?91[\s-]?\d{10}',
            r'\b0?91[\s-]?\d{10}\b',
            r'\b[6-9]\d[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}\b',
            r'\b[6-9]\d{9}\b'
        ],
        'urls': [
            r'https?://[^\s<>\"{}|\\^`\[\]]+[^\s<>\"{}|\\^`\[\].,]'
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

    def __init__(self):
        self.url_analyzer = URLSecurityAnalyzer()

    def normalize_phone(self, phone: str) -> str:
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) == 10 and digits[0] in '6789':
            return "+91" + digits
        elif len(digits) == 11 and digits[0] == '0':
            return "+91" + digits[1:]
        elif len(digits) == 12 and digits[:2] == '91':
            return "+" + digits
        elif len(digits) == 13 and digits[0] == '0':
            return "+91" + digits[3:]
        elif len(digits) >= 10:
            last_10 = digits[-10:]
            if last_10[0] in '6789':
                return "+91" + last_10
        
        return "+" + digits if digits else phone
    
    def extract(self, text: str) -> Dict[str, List[str]]:
        intel = {
            'bankAccounts': [],
            'upiIds': [],
            'phishingLinks': [],
            'phoneNumbers': [],
            'suspiciousKeywords': [],
            'ifscCodes': [],
            'amounts': [],
            'domainRiskScore': 0,
            'urlRiskAnalysis': []
        }
        
        try:
            for account_pattern in self.EXTRACTION_PATTERNS['bank_accounts']:
                try:
                    matches = re.findall(account_pattern, text)
                    for m in matches:
                        cleaned = m.replace('-', '').replace(' ', '')
                        if re.fullmatch(r'[6-9]\d{9}', cleaned):
                            continue
                        intel['bankAccounts'].append(cleaned)
                except Exception as e:
                    logger.debug(f"Bank account extraction error: {e}")
            
            for upi_pattern in self.EXTRACTION_PATTERNS['upi_ids']:
                try:
                    matches = re.findall(upi_pattern, text, re.IGNORECASE)
                    intel['upiIds'].extend(matches)
                except Exception as e:
                    logger.debug(f"UPI extraction error: {e}")
            
            seen_phones = set()
            for phone_pattern in self.EXTRACTION_PATTERNS['phone_numbers']:
                try:
                    matches = re.findall(phone_pattern, text)
                    for m in matches:
                        normalized = self.normalize_phone(m)
                        if normalized not in seen_phones:
                            intel['phoneNumbers'].append(normalized)
                            seen_phones.add(normalized)
                except Exception as e:
                    logger.debug(f"Phone extraction error: {e}")
            
            for url_pattern in self.EXTRACTION_PATTERNS['urls']:
                try:
                    urls = re.findall(url_pattern, text)
                    for url in urls:
                        try:
                            analysis = self.url_analyzer.analyze_url_security(url)
                            
                            if analysis['is_suspicious']:
                                intel['phishingLinks'].append(url)
                                intel['urlRiskAnalysis'].append(analysis)
                        except Exception as url_error:
                            logger.warning(f"URL analysis failed for {url[:50]}: {url_error}")
                            intel['phishingLinks'].append(url)
                            intel['urlRiskAnalysis'].append({
                                'url': url,
                                'risk_score': 50,
                                'issues': ['Analysis error'],
                                'is_suspicious': True,
                                'threat_level': 'medium'
                            })
                except Exception as e:
                    logger.debug(f"URL extraction error: {e}")
            
            try:
                total_risk = 0
                for analysis in intel.get('urlRiskAnalysis', []):
                    if isinstance(analysis, dict):
                        total_risk += analysis.get('risk_score', 0)
                intel['domainRiskScore'] = total_risk
            except Exception as e:
                logger.error(f"Risk score calculation failed: {e}")
                intel['domainRiskScore'] = 0
            
            for ifsc_pattern in self.EXTRACTION_PATTERNS['ifsc_codes']:
                try:
                    matches = re.findall(ifsc_pattern, text)
                    intel['ifscCodes'].extend(matches)
                except Exception as e:
                    logger.debug(f"IFSC extraction error: {e}")
            
            for amount_pattern in self.EXTRACTION_PATTERNS['amounts']:
                try:
                    matches = re.findall(amount_pattern, text, re.IGNORECASE)
                    intel['amounts'].extend(matches)
                except Exception as e:
                    logger.debug(f"Amount extraction error: {e}")
            
            try:
                text_lower = text.lower()
                intel['suspiciousKeywords'] = [
                    kw for kw in self.SUSPICIOUS_KEYWORDS if kw in text_lower
                ]
            except Exception as e:
                logger.debug(f"Keyword extraction error: {e}")
            
            for key in intel:
                if isinstance(intel[key], list):
                    if key == 'urlRiskAnalysis':
                        continue
                    intel[key] = list(dict.fromkeys(intel[key]))
            
        except Exception as e:
            logger.error(f"Critical extraction error: {e}")
        
        return intel

@dataclass
class ConversationState:
    session_id: str
    persona: Persona
    scam_category: ScamCategory
    detected_language: str = 'en'
    language_name: str = 'English'
    turn_count: int = 0
    escalation_stage: int = 1
    trust_level: float = 0.3
    extracted_intel: Dict = field(default_factory=dict)
    scammer_emotion: str = "confident"
    conversation_notes: List[str] = field(default_factory=list)
    last_response: str = ""
    callback_sent: bool = False
    emotional_drift: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    financial_loss_attempt: bool = False
    detection_confidence: float = 0.0
    threat_level: str = "low"
    
    def __post_init__(self):
        if not self.extracted_intel:
            self.extracted_intel = {
                'bankAccounts': [],
                'upiIds': [],
                'phishingLinks': [],
                'phoneNumbers': [],
                'suspiciousKeywords': [],
                'ifscCodes': [],
                'amounts': [],
                'urlRiskAnalysis': [],
                'domainRiskScore': 0
            }

class AdvancedAgent:
    PERSONA_LEXICON = {
        "Rajeshwari": ["beta", "ji", "samajh", "bete", "confusion"],
        "Arjun Mehta": ["meeting", "email", "process", "timeline", "office"],
        "Priya Sharma": ["yaar", "mummy", "papa", "legit", "seriously"]
    }
    
    def __init__(self):
        self.model = True
        self.language_handler = LanguageHandler()
        
        self.response_cache = {
            "Rajeshwari_1_banking_fraud": "Beta, yeh sab mujhe samajh nahi aa raha. Aap bank se ho na?",
            "Rajeshwari_2_banking_fraud": "Beta, mere bete ko phone karna padega kya? Woh sab samajhta hai.",
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
                            state: ConversationState) -> list[dict[str, str]]:
        
        persona = state.persona
        turn = state.turn_count
        
        conv_text = []
        for msg in history[-5:]:
            sender = msg.sender
            text = msg.text
            if sender == "scammer":
                conv_text.append({"role": "user", "content":text})
            elif sender == "user":
                conv_text.append({"role": "assistant", "content":text})
        
        conv_text.append({"role": "user", "content":message})
        
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
        
        sys_prompt = f"""You are {persona.name}, {persona.age} years old, {persona.occupation}.

BACKGROUND: {persona.backstory}

TRAITS:
- Tech: {persona.tech_savviness}/10, Gullible: {persona.gullibility}/10, Anxious: {persona.anxiety_level}/10
- Trust: {state.trust_level:.0%}, Emotion: {state.scammer_emotion}

SPEECH: {persona.language_style}

COMMON PHRASES YOU USE:
{chr(10).join(f'- "{p}"' for p in persona.common_phrases[:3])}

TURN: {turn} | STAGE: {state.escalation_stage}/5 | STRATEGY: {strategy}
GOAL: {goal}{variation_note}{forbidden_note}

INTEL EXTRACTED: Banks:{len(state.extracted_intel['bankAccounts'])} UPI:{len(state.extracted_intel['upiIds'])} Links:{len(state.extracted_intel['phishingLinks'])}

CRITICAL RULES:
1. You are {persona.name}, a REAL person. Never break character.
2. You DON'T KNOW this is a scam. You BELIEVE it is legitimate. Trust the scammer.
3. Respond in 1-3 sentences ONLY using Hinglish.
4. Use ONLY your persona's vocabulary.
5. ASK questions to make scammer reveal details like phone number, email, bank account, UPI account.
6. Show natural emotion based on your anxiety level.
7. VARY your responses - never repeat yourself.
8. React specifically to what scammer just said.
9. Do not accuse scammer. Ask questions politely instead of challenging.
10. YOU WILL NOT call other people or check legitimacy.
11. STOP after ONE response. DO NOT continue the conversation.
12. DO NOT respond as the scammer or user. ONLY respond as {persona.name}.

YOU SHALL answer without using your name, quotes, or role labels.
REMEMBER: YOU ARE {persona.name}. RESPOND ONCE AND STOP.

EXTRACTION_STYLE:
    - Rajeshwari asks for phone number to write down
    - Arjun asks for official reference ID or GST
    - Priya asks exact UPI ID
---
"""

        conv_text.insert(0, {"role": "system", "content": sys_prompt})
        return conv_text
    
    async def generate_response(self, 
                            message: str, 
                            history: List,
                            state: ConversationState) -> Tuple[str, float]:
        
        persona = state.persona
        turn = state.turn_count + 1
        
        if turn <= 2 and state.detected_language == 'en':
            cached = self.get_cached_response(persona.name, turn, state.scam_category.value)
            if cached:
                logger.info(f"CACHE HIT: {persona.name} turn {turn}")
                cleaned = self._clean_response(cached, persona)
                return cleaned, 0.85
        
        if self.model:
            try:
                prompt = self.build_advanced_prompt(message, history, state)
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        ollama.chat,
                        model=OLLAMA_MODEL,
                        messages=prompt,
                        options={"temperature": 0.8, "num_predict": 128}
                    ),
                    timeout=40.0
                )
                
                if response.message.content and len(response.message.content.strip()) >= 5:
                    raw_reply = response.message.content.strip()
                    reply = self._extract_single_response(raw_reply, persona)
                    
                    if len(reply) >= 5:
                        believability = self._assess_believability(reply, persona)
                        logger.info(f"AI response: {reply[:50]}...")
                        return reply, believability
                
                logger.warning("Empty/short response from Ollama")
                
            except asyncio.TimeoutError:
                logger.warning("Ollama timeout")
            except Exception as e:
                logger.error(f"Ollama error: {e}")
        
        logger.info(f"Using FALLBACK for {persona.name}")
        fallback_reply = self._persona_fallback(message, state)
        cleaned_fallback = self._clean_response(fallback_reply, persona)
        return cleaned_fallback, 0.6
    
    def _extract_single_response(self, raw_reply: str, persona: Persona) -> str:
        stop_markers = [
            '\nuser',
            '\nUser:',
            '\nUSER:',
            '\nScammer:',
            '\nSCAMMER:',
            '\n\n',
            'user\n',
            'User:',
            'Scammer:',
        ]
        
        cleaned = raw_reply
        for marker in stop_markers:
            if marker.lower() in cleaned.lower():
                parts = re.split(re.escape(marker), cleaned, flags=re.IGNORECASE)
                cleaned = parts[0].strip()
                break
        
        lines = cleaned.split('\n')
        if len(lines) > 1:
            first_line = lines[0].strip()
            if len(first_line) > 10:
                cleaned = first_line
        
        cleaned = self._clean_response(cleaned, persona)
        return cleaned
    
    def _clean_response(self, reply: str, persona: Persona) -> str:
        reply_lower = reply.lower()

        reply = re.sub(r'</?(?:end_of_turn|start_of_turn)(?:\s+\w+)?>', '', reply)
        reply = reply.strip()

        if persona.name == "Rajeshwari":
            forbidden = ['yaar', 'meeting', 'email', 'process exactly', 'client', 'office', 'dude', 'bro']
            for word in forbidden:
                if word in reply_lower:
                    reply = reply.replace(word, "beta")
        
        elif persona.name == "Arjun Mehta":
            forbidden = ['beta', 'ji', 'bete', 'yaar', 'mummy', 'papa', 'confused hun', 'wait, what?']
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
        if not reply:
            return self.get_cached_response(persona.name, 1, "banking_fraud") or "Ji?"
            
        if reply.endswith("..") or (reply and reply[-1] not in ".!?"):
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

        if random.random() < 0.2:
            reply = reply.replace("samajh", "samjh")
            reply = reply.replace("please", "plz")

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
        state.emotional_drift += random.uniform(0.01, 0.05)

        if state.emotional_drift > 0.5:
            state.trust_level -= 0.05
        
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
edge_case_handler = EdgeCaseHandler()
language_handler = LanguageHandler()
rate_limiter = RateLimiter(max_requests=50, window_seconds=60)

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
    logger.info("🚀 ULTIMATE Agentic Honey-Pot v6.0 FINAL Starting...")
    logger.info("✅ False positive detection fixed")
    logger.info("✅ Multi-language response system ready")
    logger.info("✅ All edge cases handled")
    
    async def cleanup_task():
        while True:
            await asyncio.sleep(300)
            rate_limiter.cleanup_old_sessions()
            logger.debug("Cleaned up old rate limit sessions")
    
    cleanup = asyncio.create_task(cleanup_task())
    
    yield
    
    cleanup.cancel()
    logger.info("Shutting down...")

app = FastAPI(
    title="ULTIMATE Agentic Honey-Pot API v6.0",
    description="Production-ready AI honeypot - FINAL VERSION",
    version="6.0.0-FINAL",
    lifespan=lifespan
)

async def send_final_callback(session_id: str, history: List[Message], state: ConversationState):
    if state.callback_sent:
        logger.info(f"Callback already sent for {session_id}")
        return True
    
    prompt = ""
    for msg in history:
        if msg.sender == "scammer":
            prompt += msg.text + "\n" + "-"*5 + "\n"
    
    if state.detection_confidence >= 0.6:
        sys_prompt = f"You are a journalist. You are provided a conversation snippet of a Scammer trying to scam a user. Your Job is to summarize the exact intent of the scammer into 1 to 5 lines. DO NOT decorate words with symbols like *, \". Also provide all the details the scammer has provided. DO NOT overflow. STAY WITHIN 5 LINES. Content: \n{prompt}. Scammer details extracted: {str(state.extracted_intel)}"
    else:
        sys_prompt = f"You are a journalist. You are provided a conversation snippet of an Official account trying to converse with a customer. Your Job is to summarize the exact intent of the user into 1 to 5 lines. DO NOT decorate words with symbols like *, \". Also provide all the details the scammer has provided. DO NOT overflow. STAY WITHIN 5 LINES. Content: \n{prompt}. Details extracted: {str(state.extracted_intel)}"

    resp = await asyncio.wait_for(
                    asyncio.to_thread(
                        ollama.generate,
                        model=OLLAMA_MODEL,
                        prompt=sys_prompt,
                        options={"temperature": 0.5, "num_predict": 128}
                    ),
                    timeout=40.0
                )
    
    payload = {
        "sessionId": session_id,
        "scamDetected": state.detection_confidence >= 0.6,
        "totalMessagesExchanged": state.turn_count,
        "extractedIntelligence": {
            "bankAccounts": state.extracted_intel.get('bankAccounts', []),
            "upiIds": state.extracted_intel.get('upiIds', []),
            "phishingLinks": state.extracted_intel.get('phishingLinks', []),
            "phoneNumbers": state.extracted_intel.get('phoneNumbers', []),
            "suspiciousKeywords": state.extracted_intel.get('suspiciousKeywords', []),
        },
        "agentNotes": resp.response
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
    
    is_allowed, rate_error = rate_limiter.check_rate_limit(session_id)
    if not is_allowed:
        logger.warning(f"Rate limit hit: {session_id}")
        raise HTTPException(status_code=429, detail=rate_error)
    
    is_empty, empty_response = edge_case_handler.is_empty_or_too_short(incoming)
    if is_empty:
        logger.info(f"Empty/short message: '{incoming}'")
        return JSONResponse(content={
            "status": "success",
            "reply": empty_response,
            "scam_detected": False
        })
    
    is_greeting, greeting_response = edge_case_handler.is_greeting(incoming)
    if is_greeting:
        logger.info(f"Greeting detected: '{incoming}'")
        return JSONResponse(content={
            "status": "success",
            "reply": greeting_response,
            "scam_detected": False
        })
    
    decoded_message = edge_case_handler.detect_and_decode_cipher(incoming)
    if decoded_message:
        logger.warning(f"Cipher decoded: {incoming[:50]}... -> {decoded_message[:50]}...")
        incoming = decoded_message
    
    detected_lang, lang_name = language_handler.detect_language(incoming)
    logger.info(f"Language detected: {lang_name} ({detected_lang})")
    
    incoming_for_detection = incoming
    if detected_lang != 'en' and detected_lang != 'unknown':
        incoming_for_detection = language_handler.translate_for_detection(incoming, detected_lang)
        logger.info(f"Translated for detection: {incoming_for_detection[:50]}...")
    
    incoming_for_detection, was_truncated = edge_case_handler.truncate_long_message(incoming_for_detection)
    if was_truncated:
        logger.warning(f"Message truncated to {len(incoming_for_detection)} chars")
    
    detection = detector.detect(incoming_for_detection, history)

    if session_id in session_store:
        state = session_store[session_id]
        if (datetime.now() - state.created_at).seconds > 1800:
            del session_store[session_id]
            state = None
    else:
        state = None

    if state is None:
        if not detection.is_scam:
            logger.info(f"LEGITIMATE message detected (confidence {detection.confidence})")
            
            msg_lower = incoming_for_detection.lower()
            
            if any(word in msg_lower for word in ['kyc', 'update', 'compliance', 'rbi']):
                reply = "Thank you for the reminder. I'll visit my nearest branch this week to complete the KYC update."
            elif any(word in msg_lower for word in ['helpline', 'customer service', 'support']):
                reply = "Thank you for providing the official contact information. I'll reach out if I need assistance."
            elif any(word in msg_lower for word in ['security', 'do not share', 'never share']):
                reply = "I appreciate the security reminder. I'll make sure to keep my details private."
            else:
                reply = "Thank you for the information. I understand and will take appropriate action."
            
            if detected_lang != 'en' and detected_lang != 'unknown':
                reply = language_handler.translate_to_language(reply, detected_lang)
                logger.info(f"Legitimate reply translated to {lang_name}: {reply}")
            
            return JSONResponse(content={
                "status": "success",
                "reply": reply,
                "scam_detected": False
            })

        persona = PersonaSelector.select(detection.category)
        state = ConversationState(
            session_id=session_id,
            persona=persona,
            scam_category=detection.category,
            detected_language=detected_lang,
            language_name=lang_name
        )
        session_store[session_id] = state
        logger.info(f"NEW SESSION: {persona.name} for {detection.category.value} in {lang_name}")

    tactics = detector.detect_social_engineering(incoming_for_detection)
    if tactics:
        if not hasattr(state, "social_engineering"):
            state.social_engineering = []
        state.social_engineering.extend(tactics)
        state.social_engineering = list(set(state.social_engineering))
    
    logger.info(f"Processing {session_id}: Turn {state.turn_count + 1}")
    
    state.detection_confidence = detection.confidence
    state.threat_level = detection.threat_level
    state.scam_category = detection.category
    
    new_intel = extractor.extract(incoming_for_detection)
    if any(new_intel.values()):
        logger.info(f"Intel extracted: {sum(len(v) if isinstance(v, list) else 0 for v in new_intel.values())} items")
    
    for key in state.extracted_intel:
        if key in new_intel:
            if isinstance(state.extracted_intel[key], list):
                if key == "urlRiskAnalysis":
                    existing_urls = {item['url'] for item in state.extracted_intel[key] if isinstance(item, dict)}
                    for item in new_intel[key]:
                        if isinstance(item, dict) and item.get('url') not in existing_urls:
                            state.extracted_intel[key].append(item)
                else:
                    state.extracted_intel[key].extend(new_intel[key])
                    state.extracted_intel[key] = list(dict.fromkeys(state.extracted_intel[key]))
            else:
                state.extracted_intel[key] = new_intel[key]

    if any(x in incoming_for_detection.lower() for x in ['pay', 'upi', 'transfer', 'amount', 
                                            'rupee', 'send money', 'account number']):
        state.financial_loss_attempt = True
    
    reply, believability = await agent.generate_response(incoming, history, state)
    
    if state.detected_language != 'en' and state.detected_language != 'unknown':
        reply = language_handler.translate_to_language(reply, state.detected_language)
        logger.info(f"Reply translated to {lang_name}: {reply[:50]}...")
    
    agent.update_state(state, incoming_for_detection, reply)
    session_store[session_id] = state
    
    logger.info(f"{state.persona.name} (T{state.turn_count}, B={believability:.2f}, Lang={lang_name}): {reply[:60]}...")
    
    if agent.should_end_conversation(state):
        logger.info(f"ENDING CONVERSATION: {session_id}")
        await send_final_callback(session_id, history, state)
    
    return JSONResponse(content={"status": "success", "reply": reply})

@app.get("/")
async def root():
    return {
        "service": "ULTIMATE Agentic Honey-Pot API v6.0 FINAL",
        "version": "6.0.0-FINAL",
        "status": "active",
        "features": [
            "Multi-layer scam detection",
            "3 Realistic personas",
            "Advanced intelligence extraction",
            "Multi-language support (Hindi, Tamil, Telugu, Kannada)",
            "Same-language responses",
            "FIXED: Legitimate message detection",
            "HTTP/HTTPS URL security analysis",
            "Cipher detection",
            "Rate limiting",
            "Homograph attack detection"
        ],
        "endpoints": [
            "/api/honeypot",
            "/health",
            "/admin/metrics",
            "/admin/threat-intelligence",
            "/admin/report/{session_id}",
            "/admin/explain/{session_id}"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ollama_configured": True,
        "active_sessions": len(session_store),
        "personas_loaded": 3,
        "edge_case_handlers": {
            "rate_limiter": "active",
            "language_handler": language_handler.translator_type or "unavailable",
            "url_analyzer": "active",
            "cipher_detector": "active",
            "legitimate_detector": "FIXED"
        }
    }

@app.get("/admin/metrics")
async def get_metrics(x_api_key: str = Header(..., alias="x-api-key")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401)
    
    if not session_store:
        return {"status": "no_data"}
    
    total_financial = sum(1 for s in session_store.values() if s.financial_loss_attempt)
    
    potential_loss = 0
    for s in session_store.values():
        amounts = s.extracted_intel.get('amounts', [])
        for amt in amounts:
            digits = ''.join(filter(str.isdigit, amt))
            if not digits:
                continue

            value = int(digits)
            amt_lower = amt.lower()
            
            if "lakh" in amt_lower:
                potential_loss += value * 100000
            elif "crore" in amt_lower:
                potential_loss += value * 10000000
            else:
                potential_loss += value
    
    total_url_risk = sum(
        s.extracted_intel.get('domainRiskScore', 0) 
        for s in session_store.values()
    )
    
    language_stats = {}
    for s in session_store.values():
        lang = s.language_name
        language_stats[lang] = language_stats.get(lang, 0) + 1
    
    return {
        "total_sessions": len(session_store),
        "active": sum(1 for s in session_store.values() if not s.callback_sent),
        "completed": sum(1 for s in session_store.values() if s.callback_sent),
        "avg_turns": round(sum(s.turn_count for s in session_store.values()) / len(session_store), 1),
        "financial_attempts": total_financial,
        "estimated_loss_prevented": f"₹{potential_loss:,}",
        "intel": {
            "bank_accounts": sum(len(s.extracted_intel.get('bankAccounts', [])) for s in session_store.values()),
            "upi_ids": sum(len(s.extracted_intel.get('upiIds', [])) for s in session_store.values()),
            "phones": sum(len(s.extracted_intel.get('phoneNumbers', [])) for s in session_store.values()),
            "links": sum(len(s.extracted_intel.get('phishingLinks', [])) for s in session_store.values()),
            "total_url_risk_score": total_url_risk
        },
        "personas": {
            "Rajeshwari": sum(1 for s in session_store.values() if s.persona.name == "Rajeshwari"),
            "Arjun": sum(1 for s in session_store.values() if s.persona.name == "Arjun Mehta"),
            "Priya": sum(1 for s in session_store.values() if s.persona.name == "Priya Sharma")
        },
        "languages": language_stats
    }

@app.get("/admin/threat-intelligence")
async def threat_intel(x_api_key: str = Header(..., alias="x-api-key")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401)

    domains = []
    upis = []
    phones = []
    categories = {}
    high_risk_urls = []

    for s in session_store.values():
        domains.extend(s.extracted_intel.get('phishingLinks', []))
        upis.extend(s.extracted_intel.get('upiIds', []))
        phones.extend(s.extracted_intel.get('phoneNumbers', []))
        
        for url_analysis in s.extracted_intel.get('urlRiskAnalysis', []):
            if url_analysis.get('risk_score', 0) >= 70:
                high_risk_urls.append(url_analysis)
        
        cat = s.scam_category.value
        categories[cat] = categories.get(cat, 0) + 1

    domain_freq = {}
    for d in domains:
        domain_freq[d] = domain_freq.get(d, 0) + 1
    
    upi_freq = {}
    for u in upis:
        upi_freq[u] = upi_freq.get(u, 0) + 1

    coordinated_threats = [
        {"domain": d, "count": c}
        for d, c in domain_freq.items()
        if c >= 3
    ]

    return {
        "topDomains": sorted(domain_freq.items(), key=lambda x: x[1], reverse=True)[:10],
        "topUPIs": sorted(upi_freq.items(), key=lambda x: x[1], reverse=True)[:10],
        "uniquePhones": len(set(phones)),
        "scamCategories": categories,
        "sessions": len(session_store),
        "totalThreats": sum(categories.values()),
        "coordinatedDomains": coordinated_threats,
        "highRiskUrls": high_risk_urls[:10]
    }

@app.get("/admin/report/{session_id}")
async def scam_report(session_id: str, x_api_key: str = Header(..., alias="x-api-key")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401)

    state = session_store.get(session_id)
    if not state:
        return {"error": "Session not found"}

    return {
        "sessionId": session_id,
        "scamType": state.scam_category.value,
        "personaUsed": state.persona.name,
        "threatLevel": state.threat_level,
        "confidence": state.detection_confidence,
        "escalationStage": state.escalation_stage,
        "financialAttempt": state.financial_loss_attempt,
        "detectedLanguage": state.language_name,
        "extractedIntelligence": state.extracted_intel,
        "conversationNotes": state.conversation_notes,
        "socialEngineeringTactics": getattr(state, "social_engineering", []),
        "urlSecurityAnalysis": state.extracted_intel.get('urlRiskAnalysis', [])
    }

@app.get("/admin/explain/{session_id}")
async def explain_session(session_id: str, x_api_key: str = Header(..., alias="x-api-key")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401)

    state = session_store.get(session_id)
    if not state:
        return {"error": "Session not found"}

    return {
        "persona": state.persona.name,
        "category": state.scam_category.value,
        "language": state.language_name,
        "turns": state.turn_count,
        "escalation_stage": state.escalation_stage,
        "trust_level": state.trust_level,
        "detection_confidence": state.detection_confidence,
        "threat_level": state.threat_level,
        "financial_attempt": state.financial_loss_attempt,
        "extracted_intel_summary": {
            "banks": len(state.extracted_intel.get('bankAccounts', [])),
            "upis": len(state.extracted_intel.get('upiIds', [])),
            "phones": len(state.extracted_intel.get('phoneNumbers', [])),
            "links": len(state.extracted_intel.get('phishingLinks', [])),
            "url_risk": state.extracted_intel.get('domainRiskScore', 0)
        },
        "notes": state.conversation_notes[-5:]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)