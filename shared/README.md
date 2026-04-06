# GraphQL Data Connect SDK - Shared Schemas

This directory contains language-agnostic schema definitions and specifications for the credit history data connect SDK.

## Files

- **credit_history_schema.json**: JSON Schema definition for normalized credit history records
- **graphql_schema.graphql**: Reference GraphQL schema for data provider queries
- **provider_config_schema.json**: Configuration schema for registering data providers

## Schema Design Philosophy

### ETL Pipeline

```
┌──────────────────┐
│  Data Provider   │
│   (GraphQL API)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   EXTRACT        │
│ GraphQL queries  │
│ with pagination  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   TRANSFORM      │
│ Normalize fields │
│ to unified schema│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   ENRICH         │
│ Map company_id   │
│ to Shopify B2B ID│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   LOAD           │
│ RAG Pipeline     │
│ (LangChain +     │
│  ChromaDB)       │
└──────────────────┘
```

## Field Mappings

### Required Fields
- `company_id`: External provider's company identifier → Will be mapped to Shopify B2B company GID
- `email`: Company contact email
- `date`: Transaction timestamp (ISO 8601)
- `reference`: Transaction description/reference

### Optional Financial Fields
- `inflow`: Money received (credits)
- `outflow`: Money spent (debits)
- `account_name`: Account holder name
- `account_number`: Bank account number (masked for security)
- `bank`: Financial institution name
- `currency`: ISO 4217 currency code

### Enriched Fields (Added by SDK)
- `shopify_company_id`: Shopify B2B company GID after mapping
- `provider_id`: Identifier of the data provider source

## Multi-Language Support

This schema is designed to be consumed by code generators for:
- **Python**: Pydantic models with validation
- **Node.js**: TypeScript interfaces with Zod validation
- **Java**: POJOs with Jackson annotations
- **Rust**: Structs with serde derive macros

## Security Considerations

⚠️ **Sensitive Financial Data** - Credit history contains PII and financial information:
- All data in transit MUST use TLS 1.2+
- Provider API keys stored in encrypted secret management
- Field-level encryption for account numbers before persistence
- Audit logs for all data access
- Data retention policies and GDPR compliance
