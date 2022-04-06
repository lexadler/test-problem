CREATE TABLE IF NOT EXISTS nodes(
    id SERIAL PRIMARY KEY,
    parent_id INT,
    "value" TEXT,
    deleted BOOLEAN DEFAULT FALSE
);
