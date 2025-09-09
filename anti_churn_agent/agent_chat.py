#!/usr/bin/env python3
"""
Anti-Churn Multi-Agent Chat Interface
Gradio web interface version
"""

import os
import asyncio
import gradio as gr
import uuid
import hashlib
import threading
import time
from typing import List, Dict, Any
from traced_system import TracedMultiAgentSystem
from data_loader import DataLoader
from chat_memory import ChatMemory

class ResponseTimer:
    """Simple response timer for chat interface"""
    
    def __init__(self):
        self.start_time = None
        self.is_running = False
        self.last_duration = None
    
    def start(self):
        """Start the timer"""
        self.start_time = time.time()
        self.is_running = True
        self.last_duration = None
    
    def stop(self):
        """Stop the timer and return duration"""
        if self.is_running and self.start_time:
            self.last_duration = time.time() - self.start_time
            self.is_running = False
            return self.last_duration
        return None
    
    def reset(self):
        """Reset timer to clean slate"""
        self.start_time = None
        self.is_running = False
        self.last_duration = None
    
    def get_status(self):
        """Get current timer status"""
        if self.is_running and self.start_time:
            current_duration = time.time() - self.start_time
            return f"⏱️ {current_duration:.1f}s"
        elif self.last_duration is not None:
            return f"✅ {self.last_duration:.1f}s"
        else:
            return "⏱️ Ready"

class GradioChatInterface:
    """Gradio web chat interface for the anti-churn agent system"""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.memory = ChatMemory()
        self.user_systems = {}  # Store systems per user
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.tool_status = {}  # Store tool status per user
        self.tool_history = {}  # Store tool call history per user
        self.timer = ResponseTimer()  # Response timer instance
    
    def generate_user_id(self, request: gr.Request) -> str:
        """Generate a unique session ID for each browser tab"""
        # Try to get username first (if available)
        username = getattr(request, 'username', None)
        if username:
            # For authenticated users, still create unique sessions per tab
            return f"user_{username}_{uuid.uuid4().hex[:8]}"
        
        # For anonymous users, create a unique session per browser tab
        # Use IP + User-Agent (without port) for stability across requests
        ip = request.client.host
        user_agent = getattr(request, 'headers', {}).get('user-agent', '')
        
        # Create a unique ID that's consistent within a browser but unique across browsers
        # Remove port dependency since ports change between requests
        combined = f"{ip}_{user_agent}"
        session_hash = hashlib.md5(combined.encode()).hexdigest()[:12]
        session_id = f"session_{session_hash}"
        
        # Debug: Print session ID generation
        print(f"DEBUG: Generated session ID: {session_id}")
        print(f"DEBUG: IP: {ip}, User-Agent: {user_agent[:50]}...")
        
        return session_id
    
    def get_or_create_user_system(self, user_id: str):
        """Get or create a system for a specific user"""
        # Debug: Print system lookup
        print(f"DEBUG: Looking for user_id: {user_id}")
        print(f"DEBUG: Current user_systems keys: {list(self.user_systems.keys())}")
        
        if user_id not in self.user_systems:
            if not self.api_key:
                return None
            
            # Create new system for this user
            system = TracedMultiAgentSystem(self.api_key)
            session_id = f"user_{user_id}_{uuid.uuid4().hex[:8]}"
            system.set_session_id(session_id)
            
            # Set up tool call callback for this user
            def tool_callback(tool_name: str, status: str):
                self.tool_status[user_id] = {
                    'tool_name': tool_name,
                    'status': status,
                    'timestamp': time.time()
                }
                
                # Add to tool history
                if user_id not in self.tool_history:
                    self.tool_history[user_id] = []
                
                self.tool_history[user_id].append({
                    'tool_name': tool_name,
                    'status': status,
                    'timestamp': time.time()
                })
                
                # Keep only last 10 tool calls
                if len(self.tool_history[user_id]) > 10:
                    self.tool_history[user_id] = self.tool_history[user_id][-10:]
                
                print(f"Tool call for user {user_id}: {tool_name} - {status}")
            
            system.set_tool_call_callback(tool_callback)
            
            self.user_systems[user_id] = {
                'system': system,
                'session_id': session_id
            }
            self.tool_status[user_id] = {'tool_name': None, 'status': 'idle', 'timestamp': time.time()}
            self.tool_history[user_id] = []
            print(f"DEBUG: Created new system for user_id: {user_id}")
        else:
            print(f"DEBUG: Found existing system for user_id: {user_id}")
        
        return self.user_systems[user_id]
    
    async def process_message(self, message: str, history: List[List[str]], user_id: str = None) -> str:
        """Process a message through the traced multi-agent system"""
        if not user_id:
            user_id = "anonymous"
        
        user_system_data = self.get_or_create_user_system(user_id)
        if not user_system_data:
            return "Error: System not initialized. Please check your OPENAI_API_KEY."
        
        system = user_system_data['system']
        session_id = user_system_data['session_id']
        
        try:
            # Process the message (memory is handled internally by the system)
            result = await system.process_user_query_with_trace(message)
            
            # Let the LLM handle all formatting and response structure
            return result['decision_result']
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            # Add error to system memory
            system.memory.add_message(session_id, "assistant", error_msg)
            return error_msg
    
    def get_memory_summary(self, user_id: str = None) -> str:
        """Get conversation memory summary"""
        if not user_id:
            user_id = "anonymous"
        
        # Debug: Print memory retrieval (remove in production)
        # print(f"DEBUG: Getting memory summary for user_id: {user_id}")
        
        user_system_data = self.get_or_create_user_system(user_id)
        if not user_system_data:
            # print(f"DEBUG: No system data found for user_id: {user_id}")
            return "Memory not available"
        
        try:
            session_id = user_system_data['session_id']
            # print(f"DEBUG: Getting memory for session_id: {session_id}")
            summary = user_system_data['system'].get_conversation_summary()
            # print(f"DEBUG: Memory summary length: {len(summary) if summary else 0}")
            return summary
        except Exception as e:
            # print(f"DEBUG: Error getting memory: {e}")
            return "Memory not available"
    
    def clear_memory(self, user_id: str = None) -> str:
        """Clear conversation memory"""
        if not user_id:
            user_id = "anonymous"
        
        user_system_data = self.get_or_create_user_system(user_id)
        if not user_system_data:
            return "Memory not available"
        
        system = user_system_data['system']
        session_id = user_system_data['session_id']
        
        # Clear the session
        system.memory.clear_session(session_id)
        
        # Generate new session ID
        new_session_id = f"user_{user_id}_{uuid.uuid4().hex[:8]}"
        system.set_session_id(new_session_id)
        user_system_data['session_id'] = new_session_id
        
        return "Memory cleared"
    
    def get_tool_status(self, user_id: str = None) -> str:
        """Get current tool status for a user"""
        if not user_id:
            user_id = "anonymous"
        
        if user_id not in self.tool_status:
            return "🟢 Ready"
        
        status_info = self.tool_status[user_id]
        tool_name = status_info.get('tool_name')
        status = status_info.get('status', 'idle')
        
        if status == 'idle' or not tool_name:
            return "🟢 Ready"
        elif status == 'starting':
            # Show more detailed tool names
            if tool_name == "Agent Processing":
                return "🤖 Agent is thinking..."
            elif tool_name.startswith("get_"):
                return f"🔍 Fetching {tool_name.replace('get_', '').replace('_', ' ')}..."
            elif tool_name.startswith("find_"):
                return f"🔎 Searching {tool_name.replace('find_', '').replace('_', ' ')}..."
            else:
                return f"🔄 Using {tool_name}..."
        elif status == 'completed':
            if tool_name == "Agent Processing":
                return "✅ Agent finished processing"
            else:
                return f"✅ Completed {tool_name}"
        elif status.startswith('error'):
            return f"❌ Error with {tool_name}"
        else:
            return f"🔄 {tool_name}: {status}"
    
    def get_tool_history(self, user_id: str = None) -> str:
        """Get tool call history for a user"""
        if not user_id:
            user_id = "anonymous"
        
        if user_id not in self.tool_history or not self.tool_history[user_id]:
            return "No recent tool activity"
        
        history_lines = ["**Recent Tool Activity:**"]
        for entry in self.tool_history[user_id][-5:]:  # Show last 5 tools
            tool_name = entry['tool_name']
            status = entry['status']
            timestamp = time.strftime('%H:%M:%S', time.localtime(entry['timestamp']))
            
            if status == 'starting':
                if tool_name == "Agent Processing":
                    history_lines.append(f"🤖 {timestamp} - Agent started processing")
                elif tool_name.startswith("get_"):
                    history_lines.append(f"🔍 {timestamp} - Fetching {tool_name.replace('get_', '').replace('_', ' ')}")
                elif tool_name.startswith("find_"):
                    history_lines.append(f"🔎 {timestamp} - Searching {tool_name.replace('find_', '').replace('_', ' ')}")
                else:
                    history_lines.append(f"🔄 {timestamp} - Using {tool_name}")
            elif status == 'completed':
                if tool_name == "Agent Processing":
                    history_lines.append(f"✅ {timestamp} - Agent finished processing")
                else:
                    history_lines.append(f"✅ {timestamp} - Completed {tool_name}")
            elif status.startswith('error'):
                history_lines.append(f"❌ {timestamp} - Error with {tool_name}")
        
        return "\n".join(history_lines)
    
    def create_interface(self):
        """Create the Gradio interface"""
        # Simple CSS for clean interface
        custom_css = """
        /* Clean interface styling */
        .gradio-container .chatbot {
            border-radius: 8px;
        }
        
        /* Hide the "processing" text from Gradio's built-in timer */
        .progress-text {
            display: none !important;
        }
        """
        
        with gr.Blocks(
            title="Anti-Churn Multi-Agent Chat", 
            theme=gr.themes.Soft(),
            css=custom_css
        ) as interface:
            gr.Markdown("# 🤖 Anti-Churn Multi-Agent Chat")
            gr.Markdown("**AI-powered customer success assistant using multi-agent system**")
            
            # Welcome message
            with gr.Row():
                with gr.Column():
                    gr.Markdown("""
                    👋 **Welcome!** I'm your AI customer success assistant. I can help you with:
                    
                    • **Customer Analysis** - Churn risk, performance metrics, usage trends  
                    • **Retention Strategies** - Action plans, implementation advice, best practices
                    • **Business Intelligence** - Data insights, trends, recommendations
                    • **Memory & Context** - I remember our conversations and customer discussions
                    
                    💡 **Pro Tip:** Start with a simple question like "What's the churn risk for ACME001?" or "Show me all customers"
                    """)
            
            with gr.Row():
                with gr.Column(scale=3):
                    # Chat interface
                    chatbot = gr.Chatbot(
                        label="Chat",
                        height=500,
                        show_label=True,
                        type="messages"
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            label="Message",
                            placeholder="Ask about customer churn, retention strategies, or business advice...",
                            scale=4
                        )
                        submit_btn = gr.Button("Send", variant="primary", scale=1)
                    
                    # Quick action buttons
                    with gr.Row():
                        quick_btn1 = gr.Button("📊 List Customers", variant="secondary", size="sm")
                        quick_btn2 = gr.Button("⚠️ High Risk Customers", variant="secondary", size="sm")
                        quick_btn3 = gr.Button("💡 Retention Tips", variant="secondary", size="sm")
                        quick_btn4 = gr.Button("🧠 Show Memory", variant="secondary", size="sm")
                    
                    # Tips section
                    with gr.Accordion("💡 Chat Tips & Examples", open=True):
                        gr.Markdown("""
                        **🚀 Quick Start Examples:**
                        
                        **Customer Analysis:**
                        - "What's the churn risk for ACME001?"
                        - "Show me the profile of TECH002"
                        - "List all customers with high churn risk"
                        - "What are the key issues with FIN001?"
                        
                        **Retention Strategies:**
                        - "How can I reduce churn for ACME001?"
                        - "What retention strategies work for tech companies?"
                        - "Give me an action plan for TECH002"
                        - "How can I improve customer success for FIN001?"
                        
                        **Business Intelligence:**
                        - "What trends do you see in customer usage?"
                        - "Which customers need immediate attention?"
                        - "How can I improve overall retention rates?"
                        - "What are the common churn indicators?"
                        
                        **Data & Memory:**
                        - "Show me all customers"
                        - "What have we discussed about ACME001?"
                        - "Give me a summary of our conversation"
                        - "What recommendations did you make earlier?"
                        """)
                
                with gr.Column(scale=1):
                    # System status and controls
                    gr.Markdown("### 🟢 System Status")
                    status_text = gr.Markdown("✅ **All systems ready**")
                    
                    # Tool status display
                    gr.Markdown("### 🛠️ Tool Status")
                    tool_status_display = gr.Markdown("🟢 Ready", elem_id="tool-status")
                    
                    # Tool history display
                    gr.Markdown("### 📋 Tool History")
                    tool_history_display = gr.Markdown("No recent tool activity", elem_id="tool-history")
                    
                    # Response Timer Display
                    gr.Markdown("### ⏱️ Response Timer")
                    timer_display = gr.Markdown("⏱️ Ready", elem_id="response-timer")
                    
                    # Available tools info
                    with gr.Accordion("🛠️ Available Tools", open=False):
                        gr.Markdown("""
                        **Customer Data Tools:**
                        • Customer profiles & risk scores
                        • Usage patterns & trends
                        • Support ticket analysis
                        • Campaign performance data
                        
                        **AI Tools:**
                        • Decision Agent (analyzes queries)
                        • Evaluator (assesses recommendations)
                        • Web Search (industry research)
                        • Memory System (conversation context)
                        """)
                    
                    gr.Markdown("### 🎛️ Controls")
                    clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary")
                    memory_btn = gr.Button("🧠 Show Memory", variant="secondary")
                    clear_memory_btn = gr.Button("🧹 Clear Memory", variant="secondary")
                    refresh_tool_status_btn = gr.Button("🔄 Refresh Tool Status", variant="secondary")
                    refresh_tool_history_btn = gr.Button("🔄 Refresh History", variant="secondary")
                    
                    # Memory display
                    gr.Markdown("### 💾 Memory")
                    memory_display = gr.Markdown("No memory data")
            
            # Event handlers
            def user_input(message, history):
                return "", history + [{"role": "user", "content": message}]
            
            def bot_response(history, request: gr.Request):
                if not history or not history[-1].get("content"):
                    return history, "🟢 Ready", "No recent tool activity", "⏱️ Ready"
                
                user_message = history[-1]["content"]
                # Generate stable user ID
                user_id = self.generate_user_id(request)
                
                # Start timer
                self.timer.start()
                
                # Process message asynchronously using asyncio.run
                try:
                    response = asyncio.run(self.process_message(user_message, history, user_id))
                except Exception as e:
                    response = f"Error: {str(e)}"
                finally:
                    # Stop timer
                    self.timer.stop()
                
                history.append({"role": "assistant", "content": response})
                tool_status = self.get_tool_status(user_id)
                tool_history = self.get_tool_history(user_id)
                timer_status = self.timer.get_status()
                return history, tool_status, tool_history, timer_status
            
            # Connect events with default processing indicator
            msg.submit(user_input, [msg, chatbot], [msg, chatbot], queue=False).then(
                bot_response, [chatbot], [chatbot, tool_status_display, tool_history_display, timer_display]
            )
            
            submit_btn.click(user_input, [msg, chatbot], [msg, chatbot], queue=False).then(
                bot_response, [chatbot], [chatbot, tool_status_display, tool_history_display, timer_display]
            )
            
            # Quick action button handlers
            def quick_action1():
                return "", [{"role": "user", "content": "Show me all customers"}]
            
            def quick_action2():
                return "", [{"role": "user", "content": "Which customers have high churn risk?"}]
            
            def quick_action3():
                return "", [{"role": "user", "content": "What are the best retention strategies for reducing customer churn?"}]
            
            def quick_action4():
                return "", [{"role": "user", "content": "What have we discussed in our conversation?"}]
            
            quick_btn1.click(quick_action1, outputs=[msg, chatbot], queue=False).then(
                bot_response, [chatbot], [chatbot, tool_status_display, tool_history_display, timer_display]
            )
            
            quick_btn2.click(quick_action2, outputs=[msg, chatbot], queue=False).then(
                bot_response, [chatbot], [chatbot, tool_status_display, tool_history_display, timer_display]
            )
            
            quick_btn3.click(quick_action3, outputs=[msg, chatbot], queue=False).then(
                bot_response, [chatbot], [chatbot, tool_status_display, tool_history_display, timer_display]
            )
            
            quick_btn4.click(quick_action4, outputs=[msg, chatbot], queue=False).then(
                bot_response, [chatbot], [chatbot, tool_status_display, tool_history_display, timer_display]
            )
            
            clear_btn.click(lambda: [], outputs=chatbot)
            
            def get_memory_for_user(request: gr.Request):
                user_id = self.generate_user_id(request)
                return self.get_memory_summary(user_id)
            
            def clear_memory_for_user(request: gr.Request):
                user_id = self.generate_user_id(request)
                return self.clear_memory(user_id)
            
            def get_tool_status_for_user(request: gr.Request):
                user_id = self.generate_user_id(request)
                return self.get_tool_status(user_id)
            
            def get_tool_history_for_user(request: gr.Request):
                user_id = self.generate_user_id(request)
                return self.get_tool_history(user_id)
            
            memory_btn.click(
                get_memory_for_user,
                outputs=memory_display
            )
            
            clear_memory_btn.click(
                clear_memory_for_user,
                outputs=memory_display
            )
            
            refresh_tool_status_btn.click(
                get_tool_status_for_user,
                outputs=tool_status_display
            )
            
            refresh_tool_history_btn.click(
                get_tool_history_for_user,
                outputs=tool_history_display
            )
        
        return interface

def main():
    """Main function to run the Gradio interface"""
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Create and run the Gradio interface
    chat_interface = GradioChatInterface()
    interface = chat_interface.create_interface()
    
    # Launch the interface
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()
