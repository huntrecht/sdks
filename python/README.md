# GraphQL Data Connect SDK - Python Implementation

Complete GraphQL server for ingesting customer credit history from external data providers and feeding it to the RAG pipeline with automatic Shopify B2B company mapping.

## Features

✅ **GraphQL Server** with Strawberry GraphQL  
✅ **Data Provider Connectors** for external GraphQL APIs  
✅ **Shopify B2B Company Registry** with auto-creation  
✅ **RAG Pipeline Integration** with LangChain documents  
✅ **PostgreSQL Storage** with optimized indexes  
✅ **Credit History Analytics** with aggregated views  
✅ **Multi-Provider Support** with connector framework  

## Quick Start

### 1. Access GraphiQL IDE

Navigate to http://localhost:5000/graphql/credit-history in your browser to access the interactive GraphQL playground.

### 2. Example Queries

#### Fetch Credit History
```graphql
query GetCreditHistory {
  creditHistory(
    companyId: "ext_company_123"
    startDate: "2025-01-01T00:00:00Z"
    limit: 50
  ) {
    totalCount
    edges {
      node {
        id
        companyId
        shopifyCompanyId
        email
        date
        inflow
        outflow
        reference
        bank
        currency
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

#### Get Company Summary
```graphql
query GetCompanySummary {
  companyCreditSummary(
    shopifyCompanyId: "gid://shopify/Company/12345"
  )
}
```

### 3. Example Mutations

#### Ingest Credit History
```graphql
mutation IngestCreditHistory {
  ingestCreditHistory(
    providerId: "provider_1"
    companyId: "ext_company_123"
    enrichShopify: true
    records: [
      {
        companyId: "ext_company_123"
        email: "finance@acmecorp.com"
        date: "2025-01-15T10:30:00Z"
        reference: "Invoice payment - INV-2025-001"
        inflow: 50000.00
        outflow: 0.00
        accountName: "Acme Corporation Ltd"
        accountNumber: "****1234"
        bank: "First National Bank"
        currency: "USD"
      }
    ]
  ) {
    success
    recordsProcessed
    recordsEnriched
    shopifyCompaniesCreated
    errors
  }
}
```

#### Trigger Provider Sync
```graphql
mutation TriggerSync {
  triggerProviderSync(
    providerId: "provider_1"
    companyId: "ext_company_123"
    startDate: "2025-01-01T00:00:00Z"
  ) {
    success
    recordsProcessed
    recordsEnriched
    shopifyCompaniesCreated
    errors
  }
}
```

## Architecture

```
┌──────────────────────┐
│  External Provider   │
│   GraphQL API        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Data Provider       │
│  Connector           │
│  (Extract & Transform)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Shopify Company     │
│  Registry            │
│  (Map/Create)        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Credit History      │
│  RAG Loader          │
│  (LangChain Docs)    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Analytics RAG       │
│  Pipeline            │
│  (Groq LLM)          │
└──────────────────────┘
```

## Components

### 1. GraphQL Schema (`credit_history_schema.py`)
- Strawberry GraphQL types and schema
- Queries: `creditHistory`, `companyCreditSummary`
- Mutations: `ingestCreditHistory`, `triggerProviderSync`

### 2. Data Provider Connector (`data_provider_connector.py`)
- Abstract connector framework
- Generic GraphQL provider implementation
- Provider registry for multi-source support

### 3. Shopify Company Registry (`shopify_company_registry.py`)
- External ID → Shopify B2B company ID mapping
- Auto-creation of missing companies
- Database caching with 1-hour TTL

### 4. RAG Loader (`credit_history_rag_loader.py`)
- PostgreSQL storage with deduplication
- LangChain document creation
- Credit history analytics summaries

### 5. GraphQL Resolvers (`credit_history_resolvers.py`)
- Query and mutation resolvers
- ETL pipeline orchestration
- Error handling and validation

## Database Schema

### Tables

**company_id_mappings**
- Maps external company IDs to Shopify B2B company GIDs
- Prevents duplicate company creation

**credit_history**
- Stores all credit transactions
- Indexed by company, date, provider
- JSONB metadata for provider-specific fields

**data_provider_configs**
- Registry of configured data providers
- Encrypted API keys
- Active/inactive status

### Views

**credit_history_summary**
- Aggregated metrics by company and currency
- Total inflow, outflow, net position
- Transaction counts and date ranges

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/graphql/credit-history` | POST | GraphQL API endpoint |
| `/graphql/credit-history` | GET | GraphiQL IDE |

## Security

🔒 **Data Protection**
- TLS 1.2+ for all API connections
- Encrypted API keys in database
- Field-level encryption for account numbers
- Audit logs for data access

🔐 **Authentication**
- API key authentication for data providers
- OAuth client credentials support
- Session-based auth for GraphiQL

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Shopify
SHOPIFY_ADMIN_API_KEY=your_admin_api_key
SHOPIFY_SHOP_NAME=your-shop.myshopify.com

# Data Provider (example)
PROVIDER_API_URL=https://provider.example.com/graphql
PROVIDER_API_KEY=your_provider_api_key
```

## Next Steps

1. **Register Data Provider**
   ```python
   from sdk.python.data_provider_connector import DataProviderRegistry
   
   registry = DataProviderRegistry()
   registry.register_provider(
       provider_id="my_provider",
       api_url="https://provider.example.com/graphql",
       api_key="your_api_key"
   )
   ```

2. **Query Credit History via GraphQL**
   - Use GraphiQL IDE or POST to `/graphql/credit-history`

3. **Integrate with Analytics Agent**
   - Credit history automatically available in RAG pipeline
   - Query via analytics_agent for AI-powered insights

## Troubleshooting

**Issue**: GraphQL queries return empty results  
**Solution**: Check that records have been ingested and `shopify_company_id` is enriched

**Issue**: Company auto-creation fails  
**Solution**: Verify Shopify Admin API credentials and `write_companies` scope

**Issue**: Provider sync fails  
**Solution**: Validate provider GraphQL schema matches expected structure

## Support

For issues or questions:
1. Check GraphiQL IDE error messages
2. Review database logs in PostgreSQL
3. Verify provider API connectivity
4. Ensure Shopify B2B company exists

---

Built with ❤️ using Strawberry GraphQL, LangChain, and FastAPI
