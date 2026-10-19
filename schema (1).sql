CREATE TABLE sources (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  source_type TEXT NOT NULL,
  trust_level SMALLINT NOT NULL DEFAULT 3 CHECK (trust_level BETWEEN 1 AND 5),
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  last_attempt_at TIMESTAMPTZ,
  last_success_at TIMESTAMPTZ,
  last_error TEXT
);

CREATE TABLE tournaments (
  id BIGSERIAL PRIMARY KEY,
  canonical_key TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  sport TEXT NOT NULL CHECK (sport IN ('golf', 'mini_golf', 'other')),
  start_date DATE,
  end_date DATE,
  country TEXT,
  region TEXT,
  city TEXT,
  venue TEXT,
  level TEXT,
  status TEXT NOT NULL DEFAULT 'unknown',
  organizer TEXT,
  registration_url TEXT,
  regulations_url TEXT,
  winner TEXT,
  score TEXT,
  source_id BIGINT REFERENCES sources(id),
  source_url TEXT,
  source_excerpt TEXT,
  confidence NUMERIC(4,3),
  verified_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tournament_results (
  id BIGSERIAL PRIMARY KEY,
  tournament_id BIGINT NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
  participant_name TEXT NOT NULL,
  team_name TEXT,
  place INTEGER,
  total_score TEXT,
  round_scores JSONB,
  is_official BOOLEAN NOT NULL DEFAULT FALSE,
  source_url TEXT,
  verified_at TIMESTAMPTZ
);

CREATE TABLE change_log (
  id BIGSERIAL PRIMARY KEY,
  tournament_id BIGINT REFERENCES tournaments(id) ON DELETE SET NULL,
  field_name TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  source_url TEXT NOT NULL,
  detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  review_required BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE articles (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  language TEXT NOT NULL DEFAULT 'ru',
  source_urls JSONB NOT NULL DEFAULT '[]'::jsonb,
  generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'draft',
  model_name TEXT
);

CREATE INDEX tournaments_dates_idx ON tournaments(start_date, end_date);
CREATE INDEX tournaments_country_level_idx ON tournaments(country, level);
CREATE INDEX results_tournament_place_idx ON tournament_results(tournament_id, place);
