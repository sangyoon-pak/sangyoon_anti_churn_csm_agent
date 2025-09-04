"""
SQLite-based Chat Memory System for Anti-Churn Agent
Maintains conversation context and customer information across chat sessions
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import contextmanager

class ChatMemory:
    """SQLite-based chat memory system"""
    
    def __init__(self, db_path: str = "chat_memory.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    customer_id TEXT,
                    customer_name TEXT,
                    industry TEXT,
                    churn_risk_score REAL,
                    tools_used TEXT,
                    evaluation_result TEXT
                )
            """)
            
            # Create customer_contexts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer_contexts (
                    customer_id TEXT PRIMARY KEY,
                    customer_name TEXT,
                    industry TEXT,
                    churn_risk_score REAL,
                    last_discussed DATETIME,
                    topics_discussed TEXT,
                    recommendations_given TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_customer ON messages(customer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
            
            conn.commit()
    
    def add_message(self, session_id: str, role: str, content: str, 
                   customer_context: Optional[Dict] = None, tools_used: Optional[List[str]] = None,
                   evaluation_result: Optional[str] = None):
        """Add a new message to the conversation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Extract customer context
            customer_id = customer_context.get('customer_id') if customer_context else None
            customer_name = customer_context.get('customer_name') if customer_context else None
            industry = customer_context.get('industry') if customer_context else None
            churn_risk_score = customer_context.get('churn_risk_score') if customer_context else None
            
            # Insert message
            cursor.execute("""
                INSERT INTO messages (session_id, role, content, customer_id, customer_name, 
                                   industry, churn_risk_score, tools_used, evaluation_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, role, content, customer_id, customer_name, 
                industry, churn_risk_score, 
                json.dumps(tools_used) if tools_used else None,
                evaluation_result
            ))
            
            # Update or create session
            cursor.execute("""
                INSERT OR REPLACE INTO sessions (session_id, last_activity, message_count)
                VALUES (?, CURRENT_TIMESTAMP, 
                       (SELECT COUNT(*) FROM messages WHERE session_id = ?))
            """, (session_id, session_id))
            
            # Update customer context if provided
            if customer_context and customer_id:
                self.update_customer_context(customer_context)
            
            conn.commit()
    
    def update_customer_context(self, customer_info: Dict):
        """Update or create customer context"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            customer_id = customer_info.get('customer_id')
            if not customer_id:
                return
            
            # Get existing context
            cursor.execute("SELECT * FROM customer_contexts WHERE customer_id = ?", (customer_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing context
                topics = json.loads(existing['topics_discussed']) if existing['topics_discussed'] else []
                recommendations = json.loads(existing['recommendations_given']) if existing['recommendations_given'] else []
                
                # Add new topics/recommendations
                if customer_info.get('topic') and customer_info['topic'] not in topics:
                    topics.append(customer_info['topic'])
                if customer_info.get('recommendation') and customer_info['recommendation'] not in recommendations:
                    recommendations.append(customer_info['recommendation'])
                
                cursor.execute("""
                    UPDATE customer_contexts 
                    SET customer_name = ?, industry = ?, churn_risk_score = ?, 
                        last_discussed = CURRENT_TIMESTAMP, topics_discussed = ?, 
                        recommendations_given = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = ?
                """, (
                    customer_info.get('customer_name', existing['customer_name']),
                    customer_info.get('industry', existing['industry']),
                    customer_info.get('churn_risk_score', existing['churn_risk_score']),
                    json.dumps(topics),
                    json.dumps(recommendations),
                    customer_id
                ))
            else:
                # Create new context
                topics = [customer_info.get('topic')] if customer_info.get('topic') else []
                recommendations = [customer_info.get('recommendation')] if customer_info.get('recommendation') else []
                
                cursor.execute("""
                    INSERT INTO customer_contexts (customer_id, customer_name, industry, 
                                                churn_risk_score, last_discussed, 
                                                topics_discussed, recommendations_given)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                """, (
                    customer_id,
                    customer_info.get('customer_name'),
                    customer_info.get('industry'),
                    customer_info.get('churn_risk_score'),
                    json.dumps(topics),
                    json.dumps(recommendations)
                ))
            
            conn.commit()
    
    def get_conversation_summary(self, session_id: str, max_messages: int = 10) -> str:
        """Generate a summary of the conversation for context"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            session = cursor.fetchone()
            
            if not session:
                return f"No conversation history found for session {session_id}"
            
            # Get recent messages
            cursor.execute("""
                SELECT * FROM messages 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (session_id, max_messages))
            recent_messages = cursor.fetchall()
            
            # Get customer contexts for this session
            cursor.execute("""
                SELECT DISTINCT customer_id, customer_name, industry, churn_risk_score
                FROM messages 
                WHERE session_id = ? AND customer_id IS NOT NULL
                ORDER BY timestamp DESC
            """, (session_id,))
            customers = cursor.fetchall()
            
            # Build summary
            summary_parts = [f"**Conversation Summary (Session: {session_id})**"]
            summary_parts.append(f"**Created:** {session['created_at']}")
            summary_parts.append(f"**Last Activity:** {session['last_activity']}")
            summary_parts.append(f"**Total Messages:** {session['message_count']}")
            
            # Add customer contexts
            if customers:
                summary_parts.append("\n**Customers Discussed:**")
                for customer in customers:
                    summary_parts.append(f"- **{customer['customer_name'] or customer['customer_id']}** ({customer['industry'] or 'Unknown'})")
                    if customer['churn_risk_score']:
                        summary_parts.append(f"  - Churn Risk: {customer['churn_risk_score']:.1%}")
                    summary_parts.append(f"  - Last Discussed: Recent")
            
            # Add recent conversation highlights
            summary_parts.append("\n**Recent Conversation Highlights:**")
            for msg in reversed(recent_messages[-5:]):  # Last 5 messages, in chronological order
                role_emoji = "👤" if msg['role'] == "user" else "🤖"
                timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M')
                content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                summary_parts.append(f"- {role_emoji} **{msg['role'].title()}** ({timestamp}): {content_preview}")
            
            return "\n".join(summary_parts)
    
    def get_customer_context_summary(self, customer_id: str = None) -> str:
        """Get summary of customer context for a specific customer or all customers"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if customer_id:
                # Get specific customer context
                cursor.execute("SELECT * FROM customer_contexts WHERE customer_id = ?", (customer_id,))
                context = cursor.fetchone()
                
                if context:
                    topics = json.loads(context['topics_discussed']) if context['topics_discussed'] else []
                    recommendations = json.loads(context['recommendations_given']) if context['recommendations_given'] else []
                    
                    return f"""**Customer Context for {context['customer_name'] or customer_id}:**
- **Industry:** {context['industry'] or 'Unknown'}
- **Churn Risk:** {context['churn_risk_score']:.1%} if context['churn_risk_score'] else 'Unknown'
- **Topics Discussed:** {', '.join(topics) if topics else 'None'}
- **Recommendations Given:** {', '.join(recommendations) if recommendations else 'None'}
- **Last Discussed:** {context['last_discussed']}"""
                else:
                    return f"No conversation history found for customer {customer_id}"
            
            # Return summary for all customers
            cursor.execute("SELECT * FROM customer_contexts ORDER BY last_discussed DESC")
            customers = cursor.fetchall()
            
            if not customers:
                return "No customer context available."
            
            summary_parts = ["**Customer Context Summary:**"]
            for customer in customers:
                topics = json.loads(customer['topics_discussed']) if customer['topics_discussed'] else []
                recommendations = json.loads(customer['recommendations_given']) if customer['recommendations_given'] else []
                
                summary_parts.append(f"\n**{customer['customer_name'] or customer['customer_id']}:**")
                summary_parts.append(f"- Industry: {customer['industry'] or 'Unknown'}")
                if customer['churn_risk_score']:
                    summary_parts.append(f"- Churn Risk: {customer['churn_risk_score']:.1%}")
                else:
                    summary_parts.append("- Churn Risk: Unknown")
                summary_parts.append(f"- Topics: {', '.join(topics) if topics else 'None'}")
                summary_parts.append(f"- Last Discussed: {customer['last_discussed']}")
            
            return "\n".join(summary_parts)
    
    def get_recent_context(self, session_id: str, max_messages: int = 5) -> str:
        """Get recent conversation context for the agent"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM messages 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (session_id, max_messages))
            recent_messages = cursor.fetchall()
            
            if not recent_messages:
                return "No recent conversation context available."
            
            context_parts = ["**Recent Conversation Context:**"]
            for msg in reversed(recent_messages):  # Reverse to show in chronological order
                role_emoji = "👤" if msg['role'] == "user" else "🤖"
                timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M')
                context_parts.append(f"- {role_emoji} **{msg['role'].title()}** ({timestamp}): {msg['content']}")
            
            return "\n".join(context_parts)
    
    def get_sessions(self) -> List[Dict]:
        """Get list of all sessions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions 
                ORDER BY last_activity DESC
            """)
            sessions = cursor.fetchall()
            return [dict(session) for session in sessions]
    
    def clear_session(self, session_id: str):
        """Clear all messages for a specific session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
    
    def clear_all_memory(self):
        """Clear all memory data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM customer_contexts")
            cursor.execute("DELETE FROM sessions")
            conn.commit()

def create_memory_manager(db_path: str = "chat_memory.db") -> ChatMemory:
    """Factory function to create a memory manager"""
    return ChatMemory(db_path)
