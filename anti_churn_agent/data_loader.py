"""
Data Loader for Anti-Churn Agent
Handles loading and processing customer data from CSV files
"""

import pandas as pd
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import glob

class DataLoader:
    """Loads and manages customer-specific mock data for the anti-churn agent"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the data loader with the data directory path"""
        self.data_dir = data_dir
        self.customers_dir = os.path.join(data_dir, "customers")
        self.customer_data = {}
        
    def get_available_customers(self) -> List[str]:
        """Get list of available customer IDs"""
        if not os.path.exists(self.customers_dir):
            return []
        
        # Find all customer directories
        customer_dirs = [d for d in os.listdir(self.customers_dir) 
                        if os.path.isdir(os.path.join(self.customers_dir, d))]
        
        return sorted(customer_dirs)
    
    def load_customer_data(self, customer_id: str) -> Dict[str, pd.DataFrame]:
        """Load all data for a specific customer"""
        if customer_id in self.customer_data:
            return self.customer_data[customer_id]
        
        customer_data = {}
        customer_dir = os.path.join(self.customers_dir, customer_id)
        
        if not os.path.exists(customer_dir):
            return customer_data
        
        # Load profile data
        profile_file = os.path.join(customer_dir, "profile.csv")
        if os.path.exists(profile_file):
            try:
                customer_data['profile'] = pd.read_csv(profile_file)
                # Convert date columns
                date_columns = ['contract_start_date', 'contract_end_date', 'renewal_date', 
                              'last_contact_date', 'next_contact_date']
                for col in date_columns:
                    if col in customer_data['profile'].columns:
                        try:
                            customer_data['profile'][col] = pd.to_datetime(customer_data['profile'][col])
                        except Exception as e:
                            print(f"Warning: Could not parse dates in column {col}: {e}")
            except Exception as e:
                print(f"Error loading profile for {customer_id}: {e}")
        
        # Load campaign data
        campaign_file = os.path.join(customer_dir, "campaigns.csv")
        if os.path.exists(campaign_file):
            try:
                customer_data['campaigns'] = pd.read_csv(campaign_file)
                customer_data['campaigns']['date_sent'] = pd.to_datetime(customer_data['campaigns']['date_sent'])
            except Exception as e:
                print(f"Error loading campaigns for {customer_id}: {e}")
        
        # Load support data
        support_file = os.path.join(customer_dir, "support.csv")
        if os.path.exists(support_file):
            try:
                customer_data['support'] = pd.read_csv(support_file)
                customer_data['support']['created_date'] = pd.to_datetime(customer_data['support']['created_date'])
                customer_data['support']['resolved_date'] = pd.to_datetime(customer_data['support']['resolved_date'])
            except Exception as e:
                print(f"Error loading support for {customer_id}: {e}")
        
        # Load usage data
        usage_file = os.path.join(customer_dir, "usage.csv")
        if os.path.exists(usage_file):
            try:
                customer_data['usage'] = pd.read_csv(usage_file)
                customer_data['usage']['date'] = pd.to_datetime(customer_data['usage']['date'])
            except Exception as e:
                print(f"Error loading usage for {customer_id}: {e}")
        
        self.customer_data[customer_id] = customer_data
        return customer_data
    
    def get_customer_profile(self, customer_id: str) -> Optional[pd.Series]:
        """Get customer profile information"""
        customer_data = self.load_customer_data(customer_id)
        if 'profile' in customer_data and not customer_data['profile'].empty:
            return customer_data['profile'].iloc[0]
        return None
    
    def get_high_risk_customers(self, threshold: float = 0.7) -> List[Dict]:
        """Get customers with high churn risk scores"""
        high_risk_customers = []
        available_customers = self.get_available_customers()
        
        for customer_id in available_customers:
            profile = self.get_customer_profile(customer_id)
            if profile is not None and profile['churn_risk_score'] >= threshold:
                high_risk_customers.append({
                    'customer_id': customer_id,
                    'customer_name': profile['customer_name'],
                    'churn_risk_score': profile['churn_risk_score'],
                    'industry': profile['industry'],
                    'segment': profile['segment'],
                    'contract_value': profile['contract_value']
                })
        
        # Sort by churn risk score (highest first)
        high_risk_customers.sort(key=lambda x: x['churn_risk_score'], reverse=True)
        return high_risk_customers
    
    def get_customer_usage_trends(self, customer_id: str, days: int = 30) -> pd.DataFrame:
        """Get usage trends for a customer over the specified number of days"""
        customer_data = self.load_customer_data(customer_id)
        if 'usage' not in customer_data or customer_data['usage'].empty:
            return pd.DataFrame()
        
        usage_data = customer_data['usage']
        # Get the most recent date and filter by days
        latest_date = usage_data['date'].max()
        start_date = latest_date - timedelta(days=days)
        
        return usage_data[usage_data['date'] >= start_date].sort_values('date')
    
    def get_customer_support_summary(self, customer_id: str) -> Dict:
        """Get a summary of support tickets for a customer"""
        customer_data = self.load_customer_data(customer_id)
        if 'support' not in customer_data or customer_data['support'].empty:
            return {}
        
        support_data = customer_data['support']
        
        return {
            "total_tickets": len(support_data),
            "open_tickets": len(support_data[support_data['status'] == 'Open']),
            "resolved_tickets": len(support_data[support_data['status'] == 'Resolved']),
            "avg_sentiment": support_data['sentiment_score'].mean(),
            "avg_resolution_time": support_data['resolution_time_hours'].mean(),
            "high_priority_tickets": len(support_data[support_data['priority'] == 'High']),
            "recent_tickets": len(support_data[support_data['created_date'] >= 
                                             (datetime.now() - timedelta(days=30))])
        }
    
    def get_customer_campaign_performance(self, customer_id: str) -> Dict:
        """Get campaign performance summary for a customer"""
        customer_data = self.load_customer_data(customer_id)
        if 'campaigns' not in customer_data or customer_data['campaigns'].empty:
            return {}
        
        campaign_data = customer_data['campaigns']
        
        return {
            "total_campaigns": len(campaign_data),
            "avg_open_rate": campaign_data['email_opened'].sum() / campaign_data['email_sent'].sum(),
            "avg_click_rate": campaign_data['email_clicked'].sum() / campaign_data['email_sent'].sum(),
            "avg_conversion_rate": campaign_data['conversion_rate'].mean(),
            "total_revenue": campaign_data['revenue_generated'].sum(),
            "recent_engagement": len(campaign_data[campaign_data['date_sent'] >= 
                                                 (datetime.now() - timedelta(days=30))])
        }
    
    def get_customer_overview(self, customer_id: str) -> Dict:
        """Get a comprehensive overview of a customer"""
        profile = self.get_customer_profile(customer_id)
        if profile is None:
            return {}
        
        return {
            "customer_id": customer_id,
            "customer_name": profile['customer_name'],
            "industry": profile['industry'],
            "segment": profile['segment'],
            "account_size": profile['account_size'],
            "contract_value": profile['contract_value'],
            "churn_risk_score": profile['churn_risk_score'],
            "renewal_date": profile['renewal_date'],
            "account_manager": profile['account_manager'],
            "status": profile['status'],
            "notes": profile['notes'],
            "support_summary": self.get_customer_support_summary(customer_id),
            "campaign_performance": self.get_customer_campaign_performance(customer_id),
            "usage_trends": self.get_customer_usage_trends(customer_id)
        }
    
    def get_usage_decline_rate(self, customer_id: str, days: int = 30) -> float:
        """Calculate the rate of usage decline for a customer"""
        usage_data = self.get_customer_usage_trends(customer_id, days)
        if usage_data.empty or len(usage_data) < 2:
            return 0.0
        
        # Calculate decline in feature usage score
        first_score = usage_data.iloc[0]['feature_usage_score']
        last_score = usage_data.iloc[-1]['feature_usage_score']
        
        if first_score == 0:
            return 0.0
        
        decline_rate = (first_score - last_score) / first_score
        return max(0.0, decline_rate)  # Ensure non-negative
    
    def get_support_sentiment_trend(self, customer_id: str) -> float:
        """Get the average sentiment of recent support tickets"""
        customer_data = self.load_customer_data(customer_id)
        if 'support' not in customer_data or customer_data['support'].empty:
            return 0.0
        
        support_data = customer_data['support']
        # Get tickets from last 30 days
        recent_tickets = support_data[support_data['created_date'] >= 
                                    (datetime.now() - timedelta(days=30))]
        
        if recent_tickets.empty:
            return 0.0
        
        return recent_tickets['sentiment_score'].mean()

# Example usage
if __name__ == "__main__":
    # Initialize data loader
    loader = DataLoader()
    
    # Get available customers
    customers = loader.get_available_customers()
    print(f"Available customers: {customers}")
    
    # Get high-risk customers
    high_risk = loader.get_high_risk_customers(threshold=0.7)
    print(f"Found {len(high_risk)} high-risk customers:")
    for customer in high_risk:
        print(f"  - {customer['customer_name']}: {customer['churn_risk_score']:.2f}")
    
    # Get customer overview
    if customers:
        customer_overview = loader.get_customer_overview(customers[0])
        print(f"\nCustomer overview for {customers[0]}: {customer_overview['customer_name']}")
        print(f"Churn risk score: {customer_overview['churn_risk_score']}")
        print(f"Usage decline rate: {loader.get_usage_decline_rate(customers[0]):.2%}")
        print(f"Recent support sentiment: {loader.get_support_sentiment_trend(customers[0]):.2f}")
