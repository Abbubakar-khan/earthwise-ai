-- EARTHWISE AI user dataset storage
-- Apply once to the target Neon branch using a migration/admin role.
-- The application runtime only performs parameterized DML and SELECTs.

CREATE TABLE IF NOT EXISTS public.earthwise_user_datasets (
    id UUID PRIMARY KEY,
    workspace_hash CHAR(64) NOT NULL,
    filename TEXT NOT NULL,
    file_format TEXT NOT NULL,
    row_count INTEGER NOT NULL CHECK (row_count >= 0),
    column_names JSONB NOT NULL,
    records JSONB NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS earthwise_user_datasets_workspace_idx
    ON public.earthwise_user_datasets (workspace_hash, uploaded_at DESC);
