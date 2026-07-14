CREATE DATABASE IF NOT EXISTS glavk CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE glavk;

CREATE TABLE IF NOT EXISTS admin_users (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_admin_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS web_projects (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    url VARCHAR(500) NOT NULL,
    category VARCHAR(80) NOT NULL DEFAULT '未分类',
    description VARCHAR(300) NOT NULL DEFAULT '',
    notes TEXT NOT NULL,
    username VARCHAR(160) NOT NULL DEFAULT '',
    password_ciphertext TEXT NULL,
    screenshot_path VARCHAR(500) NULL,
    is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_web_projects_updated_at (updated_at),
    INDEX ix_web_projects_category (category),
    INDEX ix_web_projects_favorite (is_favorite),
    INDEX ix_web_projects_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
