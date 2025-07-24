# ConnectWise Integration Guide for Accellis Client Engagement Platform

## Overview
This guide explains how to integrate your Accellis Client Engagement platform with ConnectWise PSA to automatically synchronize client data and generate engagement scores based on real service delivery metrics.

## Prerequisites

### 1. ConnectWise API Access
You'll need the following from your ConnectWise administrator:
- **Base URL**: Your ConnectWise server URL (e.g., `https://api-na.myconnectwise.net`)
- **Company ID**: Your ConnectWise company identifier
- **Public Key**: API public key (also called Member ID)
- **Private Key**: API private key (also called Member Password)
- **Client ID**: Your ConnectWise application client ID

### 2. ConnectWise API Member Setup
1. Log into ConnectWise Manage
2. Go to **System** → **Members**
3. Create or edit an API user with the following permissions:
   - **Company**: View, Edit
   - **Contacts**: View
   - **Service Tickets**: View
   - **Time Entries**: View
   - **Agreements**: View
   - **Finance**: View (for billing data)

### 3. Environment Variables
Set the following environment variables in your Replit project:

```bash
CONNECTWISE_BASE_URL=https://api-na.myconnectwise.net
CONNECTWISE_COMPANY_ID=YourCompanyID
CONNECTWISE_PUBLIC_KEY=YourPublicKey
CONNECTWISE_PRIVATE_KEY=YourPrivateKey
CONNECTWISE_CLIENT_ID=YourClientID
```

## Integration Features

### 1. Client Data Synchronization
- **Automatic Import**: Import all active companies from ConnectWise
- **Contact Sync**: Primary contact information for each client
- **Status Updates**: Active/inactive status synchronization
- **Industry Mapping**: Map ConnectWise market types to Accellis industries

### 2. Auto-Generated Engagement Scores
Based on ConnectWise data, the system automatically calculates:

| Metric | Data Source | Calculation Method |
|--------|-------------|-------------------|
| **Help Desk Usage** | Service Tickets | Ticket volume: 2+ tickets = 1 point (max 5) |
| **First Touch Resolution** | Ticket Resolution Time | Tickets resolved within 4 hours |
| **Support Satisfaction** | CrewHu CSAT Data | Requires separate CrewHu integration |
| **Project Engagement** | Time Entries | Billable hours: 40+hrs=5pts, 20+hrs=4pts, 10+hrs=3pts |
| **Procurement** | Agreement Changes | Recent agreements/additions |

### 3. Real-Time Updates
- **Webhooks**: Receive real-time updates from ConnectWise
- **Automatic Scoring**: Trigger score recalculation on data changes
- **Client Updates**: Sync company information changes

## Setup Process

### Step 1: Configure Environment Variables
1. In your Replit project, go to the **Secrets** tab
2. Add each ConnectWise environment variable with your credentials
3. Restart your application

### Step 2: Initialize Integration
1. Navigate to `/connectwise` in your application
2. Click **Setup** to initialize the database schema
3. Test the connection using the **Test Connection** button

### Step 3: Sync Client Data
1. Click **Sync Clients Now** to import all companies from ConnectWise
2. Review the **Client Mapping** to ensure proper associations
3. Map any unmatched clients manually if needed

### Step 4: Configure Auto-Scoring
1. Go to **Client Mapping** and select clients for auto-scoring
2. Choose the data period (30, 60, or 90 days)
3. Click **Auto-Score Clients** to generate initial scores

## API Endpoints

### Authentication
All API calls use Basic Authentication with Base64 encoded credentials:
```
Authorization: Basic base64(CompanyID+PublicKey:PrivateKey)
ClientId: YourClientID
```

### Key Endpoints Used
- `GET /company/companies` - Retrieve client companies
- `GET /company/companies/{id}/contacts` - Get company contacts
- `GET /service/tickets` - Retrieve service tickets
- `GET /time/entries` - Get time tracking entries
- `GET /finance/agreements` - Fetch managed service agreements

## Webhook Configuration

### Setup Webhooks in ConnectWise
1. Go to **System** → **API Reports**
2. Create new callbacks for:
   - `company.updated`
   - `ticket.created`
   - `ticket.updated`
   - `agreement.created`

### Webhook URL
```
https://your-replit-app.replit.app/connectwise/webhook
```

## Data Mapping

### Industry Mapping
ConnectWise Market → Accellis Industry:
- Legal → legal
- Healthcare → healthcare  
- Manufacturing → manufacturing
- Retail → retail
- Financial → finance
- Education → education
- Non-Profit → nonprofit
- (Other) → other

### Score Calculation Logic

#### Help Desk Usage (Weight: 5)
```python
score = min(5, ticket_count // 2)  # 2 tickets = 1 point
```

#### First Touch Resolution (Weight: 4)
```python
quick_resolutions = tickets_resolved_under_4_hours
score = min(5, quick_resolutions)
```

#### Support Satisfaction (Weight: 4)
```python
# Note: This metric requires CrewHu CSAT integration
# ConnectWise integration skips this metric
# Scores pulled from separate CrewHu API
csat_score = get_csat_from_crewhu(client_id)
score = csat_score  # 1-5 scale from CrewHu
```

#### Project Engagement (Weight: 5)
```python
total_hours = sum(billable_time_entries)
if total_hours >= 40: score = 5
elif total_hours >= 20: score = 4
elif total_hours >= 10: score = 3
else: score = 2
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
- Verify all credentials are correct
- Ensure API member has proper permissions
- Check if ClientId is registered in ConnectWise

#### 2. No Data Retrieved
- Confirm date ranges in API calls
- Check company status filters (active vs inactive)
- Verify member permissions for specific modules

#### 3. Sync Failures
- Review ConnectWise server logs
- Check rate limiting (ConnectWise has API call limits)
- Ensure network connectivity to ConnectWise servers

### Debug Mode
Enable debug logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

### 1. Credential Management
- Store all credentials as environment variables
- Never commit API keys to version control
- Use HTTPS for all API communications
- Implement credential rotation schedule

### 2. API Rate Limiting
- ConnectWise limits API calls per minute
- Implement retry logic with exponential backoff
- Cache frequently accessed data

### 3. Data Privacy
- Ensure compliance with data protection regulations
- Log API access for audit trails
- Implement proper data retention policies

## Monitoring and Maintenance

### 1. Regular Health Checks
- Daily connection tests
- Weekly sync verification
- Monthly score accuracy reviews

### 2. Performance Monitoring
- Track API response times
- Monitor sync success rates
- Alert on integration failures

### 3. Data Quality
- Regular data validation checks
- Score calculation audits
- Client mapping verification

## Support and Resources

### ConnectWise Documentation
- [ConnectWise REST API Guide](https://developer.connectwise.com/Products/Manage/REST)
- [Authentication Documentation](https://developer.connectwise.com/Products/Manage/REST#authentication)
- [Webhook Setup Guide](https://developer.connectwise.com/Products/Manage/REST#webhooks)

### Accellis Integration Support
- Integration dashboard: `/connectwise`
- Sync history: `/connectwise/sync-history`
- Client mapping: `/connectwise/client-mapping`
- Test connection: `/connectwise/test-connection`

## Next Steps

After successful integration:
1. **Train your team** on the new auto-scoring features
2. **Review score calculations** to ensure they align with business goals
3. **Set up monitoring** for ongoing data quality
4. **Configure alerts** for integration failures
5. **Plan regular reviews** of client mappings and scores

This integration transforms your ConnectWise service data into actionable client engagement insights, enabling proactive client management and improved service delivery.