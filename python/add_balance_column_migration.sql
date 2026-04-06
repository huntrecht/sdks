-- Migration: Add balance column to credit_history table
-- Date: 2025-11-19
-- Description: Adds balance field to track running balance after each transaction

-- Add balance column to existing credit_history table (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='credit_history' AND column_name='balance'
    ) THEN
        ALTER TABLE credit_history 
        ADD COLUMN balance DECIMAL(15, 2);
        
        RAISE NOTICE 'âœ… Added balance column to credit_history table';
    ELSE
        RAISE NOTICE 'âœ" Balance column already exists in credit_history table';
    END IF;
END $$;

-- Create index on balance for efficient queries (optional)
CREATE INDEX IF NOT EXISTS idx_credit_history_balance ON credit_history(balance DESC);

COMMENT ON COLUMN credit_history.balance IS 'Running balance after transaction';
