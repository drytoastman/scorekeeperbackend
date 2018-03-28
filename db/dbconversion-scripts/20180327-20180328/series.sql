CREATE TABLE weekendmembers (
    membership    INTEGER     NOT NULL,
    driverid      UUID        NOT NULL REFERENCES public.drivers, 
    startdate     DATE        NOT NULL,
    enddate       DATE        NOT NULL,
    issuer        TEXT        NOT NULL,
    issuermem     TEXT        NOT NULL,
    region        TEXT        NOT NULL,
    area          TEXT        NOT NULL,
    modified      TIMESTAMP   NOT NULL DEFAULT now()
);
REVOKE ALL ON weekendmembers FROM public;
GRANT  ALL ON weekendmembers TO <seriesname>;
CREATE TRIGGER weekmod AFTER INSERT OR UPDATE OR DELETE ON weekendmembers FOR EACH ROW EXECUTE PROCEDURE logmods('<seriesname>.serieslog');
CREATE TRIGGER weekuni BEFORE UPDATE ON weekendmembers FOR EACH ROW EXECUTE PROCEDURE updatechecks();
COMMENT ON TABLE weekendmembers IS 'A table for storing weekend membership information';

