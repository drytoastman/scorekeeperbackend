-- Create a template series for introspection with user that can't login
CREATE ROLE template;
SELECT verify_series('template');

