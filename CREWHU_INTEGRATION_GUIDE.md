# CrewHu CSAT Integration Guide for Accellis Client Engagement Platform

## Overview
This guide explains how to integrate your Accellis Client Engagement platform with CrewHu CSAT to automatically pull customer satisfaction scores for the "Support Engagement Satisfaction" metric in your client scoresheets.

## Integration Architecture

### ConnectWise + CrewHu Strategy
Your Accellis platform uses a **dual integration approach** for comprehensive client engagement scoring:

- **ConnectWise PSA**: Provides operational metrics (tickets, time, agreements)
- **CrewHu CSAT**: Provides customer satisfaction scores

This combination gives you both objective service delivery metrics AND subjective customer satisfaction data.

## Prerequisites

### 1. CrewHu API Access
You'll need the following from your CrewHu administrator:
- **API Key**: Your CrewHu API authentication token
- **Company ID**: Your CrewHu company identifier
- **Base URL**: CrewHu API endpoint (usually `https://api.crewhu.com`)

### 2. CrewHu API Permissions
Ensure your API key has the following permissions:
- **CSAT Data Access**: Read access to customer satisfaction scores
- **Client/Company Data**: Access to client/company mappings
- **Date Range Queries**: Ability to query historical CSAT data

### 3. Environment Variables
Set the following environment variables in your Replit project:

```bash
CREWHU_API_KEY=your_crewhu_api_key
CREWHU_COMPANY_ID=your_company_id
CREWHU_BASE_URL=https://api.crewhu.com
```

## Integration Features

### 1. CSAT Score Synchronization
- **Automatic Import**: Pull CSAT scores for all active clients
- **Date Range Filtering**: Configurable lookback period (30, 60, 90 days)
- **Client Mapping**: Match CrewHu client names to Accellis client records
- **Score Averaging**: Calculate average satisfaction from multiple responses

### 2. Support Engagement Satisfaction Metric
The CrewHu integration specifically provides the **Support Engagement Satisfaction** metric:

| Metric | Data Source | Calculation Method |
|--------|-------------|-------------------|
| **Support Engagement Satisfaction** | CrewHu CSAT | Average customer satisfaction score (1-5 scale) |

### 3. Real-Time CSAT Updates
- **Scheduled Sync**: Regular polling of CrewHu API for new CSAT data
- **Client-Specific Queries**: Pull satisfaction scores for individual clients
- **Historical Analysis**: Trend analysis of satisfaction over time

## Setup Process

### Step 1: Configure Environment Variables
1. In your Replit project, go to the **Secrets** tab
2. Add each CrewHu environment variable with your credentials:
   ```
   CREWHU_API_KEY=your_api_key_here
   CREWHU_COMPANY_ID=your_company_id
   CREWHU_BASE_URL=https://api.crewhu.com
   ```
3. Restart your application

### Step 2: Test CrewHu Connection
1. Navigate to your integration dashboard
2. Click **Test CrewHu Connection** to verify API access
3. Confirm you can retrieve CSAT data

### Step 3: Configure Client Mapping
1. Ensure client names in Accellis match those in CrewHu
2. Map any clients with different names between systems
3. Test CSAT retrieval for key clients

### Step 4: Enable Auto-Scoring
1. Configure CSAT sync frequency (daily/weekly)
2. Set lookback period for satisfaction calculations
3. Enable automatic scoresheet updates with CSAT data

## API Integration Details

### Authentication
CrewHu uses Bearer token authentication:
```
Authorization: Bearer your_api_key_here
Content-Type: application/json
```

### Key Endpoints Used
- `GET /api/v1/csat/scores` - Retrieve customer satisfaction scores
- `GET /api/v1/health` - Test API connection
- `GET /api/v1/clients` - Get client/company mappings

### CSAT Score Calculation
```python
def calculate_satisfaction_score(client_name, days_back=30):
    # Get all CSAT responses for client in time period
    csat_responses = get_client_csat_scores(client_name, days_back)
    
    # Calculate average score
    if csat_responses:
        scores = [response['score'] for response in csat_responses]
        avg_score = sum(scores) / len(scores)
        return max(1, min(5, round(avg_score)))  # Ensure 1-5 scale
    
    return None  # No CSAT data available
```

## Client Name Mapping

### Automatic Matching
The system attempts to automatically match clients by:
1. **Exact Name Match**: Direct comparison of client names
2. **Normalized Matching**: Remove special characters and compare
3. **Partial Matching**: Match on company name without suffixes

### Manual Mapping
For clients that don't auto-match:
1. Go to **Client Mapping** in the integration dashboard
2. Select unmatched Accellis clients
3. Choose corresponding CrewHu client names
4. Save mappings for future sync operations

## Data Flow

### 1. CSAT Data Collection
```
CrewHu → API Call → Accellis Integration → Client Mapping → Score Calculation
```

### 2. Scoresheet Integration
```
CSAT Score → Support Engagement Satisfaction Metric → Client Scoresheet → Dashboard Analytics
```

### 3. Combined Scoring
```
ConnectWise Metrics + CrewHu CSAT = Complete Engagement Score
```

## Troubleshooting

### Common Issues

#### 1. No CSAT Data Retrieved
- **Check API Key**: Verify CrewHu API key is valid and has proper permissions
- **Verify Client Names**: Ensure client names match between systems
- **Check Date Range**: Expand lookback period if recent CSAT data is limited

#### 2. Client Mapping Failures
- **Name Variations**: Check for different company name formats
- **Special Characters**: Remove punctuation and try again
- **Manual Mapping**: Use manual mapping for complex name differences

#### 3. Authentication Errors
- **API Key Expiration**: Check if API key needs renewal
- **Permission Changes**: Verify API permissions haven't changed
- **Rate Limiting**: Check if you're hitting API rate limits

### Debug Mode
Enable debug logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

### 1. API Key Management
- Store API key as environment variable
- Never commit API keys to version control
- Implement API key rotation schedule
- Monitor API key usage and access logs

### 2. Data Privacy
- Ensure CSAT data handling complies with privacy regulations
- Implement data retention policies
- Log API access for audit trails
- Secure data transmission with HTTPS

### 3. Rate Limiting
- Respect CrewHu API rate limits
- Implement retry logic with exponential backoff
- Cache frequently accessed data
- Monitor API usage metrics

## Monitoring and Maintenance

### 1. Data Quality Checks
- **Daily CSAT Sync Verification**: Ensure new CSAT data is being imported
- **Client Mapping Validation**: Regular review of client name mappings
- **Score Accuracy Audits**: Verify CSAT scores match CrewHu dashboard

### 2. Performance Monitoring
- **API Response Times**: Track CrewHu API performance
- **Sync Success Rates**: Monitor integration reliability
- **Data Freshness**: Ensure CSAT data is current

### 3. Integration Health
- **Connection Tests**: Daily automated connection verification
- **Error Alerting**: Notifications for integration failures
- **Usage Analytics**: Track which clients have CSAT data

## CrewHu-Specific Features

### 1. CSAT Score Types
CrewHu typically provides multiple satisfaction metrics:
- **Overall Satisfaction**: General service satisfaction
- **Resolution Satisfaction**: Specific to issue resolution
- **Communication Satisfaction**: Quality of support interactions
- **Timeliness Satisfaction**: Speed of service delivery

### 2. Response Filtering
Configure which CSAT responses to include:
- **Minimum Response Threshold**: Require minimum number of responses
- **Response Recency**: Weight recent responses more heavily
- **Response Validity**: Filter out incomplete or invalid responses

### 3. Satisfaction Trends
Track satisfaction trends over time:
- **Monthly Averages**: Rolling monthly satisfaction scores
- **Trend Analysis**: Identify improving/declining satisfaction
- **Comparative Analysis**: Compare clients against benchmarks

## Integration with Scoresheet System

### Automatic Score Updates
When CSAT data is available:
```python
# Support Engagement Satisfaction gets auto-populated
scoresheet_metrics = {
    'Support Engagement Satisfaction': crewhu_csat_score,  # From CrewHu
    'Help Desk Usage': connectwise_ticket_score,           # From ConnectWise
    'Project Engagement': connectwise_time_score,          # From ConnectWise
    # ... other metrics
}
```

### Manual Override
Users can still manually override CSAT scores when:
- CrewHu data is unavailable
- Manual assessment differs from CSAT
- Special circumstances require adjustment

## Benefits of CrewHu Integration

### 1. Objective Customer Feedback
- **Real Customer Voice**: Actual satisfaction from service recipients
- **Quantified Feedback**: Numeric scores for trend analysis
- **Response Volume**: Multiple data points for statistical validity

### 2. Complete Service Picture
- **Operational Metrics** (ConnectWise): How efficiently you deliver service
- **Customer Satisfaction** (CrewHu): How customers feel about the service
- **Combined Insights**: Balanced view of service effectiveness

### 3. Proactive Client Management
- **Early Warning System**: Declining satisfaction alerts
- **Success Validation**: High satisfaction confirms good service
- **Improvement Targeting**: Focus on clients with low satisfaction

## Next Steps

After successful CrewHu integration:
1. **Train your team** on interpreting CSAT data in client scoresheets
2. **Set satisfaction benchmarks** for different client types
3. **Create alerting rules** for declining satisfaction trends
4. **Establish review processes** for low-satisfaction clients
5. **Integrate satisfaction data** into client review meetings

This CrewHu integration complements your ConnectWise PSA data to provide comprehensive, data-driven client engagement insights that balance operational efficiency with customer satisfaction.