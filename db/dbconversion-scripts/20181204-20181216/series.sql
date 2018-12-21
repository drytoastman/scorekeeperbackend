
ALTER TABLE events ADD COLUMN isexternal BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE externalresults (
    eventid   UUID NOT NULL REFERENCES events,
    classcode VARCHAR(16) NOT NULL REFERENCES classlist, 
    driverid  UUID NOT NULL REFERENCES drivers,
    net       FLOAT NOT NULL,
    modified  TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (eventid, classcode, driverid)
);
REVOKE ALL ON externalresults FROM public;
GRANT  ALL ON externalresults TO <seriesname>;
CREATE TRIGGER externalmod AFTER INSERT OR UPDATE OR DELETE ON externalresults FOR EACH ROW EXECUTE PROCEDURE logmods('<seriesname>.serieslog');
CREATE TRIGGER externaluni BEFORE UPDATE ON externalresults FOR EACH ROW EXECUTE PROCEDURE updatechecks('eventid', 'classcode', 'driverid');
COMMENT ON TABLE externalresults IS 'Results for external events to apply to local series, used for integrating national pro points without run data';
