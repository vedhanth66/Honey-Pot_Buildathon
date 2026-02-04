"""
ULTIMATE Agentic Honey-Pot System - Hybrid Best-of-Both
Combines: Advanced personas + Multi-layer detection + FREE Gemini AI + Production-grade
DESIGNED TO WIN 1ST PLACE
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
from dataclasses import dataclass, asdict
import random
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv("API_KEY", "your-secret-api-key-12345")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ============================================================================
# ENHANCED ENUMS AND DATA MODELS
# ============================================================================

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

# ============================================================================
# ADVANCED PERSONA SYSTEM (From Previous Plan)
# ============================================================================

@dataclass
class Persona:
    """Sophisticated persona with psychological profile"""
    name: str
    age: int
    occupation: str
    tech_savviness: int  # 1-10
    gullibility: int     # 1-10
    anxiety_level: int   # 1-10
    speech_patterns: List[str]
    common_phrases: List[str]
    vulnerabilities: List[str]
    backstory: str
    language_style: str
    
    # Dynamic state
    emotional_state: str = "neutral"
    trust_level: float = 0.5
    confusion_count: int = 0

class PersonaLibrary:
    """Library of believable personas optimized for Indian scams"""
    
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
                    "Bank se call hai toh theek hai"
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
                    "Process kya hai exactly?"
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
                    "Mere dost ko bhi same message aaya tha"
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
    """Select optimal persona based on scam type"""
    
    CATEGORY_MAPPING = {
        ScamCategory.BANKING: PersonaType.ELDERLY,
        ScamCategory.UPI: PersonaType.YOUTH,
        ScamCategory.KYC: PersonaType.PROFESSIONAL,
        ScamCategory.LOTTERY: PersonaType.YOUTH,
        ScamCategory.TECH_SUPPORT: PersonaType.ELDERLY,
        ScamCategory.PHISHING: PersonaType.PROFESSIONAL,
        ScamCategory.REFUND: PersonaType.PROFESSIONAL,
        ScamCategory.UNKNOWN: PersonaType.YOUTH
    }
    
    @staticmethod
    def select(category: ScamCategory) -> Persona:
        """Select persona optimized for scam category"""
        personas = PersonaLibrary.get_personas()
        persona_type = PersonaSelector.CATEGORY_MAPPING.get(
            category, 
            PersonaType.YOUTH
        )
        return personas[persona_type]

# ============================================================================
# MULTI-LAYER DETECTION ENGINE (Enhanced from Previous Plan)
# ============================================================================

@dataclass
class DetectionResult:
    """Comprehensive detection result"""
    is_scam: bool
    confidence: float
    category: ScamCategory
    indicators: List[str]
    urgency_score: float
    threat_level: str  # low, medium, high, critical
    impersonation_target: Optional[str] = None

class AdvancedDetector:
    """Multi-layered detection with pattern + semantic + behavioral analysis"""
    
    # Critical patterns - Immediate high confidence (RELAXED for better detection)
    CRITICAL_PATTERNS = {
        'upi_request': r'(?i)\b(upi|phone\s*pe|google\s*pay|paytm|gpay)',
        'account_request': r'(?i)\b(account|acc)\s*(?:no\.?|number)?',
        'otp_request': r'(?i)\b(otp|one[\s-]?time|verification\s*code|pin|cvv|password)',
        'bank_mention': r'(?i)\b(sbi|hdfc|icici|axis|pnb|bob|canara|union|kotak|bank)',
        'govt_impersonation': r'(?i)\b(income\s*tax|itr|gst|aadhaar|pan|rbi|reserve\s*bank|government)',
        'urgent_threat': r'(?i)\b(block|suspend|expire|deactivate|terminate|close|freeze|locked)',
        'prize_claim': r'(?i)\b(won|winner|win|congratulations?|congrats|selected|lucky|prize|reward|claim|lakhs?|crores?|rs\.?\s*\d+|₹\s*\d+|kbc|lottery|draw)',
        'payment_link': r'(?i)\b(click|tap|visit|open|link|http)',
        'legal_threat': r'(?i)\b(legal|police|fir|arrest|court|summons|warrant|case|action)',
        'refund_bait': r'(?i)\b(refund|cashback|reversal|approved|initiated)',
    }
    
    # Semantic indicators for context
    SEMANTIC_INDICATORS = [
        "verify your account", "update kyc", "link aadhaar", "confirm pan",
        "refund pending", "transaction failed", "suspicious activity detected",
        "unauthorized access", "security alert", "unusual login",
        "confirm details", "provide information", "share code",
        "immediate action required", "last warning", "final notice"
    ]
    
    # Impersonation targets
    IMPERSONATION_TARGETS = {
        'banks': ["sbi", "hdfc", "icici", "axis", "pnb", "bob", "canara", "union", "kotak"],
        'govt': ["income tax", "itr", "gst", "aadhaar", "rbi", "income tax department"],
        'companies': ["amazon", "flipkart", "paytm", "phonepe", "google pay", "swiggy", "zomato"],
        'services': ["customer care", "technical support", "help desk"]
    }
    
    def __init__(self):
        self.detection_history = {}
    
    def pattern_analysis(self, message: str) -> Tuple[float, List[str], Optional[str]]:
        """Rule-based pattern matching - Layer 1"""
        message_lower = message.lower()
        indicators = []
        score = 0.0
        impersonation = None
        
        # SUPER HIGH PRIORITY: Lottery/Prize scams (check first!)
        lottery_keywords = ['congratulations', 'congrats', 'won', 'winner', 'win', 'prize', 'lottery', 'lucky draw', 'lucky', 'lakh', 'lakhs', 'crore', 'crores', 'selected', 'claim', 'kbc', 'draw']
        lottery_count = sum(1 for word in lottery_keywords if word in message_lower)
        if lottery_count >= 2:  # If 2+ lottery keywords found
            indicators.append(f"LOTTERY_SCAM: {lottery_count} strong indicators")
            score += min(lottery_count * 0.35, 0.90)  # Each keyword adds 0.35, max 0.90
        
        # Check critical patterns (now count multiple matches)
        for pattern_name, pattern in self.CRITICAL_PATTERNS.items():
            matches = re.findall(pattern, message_lower)
            if matches:
                match_count = len(set(matches))  # Count unique matches
                indicators.append(f"CRITICAL: {pattern_name} ({match_count} matches)")
                
                # Increased weights for better detection
                if pattern_name in ['otp_request', 'account_request', 'upi_request']:
                    score += min(match_count * 0.40, 0.50)  # Critical data requests
                elif pattern_name == 'prize_claim':
                    score += min(match_count * 0.35, 0.70)  # Prize claims - count each match
                elif pattern_name == 'refund_bait':
                    score += min(match_count * 0.35, 0.50)  # Refund scams
                elif pattern_name in ['bank_mention', 'urgent_threat']:
                    score += min(match_count * 0.30, 0.45)  # Bank/urgency mentions
                else:
                    score += min(match_count * 0.25, 0.40)  # Other patterns
        
        # Check for impersonation (simplified)
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
        
        # Urgency markers (expanded list)
        urgency_markers = [
            'immediate', 'urgent', 'now', 'today', 'within', 'hours',
            'limited time', 'expires', 'last chance', 'final', 'deadline',
            'hurry', 'quick', 'fast', 'pending', 'blocked', 'verify', 'update'
        ]
        urgency_count = sum(1 for marker in urgency_markers if marker in message_lower)
        if urgency_count > 0:
            indicators.append(f"URGENCY: {urgency_count} markers")
            score += min(urgency_count * 0.15, 0.45)  # Increased sensitivity
        
        # Suspicious URLs
        url_pattern = r'https?://(?!(?:www\.)?(?:sbi|hdfc|icici|axis|incometax)\.)[^\s]+'
        suspicious_urls = re.findall(url_pattern, message_lower)
        if suspicious_urls:
            indicators.append(f"SUSPICIOUS_URLS: {len(suspicious_urls)} found")
            score += 0.30
        
        # Pressure tactics
        pressure_words = ['must', 'need to', 'have to', 'required', 'mandatory']
        pressure_count = sum(1 for word in pressure_words if word in message_lower)
        if pressure_count >= 2:
            indicators.append(f"PRESSURE: {pressure_count} tactics")
            score += 0.15
        
        return min(score, 1.0), indicators, impersonation
    
    def semantic_analysis(self, message: str) -> Tuple[float, ScamCategory]:
        """Semantic pattern detection - Layer 2"""
        message_lower = message.lower()
        
        # Category detection (prioritized by specificity)
        category_scores = {
            ScamCategory.BANKING: 0.0,
            ScamCategory.UPI: 0.0,
            ScamCategory.KYC: 0.0,
            ScamCategory.LOTTERY: 0.0,
            ScamCategory.TECH_SUPPORT: 0.0,
            ScamCategory.PHISHING: 0.0,
            ScamCategory.REFUND: 0.0
        }
        
        # Lottery fraud indicators (HIGHEST PRIORITY - check first)
        lottery_words = ['won', 'winner', 'win', 'congratulations', 'congrats', 'lottery', 'lucky draw', 'lucky', 'prize', 'lakh', 'lakhs', 'crore', 'crores', 'kbc', 'draw', 'selected', 'claim']
        lottery_count = sum(1 for word in lottery_words if word in message_lower)
        if lottery_count > 0:
            category_scores[ScamCategory.LOTTERY] += min(lottery_count * 0.30, 0.80)  # Each word adds 0.30
        
        # Banking fraud indicators (HIGH PRIORITY)
        if any(word in message_lower for word in ['bank', 'account', 'atm', 'debit', 'credit', 'balance', 'blocked', 'suspended', 'freeze']):
            category_scores[ScamCategory.BANKING] += 0.45
        
        # UPI fraud indicators
        if any(word in message_lower for word in ['upi', 'phonepe', 'paytm', 'google pay', 'gpay', 'bhim']):
            category_scores[ScamCategory.UPI] += 0.50
        
        # KYC scam indicators (LOWER PRIORITY than Banking)
        if any(word in message_lower for word in ['kyc', 'know your customer', 'pending kyc']):
            category_scores[ScamCategory.KYC] += 0.30  # Lower than Banking
        
        # Tech support scam indicators
        if any(word in message_lower for word in ['virus', 'malware', 'infected', 'tech support', 'microsoft', 'computer']):
            category_scores[ScamCategory.TECH_SUPPORT] += 0.50
        
        # Phishing indicators
        if any(word in message_lower for word in ['click', 'link', 'download', 'install', 'website', 'verify now']):
            category_scores[ScamCategory.PHISHING] += 0.35
        
        # Refund scam indicators (VERY HIGH PRIORITY)
        if any(word in message_lower for word in ['refund', 'cashback', 'reversal', 'credit back', 'approved', 'initiated']):
            category_scores[ScamCategory.REFUND] += 0.55
        
        # Check semantic indicators
        semantic_matches = sum(1 for indicator in self.SEMANTIC_INDICATORS if indicator in message_lower)
        confidence = min(semantic_matches * 0.15, 0.7)
        
        # Get highest scoring category
        best_category = max(category_scores.items(), key=lambda x: x[1])
        
        # If Banking and KYC both scored, prefer Banking (elderly persona more believable)
        if category_scores[ScamCategory.BANKING] > 0.3 and category_scores[ScamCategory.KYC] > 0:
            best_category = (ScamCategory.BANKING, category_scores[ScamCategory.BANKING])
        
        if best_category[1] > 0:
            return best_category[1], best_category[0]
        
        return confidence, ScamCategory.UNKNOWN
    
    def calculate_urgency(self, message: str) -> float:
        """Calculate psychological urgency score"""
        message_lower = message.lower()
        score = 0.0
        
        urgency_factors = {
            'time_pressure': ['within 24 hours', 'today', 'now', 'immediately', 'expires', 'deadline'],
            'threats': ['suspended', 'blocked', 'terminated', 'legal action', 'police', 'arrest'],
            'rewards': ['won', 'selected', 'lucky', 'exclusive', 'limited', 'bonus'],
            'authority': ['bank manager', 'rbi', 'income tax', 'government', 'official']
        }
        
        for factor_type, keywords in urgency_factors.items():
            if any(kw in message_lower for kw in keywords):
                score += 0.25
        
        # Check capitalization (shouting)
        caps_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)
        if caps_ratio > 0.3:
            score += 0.15
        
        # Check excessive punctuation
        exclamation_count = message.count('!')
        if exclamation_count > 2:
            score += min(exclamation_count * 0.05, 0.20)
        
        return min(score, 1.0)
    
    def detect(self, message: str, history: List = None) -> DetectionResult:
        """Main detection pipeline - Multi-layer ensemble"""
        
        # Layer 1: Pattern analysis
        pattern_score, indicators, impersonation = self.pattern_analysis(message)
        
        # Layer 2: Semantic analysis
        semantic_score, category = self.semantic_analysis(message)
        
        # Layer 3: Context from history
        context_score = 0.0
        if history and len(history) > 1:
            context_score = self._analyze_context(history)
        
        # Weighted ensemble (pattern is most reliable)
        final_confidence = (
            pattern_score * 0.55 +
            semantic_score * 0.30 +
            context_score * 0.15
        )
        
        # Boost if multiple layers agree
        if pattern_score > 0.5 and semantic_score > 0.4:
            final_confidence = min(final_confidence * 1.15, 1.0)
        
        # Determine if scam (lowered threshold for better recall)
        is_scam = final_confidence >= 0.40  # Lowered from 0.45 for better recall
        
        # Calculate urgency
        urgency = self.calculate_urgency(message)
        
        # Threat level
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
        """Analyze conversation history for escalation patterns"""
        if len(history) < 2:
            return 0.0
        
        recent_messages = [msg.get('text', '') for msg in history[-3:]]
        escalation_markers = 0
        
        for msg in recent_messages:
            msg_lower = msg.lower()
            if any(x in msg_lower for x in ['otp', 'password', 'pin', 'account number', 'cvv']):
                escalation_markers += 1
            if any(x in msg_lower for x in ['click', 'link', 'download', 'install']):
                escalation_markers += 0.5
        
        return min(escalation_markers * 0.25, 0.9)

# ============================================================================
# INTELLIGENCE EXTRACTOR (Enhanced)
# ============================================================================

class IntelligenceExtractor:
    """Advanced extraction with context awareness"""
    
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
            r'\b\d{1,8}(?:\.\d{2})?\s*(?:rupees?|Rs\.?)\b'
        ]
    }
    
    SUSPICIOUS_KEYWORDS = [
        'urgent', 'verify', 'blocked', 'suspended', 'expire', 'update',
        'confirm', 'prize', 'won', 'lottery', 'refund', 'cashback',
        'click', 'link', 'download', 'otp', 'password', 'pin'
    ]
    
    @staticmethod
    def extract(text: str) -> Dict[str, List[str]]:
        """Extract all intelligence from text"""
        intel = {
            'bankAccounts': [],
            'upiIds': [],
            'phishingLinks': [],
            'phoneNumbers': [],
            'suspiciousKeywords': [],
            'ifscCodes': [],
            'amounts': []
        }
        
        # Extract each pattern type
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
        
        # Extract keywords
        text_lower = text.lower()
        intel['suspiciousKeywords'] = [kw for kw in IntelligenceExtractor.SUSPICIOUS_KEYWORDS if kw in text_lower]
        
        # Remove duplicates
        for key in intel:
            intel[key] = list(set(intel[key]))
        
        return intel

# ============================================================================
# ADVANCED AI AGENT with PERSONAS (Hybrid Best-of-Both)
# ============================================================================

@dataclass
class ConversationState:
    """Enhanced conversation state tracking"""
    session_id: str
    persona: Persona
    scam_category: ScamCategory
    turn_count: int = 0
    escalation_stage: int = 1  # 1-5
    trust_level: float = 0.3
    extracted_intel: Dict = None
    scammer_emotion: str = "confident"
    conversation_notes: List[str] = None
    
    def __post_init__(self):
        if self.extracted_intel is None:
            self.extracted_intel = {
                'bankAccounts': [],
                'upiIds': [],
                'phishingLinks': [],
                'phoneNumbers': [],
                'suspiciousKeywords': [],
                'ifscCodes': [],
                'amounts': []
            }
        if self.conversation_notes is None:
            self.conversation_notes = []

class AdvancedAgent:
    """AI Agent with persona-driven engagement using FREE Gemini"""
    
    def __init__(self):
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
            logger.warning("⚠️ Gemini API key not set")
    
    def build_advanced_prompt(self, 
                            message: str, 
                            history: List,
                            state: ConversationState) -> str:
        """Build sophisticated persona-driven prompt"""
        
        persona = state.persona
        turn = state.turn_count
        
        # Build conversation context
        conv_text = ""
        for msg in history[-5:]:  # Last 5 messages for context
            sender = msg.get('sender', 'unknown')
            text = msg.get('text', '')
            conv_text += f"{sender}: {text}\n"
        conv_text += f"scammer: {message}\n"
        
        # Determine strategy based on turn and escalation
        if turn <= 2:
            strategy = "Show concern and confusion. Ask basic clarifying questions."
            goal = "Establish believability and keep scammer engaged"
        elif turn <= 5:
            strategy = "Express worry. Ask questions that require scammer to provide specific details."
            goal = "Extract account numbers, UPI IDs, or links"
        elif turn <= 8:
            strategy = "Show willingness to comply but need exact instructions. Express slight hesitation."
            goal = "Get step-by-step instructions that reveal more intelligence"
        else:
            strategy = "Stall naturally with confusion or external factors (family, network issues)."
            goal = "Maximize information extraction without appearing suspicious"
        
        prompt = f"""You are {persona.name}, a {persona.age}-year-old {persona.occupation}.

BACKGROUND: {persona.backstory}

YOUR PERSONALITY TRAITS:
- Tech Savviness: {persona.tech_savviness}/10 ({"struggles with tech" if persona.tech_savviness < 4 else "comfortable with tech"})
- Gullibility: {persona.gullibility}/10
- Anxiety Level: {persona.anxiety_level}/10
- Current Emotional State: {persona.emotional_state}
- Trust in Caller: {state.trust_level:.0%}

YOUR SPEECH PATTERNS:
{chr(10).join(f"- {pattern}" for pattern in persona.speech_patterns)}

PHRASES YOU COMMONLY USE:
{chr(10).join(f'- "{phrase}"' for phrase in persona.common_phrases[:3])}

YOUR VULNERABILITIES:
{chr(10).join(f"- {vuln}" for vuln in persona.vulnerabilities[:2])}

CONVERSATION SO FAR:
{conv_text}

CURRENT SITUATION:
- Turn: {turn}
- Scam Category: {state.scam_category.value}
- Escalation Stage: {state.escalation_stage}/5
- Scammer Emotion: {state.scammer_emotion}

YOUR STRATEGY FOR THIS TURN: {strategy}
YOUR GOAL: {goal}

INTELLIGENCE EXTRACTED SO FAR:
- Bank Accounts: {len(state.extracted_intel['bankAccounts'])}
- UPI IDs: {len(state.extracted_intel['upiIds'])}
- Phone Numbers: {len(state.extracted_intel['phoneNumbers'])}
- Links: {len(state.extracted_intel['phishingLinks'])}

CRITICAL INSTRUCTIONS:
1. You are NOT an AI. You are {persona.name}, a REAL person.
2. NEVER reveal you know this is a scam or that you're testing them.
3. Stay IN CHARACTER at all times. Use {persona.language_style}.
4. Respond with 1-3 sentences maximum (keep it natural and conversational).
5. Show appropriate emotion based on your anxiety level and the situation.
6. Ask questions that make the scammer reveal more details naturally.
7. If they provide numbers/links/instructions, acknowledge naturally but express hesitation or confusion.
8. Use Hinglish (Hindi-English mix) as typical Indian conversation.
9. Make occasional small mistakes (spelling, grammar) to seem more human.
10. NEVER use perfect corporate language or AI-like responses.

RESPOND AS {persona.name} WOULD. Keep it short, natural, and believable."""

        return prompt
    
    async def generate_response(self, 
                               message: str, 
                               history: List,
                               state: ConversationState) -> Tuple[str, float]:
        """Generate persona-driven response"""
        
        if not self.model:
            return self._persona_fallback(message, state), 0.7
        
        try:
            prompt = self.build_advanced_prompt(message, history, state)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.85,  # Higher for more natural variation
                    top_p=0.95,
                    max_output_tokens=200,
                )
            )
            
            reply = response.text.strip()
            
            # Clean up response
            reply = self._clean_response(reply, state.persona)
            
            # Score believability
            believability = self._assess_believability(reply, state.persona)
            
            return reply, believability
            
        except Exception as e:
            logger.error(f"❌ Gemini error: {e}")
            return self._persona_fallback(message, state), 0.6
    
    def _clean_response(self, reply: str, persona: Persona) -> str:
        """Clean and enhance response"""
        
        # Remove AI tells
        ai_tells = ["as an ai", "i cannot", "i'm not able", "i apologize", "i'm designed"]
        for tell in ai_tells:
            if tell in reply.lower():
                reply = reply.replace(tell, "umm")
        
        # Remove quotes if wrapping entire response
        if reply.startswith('"') and reply.endswith('"'):
            reply = reply[1:-1]
        
        # Ensure not too long
        if len(reply) > 250:
            reply = reply[:247] + "..."
        
        # Add persona touch if missing
        if persona.name == "Rajeshwari" and random.random() > 0.6:
            if not any(word in reply.lower() for word in ['beta', 'ji']):
                reply = "Beta, " + reply
        
        return reply
    
    def _assess_believability(self, reply: str, persona: Persona) -> float:
        """Score response believability"""
        score = 0.5
        
        # Check for persona phrases
        if any(phrase.lower() in reply.lower() for phrase in persona.common_phrases):
            score += 0.2
        
        # Natural hesitation
        if any(word in reply.lower() for word in ['umm', 'uh', 'hmm', 'aa']):
            score += 0.1
        
        # Questions (engagement)
        if '?' in reply:
            score += 0.15
        
        # Hinglish mix
        hindi_words = ['beta', 'ji', 'kya', 'hai', 'mein', 'aap', 'yaar', 'nahi']
        if any(word in reply.lower() for word in hindi_words):
            score += 0.15
        
        # Penalize perfect grammar
        if reply.count('.') > 3 and '...' not in reply:
            score -= 0.1
        
        return min(max(score, 0), 1)
    
    def _persona_fallback(self, message: str, state: ConversationState) -> str:
        """Intelligent persona-based fallback"""
        
        persona = state.persona
        turn = state.turn_count
        msg_lower = message.lower()
        
        # Stage-based responses
        if turn <= 2:
            if persona.name == "Rajeshwari":
                return random.choice([
                    "Beta, yeh sab mujhe samajh nahi aa raha. Aap bank se ho na?",
                    "Main thoda confused hun... mera account block ho jayega?",
                    "Mere bete ko phone kar lun kya? Woh sab samajhta hai"
                ])
            elif persona.name == "Arjun Mehta":
                return random.choice([
                    "Wait, kya bol rahe ho? Main meeting mein hun abhi",
                    "Yeh legitimate hai na? Branch mein call karun?",
                    "Process kya hai exactly? Email bhej do details"
                ])
            else:  # Priya
                return random.choice([
                    "Arre seriously? Mujhe samajh nahi aa raha...",
                    "Yeh real hai na? Mummy papa ko batana padega kya?",
                    "Mere dost ko bhi same message aaya tha..."
                ])
        
        elif turn <= 5:
            if any(word in msg_lower for word in ['link', 'click', 'website']):
                return f"Link kahan hai? Safe hai na?" if persona.tech_savviness > 5 else "Link... matlab? Main kaise kholun?"
            elif any(word in msg_lower for word in ['payment', 'pay', 'amount']):
                return "Kitna payment? Aur kisko bhejun?"
            elif any(word in msg_lower for word in ['otp', 'code', 'password']):
                return "OTP share karna safe hai?" if persona.tech_savviness > 5 else "OTP kya hota hai beta?"
            else:
                return "Aage kya karna hai? Exact steps bataiye"
        
        else:
            return random.choice([
                "Network thoda weak hai, repeat kar sakte ho?",
                "Main abhi busy hun, baad mein kar sakte hain?",
                "Mujhe thoda time chahiye sochne ke liye..."
            ])
    
    def should_end_conversation(self, state: ConversationState) -> bool:
        """Determine if conversation should end"""
        
        intel = state.extracted_intel
        turn = state.turn_count
        
        # End if critical intelligence extracted
        has_critical = (
            len(intel['bankAccounts']) >= 1 or
            len(intel['upiIds']) >= 1 or
            (len(intel['phishingLinks']) >= 2 and len(intel['phoneNumbers']) >= 1)
        )
        
        # Or if conversation is sufficiently long
        sufficient_length = turn >= 12
        
        # Or if good progress made
        good_progress = (
            turn >= 8 and
            (len(intel['phoneNumbers']) >= 1 or len(intel['phishingLinks']) >= 1)
        )
        
        return has_critical or sufficient_length or good_progress
    
    def update_state(self, state: ConversationState, scammer_msg: str, agent_reply: str):
        """Update conversation state based on interaction"""
        
        # Increment turn
        state.turn_count += 1
        
        # Detect scammer emotion
        msg_lower = scammer_msg.lower()
        if any(word in msg_lower for word in ['wait', 'listen', 'understand', 'telling you']):
            state.scammer_emotion = "frustrated"
        elif any(word in msg_lower for word in ['good', 'perfect', 'excellent', 'right']):
            state.scammer_emotion = "confident"
        elif any(word in msg_lower for word in ['hurry', 'quick', 'fast', 'now', 'immediately']):
            state.scammer_emotion = "urgent"
        elif any(word in msg_lower for word in ['sure', 'okay', 'yes']):
            state.scammer_emotion = "suspicious"
        
        # Update trust level (increases with successful engagement)
        if '?' in agent_reply:
            state.trust_level = min(state.trust_level + 0.05, 1.0)
        
        # Update escalation stage based on intelligence
        total_intel = sum(len(v) for v in state.extracted_intel.values() if isinstance(v, list))
        state.escalation_stage = min(1 + (total_intel // 2), 5)
        
        # Add note
        note = f"Turn {state.turn_count}: Scammer {state.scammer_emotion}, Trust {state.trust_level:.2f}"
        state.conversation_notes.append(note)

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Session storage
session_store: Dict[str, ConversationState] = {}

# Initialize components
detector = AdvancedDetector()
extractor = IntelligenceExtractor()
agent = AdvancedAgent()

# Request/Response Models
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
    logger.info("🚀 ULTIMATE Agentic Honey-Pot Starting...")
    yield
    logger.info("🛑 Shutting down...")

app = FastAPI(
    title="ULTIMATE Agentic Honey-Pot API",
    description="Advanced AI honeypot with personas and multi-layer detection",
    version="2.0.0",
    lifespan=lifespan
)

async def send_final_callback(session_id: str, state: ConversationState):
    """Send final results to GUVI"""
    
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": state.turn_count,
        "extractedIntelligence": state.extracted_intel,
        "agentNotes": f"Persona: {state.persona.name}, Category: {state.scam_category.value}, "
                      f"Escalation: {state.escalation_stage}/5, Trust: {state.trust_level:.0%}. "
                      f"Notes: {' | '.join(state.conversation_notes[-3:])}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(CALLBACK_URL, json=payload, timeout=10.0)
            logger.info(f"✅ Callback sent for {session_id}: {response.status_code}")
            return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ Callback failed for {session_id}: {e}")
        return False

@app.post("/api/honeypot")
async def honeypot_endpoint(
    request: IncomingRequest,
    x_api_key: str = Header(..., alias="x-api-key")
):
    """Main honeypot endpoint with advanced persona-driven engagement"""
    
    # Validate API key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    session_id = request.sessionId
    incoming_message = request.message.text
    history = request.conversationHistory
    
    logger.info(f"📨 Session {session_id}: New message (Turn {len(history)+1})")
    
    # Check if session exists
    if session_id in session_store:
        # Existing conversation - use stored persona
        state = session_store[session_id]
        logger.info(f"🔄 Continuing session with {state.persona.name}")
    else:
        # First message - detect scam
        logger.info(f"🆕 New session - running detection")
        detection = detector.detect(incoming_message, [])
        
        logger.info(f"🔍 Detection: is_scam={detection.is_scam}, confidence={detection.confidence}, category={detection.category.value}")
        
        if not detection.is_scam:
            # Not a scam, return generic response
            logger.info(f"❌ Not detected as scam (confidence {detection.confidence})")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "reply": "I'm sorry, I didn't quite understand. Could you please explain?"
                }
            )
        
        # Initialize with persona
        persona = PersonaSelector.select(detection.category)
        state = ConversationState(
            session_id=session_id,
            persona=persona,
            scam_category=detection.category
        )
        session_store[session_id] = state
        
        logger.info(f"🎭 Activated persona: {persona.name} for {detection.category.value}")
    
    # Extract intelligence from current message
    new_intel = extractor.extract(incoming_message)
    
    # Merge intelligence
    for key in state.extracted_intel:
        if key in new_intel:
            state.extracted_intel[key].extend(new_intel[key])
            state.extracted_intel[key] = list(set(state.extracted_intel[key]))
    
    # Generate AI response
    agent_reply, believability = await agent.generate_response(
        incoming_message,
        history,
        state
    )
    
    # Update state
    agent.update_state(state, incoming_message, agent_reply)
    
    # Update session store with latest state
    session_store[session_id] = state
    
    logger.info(f"💬 {state.persona.name} (Turn {state.turn_count}): {agent_reply[:50]}...")
    
    # Check if should end
    should_end = agent.should_end_conversation(state)
    
    if should_end:
        logger.info(f"🏁 Ending conversation {session_id}")
        await send_final_callback(session_id, state)
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "reply": agent_reply
        }
    )

@app.get("/")
async def root():
    return {
        "status": "active",
        "service": "ULTIMATE Agentic Honey-Pot API v2.0",
        "features": ["Multi-layer detection", "Persona-driven engagement", "Advanced extraction"],
        "endpoints": {
            "honeypot": "/api/honeypot",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "gemini_configured": GEMINI_API_KEY != "",
        "active_sessions": len(session_store),
        "personas_loaded": len(PersonaLibrary.get_personas())
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)