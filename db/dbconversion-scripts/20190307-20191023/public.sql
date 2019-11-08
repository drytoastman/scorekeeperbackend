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


CREATE OR REPLACE FUNCTION verify_user(IN name varchar, IN password varchar) RETURNS boolean AS $body$
DECLARE
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename=name) THEN
        EXECUTE format('CREATE USER %I PASSWORD %L', name, password);
    ELSE
        EXECUTE format('ALTER USER %I PASSWORD %L', name, password);
    END IF;
    EXECUTE format('INSERT INTO localcache (name, data) VALUES (%L, %L) ON CONFLICT (name) DO UPDATE SET data=%L', name, password, password);
    RETURN TRUE;
END;
$body$
LANGUAGE plpgsql;
COMMENT ON FUNCTION verify_user(varchar, varchar) IS 'If user does not exist, create.  If it does exist, update password';


CREATE TABLE localcache (
    name TEXT PRIMARY KEY,
    data TEXT
);
REVOKE ALL ON localcache FROM public;
GRANT  ALL ON localcache TO mergeaccess;
