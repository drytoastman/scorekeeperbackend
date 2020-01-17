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


CREATE TRIGGER  localeventstreammod AFTER INSERT OR UPDATE OR DELETE ON localeventstream FOR EACH ROW EXECUTE PROCEDURE notifymods();
