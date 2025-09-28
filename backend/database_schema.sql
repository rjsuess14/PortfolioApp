-- Database schema for Portfolio App
-- Run this in your Supabase SQL editor to create the required tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Portfolio Accounts table (extends the schema from CLAUDE.md)
CREATE TABLE IF NOT EXISTS portfolio_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL, -- 'brokerage', 'ira', '401k', etc.
    total_value DECIMAL NOT NULL DEFAULT 0,
    plaid_account_id TEXT, -- Plaid account identifier
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Holdings table (extends the schema from CLAUDE.md)
CREATE TABLE IF NOT EXISTS holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES portfolio_accounts(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    shares DECIMAL NOT NULL DEFAULT 0,
    avg_cost DECIMAL NOT NULL DEFAULT 0,
    current_price DECIMAL NOT NULL DEFAULT 0,
    total_value DECIMAL NOT NULL DEFAULT 0,
    gain_loss DECIMAL NOT NULL DEFAULT 0,
    security_name TEXT, -- Full name of the security
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Plaid access tokens table (encrypted storage)
CREATE TABLE IF NOT EXISTS plaid_access_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL, -- Plaid item identifier
    access_token_encrypted TEXT NOT NULL, -- Encrypted access token
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, item_id)
);

-- Summaries table (for AI-generated content)
CREATE TABLE IF NOT EXISTS summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('filing', 'news')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_portfolio_accounts_user_id ON portfolio_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_accounts_plaid_account_id ON portfolio_accounts(plaid_account_id);
CREATE INDEX IF NOT EXISTS idx_holdings_account_id ON holdings(account_id);
CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON holdings(symbol);
CREATE INDEX IF NOT EXISTS idx_plaid_access_tokens_user_id ON plaid_access_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_plaid_access_tokens_item_id ON plaid_access_tokens(item_id);
CREATE INDEX IF NOT EXISTS idx_summaries_symbol ON summaries(symbol);
CREATE INDEX IF NOT EXISTS idx_summaries_type ON summaries(type);

-- Row Level Security (RLS) policies
ALTER TABLE portfolio_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE holdings ENABLE ROW LEVEL SECURITY;
ALTER TABLE plaid_access_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;

-- RLS policies for portfolio_accounts
CREATE POLICY "Users can view their own portfolio accounts" ON portfolio_accounts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own portfolio accounts" ON portfolio_accounts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own portfolio accounts" ON portfolio_accounts
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own portfolio accounts" ON portfolio_accounts
    FOR DELETE USING (auth.uid() = user_id);

-- RLS policies for holdings
CREATE POLICY "Users can view holdings of their accounts" ON holdings
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM portfolio_accounts 
            WHERE portfolio_accounts.id = holdings.account_id 
            AND portfolio_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert holdings to their accounts" ON holdings
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM portfolio_accounts 
            WHERE portfolio_accounts.id = holdings.account_id 
            AND portfolio_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update holdings of their accounts" ON holdings
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM portfolio_accounts 
            WHERE portfolio_accounts.id = holdings.account_id 
            AND portfolio_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete holdings of their accounts" ON holdings
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM portfolio_accounts 
            WHERE portfolio_accounts.id = holdings.account_id 
            AND portfolio_accounts.user_id = auth.uid()
        )
    );

-- RLS policies for plaid_access_tokens
CREATE POLICY "Users can view their own Plaid tokens" ON plaid_access_tokens
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own Plaid tokens" ON plaid_access_tokens
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own Plaid tokens" ON plaid_access_tokens
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own Plaid tokens" ON plaid_access_tokens
    FOR DELETE USING (auth.uid() = user_id);

-- RLS policies for summaries (public read for authenticated users)
CREATE POLICY "Authenticated users can view summaries" ON summaries
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Service role can manage summaries" ON summaries
    FOR ALL USING (auth.role() = 'service_role');

-- Update triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_portfolio_accounts_updated_at BEFORE UPDATE
    ON portfolio_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_holdings_updated_at BEFORE UPDATE
    ON holdings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plaid_access_tokens_updated_at BEFORE UPDATE
    ON plaid_access_tokens FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();