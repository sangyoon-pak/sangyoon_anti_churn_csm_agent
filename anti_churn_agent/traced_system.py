"""
Traced Multi-Agent System for Anti-Churn Agent
Uses OpenAI Agents framework for proper tracing and debugging
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict, List, Any, Optional, Callable
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
        self.tool_call_callback: Optional[Callable[[str, str], None]] = None  # (tool_name, status)
    
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
    
    def set_tool_call_callback(self, callback: Callable[[str, str], None]):
        """Set callback function to be called when tools are executed"""
        self.tool_call_callback = callback
    
    def _notify_tool_call(self, tool_name: str, status: str):
        """Notify about tool call status"""
        if self.tool_call_callback:
            try:
                self.tool_call_callback(tool_name, status)
            except Exception as e:
                print(f"Error in tool call callback: {e}")
    
    def _read_tool_calls_from_log(self, start_time: float):
        """Read tool calls from the log file since start_time"""
        tool_calls = []
        try:
            if os.path.exists("tool_calls.log"):
                with open("tool_calls.log", "r") as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            if log_entry["timestamp"] >= start_time:
                                tool_calls.append(log_entry)
                        except (json.JSONDecodeError, KeyError):
                            continue
        except Exception as e:
            print(f"Error reading tool log: {e}")
        return tool_calls

    async def _run_agent_with_tool_tracking(self, agent, message: str, max_turns: int = 5):
        """Run agent with tool call tracking"""
        
        # Clear the tool log file to start fresh
        try:
            if os.path.exists("tool_calls.log"):
                os.remove("tool_calls.log")
        except Exception as e:
            print(f"Error clearing tool log: {e}")
        
        # Start tracking
        start_time = time.time()
        self._notify_tool_call("Agent Processing", "starting")
        
        try:
            # Run the agent
            response = await Runner.run(agent, message, max_turns=max_turns)
            
            # Read tool calls from the log file
            tool_calls = self._read_tool_calls_from_log(start_time)
            for tool_call in tool_calls:
                self._notify_tool_call(tool_call["tool_name"], tool_call["status"])
            
            # Track individual tool calls from the response (for direct tools like Evaluator and MCP tools)
            
            # Check raw_responses for tool calls (this is where RunResult stores the actual responses)
            if hasattr(response, 'raw_responses') and response.raw_responses:
                for i, raw_response in enumerate(response.raw_responses):
                    # Check if this raw response has messages with tool calls
                    if hasattr(raw_response, 'messages') and raw_response.messages:
                        for j, msg in enumerate(raw_response.messages):
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for k, tool_call in enumerate(msg.tool_calls):
                                    tool_name = tool_call.name
                                    
                                    # Map MCP tool names to user-friendly names
                                    friendly_name = self._get_friendly_tool_name(tool_name)
                                    
                                    # Check if this tool was already tracked from the log file
                                    already_tracked = any(tc["tool_name"] == friendly_name and tc["status"] == "completed" for tc in tool_calls)
                                    
                                    if not already_tracked:
                                        # Only show completed status since the tool has already finished
                                        self._notify_tool_call(friendly_name, "completed")
            
            # Also check for tool calls in other response attributes
            for attr_name in ['tool_calls', 'tool_call_results', 'steps', 'turns', 'new_items']:
                if hasattr(response, attr_name):
                    attr_value = getattr(response, attr_name)
                    if attr_value and isinstance(attr_value, list):
                        for item in attr_value:
                            if hasattr(item, 'name'):
                                friendly_name = self._get_friendly_tool_name(item.name)
                                self._notify_tool_call(friendly_name, "completed")
                    
                    # Also check for nested tool calls in the response
                    if attr_value and isinstance(attr_value, list):
                        for item in attr_value:
                            if hasattr(item, 'tool_calls') and item.tool_calls:
                                for tool_call in item.tool_calls:
                                    if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name'):
                                        tool_name = tool_call.function.name
                                        friendly_name = self._get_friendly_tool_name(tool_name)
                                        self._notify_tool_call(friendly_name, "completed")
            
            # Removed heuristic-based web search detection to prevent false positives
            
            # Check raw_responses for ResponseFunctionToolCall format
            if hasattr(response, 'raw_responses') and response.raw_responses:
                for raw_response in response.raw_responses:
                    if hasattr(raw_response, 'output') and raw_response.output:
                        for output_item in raw_response.output:
                            if hasattr(output_item, 'name') and 'brave_web_search' in str(output_item.name):
                                # Check if we already tracked web search
                                web_search_tracked = any(tc["tool_name"] == "Web Search" and tc["status"] == "completed" for tc in tool_calls)
                                if not web_search_tracked:
                                    self._notify_tool_call("Web Search", "completed")
            
            # Check for search-related tools in response attributes
            for attr_name in dir(response):
                if not attr_name.startswith('_'):
                    try:
                        attr_value = getattr(response, attr_name)
                        if attr_value and isinstance(attr_value, list):
                            for item in attr_value:
                                if hasattr(item, 'name') and 'search' in str(item.name).lower():
                                    friendly_name = self._get_friendly_tool_name(item.name)
                                    self._notify_tool_call(friendly_name, "completed")
                    except Exception:
                        pass  # Skip attributes that can't be accessed
            
            # Check if web search was already tracked
            web_search_tracked = any(tc["tool_name"] == "Web Search" and tc["status"] == "completed" for tc in tool_calls)
            
            self._notify_tool_call("Agent Processing", "completed")
            return response
            
        except Exception as e:
            self._notify_tool_call("Agent Processing", f"error: {str(e)}")
            raise
    
    def _wrap_tool_with_notification(self, tool: Tool) -> Tool:
        """Wrap a tool to add notification functionality"""
        # Check if tool has call attribute (for direct tools)
        if hasattr(tool, 'call'):
            original_call = tool.call
            
            async def wrapped_call(*args, **kwargs):
                self._notify_tool_call(tool.name, "starting")
                try:
                    result = await original_call(*args, **kwargs)
                    self._notify_tool_call(tool.name, "completed")
                    return result
                except Exception as e:
                    self._notify_tool_call(tool.name, f"error: {str(e)}")
                    raise
            
            # Create a new tool with the wrapped call method
            wrapped_tool = Tool(
                name=tool.name,
                description=tool.description,
                call=wrapped_call
            )
            return wrapped_tool
        else:
            # For MCP tools, just return the original tool
            # The notification will be handled by the MCP server logging
            return tool

    def _wrap_mcp_server_with_tracking(self, mcp_server, server_name: str):
        """Wrap an MCP server to track tool calls"""
        # Create a wrapper class that intercepts tool calls
        class MCPTrackingWrapper:
            def __init__(self, original_server, name, callback):
                self.original_server = original_server
                self.name = name
                self.callback = callback
                self.tool_call_active = False
                # Copy all attributes from the original server
                for attr in dir(original_server):
                    if not attr.startswith('_') and not callable(getattr(original_server, attr)):
                        setattr(self, attr, getattr(original_server, attr))
            
            def __getattr__(self, name):
                # Delegate to the original server
                original_attr = getattr(self.original_server, name)
                
                # If it's a callable method, wrap it to track tool calls
                if callable(original_attr):
                    async def wrapped_method(*args, **kwargs):
                        # Only track actual tool execution, not metadata operations
                        should_track = (
                            name in ['call_tool', 'execute_tool', 'run_tool'] or
                            (name.startswith('call_') and 'tool' in name.lower()) or
                            (name.startswith('execute_') and 'tool' in name.lower())
                        )
                        
                        # Don't track list operations, metadata calls, or simple queries
                        should_not_track = (
                            'list' in name.lower() or
                            'get' in name.lower() or
                            'describe' in name.lower() or
                            'info' in name.lower() or
                            'metadata' in name.lower() or
                            name in ['list_tools', 'get_tools', 'describe_tools']
                        )
                        
                        if should_track and not should_not_track:
                            if not self.tool_call_active:
                                self.tool_call_active = True
                                self.callback(self.name, "starting")
                            try:
                                result = await original_attr(*args, **kwargs)
                                if self.tool_call_active:
                                    self.tool_call_active = False
                                    self.callback(self.name, "completed")
                                return result
                            except Exception as e:
                                if self.tool_call_active:
                                    self.tool_call_active = False
                                    self.callback(self.name, f"error: {str(e)}")
                                raise
                        else:
                            return await original_attr(*args, **kwargs)
                    
                    return wrapped_method
                else:
                    return original_attr
        
        return MCPTrackingWrapper(mcp_server, server_name, self._notify_tool_call)
    
    def _get_friendly_tool_name(self, tool_name: str) -> str:
        """Map raw tool names to user-friendly names"""
        # Web search tools from Brave MCP server
        if any(keyword in tool_name.lower() for keyword in ['search', 'brave', 'web']):
            return "Web Search"
        
        # Customer data tools
        if any(keyword in tool_name.lower() for keyword in ['customer', 'data', 'profile', 'usage', 'campaign', 'support']):
            return "Customer Data"
        
        # Appier context tools
        if any(keyword in tool_name.lower() for keyword in ['appier', 'context', 'solutions']):
            return "Appier Context"
        
        # Evaluator tool
        if 'evaluator' in tool_name.lower():
            return "Evaluator"
        
        # Memory tools
        if any(keyword in tool_name.lower() for keyword in ['memory', 'conversation', 'summary']):
            return "Memory"
        
        # Default: return the original name
        return tool_name

    async def get_decision_agent(self, mcp_servers) -> Agent:
        """Create the decision making agent"""
        decision_instructions = f"""You are a friendly anti-churn customer success agent for Appier Marketing Solution.

        **CORE RESPONSIBILITIES:**
        1. Help customers with churn risk analysis and retention strategies
        2. Provide business insights using available tools
        3. Leverage Appier's solutions (AIQUA, CrossX, BotBonnie, AIRIS) in recommendations

        **TOOL USAGE RULES:**
        - **For tool listing requests** ("list all tools", "what tools do you have", "what can you do") → List all available tools without using any tools
        - **For "show me all customers" or "list all customers"** → Use get_customer_list() tool
        - **For "show me high-risk customers" or "which customers have high churn risk"** → Use get_high_risk_customers() tool
        - **For specific customer requests** ("tell me about ACME001", "customer details for FIN001") → Use get_customer_data() tool
        - **For contextual follow-up requests** ("how about other customers", "what about the rest", "analyze the others") → Use get_customer_list() first, then get_customer_data() for each remaining customer
        - **For retention strategy requests** ("best retention strategies", "how to reduce churn") → FIRST generate your own recommendations, THEN use evaluator to assess them
        - **For market research requests** ("industry trends", "market insights") → Use web search
        - **For strategic advice requests** ("recommendations", "action plans") → FIRST generate your own strategic recommendations, THEN use evaluator to assess them
        - **For casual conversation** (greetings, thanks) → Respond conversationally without tools

        **AVAILABLE TOOLS:**
        - **Customer Data Tools:** get_customer_data, get_customer_list, get_high_risk_customers, get_customer_usage_trends, get_customer_support_summary, get_customer_campaigns, find_customer_by_name
        - **Appier Context Tools:** get_appier_solutions_context, get_appier_solutions_summary  
        - **Strategic Tools:** Evaluator (for strategic recommendations), Web Search (for market research)

        **Appier Context:**
        {get_appier_summary()}

        **Key Appier Solutions:**
        - **AIQUA**: Customer engagement and retention
        - **CrossX**: Cross-screen marketing campaigns
        - **BotBonnie**: Conversational marketing and support
        - **AIRIS**: CDP product for Customer insights and predictive modeling"""
        
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

        **Response Format (JSON):**
        You must respond with a valid JSON object containing:
        {
            "rating": <number 1-10>,
            "pass": <boolean true/false>,
            "reasoning": "<explanation of the decision>",
            "strengths": ["<strength 1>", "<strength 2>", ...],
            "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
            "improvements": ["<improvement 1>", "<improvement 2>", ...],
            "final_recommendation": "<final recommendation with Appier solution alignment>"
        }

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
            tool_description="This tool evaluates the quality and feasibility of STRATEGIC customer success recommendations and business advice. It returns a JSON response with a clear pass/fail decision. Use this tool AFTER you have generated your own detailed recommendations to assess their quality. Do NOT use for simple data requests or basic questions."
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
                    # Add Brave server directly - tool calls will be tracked via response messages
                    mcp_servers.append(brave_server)
                else:
                    pass  # Brave search not available
            except Exception as e:
                pass  # Brave search server not available
            
            # Create decision agent with evaluator tool
            decision_agent = await self.get_decision_agent(mcp_servers)
            evaluator_tool = await self.get_evaluator_tool(mcp_servers)
            
            # Wrap tools with notification functionality
            wrapped_evaluator_tool = self._wrap_tool_with_notification(evaluator_tool)
            
            # Add wrapped evaluator tool to decision agent
            decision_agent.tools = [wrapped_evaluator_tool]
            
            # Get conversation context from memory (reduced to prevent context pollution)
            session_id = self.get_session_id()
            conversation_context = self.memory.get_recent_context(session_id, max_messages=2)  # Reduced from 5 to 2
            
            
            # Process query with decision agent
            decision_message = f"""User Query: {user_query}

**Recent Context (Last 2 messages only):**
{conversation_context}

**IMPORTANT: Focus on the CURRENT user query above. Do not be influenced by previous conversation topics unless directly relevant to the current request.**

Please analyze this query and provide an appropriate response. 

**CRITICAL INSTRUCTIONS:**
1. **DO NOT use any tools for casual conversation, greetings, or simple questions**
2. **For "what did I just say" or similar questions, just answer directly from the conversation context above**
3. **For greetings like "hi", "hihi", "hello", just respond conversationally without any tools**
4. **USE tools when the user asks for specific data, customer information, or business analysis**
5. **For requests like "show me customers", "list customers", "which customers have high risk" - USE the appropriate tools**
6. **When asked about specific customers (by code or name), use get_customer_data with the customer_id parameter to fetch full details**
7. **For customer codes like FIN001, ACME001, TECH002, call get_customer_data(customer_id="FIN001")**
8. **For contextual follow-up requests like "how about other customers", "what about the rest", "analyze the others" - FIRST use get_customer_list() to see all customers, then use get_customer_data() for each remaining customer not yet analyzed**
9. **For web research requests like "research on the web", "web search", "current market trends" - USE the web search tool**
10. **When analyzing customer issues, proactively suggest and use web search for market context and trends**
11. **IMPORTANT: For strategic recommendations - FIRST generate your own detailed recommendations, THEN use the evaluator tool to assess them**
12. **For simple data requests, greetings, or basic questions, do NOT use the evaluator tool**
13. **You must respond to the ACTUAL user query provided above**

Use the conversation context to provide more relevant and contextual responses."""
            
            # Run agent with tool tracking and automatic retry on evaluator failure
            max_retries = 2
            retry_count = 0
            decision_response = None
            decision_result = None
            evaluation_result = None
            is_fail = False
            
            while retry_count <= max_retries:
                # Run agent with tool tracking
                decision_response = await self._run_agent_with_tool_tracking(decision_agent, decision_message, max_turns=5)
                decision_result = decision_response.final_output if decision_response.final_output else "No response from decision agent"
                
                # Extract evaluation result
                evaluation_result = None
                if hasattr(decision_response, 'messages') and decision_response.messages:
                    for message in decision_response.messages:
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            for tool_call in message.tool_calls:
                                if tool_call.name == "Evaluator":
                                    evaluation_result = tool_call.output
                
                # Determine if evaluation shows FAIL
                is_fail = False
                if evaluation_result:
                    try:
                        # Try to parse as JSON first
                        import json
                        evaluation_json = json.loads(str(evaluation_result))
                        is_fail = not evaluation_json.get("pass", True)  # Default to pass if not specified
                    except (json.JSONDecodeError, TypeError):
                        # Fallback to text parsing if JSON parsing fails
                        evaluation_text = str(evaluation_result).lower()
                        if "fail" in evaluation_text or any(phrase in evaluation_text for phrase in ["unacceptable", "poor", "significant issues"]):
                            is_fail = True
                
                # If evaluation passed or no evaluation was done, break the retry loop
                if not is_fail:
                    break
                
                # If evaluation failed and we haven't exceeded max retries, retry
                retry_count += 1
                if retry_count <= max_retries:
                    # Notify about the retry
                    self._notify_tool_call("Agent Retry", f"attempt {retry_count}")
                    # Modify the decision message to include feedback about the previous failure
                    decision_message = f"""User Query: {user_query}

**Recent Context (Last 2 messages only):**
{conversation_context}

**PREVIOUS ATTEMPT FAILED EVALUATION:**
{evaluation_result}

**IMPORTANT: Focus on the CURRENT user query above. Do not be influenced by previous conversation topics unless directly relevant to the current request.**

Please analyze this query and provide an improved response. The previous response failed evaluation, so please address the issues mentioned above.

**CRITICAL INSTRUCTIONS:**
1. **DO NOT use any tools for casual conversation, greetings, or simple questions**
2. **For "what did I just say" or similar questions, just answer directly from the conversation context above**
3. **For greetings like "hi", "hihi", "hello", just respond conversationally without any tools**
4. **USE tools when the user asks for specific data, customer information, or business analysis**
5. **For requests like "show me customers", "list customers", "which customers have high risk" - USE the appropriate tools**
6. **When asked about specific customers (by code or name), use get_customer_data with the customer_id parameter to fetch full details**
7. **For customer codes like FIN001, ACME001, TECH002, call get_customer_data(customer_id="FIN001")**
8. **For contextual follow-up requests like "how about other customers", "what about the rest", "analyze the others" - FIRST use get_customer_list() to see all customers, then use get_customer_data() for each remaining customer not yet analyzed**
9. **For web research requests like "research on the web", "web search", "current market trends" - USE the web search tool**
10. **When analyzing customer issues, proactively suggest and use web search for market context and trends**
11. **IMPORTANT: For strategic recommendations - FIRST generate your own detailed recommendations, THEN use the evaluator tool to assess them**
12. **For simple data requests, greetings, or basic questions, do NOT use the evaluator tool**
13. **You must respond to the ACTUAL user query provided above**

Use the conversation context to provide more relevant and contextual responses."""
            
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
    

