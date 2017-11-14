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
    otime   TIMESTAMP NOT NULL,
    ltime   TIMESTAMP NOT NULL,
    olddata JSONB     NOT NULL,
    newdata JSONB     NOT NULL
);
REVOKE ALL ON publiclog FROM public;
GRANT  ALL ON publiclog TO driversaccess;
GRANT  ALL ON publiclog_logid_seq TO driversaccess;
CREATE INDEX ON publiclog(otime);
CREATE INDEX ON publiclog(ltime);
COMMENT ON TABLE publiclog IS 'Change logs that are specific to this local database';


CREATE OR REPLACE FUNCTION logmods() RETURNS TRIGGER AS $body$
DECLARE
    audit_row publiclog;
BEGIN
    audit_row = ROW(NULL, session_user::text, current_setting('application_name'), TG_TABLE_NAME::text, SUBSTRING(TG_OP,1,1), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '{}', '{}');
    IF (TG_OP = 'UPDATE') THEN
        IF OLD = NEW THEN
            RETURN NULL;
        END IF;
        audit_row.olddata = to_jsonb(OLD.*);
        audit_row.newdata = to_jsonb(NEW.*);
        audit_row.otime = NEW.modified;
    ELSIF (TG_OP = 'DELETE') THEN
        audit_row.olddata = to_jsonb(OLD.*);
        audit_row.newdata = '{}';
    ELSIF (TG_OP = 'INSERT') THEN
        audit_row.olddata = '{}';
        audit_row.newdata = to_jsonb(NEW.*);
        audit_row.otime = NEW.modified;
    ELSE
        RETURN NULL;
    END IF;

    audit_row.logid = NEXTVAL(TG_ARGV[0] || '_logid_seq');
    EXECUTE 'INSERT INTO ' || TG_ARGV[0] || ' VALUES (($1).*)' USING audit_row;
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
COMMENT ON FUNCTION updatechecks() IS 'Do not UPDATE rows if there are no changes or the only change is [modified] (except when syncing), also disallow some primary key changes in UPDATE';


CREATE OR REPLACE FUNCTION verify_user(IN name varchar, IN password varchar) RETURNS boolean AS $body$
DECLARE
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename=name) THEN
        EXECUTE format('CREATE USER %I UNENCRYPTED PASSWORD %L', name, password);
    ELSE
        EXECUTE format('ALTER USER %I UNENCRYPTED PASSWORD %L', name, password);
    END IF;
    RETURN TRUE;
END;
$body$
LANGUAGE plpgsql;
COMMENT ON FUNCTION verify_user(varchar, varchar) IS 'If user does not exist, create.  If it does exist, update password';


CREATE OR REPLACE FUNCTION verify_series(IN name varchar) RETURNS boolean AS $body$
DECLARE
    cmds text[];
BEGIN
    IF NOT EXISTS (SELECT schema_name FROM information_schema.schemata WHERE schema_name=name) THEN
        SELECT regexp_split_to_array(replace(replace(pg_read_file('series.sql'), '<seriesname>', name), '\r\n', ''), ';') INTO cmds;
        FOR i in 1 .. array_upper(cmds, 1)
        LOOP
            EXECUTE cmds[i];
        END LOOP;
    END IF;
    RETURN TRUE;
END;
$body$
LANGUAGE plpgsql;
COMMENT ON FUNCTION verify_series(varchar) IS 'If series does not exist, reads in series template, replaces series variable name and executes the commands, requires series user to be present';


CREATE OR REPLACE FUNCTION upgrade(IN seriesscript varchar, IN publicscript varchar, IN newversion varchar) RETURNS boolean AS $body$
DECLARE
    cmds text[];
    schema text;
BEGIN
    FOR schema IN SELECT nspname FROM pg_catalog.pg_namespace where nspname !~ '^pg_' and nspname not in ('information_schema', 'public') 
    LOOP
        PERFORM set_config('search_path', schema||',public', true);
        EXECUTE seriesscript;
    END LOOP;
    PERFORM set_config('search_path', 'public', true);
    EXECUTE publicscript;
    UPDATE version SET version=newversion;
    RETURN TRUE;
END;
$body$
LANGUAGE plpgsql;
COMMENT ON FUNCTION upgrade(varchar, varchar, varchar) IS 'Run the upgrade scripts (series on each schema) and update the version to version, all within a transaction in case there is a failure';
REVOKE ALL ON FUNCTION upgrade(varchar, varchar, varchar) FROM public;


-- Single row table to set and track schema version
CREATE TABLE version (
    id       INTEGER   PRIMARY KEY CHECK (id=1),
    version  TEXT      NOT NULL,
    modified TIMESTAMP NOT NULL DEFAULT now()
);
REVOKE ALL    ON version FROM public;
GRANT  SELECT ON version TO driversaccess;
CREATE TRIGGER versionmod AFTER INSERT OR UPDATE OR DELETE ON version FOR EACH ROW EXECUTE PROCEDURE logmods('publiclog');
CREATE TRIGGER versionuni BEFORE UPDATE ON version FOR EACH ROW EXECUTE PROCEDURE updatechecks();


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
    optoutmail BOOLEAN     NOT NULL DEFAULT FALSE,
    attr       JSONB       NOT NULL DEFAULT '{}', 
    modified   TIMESTAMP   NOT NULL DEFAULT now(),
    CONSTRAINT uniqueusername UNIQUE (username)
);
CREATE INDEX ON drivers(lower(firstname));
CREATE INDEX ON drivers(lower(lastname));
REVOKE ALL   ON drivers FROM public;
GRANT  ALL   ON drivers TO driversaccess;
CREATE TRIGGER driversmod AFTER INSERT OR UPDATE OR DELETE ON drivers FOR EACH ROW EXECUTE PROCEDURE logmods('publiclog');
CREATE TRIGGER driversuni BEFORE UPDATE ON drivers FOR EACH ROW EXECUTE PROCEDURE updatechecks('driverid');
COMMENT ON TABLE drivers IS 'The global list of drivers for all series';


CREATE TABLE mergeservers (
    serverid   UUID       PRIMARY KEY,
    hostname   TEXT       NOT NULL DEFAULT '',
    address    TEXT       NOT NULL DEFAULT '',
    lastcheck  TIMESTAMP  NOT NULL DEFAULT 'epoch',
    nextcheck  TIMESTAMP  NOT NULL DEFAULT 'epoch',
    waittime   INTEGER    NOT NULL DEFAULT 60,
    ctimeout   INTEGER    NOT NULL DEFAULT 3,
    cfailures  INTEGER    NOT NULL DEFAULT 0,
    hoststate  CHAR(1)    NOT NULL DEFAULT 'I' CHECK (hoststate IN ('A', '1', 'I')),
    mergestate JSONB      NOT NULL DEFAULT '{}'
);
REVOKE ALL   ON mergeservers FROM public;
GRANT  ALL   ON mergeservers TO mergeaccess;
CREATE TRIGGER  mergemod AFTER INSERT OR UPDATE OR DELETE ON mergeservers FOR EACH ROW EXECUTE PROCEDURE notifymods();
COMMENT ON TABLE mergeservers IS 'Local state of other sevrers we are periodically merging with, not part of merge process';

