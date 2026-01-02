-- AIKU Travel Agent - Initial Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
    content TEXT NOT NULL,
    tool_calls JSONB,
    tool_call_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Row Level Security (RLS)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies for conversations
-- Users can only see their own conversations
CREATE POLICY "Users can view own conversations"
    ON conversations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own conversations"
    ON conversations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversations"
    ON conversations FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own conversations"
    ON conversations FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policies for messages
-- Users can only see messages from their conversations
CREATE POLICY "Users can view messages from own conversations"
    ON messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM conversations
            WHERE conversations.id = messages.conversation_id
            AND conversations.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create messages in own conversations"
    ON messages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversations
            WHERE conversations.id = messages.conversation_id
            AND conversations.user_id = auth.uid()
        )
    );

-- Service role bypass for backend
-- The service role key bypasses RLS, allowing the backend to manage all data

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to conversations
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Tool Executions table - logs all tool calls with inputs/outputs
CREATE TABLE IF NOT EXISTS tool_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    tool_name TEXT NOT NULL,
    tool_call_id TEXT,
    input_params JSONB NOT NULL,
    output_data JSONB,
    output_type TEXT, -- 'flights', 'hotels', 'weather', 'transfers', 'activities', 'exchange', 'error'
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for tool_executions
CREATE INDEX IF NOT EXISTS idx_tool_executions_conversation_id ON tool_executions(conversation_id);
CREATE INDEX IF NOT EXISTS idx_tool_executions_tool_name ON tool_executions(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_executions_created_at ON tool_executions(created_at);
CREATE INDEX IF NOT EXISTS idx_tool_executions_output_type ON tool_executions(output_type);

-- RLS for tool_executions
ALTER TABLE tool_executions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view tool executions from own conversations"
    ON tool_executions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM conversations
            WHERE conversations.id = tool_executions.conversation_id
            AND conversations.user_id = auth.uid()
        )
    );

-- Travel Results table - structured data for UI rendering
-- Stores flights, hotels, etc. as structured data that frontend can render as cards
CREATE TABLE IF NOT EXISTS travel_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    tool_execution_id UUID REFERENCES tool_executions(id) ON DELETE CASCADE,
    result_type TEXT NOT NULL CHECK (result_type IN ('flight', 'hotel', 'transfer', 'activity', 'weather', 'exchange')),
    data JSONB NOT NULL,
    selected BOOLEAN DEFAULT false, -- user selected this option
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for travel_results
CREATE INDEX IF NOT EXISTS idx_travel_results_conversation_id ON travel_results(conversation_id);
CREATE INDEX IF NOT EXISTS idx_travel_results_result_type ON travel_results(result_type);
CREATE INDEX IF NOT EXISTS idx_travel_results_selected ON travel_results(selected) WHERE selected = true;

-- RLS for travel_results
ALTER TABLE travel_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view travel results from own conversations"
    ON travel_results FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM conversations
            WHERE conversations.id = travel_results.conversation_id
            AND conversations.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update travel results in own conversations"
    ON travel_results FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM conversations
            WHERE conversations.id = travel_results.conversation_id
            AND conversations.user_id = auth.uid()
        )
    );
