-- Layer: consents
-- Each athlete's consent decisions, append-only like one_rep_maxes: the
-- newest row per (athlete_id, consent_type) is their current decision,
-- older rows stay as an audit trail. A notice_version bump re-prompts
-- athletes whose latest row is still on an older version (see issue #16).
-- Written by POST /api/consents, read by GET /api/consents.

CREATE TABLE IF NOT EXISTS `gen-lang-client-0937519537.Optimmax.consents` (
    athlete_id STRING NOT NULL,
    consent_type STRING NOT NULL,   -- 'data_storage' | 'share_logs'
    granted BOOL NOT NULL,
    notice_version STRING NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
