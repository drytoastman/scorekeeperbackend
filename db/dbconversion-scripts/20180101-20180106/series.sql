ALTER TABLE events  ADD COLUMN created TIMESTAMP NOT NULL DEFAULT now();
ALTER TABLE cars    ADD COLUMN created TIMESTAMP NOT NULL DEFAULT now();
UPDATE events SET created='epoch';
UPDATE cars SET created='epoch';
