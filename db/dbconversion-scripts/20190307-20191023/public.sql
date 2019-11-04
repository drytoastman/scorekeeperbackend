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

  IF (EXISTS (select unnest(NEW.cars) as v group by v having count(*) > 1)) THEN
    RAISE EXCEPTION 'You cannot add a car multiple times to the same rungroup';
  END IF;

  RETURN NEW;
END;
$body$
LANGUAGE plpgsql;
COMMENT ON FUNCTION runorderconstraints() IS 'Complex check of constraints for cars ARRAY in runorder';
