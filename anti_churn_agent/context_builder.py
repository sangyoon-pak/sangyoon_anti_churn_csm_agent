"""
Context Builder for Anti-Churn Agent
Converts customer data into natural language context for LLMs
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from data_loader import DataLoader

class ContextBuilder:
    """Builds natural language context from customer data for LLM analysis"""
    
    def __init__(self, data_loader: DataLoader):
        """Initialize with a data loader instance"""
        self.data_loader = data_loader
    
    def build_customer_context(self, customer_id: str) -> str:
        """Build comprehensive context for a customer"""
        customer_overview = self.data_loader.get_customer_overview(customer_id)
        if not customer_overview:
            return f"Customer {customer_id} not found."
        
        context_parts = []
        
        # Basic customer info
        context_parts.append(self._build_basic_info(customer_id))
        
        # Usage trends
        usage_context = self._build_usage_context(customer_id)
        if usage_context:
            context_parts.append(usage_context)
        
        # Support summary
        support_context = self._build_support_context(customer_id)
        if support_context:
            context_parts.append(support_context)
        
        # Campaign performance
        campaign_context = self._build_campaign_context(customer_id)
        if campaign_context:
            context_parts.append(campaign_context)
        
        # Risk indicators
        risk_context = self._build_risk_context(customer_overview)
        if risk_context:
            context_parts.append(risk_context)
        
        return "\n\n".join(context_parts)
    
    def _build_basic_info(self, customer_id: str) -> str:
        """Build basic customer information context"""
        profile = self.data_loader.get_customer_profile(customer_id)
        if profile is None or profile.empty:
            return f"**Customer Profile:** Customer {customer_id} not found."
        
        return f"""**Customer Profile:**
- **Name:** {profile['customer_name']}
- **Industry:** {profile['industry']}
- **Segment:** {profile['segment']}
- **Account Size:** {profile['account_size']}
- **Annual Revenue:** ${profile['annual_revenue']:,}
- **Contract Value:** ${profile['contract_value']:,}
- **Contract Period:** {profile['contract_start_date'].strftime('%Y-%m-%d')} to {profile['contract_end_date'].strftime('%Y-%m-%d')}
- **Renewal Date:** {profile['renewal_date'].strftime('%Y-%m-%d')}
- **Account Manager:** {profile['account_manager']}
- **Status:** {profile['status']}
- **Churn Risk Score:** {profile['churn_risk_score']:.1%}
- **Notes:** {profile['notes']}"""
    
    def _build_usage_context(self, customer_id: str) -> str:
        """Build usage trends context"""
        usage_trends = self.data_loader.get_customer_usage_trends(customer_id, days=30)
        if usage_trends.empty:
            return "**Usage Data:** No recent usage data available."
        
        # Calculate key metrics
        recent_usage = usage_trends.tail(7)  # Last 7 days
        previous_usage = usage_trends.head(7)  # First 7 days
        
        avg_recent_logins = recent_usage['login_count'].mean()
        avg_previous_logins = previous_usage['login_count'].mean()
        avg_recent_active_users = recent_usage['active_users'].mean()
        avg_previous_active_users = previous_usage['active_users'].mean()
        
        # Calculate decline rates
        login_decline = ((avg_previous_logins - avg_recent_logins) / avg_previous_logins * 100) if avg_previous_logins > 0 else 0
        user_decline = ((avg_previous_active_users - avg_recent_active_users) / avg_previous_active_users * 100) if avg_previous_active_users > 0 else 0
        
        # Feature usage trend
        first_feature_score = usage_trends.iloc[0]['feature_usage_score']
        last_feature_score = usage_trends.iloc[-1]['feature_usage_score']
        feature_decline = ((first_feature_score - last_feature_score) / first_feature_score * 100) if first_feature_score > 0 else 0
        
        return f"""**Usage Trends (Last 30 Days):**
- **Recent Activity:** {avg_recent_logins:.1f} logins/day, {avg_recent_active_users:.1f} active users/day
- **Previous Activity:** {avg_previous_logins:.1f} logins/day, {avg_previous_active_users:.1f} active users/day
- **Login Decline:** {login_decline:.1f}% decrease
- **Active User Decline:** {user_decline:.1f}% decrease
- **Feature Usage Score:** Declined from {first_feature_score:.0f} to {last_feature_score:.0f} ({feature_decline:.1f}% decrease)
- **Current Status:** {'No recent activity' if avg_recent_logins == 0 else 'Low activity' if avg_recent_logins < 5 else 'Moderate activity' if avg_recent_logins < 20 else 'High activity'}"""
    
    def _build_support_context(self, customer_id: str) -> str:
        """Build support tickets context"""
        support_summary = self.data_loader.get_customer_support_summary(customer_id)
        if not support_summary:
            return "**Support Data:** No support tickets found."
        
        # Get recent tickets for more detail
        customer_data = self.data_loader.load_customer_data(customer_id)
        if 'support' not in customer_data:
            return "**Support Data:** No support data available."
        
        support_data = customer_data['support']
        recent_tickets = support_data[support_data['created_date'] >= (datetime.now() - timedelta(days=30))]
        
        # Build ticket details
        ticket_details = []
        for _, ticket in recent_tickets.head(3).iterrows():  # Show last 3 tickets
            status_emoji = "🔴" if ticket['priority'] == 'High' else "🟡" if ticket['priority'] == 'Medium' else "🟢"
            ticket_details.append(f"- {status_emoji} {ticket['subject']} ({ticket['status']}, {ticket['priority']} priority)")
        
        # Calculate open high priority tickets
        open_high_priority = len(support_data[(support_data['status'] == 'Open') & (support_data['priority'] == 'High')])
        
        return f"""**Support Summary:**
- **Total Tickets:** {support_summary['total_tickets']}
- **Open Tickets:** {support_summary['open_tickets']} ({open_high_priority} high priority)
- **Resolved Tickets:** {support_summary['resolved_tickets']}
- **High Priority Tickets:** {support_summary['high_priority_tickets']} ({support_summary['high_priority_tickets'] - open_high_priority} resolved)
- **Recent Tickets (Last 30 Days):** {support_summary['recent_tickets']}
- **Average Sentiment:** {support_summary['avg_sentiment']:.2f} ({'Negative' if support_summary['avg_sentiment'] < -0.3 else 'Neutral' if support_summary['avg_sentiment'] < 0.3 else 'Positive'})
- **Average Resolution Time:** {support_summary['avg_resolution_time']:.1f} hours

**Recent Ticket Details:**
{chr(10).join(ticket_details) if ticket_details else 'No recent tickets'}"""
    
    def _build_campaign_context(self, customer_id: str) -> str:
        """Build campaign performance context"""
        campaign_perf = self.data_loader.get_customer_campaign_performance(customer_id)
        if not campaign_perf:
            return "**Campaign Data:** No campaign data available."
        
        # Get recent campaigns for more detail
        customer_data = self.data_loader.load_customer_data(customer_id)
        if 'campaigns' not in customer_data:
            return "**Campaign Data:** No campaign data available."
        
        campaign_data = customer_data['campaigns']
        recent_campaigns = campaign_data[campaign_data['date_sent'] >= (datetime.now() - timedelta(days=30))]
        
        # Build campaign details
        campaign_details = []
        for _, campaign in recent_campaigns.head(3).iterrows():  # Show last 3 campaigns
            campaign_details.append(f"- {campaign['campaign_name']}: {campaign['conversion_rate']:.1f}% conversion rate")
        
        return f"""**Campaign Performance:**
- **Total Campaigns:** {campaign_perf['total_campaigns']}
- **Average Open Rate:** {campaign_perf['avg_open_rate']:.1%}
- **Average Click Rate:** {campaign_perf['avg_click_rate']:.1%}
- **Average Conversion Rate:** {campaign_perf['avg_conversion_rate']:.1f}%
- **Total Revenue Generated:** ${campaign_perf['total_revenue']:,}
- **Recent Engagement:** {campaign_perf['recent_engagement']} campaigns in last 30 days

**Recent Campaigns:**
{chr(10).join(campaign_details) if campaign_details else 'No recent campaigns'}"""
    
    def _build_risk_context(self, customer_overview: Dict) -> str:
        """Build risk indicators context"""
        profile = self.data_loader.get_customer_profile(customer_overview['customer_id'])
        if profile is None or profile.empty:
            return "**Risk Assessment:** Customer profile not found."
        
        risk_score = profile['churn_risk_score']
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = "CRITICAL"
            risk_emoji = "🔴"
        elif risk_score >= 0.6:
            risk_level = "HIGH"
            risk_emoji = "🟠"
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
            risk_emoji = "🟡"
        else:
            risk_level = "LOW"
            risk_emoji = "🟢"
        
        # Days until renewal
        days_to_renewal = (profile['renewal_date'] - datetime.now()).days
        
        return f"""**Risk Assessment:**
- **Risk Level:** {risk_emoji} {risk_level} ({risk_score:.1%})
- **Days Until Renewal:** {days_to_renewal} days
- **Contract Status:** {'Expired' if days_to_renewal < 0 else 'Expiring Soon' if days_to_renewal < 30 else 'Active'}
- **Account Value:** ${profile['contract_value']:,} annually

**Key Risk Factors:**
- {'High usage decline' if self.data_loader.get_usage_decline_rate(profile['customer_id']) > 50 else 'Moderate usage decline' if self.data_loader.get_usage_decline_rate(profile['customer_id']) > 20 else 'Stable usage'}
- {'Multiple open support tickets' if customer_overview.get('support_summary', {}).get('open_tickets', 0) > 3 else 'Few support issues' if customer_overview.get('support_summary', {}).get('open_tickets', 0) > 0 else 'No support issues'}
- {'Negative support sentiment' if self.data_loader.get_support_sentiment_trend(profile['customer_id']) < -0.3 else 'Neutral support sentiment' if self.data_loader.get_support_sentiment_trend(profile['customer_id']) < 0.3 else 'Positive support sentiment'}"""
    
    def build_focused_context(self, customer_id: str, focus_area: str) -> str:
        """Build context focused on a specific area"""
        if focus_area.lower() in ['usage', 'usage_trends', 'activity']:
            return self._build_usage_context(customer_id)
        elif focus_area.lower() in ['support', 'tickets', 'issues']:
            return self._build_support_context(customer_id)
        elif focus_area.lower() in ['campaigns', 'marketing', 'engagement']:
            return self._build_campaign_context(customer_id)
        elif focus_area.lower() in ['risk', 'churn', 'retention']:
            customer_overview = self.data_loader.get_customer_overview(customer_id)
            return self._build_risk_context(customer_overview) if customer_overview else "Customer not found."
        else:
            return self.build_customer_context(customer_id)
    
    def build_comparison_context(self, customer_ids: List[str]) -> str:
        """Build context comparing multiple customers"""
        if len(customer_ids) < 2:
            return "Need at least 2 customers for comparison."
        
        comparison_parts = ["**Customer Comparison:**"]
        
        for customer_id in customer_ids:
            customer_overview = self.data_loader.get_customer_overview(customer_id)
            if customer_overview:
                comparison_parts.append(f"\n**{customer_overview['customer_name']} ({customer_id}):**")
                comparison_parts.append(f"- Industry: {customer_overview['industry']}")
                comparison_parts.append(f"- Churn Risk: {customer_overview['churn_risk_score']:.1%}")
                comparison_parts.append(f"- Contract Value: ${customer_overview['contract_value']:,}")
                comparison_parts.append(f"- Usage Decline: {self.data_loader.get_usage_decline_rate(customer_id):.1f}%")
        
        return "\n".join(comparison_parts)

# Example usage
if __name__ == "__main__":
    from data_loader import DataLoader
    
    # Initialize
    loader = DataLoader()
    context_builder = ContextBuilder(loader)
    
    # Test context building
    context = context_builder.build_customer_context("ACME001")
    print("Customer Context:")
    print(context)
    
    # Test focused context
    usage_context = context_builder.build_focused_context("ACME001", "usage")
    print("\nUsage Context:")
    print(usage_context)
