DROP TABLE timertimes;
CREATE TABLE timertimes(
    timeid   UUID       PRIMARY KEY,
    course   INTEGER    NOT NULL DEFAULT 1,
    raw      FLOAT      NOT NULL,
    status   VARCHAR(8) NOT NULL DEFAULT 'OK',
    attr     JSONB      NOT NULL,
    modified TIMESTAMP  NOT NULL DEFAULT now()
);
REVOKE ALL ON timertimes FROM public;
GRANT  ALL ON timertimes TO <seriesname>;
CREATE TRIGGER timmod AFTER INSERT OR UPDATE OR DELETE ON timertimes FOR EACH ROW EXECUTE PROCEDURE logmods('<seriesname>.serieslog');
CREATE TRIGGER timuni BEFORE UPDATE ON timertimes FOR EACH ROW EXECUTE PROCEDURE updatechecks('timeid');
COMMENT ON TABLE timertimes IS 'The list of all times received by data entry via whatever timer is active';

