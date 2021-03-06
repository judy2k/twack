DROP TABLE IF EXISTS relationship_load CASCADE;
DROP TABLE IF EXISTS versions CASCADE;
DROP TABLE IF EXISTS twitter_account CASCADE;
DROP TABLE IF EXISTS relationship_event CASCADE;
DROP TYPE  IF EXISTS event_verb CASCADE;
DROP FUNCTION IF EXISTS previous_relationship_load(TIMESTAMP WITH TIME ZONE) CASCADE;
DROP FUNCTION IF EXISTS create_events() CASCADE;
