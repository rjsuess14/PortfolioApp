-- Create portfolio_accounts table
CREATE TABLE IF NOT EXISTS public.portfolio_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    institution_name TEXT,
    account_number_mask TEXT,
    total_value DECIMAL(15,2) DEFAULT 0,
    plaid_account_id TEXT,
    plaid_item_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create holdings table
CREATE TABLE IF NOT EXISTS public.holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES public.portfolio_accounts(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    security_name TEXT,
    shares DECIMAL(15,6) NOT NULL,
    avg_cost DECIMAL(15,2) NOT NULL,
    current_price DECIMAL(15,2) NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    gain_loss DECIMAL(15,2) NOT NULL,
    gain_loss_percent DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create plaid_access_tokens table for secure token storage
CREATE TABLE IF NOT EXISTS public.plaid_access_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL, -- Plaid item identifier
    access_token_encrypted TEXT NOT NULL, -- Encrypted access token
    institution_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, item_id)
);

-- Create summaries table for AI-generated content
CREATE TABLE IF NOT EXISTS public.summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('filing', 'news')),
    content TEXT NOT NULL,
    source TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_portfolio_accounts_user_id ON public.portfolio_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_holdings_account_id ON public.holdings(account_id);
CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON public.holdings(symbol);
CREATE INDEX IF NOT EXISTS idx_plaid_access_tokens_user_id ON public.plaid_access_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_summaries_symbol ON public.summaries(symbol);

-- Enable Row Level Security (RLS)
ALTER TABLE public.portfolio_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.holdings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plaid_access_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.summaries ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for portfolio_accounts
CREATE POLICY "Users can view their own portfolio accounts"
    ON public.portfolio_accounts FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own portfolio accounts"
    ON public.portfolio_accounts FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own portfolio accounts"
    ON public.portfolio_accounts FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own portfolio accounts"
    ON public.portfolio_accounts FOR DELETE
    USING (auth.uid() = user_id);

-- Create RLS policies for holdings
CREATE POLICY "Users can view holdings for their accounts"
    ON public.holdings FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.portfolio_accounts
            WHERE portfolio_accounts.id = holdings.account_id
            AND portfolio_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert holdings for their accounts"
    ON public.holdings FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.portfolio_accounts
            WHERE portfolio_accounts.id = holdings.account_id
            AND portfolio_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update holdings for their accounts"
    ON public.holdings FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.portfolio_accounts
            WHERE portfolio_accounts.id = holdings.account_id
            AND portfolio_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete holdings for their accounts"
    ON public.holdings FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.portfolio_accounts
            WHERE portfolio_accounts.id = holdings.account_id
            AND portfolio_accounts.user_id = auth.uid()
        )
    );

-- Create RLS policies for plaid_access_tokens
CREATE POLICY "Users can view their own access tokens"
    ON public.plaid_access_tokens FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own access tokens"
    ON public.plaid_access_tokens FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own access tokens"
    ON public.plaid_access_tokens FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own access tokens"
    ON public.plaid_access_tokens FOR DELETE
    USING (auth.uid() = user_id);

-- Create RLS policies for summaries (public read, admin write)
CREATE POLICY "Anyone can view summaries"
    ON public.summaries FOR SELECT
    USING (true);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_portfolio_accounts_updated_at BEFORE UPDATE
    ON public.portfolio_accounts FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_holdings_updated_at BEFORE UPDATE
    ON public.holdings FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plaid_access_tokens_updated_at BEFORE UPDATE
    ON public.plaid_access_tokens FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
