"""
Traced Multi-Agent System for Anti-Churn Agent
Uses OpenAI Agents framework for proper tracing and debugging
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Any, Optional
from contextlib import AsyncExitStack

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# OpenAI Agents imports
from agents import Agent, Tool, Runner, OpenAIChatCompletionsModel, trace
from agents.mcp import MCPServerStdio
from tracers import make_trace_id

from data_loader import DataLoader
from context_builder import ContextBuilder
from appier_context import get_appier_context, get_appier_summary
from chat_memory import ChatMemory

class TracedMultiAgentSystem:
    """Multi-agent system with proper OpenAI Agents tracing"""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        from openai import AsyncOpenAI
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.model = OpenAIChatCompletionsModel(
            model="gpt-4o-mini",
            openai_client=self.openai_client
        )
        self.memory = ChatMemory()
        self.current_session_id = None
    
    def get_model(self):
        """Get the model for agents"""
        return self.model
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation"""
        session_id = self.get_session_id()
        return self.memory.get_conversation_summary(session_id)
    
    def get_customer_context_summary(self, customer_id: str = None) -> str:
        """Get summary of customer context"""
        return self.memory.get_customer_context_summary(customer_id)
    
    def clear_memory(self):
        """Clear the conversation memory"""
        self.memory.clear_memory()
    
    def set_session_id(self, session_id: str):
        """Set the current session ID for memory management"""
        self.current_session_id = session_id
    
    def get_session_id(self) -> str:
        """Get the current session ID, create one if none exists"""
        if not self.current_session_id:
            from datetime import datetime
            self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.current_session_id
    
    async def get_decision_agent(self, mcp_servers) -> Agent:
        """Create the decision making agent"""
        decision_instructions = f"""You are a friendly, conversational anti-churn customer success agent for Appier Marketing Solution. Your role is to:

        1. **Be conversational and helpful** - respond naturally to greetings and casual conversation
        2. **Analyze business queries** when customers ask about churn risk, retention strategies, or business analysis
        3. **Provide appropriate responses** based on the query type and context, leveraging Appier's expertise
        4. **Use customer data tools** when needed for specific customer inquiries
        5. **Keep responses concise** and relevant to what the customer actually asked
        6. **Leverage Appier's solutions** when making recommendations (AIQUA, CrossX, BotBonnie, Appier Data)
        7. **Remember conversation context** - use previous conversation history to provide more relevant responses

        **Response Guidelines:**

        **For casual conversation (greetings, thanks, etc.):**
        - Be friendly and conversational
        - Briefly introduce yourself as an anti-churn agent
        - Ask how you can help them today
        - Keep it short and natural

        **For business queries (churn risk, customer analysis, etc.):**
        - Provide strategic analysis and recommendations
        - Use customer data tools when relevant
        - Give actionable next steps
        - Be thorough but not overly verbose

        **For simple questions:**
        - Answer directly and concisely
        - Don't overcomplicate simple requests
        - Focus on what the customer actually needs

        **Available Tools:**
        - Customer data access tools (use when analyzing specific customers)
        - Web search tools (use only for high-risk client research)
        - Evaluation tool (ONLY use when providing strategic recommendations or business advice)

        **When to use the Evaluator tool:**
        - ✅ Strategic recommendations (churn reduction strategies, retention plans)
        - ✅ Business advice (action plans, implementation strategies)
        - ❌ Simple data requests (customer lists, basic information)
        - ❌ Greetings and casual conversation
        - ❌ Basic questions that don't require strategic planning

        **Remember:** Match your response style and length to the customer's query. Don't give a complex business analysis for a simple greeting! Only evaluate recommendations when they are strategic in nature.

        **Appier Marketing Solution Context:**
        {get_appier_summary()}

        **Key Appier Solutions to Leverage:**
        - **AIQUA**: For customer engagement, retention, and churn prevention strategies
        - **CrossX**: For cross-screen marketing campaigns and audience targeting
        - **BotBonnie**: For conversational marketing and customer support automation
        - **Appier Data**: For customer insights, predictive modeling, and data-driven decisions

        **When making recommendations, always consider how Appier's solutions can help:**
        - Suggest specific Appier products that address the customer's needs
        - Reference Appier's expertise in the customer's industry
        - Provide examples of how similar customers have succeeded with Appier
        - Emphasize Appier's AI-powered approach and competitive advantages"""
        
        return Agent(
            name="DecisionAgent",
            instructions=decision_instructions,
            model=self.get_model(),
            mcp_servers=mcp_servers
        )

    async def get_evaluator_tool(self, mcp_servers) -> Tool:
        """Create the evaluator as a tool"""
        evaluator_instructions = f"""You are an evaluator tool responsible for assessing the quality and effectiveness of customer success recommendations for Appier Marketing Solution. Your role is to:

        1. **Evaluate recommendation quality** based on Appier's best practices and industry expertise
        2. **Assess feasibility** of proposed actions using Appier's solutions
        3. **Identify potential risks** and unintended consequences
        4. **Rate recommendations** on a scale of 1-10
        5. **Provide feedback** for improvement, considering Appier's capabilities

        **Evaluation Criteria:**
        - **Relevance:** Does the recommendation address the core issue using Appier's solutions?
        - **Feasibility:** Can this be implemented with Appier's platform and resources?
        - **Impact:** Will this significantly improve customer retention leveraging Appier's AI capabilities?
        - **Risk:** Are there potential negative consequences or limitations with Appier's approach?
        - **Timing:** Is this the right time for this action given Appier's implementation timeline?
        - **Appier Alignment:** Does the recommendation properly leverage Appier's products and expertise?

        **Evaluation Scale:**
        - 9-10: Excellent - Highly recommended, low risk, high impact
        - 7-8: Good - Recommended with minor adjustments
        - 5-6: Acceptable - Needs improvements but generally sound
        - 3-4: Poor - Significant issues, needs major revision
        - 1-2: Unacceptable - High risk, low impact, or infeasible

        **Response Format:**
        - Overall rating (1-10)
        - Pass/Fail decision
        - Key strengths and weaknesses
        - Specific improvement suggestions considering Appier's capabilities
        - Final recommendation with Appier solution alignment

        **Appier Context for Evaluation:**
        {get_appier_summary()}

        **Remember:** Always evaluate whether recommendations properly leverage Appier's AI-powered marketing solutions and industry expertise."""
        
        evaluator_agent = Agent(
            name="EvaluatorTool",
            instructions=evaluator_instructions,
            model=self.get_model(),
            mcp_servers=mcp_servers
        )
        
        return evaluator_agent.as_tool(
            tool_name="Evaluator",
            tool_description="This tool evaluates the quality and feasibility of STRATEGIC customer success recommendations and business advice. Only use this tool when you are providing strategic recommendations, retention strategies, or business action plans. Do NOT use for simple data requests or basic questions."
        )

    async def process_user_query_with_trace(self, user_query: str) -> Dict[str, Any]:
        """Process user query with OpenAI Agents tracing"""
        trace_name = "anti-churn-analysis"
        trace_id = make_trace_id("anti_churn")
        
        with trace(trace_name, trace_id=trace_id):
            return await self._process_query_internal(user_query)

    async def _process_query_internal(self, user_query: str) -> Dict[str, Any]:
        """Internal method to process the query"""
        async with AsyncExitStack() as stack:
            # Start MCP servers
            mcp_servers = []
            
            # Start local data server
            local_server = await stack.enter_async_context(
                MCPServerStdio({
                    "command": "python",
                    "args": ["local_data_server.py"]
                })
            )
            mcp_servers.append(local_server)
            
            # Start Brave search server (if API key is available)
            try:
                # Get Brave API key from environment
                brave_api_key = os.getenv("BRAVE_API_KEY")
                if brave_api_key:
                    brave_server = await stack.enter_async_context(
                        MCPServerStdio({
                            "command": "npx",
                            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                            "env": {"BRAVE_API_KEY": brave_api_key}
                        })
                    )
                    mcp_servers.append(brave_server)
                else:
                    pass  # Brave search not available
            except Exception as e:
                pass  # Brave search server not available
            
            # Create decision agent with evaluator tool
            decision_agent = await self.get_decision_agent(mcp_servers)
            evaluator_tool = await self.get_evaluator_tool(mcp_servers)
            
            # Add evaluator tool to decision agent
            decision_agent.tools = [evaluator_tool]
            
            # Get conversation context from memory
            session_id = self.get_session_id()
            conversation_context = self.memory.get_recent_context(session_id, max_messages=5)
            
            # Process query with decision agent
            decision_message = f"""User Query: {user_query}

**Conversation Context:**
{conversation_context}

Please analyze this query and provide an appropriate response. IMPORTANT: Only use the evaluator tool when you are providing strategic recommendations or business advice. For simple data requests, greetings, or basic questions, do NOT use the evaluator tool.

Use the conversation context to provide more relevant and contextual responses."""
            
            decision_response = await Runner.run(decision_agent, decision_message, max_turns=5)
            decision_result = decision_response.final_output if decision_response.final_output else "No response from decision agent"
            
            # Extract evaluation result if available
            evaluation_result = None
            if hasattr(decision_response, 'messages') and decision_response.messages:
                for message in decision_response.messages:
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        for tool_call in message.tool_calls:
                            if tool_call.name == "Evaluator":
                                evaluation_result = tool_call.output
                                break
            
            # Determine if evaluation shows FAIL
            is_fail = False
            if evaluation_result:
                # Check if evaluation contains "FAIL" or low rating
                evaluation_text = str(evaluation_result).lower()
                if "fail" in evaluation_text or any(phrase in evaluation_text for phrase in ["unacceptable", "poor", "significant issues"]):
                    is_fail = True
            
            # Update memory with this conversation
            session_id = self.get_session_id()
            self.memory.add_message(
                session_id=session_id,
                role="user",
                content=user_query,
                customer_context=None  # Will be extracted by the agent if needed
            )
            
            self.memory.add_message(
                session_id=session_id,
                role="assistant",
                content=decision_result,
                evaluation_result=evaluation_result if is_fail else None
            )
            
            return {
                "decision_result": decision_result,
                "evaluation_result": evaluation_result if is_fail else None,  # Only show evaluation on FAIL
                "is_fail": is_fail,
                "trace_id": make_trace_id("anti_churn")
            }
    

