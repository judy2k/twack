-- All dates & times are stored in UTC:
SET TIMEZONE TO 'UTC';

-- versions Table -------------------------------------------------------------
-- Stores the schema versions that have been loaded:
CREATE TABLE versions (
  version_number INTEGER                  NOT NULL UNIQUE,
  added_dt       TIMESTAMP WITH TIME ZONE NOT NULL
    DEFAULT CURRENT_TIMESTAMP
);

-- relationship_load Table ----------------------------------------------------
CREATE SEQUENCE relationship_load_id_seq;
CREATE TABLE relationship_load (
  id         INTEGER PRIMARY KEY
    DEFAULT nextval('relationship_load_id_seq'),
  account_id BIGINT                   NOT NULL,
  followers  BIGINT []                NOT NULL,
  friends    BIGINT []                NOT NULL,
  added_dt   TIMESTAMP WITH TIME ZONE NOT NULL UNIQUE,
  CHECK (EXTRACT(TIMEZONE FROM added_dt) = '0')  -- ensure UTC
);
ALTER SEQUENCE relationship_load_id_seq OWNED BY relationship_load.id;

-- twitter_account Table ------------------------------------------------------
CREATE TABLE twitter_account (
  id           BIGINT PRIMARY KEY,
  screen_name  VARCHAR(128) UNIQUE,
  account_name VARCHAR(256),
  added_dt     TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_dt   TIMESTAMP WITH TIME ZONE NOT NULL,
  CHECK (EXTRACT(TIMEZONE FROM added_dt) = '0'), -- ensure UTC
  CHECK (EXTRACT(TIMEZONE FROM updated_dt) = '0')  -- ensure UTC
);

-- relationship_event Table ---------------------------------------------------
CREATE TYPE event_verb AS ENUM ('follow', 'unfollow');
CREATE SEQUENCE relationship_event_id_seq;
CREATE TABLE relationship_event (
  id             INTEGER PRIMARY KEY
    DEFAULT nextval('relationship_event_id_seq'),
  subject_id     BIGINT                   NOT NULL, -- REFERENCES twitter_account,
  verb           event_verb               NOT NULL,
  object_id      BIGINT                   NOT NULL, -- REFERENCES twitter_account,
  event_start_dt TIMESTAMP WITH TIME ZONE NOT NULL,
  event_end_dt   TIMESTAMP WITH TIME ZONE NOT NULL,
  CHECK (EXTRACT(TIMEZONE FROM event_start_dt) = '0'), -- ensure UTC
  CHECK (EXTRACT(TIMEZONE FROM event_end_dt) = '0')    -- ensure UTC
);

-- Avoid duplicate events:
CREATE UNIQUE INDEX unique_event ON relationship_event (
  subject_id, verb, object_id, event_start_dt, event_end_dt
);
ALTER SEQUENCE relationship_event_id_seq OWNED BY relationship_event.id;

-- Register that this schema is version 1:
INSERT INTO versions (version_number) VALUES (1);

