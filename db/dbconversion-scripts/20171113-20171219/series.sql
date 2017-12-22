ALTER TABLE secrets RENAME TO paymentsecrets;


CREATE TABLE paymentitems (
    itemid    TEXT      PRIMARY KEY,
    accountid TEXT      NOT NULL REFERENCES paymentaccounts,
    name      TEXT      NOT NULL,
    price     INTEGER   NOT NULL DEFAULT 100,
    currency  CHAR(3)   NOT NULL DEFAULT 'USD',
    modified  TIMESTAMP NOT NULL DEFAULT now()
);
REVOKE ALL ON paymentitems FROM public;
GRANT  ALL ON paymentitems TO <seriesname>;
CREATE TRIGGER payitmmod AFTER INSERT OR UPDATE OR DELETE ON paymentitems FOR EACH ROW EXECUTE PROCEDURE logmods('<seriesname>.serieslog');
CREATE TRIGGER payitmuni BEFORE UPDATE ON paymentitems FOR EACH ROW EXECUTE PROCEDURE updatechecks('accountid');
COMMENT ON TABLE paymentitems IS 'the list of configured items for an account';


CREATE SEQUENCE ordercounter;
REVOKE ALL ON ordercounter FROM public;
GRANT ALL  ON ordercounter TO localuser;
COMMENT ON SEQUENCE ordercounter IS 'Unsynced counter for main server when counting orders for series payments';

CREATE TABLE tempcache (
    key       TEXT      PRIMARY KEY,
    data      JSONB     NOT NULL DEFAULT '{}'
);
REVOKE ALL ON tempcache FROM public;
GRANT ALL  ON tempcache TO localuser;
COMMENT ON TABLE tempcache IS 'Local only table that can be used for caching data on the webserver, only needs to be on the main server, localuser required to access, no remotes';


DROP TABLE registered;
CREATE TABLE registered (
    eventid    UUID      NOT NULL REFERENCES events,
    carid      UUID      NOT NULL REFERENCES cars,
    txid       TEXT,
    txtime     TIMESTAMP,
    itemname   TEXT,
    amount     FLOAT,
    modified   TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (eventid, carid)
);
CREATE INDEX ON registered(eventid);
REVOKE ALL ON registered FROM public;
GRANT  ALL ON registered TO <seriesname>;
CREATE TRIGGER regmod AFTER INSERT OR UPDATE OR DELETE ON registered FOR EACH ROW EXECUTE PROCEDURE logmods('<seriesname>.serieslog');
CREATE TRIGGER reguni BEFORE UPDATE ON registered FOR EACH ROW EXECUTE PROCEDURE updatechecks('eventid', 'carid');
COMMENT ON TABLE registered IS 'The list of cars registered for events along with any payment information';


DROP TABLE payments;

