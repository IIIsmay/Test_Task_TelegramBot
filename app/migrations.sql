DROP TABLE IF EXISTS video_snapshots;
DROP TABLE IF EXISTS videos;

CREATE TABLE videos (
    id UUID PRIMARY KEY,
    creator_id UUID NOT NULL,
    video_created_at TIMESTAMPTZ NOT NULL,
    views_count BIGINT NOT NULL,
    likes_count BIGINT NOT NULL,
    comments_count BIGINT NOT NULL,
    reports_count BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE video_snapshots (
    id UUID PRIMARY KEY,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    views_count BIGINT NOT NULL,
    likes_count BIGINT NOT NULL,
    comments_count BIGINT NOT NULL,
    reports_count BIGINT NOT NULL,
    delta_views_count BIGINT NOT NULL,
    delta_likes_count BIGINT NOT NULL,
    delta_comments_count BIGINT NOT NULL,
    delta_reports_count BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_videos_creator_created_at
    ON videos (creator_id, video_created_at);

CREATE INDEX idx_snapshots_created_at
    ON video_snapshots (created_at);
