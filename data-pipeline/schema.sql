-- Regulatory requirements, loaded from data-pipeline/matrices/*.json by update_matrices.py.
-- Each regulator's rows are replaced as a whole, so the database always matches one
-- validated matrix version (recorded in matrix_versions).

CREATE TABLE IF NOT EXISTS regulators (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    short_name    TEXT NOT NULL,
    profession    TEXT NOT NULL,
    designation   TEXT NOT NULL,
    website       TEXT NOT NULL,
    verified_on   DATE NOT NULL,
    open_questions TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS sources (
    regulator_id  TEXT NOT NULL REFERENCES regulators(id) ON DELETE CASCADE,
    id            TEXT NOT NULL,
    title         TEXT NOT NULL,
    url           TEXT NOT NULL,
    retrieved_on  DATE NOT NULL,
    PRIMARY KEY (regulator_id, id)
);

CREATE TABLE IF NOT EXISTS pathways (
    regulator_id  TEXT NOT NULL REFERENCES regulators(id) ON DELETE CASCADE,
    id            TEXT NOT NULL,
    name          TEXT NOT NULL,
    summary       TEXT NOT NULL,
    source_id     TEXT NOT NULL,
    PRIMARY KEY (regulator_id, id),
    FOREIGN KEY (regulator_id, source_id) REFERENCES sources(regulator_id, id)
);

CREATE TABLE IF NOT EXISTS requirements (
    regulator_id  TEXT NOT NULL REFERENCES regulators(id) ON DELETE CASCADE,
    id            TEXT NOT NULL,
    category      TEXT NOT NULL,
    title         TEXT NOT NULL,
    description   TEXT NOT NULL,
    conditional   BOOLEAN NOT NULL DEFAULT FALSE,
    details       JSONB,
    source_id     TEXT NOT NULL,
    PRIMARY KEY (regulator_id, id),
    FOREIGN KEY (regulator_id, source_id) REFERENCES sources(regulator_id, id)
);

CREATE TABLE IF NOT EXISTS requirement_pathways (
    regulator_id   TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    pathway_id     TEXT NOT NULL,
    PRIMARY KEY (regulator_id, requirement_id, pathway_id),
    FOREIGN KEY (regulator_id, requirement_id) REFERENCES requirements(regulator_id, id) ON DELETE CASCADE,
    FOREIGN KEY (regulator_id, pathway_id) REFERENCES pathways(regulator_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
    regulator_id  TEXT NOT NULL REFERENCES regulators(id) ON DELETE CASCADE,
    id            TEXT NOT NULL,
    name          TEXT NOT NULL,
    description   TEXT NOT NULL,
    submitted_by  TEXT NOT NULL CHECK (submitted_by IN ('applicant', 'third_party', 'issuing_institution')),
    conditional   BOOLEAN NOT NULL DEFAULT FALSE,
    source_id     TEXT NOT NULL,
    PRIMARY KEY (regulator_id, id),
    FOREIGN KEY (regulator_id, source_id) REFERENCES sources(regulator_id, id)
);

CREATE TABLE IF NOT EXISTS fees (
    regulator_id  TEXT NOT NULL REFERENCES regulators(id) ON DELETE CASCADE,
    id            TEXT NOT NULL,
    name          TEXT NOT NULL,
    amount_cad    NUMERIC(10, 2) NOT NULL CHECK (amount_cad > 0),
    gst           TEXT NOT NULL CHECK (gst IN ('included', 'excluded')),
    refundable    BOOLEAN NOT NULL,
    period        TEXT,
    source_id     TEXT NOT NULL,
    PRIMARY KEY (regulator_id, id),
    FOREIGN KEY (regulator_id, source_id) REFERENCES sources(regulator_id, id)
);

CREATE TABLE IF NOT EXISTS timelines (
    regulator_id  TEXT NOT NULL REFERENCES regulators(id) ON DELETE CASCADE,
    id            TEXT NOT NULL,
    name          TEXT NOT NULL,
    max_days      INTEGER CHECK (max_days > 0),
    business_days BOOLEAN NOT NULL DEFAULT FALSE,
    description   TEXT,
    source_id     TEXT NOT NULL,
    PRIMARY KEY (regulator_id, id),
    FOREIGN KEY (regulator_id, source_id) REFERENCES sources(regulator_id, id)
);

CREATE TABLE IF NOT EXISTS competencies (
    regulator_id  TEXT NOT NULL REFERENCES regulators(id) ON DELETE CASCADE,
    code          TEXT NOT NULL,
    category      TEXT NOT NULL,
    name          TEXT NOT NULL,
    min_level     INTEGER,
    mandatory     BOOLEAN NOT NULL DEFAULT FALSE,
    source_id     TEXT NOT NULL,
    PRIMARY KEY (regulator_id, code),
    FOREIGN KEY (regulator_id, source_id) REFERENCES sources(regulator_id, id),
    CHECK (NOT mandatory OR min_level IS NOT NULL)
);

-- One row per load; content_hash identifies the exact matrix file that was applied.
CREATE TABLE IF NOT EXISTS matrix_versions (
    id            BIGSERIAL PRIMARY KEY,
    regulator_id  TEXT NOT NULL,
    content_hash  TEXT NOT NULL,
    verified_on   DATE NOT NULL,
    loaded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
