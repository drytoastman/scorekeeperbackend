ALTER TABLE drivers ADD COLUMN created NOT NULL DEFAULT now();
ALTER TABLE events  ADD COLUMN created NOT NULL DEFAULT now();
ALTER TABLE cars    ADD COLUMN created NOT NULL DEFAULT now();
