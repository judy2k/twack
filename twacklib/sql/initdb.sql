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

CREATE OR REPLACE FUNCTION previous_relationship_load(TIMESTAMP WITH TIME ZONE)
  RETURNS relationship_load
AS $$
SELECT r_data.*
FROM relationship_load r_data
  INNER JOIN (
               SELECT MAX(added_dt) added_dt
               FROM relationship_load
               WHERE added_dt < $1
             ) r_filter
    ON r_filter.added_dt = r_data.added_dt;
$$ LANGUAGE SQL;
COMMENT ON FUNCTION previous_relationship_load(TIMESTAMP WITH TIME ZONE)
IS 'Return the most recent load before the provided timestamp.';

CREATE OR REPLACE FUNCTION create_events()
  RETURNS VOID
AS $$
INSERT INTO relationship_event (
  subject_id, verb, object_id, event_start_dt, event_end_dt
)
  SELECT
    follower.id,
    'unfollow' :: event_verb,
    follower.ac_id,
    (SELECT added_dt
     FROM relationship_load rl
     WHERE rl.id = 3),
    (SELECT added_dt
     FROM relationship_load rl
     WHERE rl.id = 4)
  FROM (
         SELECT
           unnest(rl1.followers) id,
           rl1.account_id        ac_id
         FROM relationship_load AS rl1
         WHERE rl1.id = 3)
    AS follower
  WHERE id NOT IN (
    SELECT unnest(rl2.followers)
    FROM relationship_load rl2
    WHERE rl2.id = 4)
  UNION
  SELECT
    follower.id,
    'follow' :: event_verb,
    follower.ac_id,
    (SELECT added_dt
     FROM relationship_load rl
     WHERE rl.id = 3),
    (SELECT added_dt
     FROM relationship_load rl
     WHERE rl.id = 4)
  FROM (
         SELECT
           unnest(rl1.followers) id,
           rl1.account_id        ac_id,
           rl1.added_dt          added_dt
         FROM relationship_load AS rl1
         WHERE rl1.id = 4
       ) AS follower
  WHERE id NOT IN (
    SELECT unnest(rl2.followers)
    FROM relationship_load rl2
    WHERE rl2.id = 3
  )
  UNION
  SELECT
    ac_id,
    'unfollow' :: event_verb,
    friend.id,
    (SELECT added_dt
     FROM relationship_load rl
     WHERE rl.id = 3),
    (SELECT added_dt
     FROM relationship_load rl
     WHERE rl.id = 4)
  FROM (
         SELECT
           unnest(rl.friends) id,
           rl.account_id      ac_id,
           rl.added_dt        added_dt
         FROM relationship_load AS rl
         WHERE rl.id = 3
       ) AS friend
  WHERE id NOT IN (
    SELECT unnest(rl.friends)
    FROM relationship_load rl
    WHERE rl.id = 4
  )
  UNION
  SELECT
    ac_id,
    'follow' :: event_verb,
    friend.id,
    (SELECT added_dt
     FROM relationship_load rl
     WHERE rl.id = 3),
    (SELECT added_dt
     FROM relationship_load rl
     WHERE rl.id = 4)
  FROM (
         SELECT
           unnest(rl.friends) id,
           rl.account_id      ac_id,
           rl.added_dt        added_dt
         FROM relationship_load AS rl
         WHERE rl.id = 4
       ) AS friend
  WHERE id NOT IN (
    SELECT unnest(rl.friends)
    FROM relationship_load rl
    WHERE rl.id = 3
  );
$$ LANGUAGE SQL;
