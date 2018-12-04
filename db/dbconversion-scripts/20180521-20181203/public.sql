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

  -- check that the cars don't exist in another runorder on the same course
  IF (SELECT NEW.cars && array_agg(c) FROM (SELECT unnest(cars) FROM runorder WHERE eventid=NEW.eventid AND course=NEW.course AND rungroup!=NEW.rungroup) AS dt(c) ) THEN
      RAISE EXCEPTION 'Car cannot be in multiple rungroups with the same course';
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

CREATE TABLE IF NOT EXISTS emailqueue (
    mailid  BIGSERIAL PRIMARY KEY,
    created TIMESTAMP NOT NULL DEFAULT now(),
    content JSONB     NOT NULL DEFAULT '{}'
);
REVOKE ALL ON emailqueue FROM public;
GRANT  ALL ON emailqueue TO mergeaccess;
GRANT  ALL ON emailqueue_mailid_seq TO mergeaccess;
COMMENT ON TABLE emailqueue IS 'temporary storage for items the web interface wants send, mailman will consume and delete';


CREATE TABLE IF NOT EXISTS unsubscribe (
    driverid    UUID NOT NULL REFERENCES drivers,
    emaillistid TEXT NOT NULL,
    PRIMARY KEY (driverid, emaillistid)
);
REVOKE ALL ON unsubscribe FROM public;
GRANT  ALL ON unsubscribe TO mergeaccess;
COMMENT ON TABLE unsubscribe IS 'map of emaillistids a driverid has unsubscribed from, (i.e. nwr)';

CREATE TABLE IF NOT EXISTS emailfailures(
    email  TEXT,
    status TEXT,
    time   TIMESTAMP NOT NULL DEFAULT now()
);
REVOKE ALL ON emailfailures FROM public;
GRANT  ALL ON emailfailures TO mergeaccess;
