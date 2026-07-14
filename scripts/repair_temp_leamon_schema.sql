-- Repair an older shopping database so it matches the temp/leamon backend model.
-- Safe to rerun: every schema operation is guarded where PostgreSQL supports it.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE shops ADD COLUMN IF NOT EXISTS slug varchar(200);
ALTER TABLE shops ADD COLUMN IF NOT EXISTS description text NOT NULL DEFAULT '';
ALTER TABLE shops ADD COLUMN IF NOT EXISTS owner_id uuid;
ALTER TABLE shops ADD COLUMN IF NOT EXISTS category varchar(120);
ALTER TABLE shops ADD COLUMN IF NOT EXISTS logo_url varchar(512);
ALTER TABLE shops ADD COLUMN IF NOT EXISTS banner_url varchar(512);

UPDATE shops s
SET slug = regexp_replace(lower(s.name), '[^a-z0-9]+', '-', 'g')
WHERE s.slug IS NULL OR s.slug = '';

UPDATE shops s
SET owner_id = m.account_id
FROM managers m
WHERE s.manager_id = m.id
  AND s.owner_id IS NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'shops_slug_key'
      AND conrelid = 'shops'::regclass
  ) THEN
    ALTER TABLE shops ADD CONSTRAINT shops_slug_key UNIQUE (slug);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'shops_owner_id_fkey'
      AND conrelid = 'shops'::regclass
  ) THEN
    ALTER TABLE shops
      ADD CONSTRAINT shops_owner_id_fkey
      FOREIGN KEY (owner_id) REFERENCES accounts(id) ON DELETE RESTRICT;
  END IF;
END $$;

ALTER TABLE shops ALTER COLUMN owner_id SET NOT NULL;
ALTER TABLE shops ALTER COLUMN manager_id DROP NOT NULL;

DO $$
DECLARE
  constraint_name text;
BEGIN
  SELECT conname INTO constraint_name
  FROM pg_constraint
  WHERE conrelid = 'shops'::regclass
    AND conname LIKE '%status%check%'
  LIMIT 1;

  IF constraint_name IS NOT NULL THEN
    EXECUTE format('ALTER TABLE shops DROP CONSTRAINT %I', constraint_name);
  END IF;
END $$;

ALTER TABLE shops
  ADD CONSTRAINT shops_status_check
  CHECK (status IN ('pending', 'active', 'disabled', 'rejected', 'suspended', 'pending_deletion'));

ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS label varchar(100);
UPDATE payment_methods
SET label = initcap(replace(method_type, '_', ' '))
WHERE label IS NULL OR label = '';
ALTER TABLE payment_methods ALTER COLUMN label SET NOT NULL;
