-- Database migrations for Product Marketing MCP Agent
-- Automated email newsletters and blog content with review workflow

-- Table: marketing_content
-- Stores blog posts and email newsletter drafts
CREATE TABLE IF NOT EXISTS marketing_content (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('blog', 'newsletter')),
    title VARCHAR(500) NOT NULL,
    subject_line VARCHAR(200),
    content_html TEXT NOT NULL,
    content_markdown TEXT,
    featured_product_id VARCHAR(100),
    featured_product_title VARCHAR(500),
    featured_product_variants JSONB,
    topic_category VARCHAR(100) NOT NULL,
    target_audience VARCHAR(50) NOT NULL CHECK (target_audience IN ('d2c', 'b2b', 'both')),
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'pending_review', 'approved', 'sent', 'scheduled', 'rejected')),
    generated_by VARCHAR(100) DEFAULT 'product_marketing_agent',
    reviewed_by VARCHAR(255),
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    scheduled_send_date TIMESTAMP,
    sent_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_marketing_content_status ON marketing_content(status);
CREATE INDEX IF NOT EXISTS idx_marketing_content_type ON marketing_content(content_type);
CREATE INDEX IF NOT EXISTS idx_marketing_content_scheduled ON marketing_content(scheduled_send_date) WHERE status = 'scheduled';
CREATE INDEX IF NOT EXISTS idx_marketing_content_created ON marketing_content(created_at DESC);


-- Table: newsletter_recipients
-- Stores email recipients for newsletters (from Shopify customer API + newsletter activity API)
CREATE TABLE IF NOT EXISTS newsletter_recipients (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    shopify_customer_id VARCHAR(100),
    customer_type VARCHAR(50) DEFAULT 'd2c' CHECK (customer_type IN ('d2c', 'b2b', 'both')),
    subscribed BOOLEAN DEFAULT TRUE,
    subscription_source VARCHAR(100),
    tags JSONB,
    last_engagement_date TIMESTAMP,
    total_emails_sent INTEGER DEFAULT 0,
    total_emails_opened INTEGER DEFAULT 0,
    total_links_clicked INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_newsletter_recipients_email ON newsletter_recipients(email);
CREATE INDEX IF NOT EXISTS idx_newsletter_recipients_subscribed ON newsletter_recipients(subscribed) WHERE subscribed = TRUE;
CREATE INDEX IF NOT EXISTS idx_newsletter_recipients_customer_id ON newsletter_recipients(shopify_customer_id);


-- Table: newsletter_activity
-- Tracks email engagement (opens, clicks, bounces)
CREATE TABLE IF NOT EXISTS newsletter_activity (
    id SERIAL PRIMARY KEY,
    marketing_content_id INTEGER REFERENCES marketing_content(id) ON DELETE CASCADE,
    recipient_id INTEGER REFERENCES newsletter_recipients(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('sent', 'delivered', 'opened', 'clicked', 'bounced', 'unsubscribed', 'spam_report')),
    event_timestamp TIMESTAMP NOT NULL,
    link_url TEXT,
    user_agent TEXT,
    ip_address VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_newsletter_activity_content ON newsletter_activity(marketing_content_id);
CREATE INDEX IF NOT EXISTS idx_newsletter_activity_recipient ON newsletter_activity(recipient_id);
CREATE INDEX IF NOT EXISTS idx_newsletter_activity_event ON newsletter_activity(event_type, event_timestamp DESC);


-- Table: marketing_schedules
-- Manages recurring newsletter schedule (Tuesdays and Fridays)
CREATE TABLE IF NOT EXISTS marketing_schedules (
    id SERIAL PRIMARY KEY,
    schedule_name VARCHAR(255) NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
    send_time TIME NOT NULL DEFAULT '10:00:00',
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT TRUE,
    topic_rotation JSONB,
    last_run_date TIMESTAMP,
    next_run_date TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_marketing_schedules_active ON marketing_schedules(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_marketing_schedules_next_run ON marketing_schedules(next_run_date) WHERE is_active = TRUE;


-- Table: follow_up_campaigns
-- Stores AI-generated follow-up emails based on newsletter activity
CREATE TABLE IF NOT EXISTS follow_up_campaigns (
    id SERIAL PRIMARY KEY,
    original_marketing_content_id INTEGER REFERENCES marketing_content(id) ON DELETE SET NULL,
    target_segment VARCHAR(100) NOT NULL,
    segmentation_criteria JSONB,
    subject_line VARCHAR(200) NOT NULL,
    content_html TEXT NOT NULL,
    content_markdown TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'pending_review', 'approved', 'sent', 'rejected')),
    generated_by VARCHAR(100) DEFAULT 'product_marketing_agent',
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    scheduled_send_date TIMESTAMP,
    sent_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_follow_up_campaigns_status ON follow_up_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_follow_up_campaigns_original_content ON follow_up_campaigns(original_marketing_content_id);


-- View: newsletter_performance
-- Aggregated metrics for newsletter performance analysis
CREATE OR REPLACE VIEW newsletter_performance AS
SELECT
    mc.id AS content_id,
    mc.title,
    mc.subject_line,
    mc.content_type,
    mc.topic_category,
    mc.target_audience,
    mc.sent_at,
    COUNT(DISTINCT na.recipient_id) FILTER (WHERE na.event_type = 'sent') AS total_sent,
    COUNT(DISTINCT na.recipient_id) FILTER (WHERE na.event_type = 'delivered') AS total_delivered,
    COUNT(DISTINCT na.recipient_id) FILTER (WHERE na.event_type = 'opened') AS total_opened,
    COUNT(DISTINCT na.recipient_id) FILTER (WHERE na.event_type = 'clicked') AS total_clicked,
    COUNT(DISTINCT na.recipient_id) FILTER (WHERE na.event_type = 'bounced') AS total_bounced,
    ROUND(
        100.0 * COUNT(DISTINCT na.recipient_id) FILTER (WHERE na.event_type = 'opened') /
        NULLIF(COUNT(DISTINCT na.recipient_id) FILTER (WHERE na.event_type = 'delivered'), 0),
        2
    ) AS open_rate,
    ROUND(
        100.0 * COUNT(DISTINCT na.recipient_id) FILTER (WHERE na.event_type = 'clicked') /
        NULLIF(COUNT(DISTINCT na.recipient_id) FILTER (WHERE na.event_type = 'delivered'), 0),
        2
    ) AS click_rate
FROM marketing_content mc
LEFT JOIN newsletter_activity na ON mc.id = na.marketing_content_id
WHERE mc.status = 'sent'
GROUP BY mc.id, mc.title, mc.subject_line, mc.content_type, mc.topic_category, mc.target_audience, mc.sent_at;


-- View: top_engaged_recipients
-- Find most engaged newsletter subscribers for VIP campaigns
CREATE OR REPLACE VIEW top_engaged_recipients AS
SELECT
    nr.id,
    nr.email,
    nr.first_name,
    nr.last_name,
    nr.customer_type,
    nr.total_emails_sent,
    nr.total_emails_opened,
    nr.total_links_clicked,
    ROUND(
        100.0 * nr.total_emails_opened / NULLIF(nr.total_emails_sent, 0),
        2
    ) AS open_rate,
    ROUND(
        100.0 * nr.total_links_clicked / NULLIF(nr.total_emails_sent, 0),
        2
    ) AS click_rate,
    nr.last_engagement_date
FROM newsletter_recipients nr
WHERE nr.subscribed = TRUE
  AND nr.total_emails_sent > 0
ORDER BY nr.total_links_clicked DESC, nr.total_emails_opened DESC
LIMIT 100;


-- Insert default marketing schedules (Tuesday and Friday 10 AM UTC)
INSERT INTO marketing_schedules (schedule_name, day_of_week, send_time, timezone, is_active, topic_rotation)
VALUES
    ('Tuesday Newsletter', 1, '10:00:00', 'UTC', TRUE, '["partner_products", "credit_risk_solutions", "embedded_finance"]'),
    ('Friday Newsletter', 5, '10:00:00', 'UTC', TRUE, '["market_intelligence", "supply_chain", "b2b_features"]')
ON CONFLICT DO NOTHING;


-- ========================================
-- CONTENT CLASSIFICATION & VIDEO INTEGRATION
-- Migration: Add support for mixed video+text content and multi-channel classification
-- ========================================

-- Add columns for video integration and content classification
ALTER TABLE marketing_content 
    ADD COLUMN IF NOT EXISTS video_features JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS email_content JSONB,
    ADD COLUMN IF NOT EXISTS social_media_content JSONB,
    ADD COLUMN IF NOT EXISTS classification_metadata JSONB;

-- Add index for video features for faster lookup
CREATE INDEX IF NOT EXISTS idx_marketing_content_video_features ON marketing_content USING GIN(video_features);

-- Add index for classification metadata
CREATE INDEX IF NOT EXISTS idx_marketing_content_classification ON marketing_content USING GIN(classification_metadata);

-- Add comments for new columns
COMMENT ON COLUMN marketing_content.video_features IS 'Array of product walkthrough video feature names included in this newsletter (e.g., ["market_intelligence", "credit_risk_profile"])';
COMMENT ON COLUMN marketing_content.email_content IS 'Classified email-suitable content: {subject, preview, html_content, markdown_content}';
COMMENT ON COLUMN marketing_content.social_media_content IS 'Classified social media content: {linkedin: {headline, body, hashtags}, twitter: {tweet_text, hashtags}}';
COMMENT ON COLUMN marketing_content.classification_metadata IS 'Content classification details: {topic_category, model_used, classified_at, channels}';


-- View: video_integrated_newsletters
-- Shows newsletters that include product walkthrough videos
CREATE OR REPLACE VIEW video_integrated_newsletters AS
SELECT
    mc.id,
    mc.title,
    mc.subject_line,
    mc.topic_category,
    mc.target_audience,
    mc.video_features,
    jsonb_array_length(COALESCE(mc.video_features, '[]'::jsonb)) AS video_count,
    mc.classification_metadata->>'model_used' AS classification_model,
    mc.classification_metadata->'channels' AS distribution_channels,
    mc.status,
    mc.created_at
FROM marketing_content mc
WHERE jsonb_array_length(COALESCE(mc.video_features, '[]'::jsonb)) > 0
ORDER BY mc.created_at DESC;


-- View: social_media_ready_content
-- Shows newsletters with approved social media content ready for posting
CREATE OR REPLACE VIEW social_media_ready_content AS
SELECT
    mc.id,
    mc.title,
    mc.topic_category,
    mc.social_media_content->'linkedin'->>'headline' AS linkedin_headline,
    mc.social_media_content->'linkedin'->>'body' AS linkedin_body,
    mc.social_media_content->'linkedin'->'hashtags' AS linkedin_hashtags,
    mc.social_media_content->'twitter'->>'tweet_text' AS twitter_text,
    mc.social_media_content->'twitter'->'hashtags' AS twitter_hashtags,
    mc.approved_at,
    mc.approved_by
FROM marketing_content mc
WHERE mc.status = 'approved'
  AND mc.social_media_content IS NOT NULL
ORDER BY mc.approved_at DESC;
