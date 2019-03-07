CREATE TABLE challengestaging (
    challengeid UUID       PRIMARY KEY REFERENCES challenges ON DELETE CASCADE ON UPDATE CASCADE,
    stageinfo   JSONB      NOT NULL,
    modified    TIMESTAMP  NOT NULL DEFAULT now()
);
REVOKE ALL ON challengestaging FROM public;
GRANT  ALL ON challengestaging TO <seriesname>;
CREATE TRIGGER cstgmod AFTER INSERT OR UPDATE OR DELETE ON challengestaging FOR EACH ROW EXECUTE PROCEDURE logmods('<seriesname>.serieslog');
CREATE TRIGGER cstguni BEFORE UPDATE ON challengestaging FOR EACH ROW EXECUTE PROCEDURE updatechecks('challengeid');
COMMENT ON TABLE challengestaging IS 'the challenge staging info, json structure of ordered data pointing to challenge rounds upper and lower';
