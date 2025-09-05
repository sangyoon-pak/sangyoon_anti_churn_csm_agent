"""
Simple Local Data MCP Server for Anti-Churn Agent
"""

from mcp.server.fastmcp import FastMCP
from data_loader import DataLoader
from context_builder import ContextBuilder
from appier_context import get_appier_context, get_appier_summary
import json

mcp = FastMCP("local-data-server")
data_loader = DataLoader()
context_builder = ContextBuilder(data_loader)

# Global tool call tracking
tool_call_tracker = None
import os
import json
import time

def set_tool_call_tracker(tracker):
    """Set the tool call tracker function"""
    global tool_call_tracker
    tool_call_tracker = tracker

def notify_tool_call(tool_name: str, status: str):
    """Notify about tool call status"""
    if tool_call_tracker:
        try:
            tool_call_tracker(tool_name, status)
        except Exception as e:
            print(f"Error in tool call tracker: {e}")
    print(f"🔧 MCP Tool: {tool_name} - {status}")
    
    # Write to shared file for cross-process communication
    try:
        tool_log_file = "tool_calls.log"
        with open(tool_log_file, "a") as f:
            log_entry = {
                "timestamp": time.time(),
                "tool_name": tool_name,
                "status": status
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Error writing tool log: {e}")

@mcp.tool()
async def get_customer_data(customer_id: str) -> str:
    """Get comprehensive customer data and context by ID"""
    notify_tool_call("get_customer_data", "starting")
    try:
        result = context_builder.build_customer_context(customer_id)
        notify_tool_call("get_customer_data", "completed")
        return result
    except Exception as e:
        notify_tool_call("get_customer_data", f"error: {str(e)}")
        raise

@mcp.tool()
async def get_high_risk_customers(threshold: float = 0.7) -> str:
    """Get customers with high churn risk"""
    notify_tool_call("get_high_risk_customers", "starting")
    try:
        high_risk = data_loader.get_high_risk_customers(threshold)
        result = json.dumps(high_risk, indent=2, default=str)
        notify_tool_call("get_high_risk_customers", "completed")
        return result
    except Exception as e:
        notify_tool_call("get_high_risk_customers", f"error: {str(e)}")
        raise

@mcp.tool()
async def get_customer_list() -> str:
    """Get list of available customer IDs"""
    notify_tool_call("get_customer_list", "starting")
    try:
        customers = data_loader.get_available_customers()
        result = json.dumps(customers, indent=2)
        notify_tool_call("get_customer_list", "completed")
        return result
    except Exception as e:
        notify_tool_call("get_customer_list", f"error: {str(e)}")
        raise

@mcp.tool()
async def find_customer_by_name(customer_name: str) -> str:
    """Find customer ID by searching for customer name (case-insensitive)"""
    notify_tool_call("find_customer_by_name", "starting")
    try:
        customers = data_loader.get_available_customers()
        
        found_customers = []
        for customer_id in customers:
            profile = data_loader.get_customer_profile(customer_id)
            if profile is not None and customer_name.lower() in profile['customer_name'].lower():
                found_customers.append({
                    "customer_id": customer_id,
                    "customer_name": profile['customer_name'],
                    "industry": profile['industry'],
                    "churn_risk_score": profile['churn_risk_score']
                })
        
        if not found_customers:
            result = json.dumps({"error": f"No customers found matching '{customer_name}'"}, indent=2)
        else:
            result = json.dumps(found_customers, indent=2, default=str)
        
        notify_tool_call("find_customer_by_name", "completed")
        return result
    except Exception as e:
        notify_tool_call("find_customer_by_name", f"error: {str(e)}")
        raise

@mcp.tool()
async def get_customer_usage_trends(customer_id: str, days: int = 30) -> str:
    """Get usage trends for a customer"""
    notify_tool_call("get_customer_usage_trends", "starting")
    try:
        trends = data_loader.get_customer_usage_trends(customer_id, days)
        result = trends.to_json(orient='records', indent=2)
        notify_tool_call("get_customer_usage_trends", "completed")
        return result
    except Exception as e:
        notify_tool_call("get_customer_usage_trends", f"error: {str(e)}")
        raise

@mcp.tool()
async def get_customer_support_summary(customer_id: str) -> str:
    """Get support ticket summary for a customer"""
    notify_tool_call("get_customer_support_summary", "starting")
    try:
        summary = data_loader.get_customer_support_summary(customer_id)
        result = json.dumps(summary, indent=2, default=str)
        notify_tool_call("get_customer_support_summary", "completed")
        return result
    except Exception as e:
        notify_tool_call("get_customer_support_summary", f"error: {str(e)}")
        raise

@mcp.tool()
async def get_customer_campaigns(customer_id: str) -> str:
    """Get campaign data and performance for a specific customer"""
    notify_tool_call("get_customer_campaigns", "starting")
    try:
        customer_data = data_loader.load_customer_data(customer_id)
        if 'campaigns' not in customer_data or customer_data['campaigns'].empty:
            result = json.dumps({"error": "No campaign data available for this customer"}, indent=2)
        else:
            campaigns = customer_data['campaigns'].copy()
            # Convert datetime to string for JSON serialization
            campaigns['date_sent'] = campaigns['date_sent'].dt.strftime('%Y-%m-%d')
            
            # Sort by date (most recent first)
            campaigns = campaigns.sort_values('date_sent', ascending=False)
            
            result = {
                "customer_id": customer_id,
                "total_campaigns": len(campaigns),
                "campaigns": campaigns.to_dict('records')
            }
            result = json.dumps(result, indent=2, default=str)
        
        notify_tool_call("get_customer_campaigns", "completed")
        return result
    except Exception as e:
        notify_tool_call("get_customer_campaigns", f"error: {str(e)}")
        raise

@mcp.tool()
async def get_customer_campaign_performance(customer_id: str) -> str:
    """Get campaign performance summary for a customer"""
    notify_tool_call("get_customer_campaign_performance", "starting")
    try:
        performance = data_loader.get_customer_campaign_performance(customer_id)
        result = json.dumps(performance, indent=2, default=str)
        notify_tool_call("get_customer_campaign_performance", "completed")
        return result
    except Exception as e:
        notify_tool_call("get_customer_campaign_performance", f"error: {str(e)}")
        raise

@mcp.tool()
async def get_appier_solutions_context() -> str:
    """Get comprehensive context about Appier Marketing Solution products and capabilities"""
    notify_tool_call("get_appier_solutions_context", "starting")
    try:
        result = get_appier_context()
        notify_tool_call("get_appier_solutions_context", "completed")
        return result
    except Exception as e:
        notify_tool_call("get_appier_solutions_context", f"error: {str(e)}")
        raise

@mcp.tool()
async def get_appier_solutions_summary() -> str:
    """Get a concise summary of Appier Marketing Solution for quick reference"""
    notify_tool_call("get_appier_solutions_summary", "starting")
    try:
        result = get_appier_summary()
        notify_tool_call("get_appier_solutions_summary", "completed")
        return result
    except Exception as e:
        notify_tool_call("get_appier_solutions_summary", f"error: {str(e)}")
        raise

if __name__ == "__main__":
    mcp.run(transport='stdio')
