USE glavk;

ALTER TABLE web_projects
    ADD COLUMN IF NOT EXISTS screenshot_path VARCHAR(500) NULL AFTER password_ciphertext;
