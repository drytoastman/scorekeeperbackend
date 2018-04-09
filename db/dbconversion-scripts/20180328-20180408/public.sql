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

