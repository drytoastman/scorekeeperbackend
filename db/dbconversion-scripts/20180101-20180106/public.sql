ALTER TABLE drivers ADD COLUMN created TIMESTAMP NOT NULL DEFAULT now();
UPDATE drivers SET created='epoch';
