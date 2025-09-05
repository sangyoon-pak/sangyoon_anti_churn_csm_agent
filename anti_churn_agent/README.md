# Anti-Churn Multi-Agent System

A simplified, interactive multi-agent system for customer success management and churn prevention, built with OpenAI Agent framework and MCP servers.

## 🚀 Overview

This system uses a **decision-making agent** with an integrated **evaluator tool** to help Customer Success Managers (CSMs) analyze customer data, assess churn risk, and provide actionable recommendations:

1. **🤔 Decision Making Agent** - Analyzes queries and makes strategic decisions
2. **✅ Evaluator Tool** - Integrated tool that assesses recommendation quality

## 🏗️ Architecture

### Multi-Agent System
- **OpenAI Agent Framework** - Uses `openai-agents` for agent orchestration and tracing
- **Async Processing** - All operations use async/await for better performance
- **MCP Servers** - Model Context Protocol servers for data access and web search
- **Tool Integration** - Evaluator works as a tool within the decision agent
- **Appier Context Integration** - Comprehensive knowledge of Appier Marketing Solution products and capabilities

### MCP Servers
- **Local Data Server** - Access to customer data via `data_loader.py` and `context_builder.py`
- **Web Search Server** - External research via Brave API (public MCP server)

### Appier Marketing Solution Integration
- **Product Knowledge** - Comprehensive understanding of AIQUA, CrossX, BotBonnie, and Appier Data
- **Industry Expertise** - Deep knowledge of e-commerce, financial services, gaming, and healthcare markets
- **Solution Recommendations** - Agent suggests specific Appier products based on customer needs
- **Best Practices** - Leverages Appier's proven customer success methodologies

### Chat Memory System
- **SQLite Database** - Persistent conversation memory across chat sessions
- **Session Management** - Unique session IDs for different chat instances
- **Customer Context Tracking** - Remembers customer discussions, topics, and recommendations
- **Conversation History** - Maintains context for more relevant responses
- **Memory Persistence** - Data survives application restarts

### Tool Visibility System
- **Real-time Tool Status** - Shows when tools are being executed in the UI
- **Tool Call Tracking** - Monitors tool execution with start/completion/error status
- **User-specific Status** - Each user session has independent tool status tracking
- **Visual Indicators** - Clear status indicators (🔄 running, ✅ completed, ❌ error)
- **Tool Call Logging** - Console logging for debugging and monitoring

### Data Components
- **Data Loader** - Loads customer data from CSV files
- **Context Builder** - Converts data into natural language context

## 📁 Project Structure

```
anti_churn_agent/
├── agent_chat.py                   # Main chat interface
├── appier_context.py               # Appier-specific context and knowledge
├── chat_memory.py                  # Chat memory system
├── chat_memory.db                  # SQLite database for conversation memory
├── context_builder.py              # Context generation
├── data_loader.py                  # Customer data loading
├── local_data_server.py            # MCP server for data access
├── traced_system.py                # Traced multi-agent system
├── tracers.py                      # Trace ID generation
├── data/customers/                 # Customer data (CSV files)
│   ├── ACME001/                   # Customer data directories
│   ├── FIN001/
│   └── TECH002/
├── notebooks/                      # Jupyter notebooks for development
│   ├── brainstorm.ipynb
│   └── notebook.ipynb
├── pyproject.toml                  # Project dependencies
├── uv.lock                         # Dependency lock file
└── README.md                       # This file
```

## 🛠️ Installation

1. **Clone and setup environment:**
```bash
cd anti_churn_agent
uv sync  # Install dependencies
```

2. **Set environment variables:**
```bash
export OPENAI_API_KEY="your-openai-api-key"
export BRAVE_API_KEY="your-brave-api-key"  # Optional for web search
```

3. **Run the system:**
```bash
python agent_chat.py          # Main chat interface (Recommended)
# or
python traced_system.py       # Command line
```

## 🚀 Usage

### Chat Interface (Recommended)
```bash
python agent_chat.py
```

This starts the main chat interface where you can:
- Ask questions about customers: `"What's the churn risk for ACME001?"`
- Get recommendations: `"How can I help TECH002 reduce their churn risk?"`
- Access customer data and analysis
- See multi-agent analysis with tracing
- **Monitor tool execution in real-time** - See when tools are being called and their status

### Command Line Interface
```bash
python traced_system.py
```

This runs the traced multi-agent system directly with detailed output.

### Development and Testing
```bash
# Use the existing notebooks for development and testing
jupyter notebook notebooks/brainstorm.ipynb
jupyter notebook notebooks/notebook.ipynb
```

### Example Queries
- `"What's the churn risk for ACME001?"`
- `"How can I help TECH002 reduce their churn risk?"`
- `"What are the key issues with FIN001?"`
- `"Show me high-risk customers"`
- `"What industry trends affect our customers?"`

## 🤖 Agent Roles

### Decision Making Agent
- **Purpose**: Analyzes customer queries and makes strategic decisions
- **Capabilities**:
  - Understands customer context and problems
  - Determines what data and research is needed
  - Makes decisions based on evidence and best practices
  - Provides clear, actionable recommendations
  - **Strategic Web Search**: Only uses web search for high churn risk clients (>70%)

### Evaluator Tool
- **Purpose**: Integrated tool that assesses recommendation quality
- **Capabilities**:
  - Rates recommendations on a scale of 1-10
  - Assesses feasibility and potential risks
  - Provides feedback for improvement
  - Determines pass/fail status
  - **UI Behavior**: Only shows evaluation results when recommendations FAIL

## 🛠️ Tool Visibility Feature

The system now includes real-time tool visibility to show users what's happening behind the scenes:

### Features
- **Real-time Status Display** - Shows current tool being executed in the UI
- **Visual Indicators**:
  - 🟢 **Ready** - System is idle and ready
  - 🔄 **Using [Tool Name]...** - Tool is currently executing
  - ✅ **Completed [Tool Name]** - Tool finished successfully
  - ❌ **Error with [Tool Name]** - Tool encountered an error
- **User-specific Tracking** - Each user session maintains independent tool status
- **Manual Refresh** - Refresh button to update tool status
- **Console Logging** - Detailed tool execution logs for debugging

### How It Works
1. When a user sends a message, the system processes it through the multi-agent framework
2. As tools are called (customer data access, web search, evaluation), the UI shows real-time status
3. Users can see exactly what the agent is doing instead of waiting in the dark
4. Each browser session maintains its own tool status independently

### Testing with Multiple Users
- **User A (Chrome)**: Can see their own tool execution status
- **User B (Firefox)**: Has completely separate tool status tracking
- **Independent Sessions**: No interference between different user sessions

## 🔧 MCP Servers

### Local Data Server
Provides access to customer data through tools:
- `get_customer_data` - Get comprehensive customer data by ID
- `get_high_risk_customers` - Find high-risk customers
- `get_customer_list` - List available customers
- `find_customer_by_name` - Search for customers by name (e.g., "ACME Corp")
- `get_customer_usage_trends` - Analyze usage patterns
- `get_customer_support_summary` - Review support tickets
- `get_customer_campaigns` - Get detailed campaign data and performance
- `get_customer_campaign_performance` - Get campaign performance summary
- `get_appier_solutions_context` - Get comprehensive Appier product information
- `get_appier_solutions_summary` - Get concise Appier company summary

### Memory Management Tools
- **Memory Display** - Shows conversation summary and customer context
- **Memory Clear** - Resets conversation memory for fresh start
- **Session Tracking** - Maintains separate memory for different chat sessions

### Web Search Server (Brave API)
Provides external research capabilities via public MCP server:
- **Strategic Use**: Only activated for high churn risk clients (>70%)
- **Research Focus**: Industry trends, best practices, market conditions
- **Efficiency**: Avoids unnecessary web searches for low-risk situations

## 📊 Data Format

Customer data is stored in CSV files under `data/customers/{customer_id}/`:
- `profile.csv` - Customer profile and contract information
- `usage.csv` - Usage patterns and activity data
- `support.csv` - Support ticket history and sentiment
- `campaigns.csv` - Marketing campaign performance

## 🧪 Testing

### Development and Testing
Use the existing Jupyter notebooks for development and testing:
```bash
jupyter notebook notebooks/brainstorm.ipynb
jupyter notebook notebooks/notebook.ipynb
```

These notebooks can be used for:
- **System Testing** - Test the multi-agent system functionality
- **Tool Integration** - Verify all tools work together properly
- **Data Analysis** - Explore customer data and patterns
- **Development** - Prototype new features and improvements

## 🔄 Workflow

1. **User Query** → CSM asks a question about a customer
2. **Decision Agent** → Analyzes the query and determines approach
3. **Data Gathering** → Accesses customer data and web research (if high-risk)
4. **Decision Agent** → Makes final recommendation with research
5. **Evaluator Tool** → Assesses recommendation quality internally
6. **Result** → Returns analysis with evaluation feedback only on FAIL

## 🎯 Key Features

- **Chat Interface** - Interactive chat interface for customer analysis
- **Integrated Evaluator Tool** - Quality assessment built into decision process
- **Strategic Web Search** - Only used when needed for high-risk clients
- **Data-Driven Analysis** - Based on real customer data
- **Async Processing** - Efficient handling of multiple operations
- **MCP Integration** - Extensible data and tool access
- **OpenAI Agents Tracing** - Comprehensive debugging and monitoring
- **Clean Architecture** - Minimal, maintainable codebase
- **Appier-Specific Recommendations** - Tailored suggestions using Appier's AI-powered solutions
- **Industry Expertise Integration** - Deep knowledge of target markets and use cases
- **Persistent Chat Memory** - SQLite-based conversation context and customer tracking
- **Session Management** - Separate memory for different chat instances

## 🚨 Requirements

- Python 3.10+
- OpenAI API key
- Brave API key (optional, for web search)
- Customer data in CSV format

## 🔮 Future Enhancements

- **CRM Integration** - Connect to real CRM systems
- **Real-time Data** - Live data feeds instead of CSV files
- **Advanced Analytics** - Machine learning for churn prediction
- **Automated Actions** - Direct integration with customer success tools
- **Multi-language Support** - Support for different languages

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.