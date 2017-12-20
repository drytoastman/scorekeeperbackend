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


CREATE TABLE tempcache (
    key       TEXT      PRIMARY KEY,
    data      JSONB     NOT NULL DEFAULT '{}'
);
REVOKE ALL ON tempcache FROM public;
GRANT ALL  ON tempcache TO localuser;
COMMENT ON TABLE tempcache IS 'Local only table that can be used for caching data on the webserver, only needs to be on the main server, localuser required to access, no remotes';


DELETE FROM payments;
ALTER TABLE payments DROP COLUMN accountid;
ALTER TABLE payments ADD  COLUMN itemid TEXT NOT NULL REFERENCES paymentitems;
ALTER TABLE payments DROP COLUMN amount;

