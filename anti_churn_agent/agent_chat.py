#!/usr/bin/env python3
"""
Anti-Churn Multi-Agent Chat Interface
Gradio web interface version
"""

import os
import asyncio
import gradio as gr
from typing import List, Dict, Any
from traced_system import TracedMultiAgentSystem
from data_loader import DataLoader
from chat_memory import ChatMemory

class GradioChatInterface:
    """Gradio web chat interface for the anti-churn agent system"""
    
    def __init__(self):
        self.system = None
        self.data_loader = DataLoader()
        self.memory = ChatMemory()
        self.session_id = None
        self.setup_system()
    
    def setup_system(self):
        """Setup the traced multi-agent system"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.system = TracedMultiAgentSystem(api_key)
            # Set session ID for memory
            self.session_id = f"gradio_session_{id(self)}"
            if self.system:
                self.system.set_session_id(self.session_id)
    
    async def process_message(self, message: str, history: List[List[str]]) -> str:
        """Process a message through the traced multi-agent system"""
        if not self.system:
            return "Error: System not initialized. Please check your OPENAI_API_KEY."
        
        try:
            # Add user message to memory
            self.memory.add_message(self.session_id, "user", message)
            
            # Process the message
            result = await self.system.process_user_query_with_trace(message)
            
            # Add assistant response to memory
            response = result['decision_result']
            self.memory.add_message(self.session_id, "assistant", response)
            
            # Let the LLM handle all formatting and response structure
            return response
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            self.memory.add_message(self.session_id, "assistant", error_msg)
            return error_msg
    
    def get_memory_summary(self) -> str:
        """Get conversation memory summary"""
        if not self.system or not self.session_id:
            return "Memory not available"
        try:
            return self.system.get_conversation_summary()
        except:
            return "Memory not available"
    
    def clear_memory(self) -> str:
        """Clear conversation memory"""
        if self.session_id:
            self.memory.clear_session(self.session_id)
            # Generate new session ID
            self.session_id = f"gradio_session_{id(self)}"
            if self.system:
                self.system.set_session_id(self.session_id)
        return "Memory cleared"
    
    def create_interface(self):
        """Create the Gradio interface"""
        with gr.Blocks(title="Anti-Churn Multi-Agent Chat", theme=gr.themes.Soft()) as interface:
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
                    
                    # Memory display
                    gr.Markdown("### 💾 Memory")
                    memory_display = gr.Markdown("No memory data")
            
            # Event handlers
            def user_input(message, history):
                return "", history + [{"role": "user", "content": message}]
            
            def bot_response(history):
                if not history or not history[-1].get("content"):
                    return history
                
                user_message = history[-1]["content"]
                # Process message asynchronously using asyncio.run
                try:
                    response = asyncio.run(self.process_message(user_message, history))
                except Exception as e:
                    response = f"Error: {str(e)}"
                
                history.append({"role": "assistant", "content": response})
                return history
            
            # Connect events
            msg.submit(user_input, [msg, chatbot], [msg, chatbot], queue=False).then(
                bot_response, chatbot, chatbot
            )
            
            submit_btn.click(user_input, [msg, chatbot], [msg, chatbot], queue=False).then(
                bot_response, chatbot, chatbot
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
                bot_response, chatbot, chatbot
            )
            
            quick_btn2.click(quick_action2, outputs=[msg, chatbot], queue=False).then(
                bot_response, chatbot, chatbot
            )
            
            quick_btn3.click(quick_action3, outputs=[msg, chatbot], queue=False).then(
                bot_response, chatbot, chatbot
            )
            
            quick_btn4.click(quick_action4, outputs=[msg, chatbot], queue=False).then(
                bot_response, chatbot, chatbot
            )
            
            clear_btn.click(lambda: [], outputs=chatbot)
            
            memory_btn.click(
                self.get_memory_summary,
                outputs=memory_display
            )
            
            clear_memory_btn.click(
                self.clear_memory,
                outputs=memory_display
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
