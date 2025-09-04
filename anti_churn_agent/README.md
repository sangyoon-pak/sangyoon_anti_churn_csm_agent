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

### Data Components
- **Data Loader** - Loads customer data from CSV files
- **Context Builder** - Converts data into natural language context

## 📁 Project Structure

```
anti_churn_agent/
├── data_loader.py                  # Customer data loading
├── context_builder.py              # Context generation
├── local_data_server.py            # Simple MCP server
├── traced_system.py                # Traced multi-agent system
├── tracers.py                      # Trace ID generation
├── gradio_traced_chat.py           # Web interface (Gradio)
├── create_testing_notebook.py      # Generate testing notebook
├── quick_test.py                   # Quick functionality test
├── data/customers/                 # Customer data (CSV files)
├── notebooks/                      # Testing & development
├── pyproject.toml                  # Project dependencies
├── mcp_config.json                 # MCP configuration
├── README.md                       # This file
├── HOW_TO_RUN.md                   # Running guide
└── start.sh                        # Setup script
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
python gradio_traced_chat.py  # Web interface (Recommended)
# or
python traced_system.py       # Command line
```

## 🚀 Usage

### Web Interface (Recommended)
```bash
python gradio_traced_chat.py
```

This starts a beautiful web interface at `http://localhost:7860` where you can:
- Ask questions about customers: `"What's the churn risk for ACME001?"`
- Get recommendations: `"How can I help TECH002 reduce their churn risk?"`
- View available customers in the sidebar
- See real-time multi-agent analysis with tracing

### Command Line Interface
```bash
python traced_system.py
```

This runs the traced multi-agent system directly with detailed output.

### Quick Testing
```bash
python quick_test.py  # Test basic functionality
```

### Comprehensive Testing
```bash
python create_testing_notebook.py  # Generate testing notebook
jupyter notebook notebooks/agent_tool_testing.ipynb  # Run tests
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

### Quick Test
```bash
python quick_test.py
```

### Comprehensive Testing
Use the generated notebook for thorough testing:
```bash
python create_testing_notebook.py
jupyter notebook notebooks/agent_tool_testing.ipynb
```

Tests include:
- **Evaluator Tool Integration** - Verify evaluator works as a tool
- **Web Search Strategy** - Test web search only for high-risk clients
- **Tool Coordination** - Ensure all tools work together properly
- **Error Handling** - Test edge cases and error scenarios
- **Performance** - Measure response times and quality

## 🔄 Workflow

1. **User Query** → CSM asks a question about a customer
2. **Decision Agent** → Analyzes the query and determines approach
3. **Data Gathering** → Accesses customer data and web research (if high-risk)
4. **Decision Agent** → Makes final recommendation with research
5. **Evaluator Tool** → Assesses recommendation quality internally
6. **Result** → Returns analysis with evaluation feedback only on FAIL

## 🎯 Key Features

- **Beautiful Web Interface** - Modern Gradio interface with real-time chat
- **Integrated Evaluator Tool** - Quality assessment built into decision process
- **Strategic Web Search** - Only used when needed for high-risk clients
- **Smart UI Behavior** - Evaluation results hidden for PASS cases
- **Data-Driven Analysis** - Based on real customer data
- **Async Processing** - Efficient handling of multiple operations
- **MCP Integration** - Extensible data and tool access
- **OpenAI Agents Tracing** - Comprehensive debugging and monitoring
- **Ultra-Clean Architecture** - Minimal, maintainable codebase
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