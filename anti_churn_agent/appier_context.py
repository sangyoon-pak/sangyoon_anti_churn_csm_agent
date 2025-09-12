"""
Appier Marketing Solution Context
Provides comprehensive information about Appier for the anti-churn agent
"""

APPIER_CONTEXT = """
# Appier Marketing Solution - Company Context & CSM Playbook

## Company Overview
**Appier** is a leading AI-powered marketing technology company that helps businesses drive growth through intelligent customer acquisition and retention solutions. Founded in 2013, Appier specializes in cross-screen marketing automation and AI-driven customer insights.
**Agent's Role:** Your function is to act as an expert CSM assistant. Use this document to connect customer problems, identified through your data tools, with specific Appier solutions to prevent churn.

## Core Products & Solutions

### 1. AIQUA (Customer Engagement & Retention)
- **Purpose**: AI-powered customer engagement platform to re-engage users and increase Customer Lifetime Value (CLV).
- **Key Features**:
  - Predictive customer behavior modeling
  - Personalized content recommendations
  - Multi-channel campaign automation
  - Customer lifecycle management
- **Use Cases**: Customer retention, upsell/cross-sell, churn prevention
- **🚨 Key Churn Signals for this Product:**
  - Data from `get_customer_usage_trends` shows declining daily/monthly active users or low feature adoption.
  - Data from `get_customer_campaign_performance` shows low Click-Through Rates (CTR) or conversion rates.
  - The customer has no clear automated onboarding or win-back strategies.
- **✅ Recommended Actions for CSMs:**
  - **If usage is low:** "Propose an automated 'Win-Back' campaign using AIQUA's multi-channel journeys (Push + Email) for inactive users."
  - **If engagement is poor:** "Suggest implementing personalized content/product recommendations on their website or app using AIQUA's AI."

### 2. BotBonnie (Conversational Marketing)
- **Purpose**: Chatbot and conversational marketing platform to improve customer satisfaction and operational efficiency.
- **Key Features**:
  - AI-powered chatbot creation
  - Multi-platform messaging integration
  - Lead qualification and nurturing
  - Customer support automation
- **Use Cases**: Lead generation, customer support, engagement
- **🚨 Key Churn Signals for this Product:**
  - `get_customer_support_summary` shows a high volume of repetitive, low-level tickets.
  - Sentiment analysis in `support.csv` is consistently negative, indicating slow response times.
  - The customer needs 24/7 support without increasing headcount.
- **✅ Recommended Actions for CSMs:**
  - **If support volume is high:** "Deploy a BotBonnie support chatbot to instantly answer the top 80% of common customer questions, freeing up human agents."
  - **If lead conversion is a problem:** "Create a lead qualification bot with BotBonnie to engage website visitors and schedule demos."

### 3. AIRIS (Customer Data Intelligence)
- **Purpose**: Customer data platform (CDP) and analytics to create a 360-degree customer view, which is foundational to any retention strategy.
- **Key Features**:
  - Customer behavior analysis
  - Predictive modeling
  - Data-driven insights
  - Integration with marketing tools
- **Use Cases**: Customer insights, campaign optimization, strategic planning
- **🚨 Key Churn Signals for this Product:**
  - The customer expresses confusion about their data or mentions that their marketing, sales, and support data are in different systems ("data silos").
  - The customer uses broad, ineffective audience segmentation for their campaigns.
  - They cannot identify their most valuable customer segments.
- **✅ Recommended Actions for CSMs:**
  - **If data is siloed:** "Position AIRIS as the 'single source of truth' to unify their disparate data sources, enabling a full customer journey view."
  - **If segmentation is weak:** "Propose a 'Customer Persona Discovery' project using AIRIS to identify their most profitable segments."

## Target Industries & Markets
(Context: Use this to understand if a customer's performance lags behind their industry peers.)

### Primary Industries
- **E-commerce & Retail**: Fashion, electronics, home goods
- **Financial Services**: Banking, insurance, fintech
- **Travel & Hospitality**: Airlines, hotels, booking platforms
- **Gaming & Entertainment**: Mobile games, streaming services
- **Healthcare**: Pharmaceuticals, medical devices, wellness

### Geographic Markets
- **Asia-Pacific**: Japan, Taiwan, Singapore, Hong Kong, Australia
- **Southeast Asia**: Thailand, Vietnam, Indonesia, Malaysia, Philippines
- **Global Expansion**: North America, Europe, Latin America

## Competitive Advantages
(Context: Use these points to reinforce the value of Appier when making a recommendation.)

### 1. AI & Machine Learning
- Proprietary AI algorithms for customer behavior prediction
- Real-time optimization and learning
- Advanced segmentation and targeting capabilities

### 2. Cross-Screen Expertise
- Deep understanding of multi-device user journeys
- Seamless cross-platform campaign management
- Advanced attribution modeling

### 3. Data Privacy & Compliance
- GDPR, CCPA, and regional privacy compliance
- First-party data focus
- Transparent data handling practices

### 4. Local Market Knowledge
- Strong presence in Asian markets
- Cultural and regional expertise
- Local partnership networks

## Customer Success Best Practices

### 1. Onboarding & Implementation
- **Phase 1**: Platform setup and integration (2-4 weeks)
- **Phase 2**: Campaign configuration and testing (1-2 weeks)
- **Phase 3**: Optimization and scaling (ongoing)

### 2. Success Metrics
- **Retention**: Customer lifetime value (CLV) improvement
- **Engagement**: Click-through rates, conversion rates
- **Efficiency**: Cost per acquisition (CPA) reduction
- **Growth**: Revenue increase, market share expansion

### 3. Common Use Cases
- **New Customer Acquisition**: Targeted advertising campaigns
- **Customer Retention**: Personalized engagement strategies
- **Upsell/Cross-sell**: Recommendation engines
- **Brand Awareness**: Multi-channel brand campaigns

## Industry-Specific Solutions
(Context: Use these as concrete examples in your recommendations.)

### E-commerce
- **Cart Abandonment Recovery**: AI-powered retargeting with AIQUA. **(Trigger: High cart abandonment rates in `usage.csv`)**
- **Product Recommendations**: Personalized suggestions via AIQUA. **(Trigger: Low cross-sell/upsell metrics)**
- **Seasonal Campaigns**: Holiday and event optimization.

### Financial Services
- **Lead Qualification**: AI-powered lead scoring via BotBonnie. **(Trigger: Low lead-to-customer conversion rate)**
- **Customer Onboarding**: Automated welcome sequences with AIQUA/BotBonnie. **(Trigger: High drop-off rate for new users)**
- **Compliance Marketing**: Regulatory-compliant campaigns.

### Gaming
- **User Acquisition**: Targeted advertising.
- **Player Retention**: Engagement optimization with AIQUA push notifications. **(Trigger: Low Day-7 / Day-30 retention metrics in `usage.csv`)**
- **Monetization**: In-app purchase optimization with personalized offers via AIQUA.

## Technical Integration

### Supported Platforms
- **Ad Platforms**: Google Ads, Facebook Ads, TikTok Ads
- **Analytics**: Google Analytics, Adobe Analytics, Mixpanel
- **CRM Systems**: Salesforce, HubSpot, Pipedrive
- **E-commerce**: Shopify, WooCommerce, Magento

### API & SDK Support
- RESTful APIs for custom integrations
- Mobile SDKs for iOS and Android
- Web tracking and pixel implementation
- Real-time data synchronization

## Pricing & Business Model

### Revenue Model
- **Subscription-based**: Monthly/annual contracts
- **Usage-based**: Pay-per-performance models
- **Enterprise**: Custom pricing for large organizations

### Customer Segments
- **SMB**: Small to medium businesses
- **Enterprise**: Large corporations and brands
- **Agencies**: Marketing and advertising agencies

## Success Stories & Case Studies
(Context: Use these statistics to support your recommendations and show proven value.)

### E-commerce Success
- **Fashion Retailer**: 40% increase in customer retention
- **Electronics Brand**: 60% reduction in customer acquisition costs
- **Home Goods**: 3x improvement in customer lifetime value

### Financial Services
- **Bank**: 50% increase in loan applications
- **Insurance**: 35% improvement in policy renewals
- **Fintech**: 4x growth in user acquisition

## Common Customer Challenges & Solutions
(Context: A direct mapping of common business problems to our product suite.)

### Challenge 1: Data Silos
- **Appier Solution**: **AIRIS** as a unified customer data platform.
- **Implementation**: API integrations and data connectors.
- **Outcome**: 360-degree customer view.

### Challenge 2: Campaign Fragmentation
- **Appier Solution**: **AIQUA** for cross-screen campaign management.
- **Implementation**: Centralized campaign dashboard.
- **Outcome**: Consistent messaging across channels.

### Challenge 3: Manual Optimization
- **Appier Solution**: AI-powered automation via **AIQUA**.
- **Implementation**: Machine learning algorithms.
- **Outcome**: Real-time campaign optimization.

### Challenge 4: Customer Churn
- **Appier Solution**: Predictive churn modeling and proactive engagement with **AIQUA** and **AIRIS**.
- **Implementation**: Behavioral analysis and automated alerts/journeys.
- **Outcome**: Proactive retention strategies.

## Best Practices for Customer Success

### 1. Regular Business Reviews
- Monthly performance reviews
- Quarterly strategic planning
- Annual business planning sessions

### 2. Proactive Monitoring
- Key performance indicators (KPIs)
- Early warning systems for churn risk
- Automated alerts and notifications
- **Agent's Role:** Your purpose is to enable this proactive monitoring by analyzing data and flagging these risks for the CSM.

### 3. Continuous Optimization
- A/B testing and experimentation
- Performance benchmarking
- Industry trend analysis

### 4. Knowledge Sharing
- Best practice documentation
- Customer success stories
- Industry insights and trends

## Support & Resources

### Customer Support
- **24/7 Technical Support**: Global support team
- **Success Managers**: Dedicated customer success representatives
- **Training Programs**: Platform and best practice training

### Resources
- **Knowledge Base**: Comprehensive documentation
- **Webinars**: Regular educational sessions
- **Community**: Customer user groups and forums
- **Research**: Industry reports and whitepapers

## Future Roadmap & Innovation

### AI & Machine Learning
- Advanced predictive analytics
- Natural language processing
- Computer vision for creative optimization

### Platform Expansion
- New advertising channels
- Enhanced analytics capabilities
- Advanced automation features

### Market Expansion
- New geographic markets
- Industry vertical expansion
- Strategic partnerships and acquisitions
"""

def get_appier_context() -> str:
    """Get the Appier context for the agent"""
    return APPIER_CONTEXT

def get_appier_summary() -> str:
    """Get a concise summary of Appier for quick reference"""
    return """Appier is a leading AI-powered marketing technology company specializing in cross-screen marketing automation, customer engagement, and data intelligence. Our solutions help businesses drive growth through intelligent customer acquisition and retention, with expertise in e-commerce, financial services, gaming, and healthcare industries. We provide AIQUA for customer engagement, CrossX for cross-screen marketing, BotBonnie for conversational marketing, and AIRIS as a CDP product for customer insights."""
