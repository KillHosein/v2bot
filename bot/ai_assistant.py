"""
AI-Powered Assistant with Natural Language Processing
Provides intelligent responses, command suggestions, and user support
"""
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from difflib import get_close_matches
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .db import query_db, execute_db
from .advanced_logging import get_advanced_logger
from .performance_optimizer import cached


class AIAssistant:
    """Intelligent assistant for enhanced user experience"""
    
    def __init__(self):
        self.logger = get_advanced_logger()
        self._create_tables()
        self.intents = self._load_intents()
        self.responses = self._load_responses()
        self.commands = self._load_commands()
        self.learning_enabled = True
    
    def _create_tables(self):
        """Create AI assistant tables"""
        try:
            execute_db("""
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_message TEXT,
                    bot_response TEXT,
                    intent TEXT,
                    confidence REAL,
                    feedback TEXT,
                    helpful BOOLEAN
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS ai_intents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intent_name TEXT UNIQUE NOT NULL,
                    patterns TEXT,
                    responses TEXT,
                    action TEXT,
                    priority INTEGER DEFAULT 0,
                    usage_count INTEGER DEFAULT 0
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS ai_learning (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT,
                    intent TEXT,
                    confidence REAL,
                    learned_at TEXT,
                    verified BOOLEAN DEFAULT 0
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'fa',
                    ai_enabled BOOLEAN DEFAULT 1,
                    suggestions_enabled BOOLEAN DEFAULT 1,
                    learning_enabled BOOLEAN DEFAULT 1,
                    preferences TEXT
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS faq (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    category TEXT,
                    views INTEGER DEFAULT 0,
                    helpful_count INTEGER DEFAULT 0,
                    not_helpful_count INTEGER DEFAULT 0
                )
            """)
            
            # Initialize default intents
            self._init_default_intents()
            
        except Exception as e:
            self.logger.log_error(e, "ai_assistant_init")
    
    def _init_default_intents(self):
        """Initialize default intents and patterns"""
        default_intents = [
            {
                'name': 'greeting',
                'patterns': ['سلام', 'hello', 'hi', 'درود', 'صبح بخیر', 'عصر بخیر'],
                'responses': [
                    'سلام! چطور می‌تونم کمکتون کنم؟ 😊',
                    'درود! به ربات Wings خوش آمدید 🚀',
                    'سلام عزیز! آماده کمک به شما هستم 💫'
                ],
                'action': None
            },
            {
                'name': 'help',
                'patterns': ['کمک', 'help', 'راهنما', 'چطور', 'چگونه', 'توضیح'],
                'responses': [
                    'برای راهنمایی از منوی اصلی استفاده کنید یا دستور /help را ارسال کنید.',
                    'می‌تونم در موارد زیر کمکتون کنم:\n• خرید VPN\n• مدیریت سرویس\n• شارژ کیف پول\n• پشتیبانی'
                ],
                'action': 'show_help_menu'
            },
            {
                'name': 'buy_vpn',
                'patterns': ['خرید', 'buy', 'قیمت', 'price', 'پلن', 'plan', 'سرویس'],
                'responses': [
                    'برای خرید VPN از منوی "🛒 خرید سرویس" استفاده کنید.',
                    'پلن‌های متنوعی داریم! از منوی خرید، پلن مناسبتون رو انتخاب کنید.'
                ],
                'action': 'show_plans'
            },
            {
                'name': 'wallet',
                'patterns': ['کیف پول', 'wallet', 'موجودی', 'شارژ', 'balance'],
                'responses': [
                    'برای مدیریت کیف پول از منوی "💳 کیف پول" استفاده کنید.',
                    'می‌تونید موجودی خود را ببینید و کیف پول را شارژ کنید.'
                ],
                'action': 'show_wallet'
            },
            {
                'name': 'support',
                'patterns': ['پشتیبانی', 'support', 'مشکل', 'problem', 'تیکت', 'ticket'],
                'responses': [
                    'برای ارتباط با پشتیبانی از منوی "📞 پشتیبانی" استفاده کنید.',
                    'تیم پشتیبانی ما آماده پاسخگویی به شماست.'
                ],
                'action': 'show_support'
            },
            {
                'name': 'connection_help',
                'patterns': ['اتصال', 'connect', 'وصل', 'آموزش', 'tutorial', 'نمیشه'],
                'responses': [
                    'برای آموزش اتصال، از منوی "📱 راهنمای اتصال" استفاده کنید.',
                    'آموزش‌های تصویری برای همه پلتفرم‌ها موجود است.'
                ],
                'action': 'show_tutorials'
            }
        ]
        
        for intent in default_intents:
            execute_db("""
                INSERT OR IGNORE INTO ai_intents 
                (intent_name, patterns, responses, action)
                VALUES (?, ?, ?, ?)
            """, (
                intent['name'],
                json.dumps(intent['patterns']),
                json.dumps(intent['responses']),
                intent['action']
            ))
    
    def _load_intents(self) -> Dict:
        """Load intents from database"""
        intents = {}
        db_intents = query_db("SELECT * FROM ai_intents")
        
        for intent in db_intents or []:
            intents[intent['intent_name']] = {
                'patterns': json.loads(intent['patterns']),
                'responses': json.loads(intent['responses']),
                'action': intent['action'],
                'priority': intent['priority']
            }
        
        return intents
    
    def _load_responses(self) -> Dict:
        """Load response templates"""
        return {
            'unknown': [
                'متوجه نشدم. می‌تونید از منوی اصلی استفاده کنید یا /help بزنید.',
                'ببخشید، منظورتون رو نفهمیدم. از دکمه‌های منو استفاده کنید.',
                'برای راهنمایی بیشتر /help را ارسال کنید.'
            ],
            'error': [
                'متاسفانه خطایی رخ داد. لطفا دوباره تلاش کنید.',
                'مشکلی پیش آمد. لطفا بعدا امتحان کنید.'
            ],
            'thanks': [
                'خواهش می‌کنم! خوشحالم که تونستم کمک کنم 😊',
                'قابلی نداشت! موفق باشید 🌟',
                'همیشه در خدمتیم! 💫'
            ]
        }
    
    def _load_commands(self) -> List[Dict]:
        """Load available commands"""
        return [
            {'command': '/start', 'description': 'شروع کار با ربات'},
            {'command': '/help', 'description': 'راهنمای استفاده'},
            {'command': '/buy', 'description': 'خرید سرویس VPN'},
            {'command': '/wallet', 'description': 'کیف پول من'},
            {'command': '/services', 'description': 'سرویس‌های من'},
            {'command': '/support', 'description': 'پشتیبانی'},
            {'command': '/referral', 'description': 'دعوت دوستان'},
            {'command': '/admin', 'description': 'پنل مدیریت (فقط ادمین)'}
        ]
    
    async def process_message(self, 
                             message: str, 
                             user_id: int,
                             context: Optional[Dict] = None) -> Tuple[str, Optional[str], float]:
        """
        Process user message and generate response
        Returns: (response, action, confidence)
        """
        # Detect intent
        intent, confidence = self.detect_intent(message)
        
        # Get response
        if intent and confidence > 0.6:
            response = self.generate_response(intent, context)
            action = self.intents[intent].get('action')
            
            # Update usage stats
            execute_db(
                "UPDATE ai_intents SET usage_count = usage_count + 1 WHERE intent_name = ?",
                (intent,)
            )
        else:
            # Try to find similar command
            suggestion = self.suggest_command(message)
            if suggestion:
                response = f"شاید منظورتون این بود: {suggestion['command']}\n{suggestion['description']}"
            else:
                # Check FAQ
                faq_answer = await self.search_faq(message)
                if faq_answer:
                    response = faq_answer
                else:
                    response = self.responses['unknown'][0]
            
            action = None
            intent = 'unknown'
        
        # Record conversation
        self._record_conversation(user_id, message, response, intent, confidence)
        
        # Learn from interaction if enabled
        if self.learning_enabled and confidence < 0.8:
            await self._learn_from_interaction(message, intent, confidence)
        
        return response, action, confidence
    
    def detect_intent(self, message: str) -> Tuple[Optional[str], float]:
        """Detect user intent from message"""
        message_lower = message.lower()
        best_intent = None
        best_confidence = 0.0
        
        # Check each intent
        for intent_name, intent_data in self.intents.items():
            for pattern in intent_data['patterns']:
                # Calculate similarity
                if pattern.lower() in message_lower:
                    confidence = 0.9
                elif self._calculate_similarity(pattern.lower(), message_lower) > 0.7:
                    confidence = 0.7
                else:
                    continue
                
                # Apply priority boost
                confidence += intent_data['priority'] * 0.1
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = intent_name
        
        # Check learned patterns
        learned = query_db(
            "SELECT intent, MAX(confidence) as conf FROM ai_learning WHERE verified = 1 GROUP BY intent"
        )
        for item in learned or []:
            if self._matches_learned_pattern(message, item['intent']):
                if item['conf'] > best_confidence:
                    best_confidence = item['conf']
                    best_intent = item['intent']
        
        return best_intent, min(best_confidence, 1.0)
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _matches_learned_pattern(self, message: str, intent: str) -> bool:
        """Check if message matches learned patterns"""
        learned_patterns = query_db(
            "SELECT pattern FROM ai_learning WHERE intent = ? AND verified = 1",
            (intent,)
        )
        
        for pattern_row in learned_patterns or []:
            if self._calculate_similarity(pattern_row['pattern'].lower(), message.lower()) > 0.8:
                return True
        
        return False
    
    def generate_response(self, intent: str, context: Optional[Dict] = None) -> str:
        """Generate response based on intent"""
        import random
        
        if intent in self.intents:
            responses = self.intents[intent]['responses']
            response = random.choice(responses)
            
            # Personalize response with context
            if context:
                if 'user_name' in context:
                    response = response.replace('{name}', context['user_name'])
                if 'service_count' in context:
                    response = response.replace('{count}', str(context['service_count']))
            
            return response
        
        return self.responses['unknown'][0]
    
    def suggest_command(self, message: str) -> Optional[Dict]:
        """Suggest closest matching command"""
        # Extract potential command
        words = message.split()
        for word in words:
            if word.startswith('/'):
                # Find closest command
                command_names = [cmd['command'] for cmd in self.commands]
                matches = get_close_matches(word, command_names, n=1, cutoff=0.6)
                
                if matches:
                    for cmd in self.commands:
                        if cmd['command'] == matches[0]:
                            return cmd
        
        # Try to match by description
        for cmd in self.commands:
            if any(keyword in message.lower() for keyword in cmd['description'].split()):
                return cmd
        
        return None
    
    @cached(ttl=300)
    async def search_faq(self, question: str) -> Optional[str]:
        """Search FAQ for answer"""
        # First try exact match
        faq = query_db(
            "SELECT * FROM faq WHERE question LIKE ? ORDER BY views DESC LIMIT 1",
            (f'%{question}%',),
            one=True
        )
        
        if faq:
            # Update view count
            execute_db(
                "UPDATE faq SET views = views + 1 WHERE id = ?",
                (faq['id'],)
            )
            return faq['answer']
        
        # Try similarity match
        all_faqs = query_db("SELECT * FROM faq")
        best_match = None
        best_score = 0.0
        
        for faq_item in all_faqs or []:
            score = self._calculate_similarity(question.lower(), faq_item['question'].lower())
            if score > best_score and score > 0.6:
                best_score = score
                best_match = faq_item
        
        if best_match:
            execute_db(
                "UPDATE faq SET views = views + 1 WHERE id = ?",
                (best_match['id'],)
            )
            return best_match['answer']
        
        return None
    
    def _record_conversation(self, 
                           user_id: int,
                           user_message: str,
                           bot_response: str,
                           intent: str,
                           confidence: float):
        """Record conversation for analysis"""
        execute_db("""
            INSERT INTO ai_conversations 
            (user_id, timestamp, user_message, bot_response, intent, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            datetime.now().isoformat(),
            user_message[:500],  # Limit message length
            bot_response[:500],
            intent,
            confidence
        ))
    
    async def _learn_from_interaction(self, message: str, intent: str, confidence: float):
        """Learn from user interactions"""
        if confidence > 0.5 and intent != 'unknown':
            # Record potential pattern
            execute_db("""
                INSERT INTO ai_learning 
                (pattern, intent, confidence, learned_at)
                VALUES (?, ?, ?, ?)
            """, (
                message,
                intent,
                confidence,
                datetime.now().isoformat()
            ))
            
            # Auto-verify if confidence is high
            if confidence > 0.85:
                execute_db(
                    "UPDATE ai_learning SET verified = 1 WHERE pattern = ? AND intent = ?",
                    (message, intent)
                )
    
    async def provide_feedback(self, 
                              conversation_id: int,
                              helpful: bool,
                              feedback: Optional[str] = None):
        """Record user feedback on responses"""
        execute_db("""
            UPDATE ai_conversations 
            SET helpful = ?, feedback = ?
            WHERE id = ?
        """, (helpful, feedback, conversation_id))
        
        # Adjust intent confidence based on feedback
        conv = query_db(
            "SELECT intent, confidence FROM ai_conversations WHERE id = ?",
            (conversation_id,),
            one=True
        )
        
        if conv and conv['intent'] != 'unknown':
            # Increase priority for helpful responses
            if helpful:
                execute_db(
                    "UPDATE ai_intents SET priority = priority + 1 WHERE intent_name = ?",
                    (conv['intent'],)
                )
            else:
                execute_db(
                    "UPDATE ai_intents SET priority = MAX(0, priority - 1) WHERE intent_name = ?",
                    (conv['intent'],)
                )
    
    def get_user_insights(self, user_id: int) -> Dict:
        """Get AI insights about user behavior"""
        conversations = query_db(
            "SELECT * FROM ai_conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT 100",
            (user_id,)
        )
        
        if not conversations:
            return {'status': 'new_user'}
        
        # Analyze patterns
        intents = {}
        for conv in conversations:
            intent = conv['intent']
            if intent not in intents:
                intents[intent] = 0
            intents[intent] += 1
        
        # Most common intent
        most_common = max(intents, key=intents.get) if intents else 'unknown'
        
        # Calculate satisfaction
        helpful_convs = query_db(
            "SELECT COUNT(*) as count FROM ai_conversations WHERE user_id = ? AND helpful = 1",
            (user_id,),
            one=True
        )
        
        satisfaction = (helpful_convs['count'] / len(conversations) * 100) if helpful_convs else 0
        
        return {
            'total_interactions': len(conversations),
            'primary_interest': most_common,
            'intent_distribution': intents,
            'satisfaction_rate': satisfaction,
            'last_interaction': conversations[0]['timestamp'] if conversations else None,
            'recommendations': self._generate_recommendations(intents)
        }
    
    def _generate_recommendations(self, intents: Dict) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        if intents.get('buy_vpn', 0) > 3:
            recommendations.append('User shows high interest in purchasing VPN')
        
        if intents.get('support', 0) > 5:
            recommendations.append('User may need proactive support')
        
        if intents.get('wallet', 0) > 2:
            recommendations.append('Consider offering wallet top-up discount')
        
        if intents.get('unknown', 0) > 10:
            recommendations.append('User needs better guidance - show tutorial')
        
        return recommendations
    
    def get_ai_stats(self) -> Dict:
        """Get AI assistant statistics"""
        total_conversations = query_db(
            "SELECT COUNT(*) as count FROM ai_conversations",
            one=True
        )
        
        helpful_rate = query_db(
            "SELECT AVG(CASE WHEN helpful = 1 THEN 100.0 ELSE 0.0 END) as rate FROM ai_conversations WHERE helpful IS NOT NULL",
            one=True
        )
        
        popular_intents = query_db(
            "SELECT intent_name, usage_count FROM ai_intents ORDER BY usage_count DESC LIMIT 5"
        )
        
        learned_patterns = query_db(
            "SELECT COUNT(*) as count FROM ai_learning WHERE verified = 1",
            one=True
        )
        
        return {
            'total_conversations': total_conversations['count'] if total_conversations else 0,
            'satisfaction_rate': helpful_rate['rate'] if helpful_rate else 0,
            'popular_intents': popular_intents or [],
            'learned_patterns': learned_patterns['count'] if learned_patterns else 0,
            'active_intents': len(self.intents),
            'faq_count': query_db("SELECT COUNT(*) as count FROM faq", one=True)['count']
        }


# Global AI assistant
_ai_assistant = None

def get_ai_assistant() -> AIAssistant:
    """Get or create AI assistant instance"""
    global _ai_assistant
    if _ai_assistant is None:
        _ai_assistant = AIAssistant()
    return _ai_assistant
