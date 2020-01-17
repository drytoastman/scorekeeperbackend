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
    EXECUTE pg_notify(TG_TABLE_NAME, TG_TABLE_SCHEMA);
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
    EXECUTE pg_notify(TG_TABLE_NAME, TG_TABLE_SCHEMA);
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
        IF oldrow -> 'modified' = newrow -> 'modified' THEN
            RAISE EXCEPTION 'Updating without changing modification time';
        END IF;
        IF ((app = 'synclocal') OR (app = 'syncremote')) THEN
            RETURN NEW;
        END IF;
        IF akeys(newrow - oldrow) = ARRAY['modified'] THEN
            -- sliently ignored updates that are only a change to modification time
            RETURN NULL;
        END IF;
    END IF;
    RETURN NEW;
END;
$body$
LANGUAGE plpgsql;
COMMENT ON FUNCTION updatechecks() IS 'Do not UPDATE rows if there are no changes or the only change is [modified] (except when syncing), also disallow some primary key changes in UPDATE';


CREATE OR REPLACE FUNCTION runorderconstraints() RETURNS TRIGGER AS $body$
DECLARE
  _carid UUID;
BEGIN
  -- check that the carids exist in the cars table
  IF NEW.cars IS NULL THEN
    RAISE EXCEPTION 'Runorder list cannot be null';
  END IF;

  FOREACH _carid IN ARRAY NEW.cars LOOP
    IF NOT EXISTS (SELECT 1 FROM cars WHERE carid = _carid) THEN
      RAISE EXCEPTION 'Attempting to create a row with an unknown carid';
    END IF;
  END LOOP;

  IF (EXISTS (select unnest(NEW.cars) as v group by v having count(*) > 1)) THEN
    RAISE EXCEPTION 'You cannot add a car multiple times to the same rungroup';
  END IF;

  RETURN NEW;
END;
$body$
LANGUAGE plpgsql;
COMMENT ON FUNCTION runorderconstraints() IS 'Complex check of constraints for cars ARRAY in runorder';


CREATE OR REPLACE FUNCTION classorderconstraints() RETURNS TRIGGER AS $body$
DECLARE
  _code TEXT;
BEGIN
  -- check that the classcodes exist in the classlist table
  IF NEW.classes IS NULL THEN
    RAISE EXCEPTION 'Class order list cannot be null';
  END IF;

  FOREACH _code IN ARRAY NEW.classes LOOP
    IF NOT EXISTS (SELECT 1 FROM classlist WHERE classcode = _code) THEN
      RAISE EXCEPTION 'Attempting to create a row with an unknown class code';
    END IF;
  END LOOP;

  -- check that the classes don't exist in another group for the same event
  IF (SELECT NEW.classes && array_agg(c) FROM (SELECT unnest(classes) FROM classorder WHERE eventid=NEW.eventid AND rungroup!=NEW.rungroup) AS dt(c) ) THEN
      RAISE EXCEPTION 'Class cannot be in multiple rungroups for the same event';
  END IF;

  RETURN NEW;
END;
$body$
LANGUAGE plpgsql;
COMMENT ON FUNCTION classorderconstraints() IS 'Complex check of constraints for classes ARRAY in classorder';


CREATE OR REPLACE FUNCTION verify_user(IN name varchar, IN password varchar) RETURNS boolean AS $body$
DECLARE
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename=name) THEN
        EXECUTE format('CREATE USER %I PASSWORD %L', name, password);
    ELSE
        EXECUTE format('ALTER USER %I PASSWORD %L', name, password);
    END IF;
    EXECUTE format('INSERT INTO localcache (name, data) VALUES (%L, %L) ON CONFLICT (name) DO UPDATE SET data=%L', name, password, password);
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
        SELECT regexp_split_to_array(replace(replace(seriesscript, '<seriesname>', schema), '\r\n', ''), ';') INTO cmds;
        FOR i in 1 .. array_upper(cmds, 1)
        LOOP
            EXECUTE cmds[i];
        END LOOP;
    END LOOP;
    PERFORM set_config('search_path', 'public', true);
    EXECUTE publicscript;
    UPDATE version SET version=newversion,modified='now()';
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
    barcode    TEXT        NOT NULL DEFAULT '',
    optoutmail BOOLEAN     NOT NULL DEFAULT FALSE,
    attr       JSONB       NOT NULL DEFAULT '{}', 
    modified   TIMESTAMP   NOT NULL DEFAULT now(),
    created    TIMESTAMP   NOT NULL DEFAULT now(),
    CONSTRAINT uniqueusername UNIQUE (username)
);
CREATE INDEX ON drivers(lower(firstname));
CREATE INDEX ON drivers(lower(lastname));
REVOKE ALL   ON drivers FROM public;
GRANT  ALL   ON drivers TO driversaccess;
CREATE TRIGGER driversmod AFTER INSERT OR UPDATE OR DELETE ON drivers FOR EACH ROW EXECUTE PROCEDURE logmods('publiclog');
CREATE TRIGGER driversuni BEFORE UPDATE ON drivers FOR EACH ROW EXECUTE PROCEDURE updatechecks('driverid');
COMMENT ON TABLE drivers IS 'The global list of drivers for all series';


CREATE TABLE weekendmembers (
    uniqueid      UUID        NOT NULL PRIMARY KEY,
    membership    INTEGER     NOT NULL,
    driverid      UUID        NOT NULL REFERENCES drivers, 
    startdate     DATE        NOT NULL,
    enddate       DATE        NOT NULL,
    issuer        TEXT        NOT NULL,
    issuermem     TEXT        NOT NULL,
    region        TEXT        NOT NULL,
    area          TEXT        NOT NULL,
    modified      TIMESTAMP   NOT NULL DEFAULT now()
);
REVOKE ALL ON weekendmembers FROM public;
GRANT  ALL ON weekendmembers TO driversaccess;
CREATE TRIGGER weekmod AFTER INSERT OR UPDATE OR DELETE ON weekendmembers FOR EACH ROW EXECUTE PROCEDURE logmods('publiclog');
CREATE TRIGGER weekuni BEFORE UPDATE ON weekendmembers FOR EACH ROW EXECUTE PROCEDURE updatechecks('uniqueid');
COMMENT ON TABLE weekendmembers IS 'A table for storing weekend membership information';
COMMENT ON COLUMN weekendmembers.uniqueid IS 'We provide our own unique id incase they use a second unconnected laptop to add a duplicate member number';

--- Everything under this point is not synced with other scorekeeper instances, they are local to this system only

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
    quickruns  TEXT,
    mergestate JSONB      NOT NULL DEFAULT '{}'
);
REVOKE ALL   ON mergeservers FROM public;
GRANT  ALL   ON mergeservers TO mergeaccess;
CREATE TRIGGER  mergemod AFTER INSERT OR UPDATE OR DELETE ON mergeservers FOR EACH ROW EXECUTE PROCEDURE notifymods();
COMMENT ON TABLE mergeservers IS 'Local state of other sevrers we are periodically merging with, not part of merge process';


CREATE TABLE localeventstream (
    etype TEXT      NOT NULL,
    event JSONB     NOT NULL,
    time  TIMESTAMP NOT NULL
);
CREATE INDEX ON localeventstream(time);
REVOKE ALL   ON localeventstream FROM public;
GRANT  ALL   ON localeventstream TO mergeaccess;
CREATE TRIGGER  localeventstreammod AFTER INSERT OR UPDATE OR DELETE ON localeventstream FOR EACH ROW EXECUTE PROCEDURE notifymods();
COMMENT ON TABLE localeventstream IS 'Local events useful for serving up to the announcer interface, not merged';


CREATE TABLE emailqueue (
    mailid  BIGSERIAL PRIMARY KEY,
    created TIMESTAMP NOT NULL DEFAULT now(),
    content JSONB     NOT NULL DEFAULT '{}'
);
REVOKE ALL ON emailqueue FROM public;
GRANT  ALL ON emailqueue TO mergeaccess;
GRANT  ALL ON emailqueue_mailid_seq TO mergeaccess;
COMMENT ON TABLE emailqueue IS 'temporary storage for items the web interface wants send, mailman will consume and delete';


CREATE TABLE unsubscribe (
    driverid    UUID NOT NULL REFERENCES drivers,
    emaillistid TEXT NOT NULL,
    PRIMARY KEY (driverid, emaillistid)
);
REVOKE ALL ON unsubscribe FROM public;
GRANT  ALL ON unsubscribe TO mergeaccess;
COMMENT ON TABLE unsubscribe IS 'map of emaillistids a driverid has unsubscribed from, (i.e. nwr)';

CREATE TABLE emailfailures(
    email  TEXT,
    status TEXT,
    time   TIMESTAMP NOT NULL DEFAULT now()
);
REVOKE ALL ON emailfailures FROM public;
GRANT  ALL ON emailfailures TO mergeaccess;

CREATE TABLE localcache (
    name TEXT PRIMARY KEY,
    data TEXT
);
REVOKE ALL ON localcache FROM public;
GRANT  ALL ON localcache TO mergeaccess;
