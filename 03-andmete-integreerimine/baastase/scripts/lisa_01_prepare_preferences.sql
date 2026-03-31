CREATE TABLE IF NOT EXISTS staging.notification_preferences (
    email TEXT PRIMARY KEY,
    newsletter_opt_in BOOLEAN,
    preferred_channel TEXT,
    updated_at DATE,
    loaded_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE analytics.user_profile
ADD COLUMN IF NOT EXISTS newsletter_opt_in BOOLEAN;

ALTER TABLE analytics.user_profile
ADD COLUMN IF NOT EXISTS preferred_channel TEXT;
