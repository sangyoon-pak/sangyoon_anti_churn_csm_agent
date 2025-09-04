"""
Simple Local Data MCP Server for Anti-Churn Agent
"""

from mcp.server.fastmcp import FastMCP
from data_loader import DataLoader
from context_builder import ContextBuilder
from appier_context import get_appier_context, get_appier_summary

mcp = FastMCP("local-data-server")
data_loader = DataLoader()
context_builder = ContextBuilder(data_loader)

@mcp.tool()
async def get_customer_data(customer_id: str) -> str:
    """Get comprehensive customer data and context by ID"""
    return context_builder.build_customer_context(customer_id)

@mcp.tool()
async def get_high_risk_customers(threshold: float = 0.7) -> str:
    """Get customers with high churn risk"""
    import json
    high_risk = data_loader.get_high_risk_customers(threshold)
    return json.dumps(high_risk, indent=2, default=str)

@mcp.tool()
async def get_customer_list() -> str:
    """Get list of available customer IDs"""
    import json
    customers = data_loader.get_available_customers()
    return json.dumps(customers, indent=2)

@mcp.tool()
async def find_customer_by_name(customer_name: str) -> str:
    """Find customer ID by searching for customer name (case-insensitive)"""
    import json
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
        return json.dumps({"error": f"No customers found matching '{customer_name}'"}, indent=2)
    
    return json.dumps(found_customers, indent=2, default=str)

@mcp.tool()
async def get_customer_usage_trends(customer_id: str, days: int = 30) -> str:
    """Get usage trends for a customer"""
    trends = data_loader.get_customer_usage_trends(customer_id, days)
    return trends.to_json(orient='records', indent=2)

@mcp.tool()
async def get_customer_support_summary(customer_id: str) -> str:
    """Get support ticket summary for a customer"""
    import json
    summary = data_loader.get_customer_support_summary(customer_id)
    return json.dumps(summary, indent=2, default=str)

@mcp.tool()
async def get_customer_campaigns(customer_id: str) -> str:
    """Get campaign data and performance for a specific customer"""
    import json
    customer_data = data_loader.load_customer_data(customer_id)
    if 'campaigns' not in customer_data or customer_data['campaigns'].empty:
        return json.dumps({"error": "No campaign data available for this customer"}, indent=2)
    
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
    
    return json.dumps(result, indent=2, default=str)

@mcp.tool()
async def get_customer_campaign_performance(customer_id: str) -> str:
    """Get campaign performance summary for a customer"""
    import json
    performance = data_loader.get_customer_campaign_performance(customer_id)
    return json.dumps(performance, indent=2, default=str)

@mcp.tool()
async def get_appier_solutions_context() -> str:
    """Get comprehensive context about Appier Marketing Solution products and capabilities"""
    return get_appier_context()

@mcp.tool()
async def get_appier_solutions_summary() -> str:
    """Get a concise summary of Appier Marketing Solution for quick reference"""
    return get_appier_summary()

if __name__ == "__main__":
    mcp.run(transport='stdio')
