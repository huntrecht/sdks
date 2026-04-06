-- Database migrations for credit history data connect SDK

-- Table: company_id_mappings
-- Maps external company IDs to Shopify B2B company GIDs
CREATE TABLE IF NOT EXISTS company_id_mappings (
    id SERIAL PRIMARY KEY,
    external_company_id VARCHAR(255) NOT NULL UNIQUE,
    shopify_company_id VARCHAR(255) NOT NULL,
    provider_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_external_id UNIQUE (external_company_id)
);

CREATE INDEX IF NOT EXISTS idx_company_mappings_external ON company_id_mappings(external_company_id);
CREATE INDEX IF NOT EXISTS idx_company_mappings_shopify ON company_id_mappings(shopify_company_id);


-- Table: credit_history
-- Stores credit history transactions from data providers
CREATE TABLE IF NOT EXISTS credit_history (
    id SERIAL PRIMARY KEY,
    company_id VARCHAR(255) NOT NULL,
    shopify_company_id VARCHAR(255),
    email VARCHAR(255) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    inflow DECIMAL(15, 2) DEFAULT 0,
    outflow DECIMAL(15, 2) DEFAULT 0,
    balance DECIMAL(15, 2),
    reference TEXT NOT NULL,
    account_name VARCHAR(255),
    account_number VARCHAR(100),
    bank VARCHAR(255),
    currency VARCHAR(10) DEFAULT 'USD',
    provider_id VARCHAR(100) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_transaction UNIQUE (provider_id, company_id, transaction_date, reference)
);

CREATE INDEX IF NOT EXISTS idx_credit_history_company ON credit_history(company_id);
CREATE INDEX IF NOT EXISTS idx_credit_history_shopify_company ON credit_history(shopify_company_id);
CREATE INDEX IF NOT EXISTS idx_credit_history_date ON credit_history(transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_credit_history_provider ON credit_history(provider_id);
CREATE INDEX IF NOT EXISTS idx_credit_history_email ON credit_history(email);


-- Table: data_provider_configs
-- Stores registered data provider configurations
CREATE TABLE IF NOT EXISTS data_provider_configs (
    id SERIAL PRIMARY KEY,
    provider_id VARCHAR(100) NOT NULL UNIQUE,
    provider_name VARCHAR(255) NOT NULL,
    api_url VARCHAR(500) NOT NULL,
    api_key_encrypted TEXT,
    connector_type VARCHAR(100) DEFAULT 'generic',
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_provider_configs_active ON data_provider_configs(provider_id) WHERE is_active = TRUE;


-- View: credit_history_summary
-- Aggregated credit history summary by company and currency
CREATE OR REPLACE VIEW credit_history_summary AS
SELECT
    shopify_company_id,
    company_id,
    currency,
    COUNT(*) as total_transactions,
    SUM(inflow) as total_inflow,
    SUM(outflow) as total_outflow,
    SUM(inflow) - SUM(outflow) as net_position,
    MIN(transaction_date) as earliest_transaction,
    MAX(transaction_date) as latest_transaction,
    COUNT(DISTINCT bank) as banks_count,
    COUNT(DISTINCT provider_id) as providers_count
FROM credit_history
WHERE shopify_company_id IS NOT NULL
GROUP BY shopify_company_id, company_id, currency;


-- Comments for documentation
COMMENT ON TABLE company_id_mappings IS 'Maps external company identifiers to Shopify B2B company GIDs';
COMMENT ON TABLE credit_history IS 'Stores credit history transactions from data providers for RAG pipeline';
COMMENT ON TABLE data_provider_configs IS 'Configuration for registered data providers';
COMMENT ON COLUMN credit_history.shopify_company_id IS 'Shopify B2B company GID after enrichment';
COMMENT ON COLUMN credit_history.provider_id IS 'Data provider identifier';
COMMENT ON COLUMN credit_history.metadata IS 'Provider-specific additional metadata (JSON)';
