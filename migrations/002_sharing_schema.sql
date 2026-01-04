-- AIKU Travel Agent - Sharing & Collaboration Schema
-- Run this in Supabase SQL Editor after 001_initial_schema.sql

-- ============================================
-- Conversation Shares Table
-- ============================================
CREATE TABLE IF NOT EXISTS conversation_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    shared_with_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,  -- NULL for pending email invites
    shared_with_email TEXT,  -- For email invitations before user accepts
    permission TEXT NOT NULL CHECK (permission IN ('view', 'comment', 'edit')),
    share_token TEXT UNIQUE,  -- For link-based sharing
    token_expires_at TIMESTAMPTZ,  -- Optional expiration for share links
    accepted_at TIMESTAMPTZ,  -- NULL until invitation is accepted
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure at least one sharing method is used
    CONSTRAINT valid_share CHECK (
        shared_with_id IS NOT NULL OR
        shared_with_email IS NOT NULL OR
        share_token IS NOT NULL
    ),
    -- Prevent duplicate shares for same user
    CONSTRAINT unique_user_share UNIQUE (conversation_id, shared_with_id)
);

-- Indexes for conversation_shares
CREATE INDEX IF NOT EXISTS idx_shares_conversation ON conversation_shares(conversation_id);
CREATE INDEX IF NOT EXISTS idx_shares_owner ON conversation_shares(owner_id);
CREATE INDEX IF NOT EXISTS idx_shares_shared_with ON conversation_shares(shared_with_id);
CREATE INDEX IF NOT EXISTS idx_shares_email ON conversation_shares(shared_with_email);
CREATE INDEX IF NOT EXISTS idx_shares_token ON conversation_shares(share_token);
CREATE INDEX IF NOT EXISTS idx_shares_pending ON conversation_shares(accepted_at) WHERE accepted_at IS NULL;

-- ============================================
-- Trip Todos Table
-- ============================================
CREATE TABLE IF NOT EXISTS trip_todos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    due_date DATE,
    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
    status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')) DEFAULT 'pending',
    category TEXT CHECK (category IN ('booking', 'packing', 'research', 'transportation', 'accommodation', 'activity', 'other')),
    linked_result_id UUID REFERENCES travel_results(id) ON DELETE SET NULL,
    position INTEGER NOT NULL DEFAULT 0,
    completed_at TIMESTAMPTZ,
    completed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for trip_todos
CREATE INDEX IF NOT EXISTS idx_todos_conversation ON trip_todos(conversation_id);
CREATE INDEX IF NOT EXISTS idx_todos_created_by ON trip_todos(created_by);
CREATE INDEX IF NOT EXISTS idx_todos_assigned_to ON trip_todos(assigned_to);
CREATE INDEX IF NOT EXISTS idx_todos_status ON trip_todos(status);
CREATE INDEX IF NOT EXISTS idx_todos_due_date ON trip_todos(due_date);
CREATE INDEX IF NOT EXISTS idx_todos_position ON trip_todos(conversation_id, position);

-- ============================================
-- RLS Policies for conversation_shares
-- ============================================
ALTER TABLE conversation_shares ENABLE ROW LEVEL SECURITY;

-- Owners can manage all their shares
CREATE POLICY "Owners can manage shares"
    ON conversation_shares FOR ALL
    USING (owner_id = auth.uid());

-- Recipients can view shares they're part of
CREATE POLICY "Recipients can view their shares"
    ON conversation_shares FOR SELECT
    USING (
        shared_with_id = auth.uid() OR
        shared_with_email = (SELECT email FROM auth.users WHERE id = auth.uid())
    );

-- Recipients can update their own shares (e.g., accept invitation)
CREATE POLICY "Recipients can accept shares"
    ON conversation_shares FOR UPDATE
    USING (
        shared_with_id = auth.uid() OR
        shared_with_email = (SELECT email FROM auth.users WHERE id = auth.uid())
    )
    WITH CHECK (
        shared_with_id = auth.uid() OR
        shared_with_email = (SELECT email FROM auth.users WHERE id = auth.uid())
    );

-- ============================================
-- RLS Policies for trip_todos
-- ============================================
ALTER TABLE trip_todos ENABLE ROW LEVEL SECURITY;

-- Users can view todos if they own the conversation OR have share access
CREATE POLICY "Users can view todos"
    ON trip_todos FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = trip_todos.conversation_id
            AND (
                c.user_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM conversation_shares cs
                    WHERE cs.conversation_id = c.id
                    AND (cs.shared_with_id = auth.uid() OR cs.share_token IS NOT NULL)
                    AND cs.accepted_at IS NOT NULL
                )
            )
        )
    );

-- Users can create todos if they own conversation or have edit permission
CREATE POLICY "Users can create todos"
    ON trip_todos FOR INSERT
    WITH CHECK (
        created_by = auth.uid() AND
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = trip_todos.conversation_id
            AND (
                c.user_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM conversation_shares cs
                    WHERE cs.conversation_id = c.id
                    AND cs.shared_with_id = auth.uid()
                    AND cs.permission = 'edit'
                    AND cs.accepted_at IS NOT NULL
                )
            )
        )
    );

-- Users can update todos if they own conversation or have edit permission
CREATE POLICY "Users can update todos"
    ON trip_todos FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = trip_todos.conversation_id
            AND (
                c.user_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM conversation_shares cs
                    WHERE cs.conversation_id = c.id
                    AND cs.shared_with_id = auth.uid()
                    AND cs.permission = 'edit'
                    AND cs.accepted_at IS NOT NULL
                )
            )
        )
    );

-- Users can delete todos if they own conversation or created the todo
CREATE POLICY "Users can delete todos"
    ON trip_todos FOR DELETE
    USING (
        created_by = auth.uid() OR
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = trip_todos.conversation_id
            AND c.user_id = auth.uid()
        )
    );

-- ============================================
-- Update existing RLS policies for shared access
-- ============================================

-- Allow shared users to view conversations
CREATE POLICY "Shared users can view conversations"
    ON conversations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM conversation_shares cs
            WHERE cs.conversation_id = conversations.id
            AND cs.shared_with_id = auth.uid()
            AND cs.accepted_at IS NOT NULL
        )
    );

-- Allow shared users to view messages (read-only for all share types)
CREATE POLICY "Shared users can view messages"
    ON messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM conversation_shares cs
            WHERE cs.conversation_id = messages.conversation_id
            AND cs.shared_with_id = auth.uid()
            AND cs.accepted_at IS NOT NULL
        )
    );

-- Allow shared users to view tool_executions
CREATE POLICY "Shared users can view tool executions"
    ON tool_executions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM conversation_shares cs
            WHERE cs.conversation_id = tool_executions.conversation_id
            AND cs.shared_with_id = auth.uid()
            AND cs.accepted_at IS NOT NULL
        )
    );

-- Allow shared users to view travel_results
CREATE POLICY "Shared users can view travel results"
    ON travel_results FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM conversation_shares cs
            WHERE cs.conversation_id = travel_results.conversation_id
            AND cs.shared_with_id = auth.uid()
            AND cs.accepted_at IS NOT NULL
        )
    );

-- ============================================
-- Triggers for updated_at
-- ============================================

-- Apply updated_at trigger to conversation_shares
CREATE TRIGGER update_conversation_shares_updated_at
    BEFORE UPDATE ON conversation_shares
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply updated_at trigger to trip_todos
CREATE TRIGGER update_trip_todos_updated_at
    BEFORE UPDATE ON trip_todos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Helper function to check share access
-- ============================================
CREATE OR REPLACE FUNCTION has_conversation_access(
    p_conversation_id UUID,
    p_user_id UUID,
    p_required_permission TEXT DEFAULT 'view'
) RETURNS BOOLEAN AS $$
DECLARE
    v_is_owner BOOLEAN;
    v_permission TEXT;
BEGIN
    -- Check if user is the owner
    SELECT EXISTS (
        SELECT 1 FROM conversations
        WHERE id = p_conversation_id AND user_id = p_user_id
    ) INTO v_is_owner;

    IF v_is_owner THEN
        RETURN TRUE;
    END IF;

    -- Check shares
    SELECT permission INTO v_permission
    FROM conversation_shares
    WHERE conversation_id = p_conversation_id
    AND shared_with_id = p_user_id
    AND accepted_at IS NOT NULL
    LIMIT 1;

    IF v_permission IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check permission level
    IF p_required_permission = 'view' THEN
        RETURN TRUE;
    ELSIF p_required_permission = 'comment' THEN
        RETURN v_permission IN ('comment', 'edit');
    ELSIF p_required_permission = 'edit' THEN
        RETURN v_permission = 'edit';
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
