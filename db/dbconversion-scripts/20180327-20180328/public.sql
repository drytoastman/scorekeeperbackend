CREATE OR REPLACE FUNCTION updatechecks() RETURNS TRIGGER AS $body$
DECLARE
    app text := current_setting('application_name');
    oldrow hstore := hstore(OLD);
    newrow hstore := hstore(NEW);
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        IF (OLD = NEW) THEN
            RETURN NULL;
        END IF;
        FOR ii IN 0..TG_NARGS LOOP
            IF (oldrow -> TG_ARGV[ii] != newrow -> TG_ARGV[ii]) THEN
                RAISE EXCEPTION 'Cannot use UPDATE to change % of the primary key', TG_ARGV[ii];
            END IF;
        END LOOP;
        IF oldrow -> 'modified' = newrow -> 'modified' THEN
            RAISE EXCEPTION 'Updating without changing modification time';
        END IF;
        IF ((app = 'synclocal') OR (app = 'syncremote')) THEN
            RETURN NEW;
        END IF;
        IF akeys(newrow - oldrow) = ARRAY['modified'] THEN
            RETURN NULL;
        END IF;
    END IF;
    RETURN NEW;
END;
$body$
LANGUAGE plpgsql;

ALTER TABLE drivers RENAME membership TO barcode;
