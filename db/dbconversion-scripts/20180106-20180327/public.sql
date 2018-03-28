CREATE OR REPLACE FUNCTION upgrade(IN seriesscript varchar, IN publicscript varchar, IN newversion varchar) RETURNS boolean AS $body$
DECLARE
    cmds text[];
    schema text;
BEGIN
    FOR schema IN SELECT nspname FROM pg_catalog.pg_namespace where nspname !~ '^pg_' and nspname not in ('information_schema', 'public')
    LOOP
        PERFORM set_config('search_path', schema||',public', true);
        SELECT regexp_split_to_array(replace(replace(seriesscript, '<seriesname>', schema), '\r\n', ''), ';') INTO cmds;
        FOR i in 1 .. array_upper(cmds, 1)
        LOOP
            EXECUTE cmds[i];
        END LOOP;
    END LOOP;
    PERFORM set_config('search_path', 'public', true);
    EXECUTE publicscript;
    UPDATE version SET version=newversion,modified='now()';
    RETURN TRUE;
END;
$body$
LANGUAGE plpgsql;
REVOKE ALL ON FUNCTION upgrade(varchar, varchar, varchar) FROM public;
