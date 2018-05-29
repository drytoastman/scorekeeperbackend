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
        IF akeys(newrow - oldrow) = ARRAY['modified'] THEN
            RETURN NULL;
        END IF;
    END IF;
    RETURN NEW;
END;
$body$
LANGUAGE plpgsql;

ALTER TABLE mergeservers ADD COLUMN quickruns BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE localeventstream (
    etype TEXT      NOT NULL,
    event JSONB     NOT NULL,
    time  TIMESTAMP NOT NULL
);
REVOKE ALL   ON localeventstream FROM public;
GRANT  ALL   ON localeventstream TO mergeaccess;
COMMENT ON TABLE localeventstream IS 'Local events useful for serving up to the announcer interface, not merged';

