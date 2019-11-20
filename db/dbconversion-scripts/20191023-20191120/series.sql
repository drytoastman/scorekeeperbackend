CREATE TABLE seriesattr (
    driverid UUID       PRIMARY KEY REFERENCES public.drivers,
    attr     JSONB      NOT NULL DEFAULT '{}',
    modified TIMESTAMP  NOT NULL DEFAULT now()
);
REVOKE ALL ON seriesattr FROM public;
GRANT  ALL ON seriesattr TO <seriesname>;
CREATE TRIGGER seriesattrmod AFTER INSERT OR UPDATE OR DELETE ON seriesattr FOR EACH ROW EXECUTE PROCEDURE logmods('<seriesname>.serieslog');
CREATE TRIGGER seriesattruni BEFORE UPDATE ON seriesattr FOR EACH ROW EXECUTE PROCEDURE updatechecks('driverid');
COMMENT ON TABLE seriesattr IS 'seriesattr records extra driver information that is specific to just this series';
