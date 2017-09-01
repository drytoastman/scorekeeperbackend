--------------------------------------------------------------------------------------
--- Create top level results and drivers tables that every series shares

CREATE EXTENSION hstore;

CREATE USER localuser;
CREATE USER nulluser WITH PASSWORD 'nulluser';
CREATE ROLE driversaccess;
CREATE ROLE mergeaccess;
GRANT driversaccess TO localuser;
GRANT mergeaccess   TO localuser;

REVOKE ALL  ON SCHEMA public FROM public;
GRANT  ALL  ON SCHEMA public TO driversaccess;
GRANT USAGE ON SCHEMA public TO mergeaccess;
GRANT USAGE ON SCHEMA public TO nulluser;

-- Logs are specific to this machine
CREATE TABLE publiclog (
    logid   BIGSERIAL PRIMARY KEY,
    usern   TEXT      NOT NULL,
    app     TEXT      NOT NULL DEFAULT '',
    tablen  TEXT      NOT NULL,
    action  CHAR(1)   NOT NULL CHECK (action IN ('I', 'D', 'U')),
    time    TIMESTAMP NOT NULL,
    olddata JSONB     NOT NULL,
    newdata JSONB     NOT NULL
);
REVOKE ALL ON publiclog FROM public;
GRANT  ALL ON publiclog TO driversaccess;
GRANT  ALL ON publiclog_logid_seq TO driversaccess;
CREATE INDEX ON publiclog(logid);
CREATE INDEX ON publiclog(time);
COMMENT ON TABLE publiclog IS 'Change logs that are specific to this local database';


CREATE OR REPLACE FUNCTION logmods() RETURNS TRIGGER AS $body$
DECLARE
    audit_row publiclog;
BEGIN
    audit_row = ROW(NULL, session_user::text, current_setting('application_name'), TG_TABLE_NAME::text, SUBSTRING(TG_OP,1,1), CURRENT_TIMESTAMP, '{}', '{}');
    IF (TG_OP = 'UPDATE') THEN
        IF OLD = NEW THEN
            RETURN NULL;
        END IF;
        audit_row.olddata = to_jsonb(OLD.*);
        audit_row.newdata = to_jsonb(NEW.*);
        audit_row.time = NEW.modified;
    ELSIF (TG_OP = 'DELETE') THEN
        audit_row.olddata = to_jsonb(OLD.*);
        audit_row.newdata = '{}';
    ELSIF (TG_OP = 'INSERT') THEN
        audit_row.olddata = '{}';
        audit_row.newdata = to_jsonb(NEW.*);
        audit_row.time = NEW.modified;
    ELSE
        RETURN NULL;
    END IF;

    audit_row.logid = NEXTVAL(TG_ARGV[0] || '_logid_seq');
    EXECUTE format('INSERT INTO %I VALUES (($1).*)', quote_ident(TG_ARGV[0])) USING audit_row;
    EXECUTE pg_notify('datachange', TG_TABLE_NAME);
    RETURN NULL;
END;
$body$
LANGUAGE plpgsql;
COMMENT ON FUNCTION logmods() IS 'Function to log details of any insert, delete or update to a log table specified in first trigger arg';


CREATE OR REPLACE FUNCTION notifymods() RETURNS TRIGGER AS $body$
DECLARE
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        IF (OLD = NEW) THEN
            RETURN NULL;
        END IF;
    END IF;
    EXECUTE pg_notify('datachange', TG_TABLE_NAME);
    RETURN NULL;
END;
$body$
LANGUAGE plpgsql;
COMMENT ON FUNCTION notifymods() IS 'Send a notification when there are changes, no logging';


CREATE OR REPLACE FUNCTION ignoreunmodified() RETURNS TRIGGER AS $body$
DECLARE
    app text;
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        app = current_setting('application_name');
        IF ((app = 'synclocal') OR (app = 'syncremote')) THEN
            RETURN NEW;
        END IF;
        IF (OLD = NEW) THEN
            RETURN NULL;
        END IF;
        IF akeys(hstore(NEW) - hstore(OLD)) = ARRAY['modified'] THEN
            RETURN NULL;
        END IF;
    END IF;
    RETURN NEW;
END;
$body$
LANGUAGE plpgsql;
COMMENT ON FUNCTION ignoreunmodified() IS 'does not update rows if only change is the modified field or less (and not syncing)';


CREATE OR REPLACE FUNCTION create_series(IN name varchar) RETURNS boolean AS $body$
DECLARE
    cmds text[];
BEGIN
    SELECT regexp_split_to_array(replace(replace(pg_read_file('series.sql'), '<seriesname>', name), '\r\n', ''), ';') INTO cmds;
    FOR i in 1 .. array_upper(cmds, 1)
    LOOP
        EXECUTE cmds[i];
    END LOOP;
    RETURN TRUE;
END;
$body$
LANGUAGE plpgsql;
COMMENT ON FUNCTION create_series(varchar) IS 'reads in series template, replaces series variable name and executes the commands, requires series user to be present';


-- The results table acts as a storage of calculated results and information for each series.  As enough information
-- will exist here to supply the results set of pages, we can delete old series schema, release old unused driver
-- information and solidify the driver information for older series (name changes, etc).
CREATE TABLE results (
    series     TEXT        NOT NULL,
    name       TEXT        NOT NULL,
    data       JSONB       NOT NULL,
    modified   TIMESTAMP   NOT NULL DEFAULT now(),
    PRIMARY KEY (series, name)
);
REVOKE ALL ON results FROM public;
GRANT  ALL ON results TO driversaccess;
-- Everyone can view results but only owner can insert, update, delete their rows
ALTER TABLE results ENABLE ROW LEVEL SECURITY;
CREATE POLICY all_view ON results FOR SELECT USING (true);
CREATE POLICY own_mod1 ON results FOR INSERT WITH CHECK (series = current_user);
CREATE POLICY own_mod2 ON results FOR UPDATE USING (series = current_user);
CREATE POLICY own_mod3 ON results FOR DELETE USING (series = current_user);
COMMENT ON TABLE results IS 'The stored list of JSON data represent event results, champ results and series related display settings';


-- attr includes alias, address, city, state, zip, phone, brag, sponsor, emergency, notes, etc
CREATE TABLE drivers (
    driverid   UUID        PRIMARY KEY, 
    firstname  TEXT        NOT NULL, 
    lastname   TEXT        NOT NULL, 
    email      TEXT        NOT NULL,
    username   TEXT        NOT NULL DEFAULT '',
    password   TEXT        NOT NULL DEFAULT '',
    membership TEXT        NOT NULL DEFAULT '',
    attr       JSONB       NOT NULL DEFAULT '{}', 
    modified   TIMESTAMP   NOT NULL DEFAULT now(),
    CONSTRAINT uniqueuser UNIQUE(username)
);
CREATE INDEX ON drivers(lower(firstname));
CREATE INDEX ON drivers(lower(lastname));
REVOKE ALL   ON drivers FROM public;
GRANT  ALL   ON drivers TO driversaccess;
CREATE TRIGGER driversmod AFTER INSERT OR UPDATE OR DELETE ON drivers FOR EACH ROW EXECUTE PROCEDURE logmods('publiclog');
CREATE TRIGGER driversuni BEFORE UPDATE ON drivers FOR EACH ROW EXECUTE PROCEDURE ignoreunmodified();
COMMENT ON TABLE drivers IS 'The global list of drivers for all series';


CREATE TABLE mergeservers (
    serverid   UUID       PRIMARY KEY,
    hostname   TEXT       NOT NULL DEFAULT '',
    address    TEXT       NOT NULL DEFAULT '',
    hosttype   TEXT       NOT NULL DEFAULT 'discovered',
    discovered TIMESTAMP  NOT NULL DEFAULT 'epoch',
    lastcheck  TIMESTAMP  NOT NULL DEFAULT 'epoch',
    active     BOOLEAN    NOT NULL DEFAULT False,
    mergenow   BOOLEAN    NOT NULL DEFAULT False,
    mergestate JSONB      NOT NULL DEFAULT '{}'
);
REVOKE ALL   ON mergeservers FROM public;
GRANT  ALL   ON mergeservers TO mergeaccess;
GRANT SELECT ON mergeservers TO nulluser;
CREATE TRIGGER  mergemod AFTER INSERT OR UPDATE OR DELETE ON mergeservers FOR EACH ROW EXECUTE PROCEDURE notifymods();
COMMENT ON TABLE mergeservers IS 'Local state of other sevrers we are periodically merging with, not part of merge process';

