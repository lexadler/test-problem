CREATE TABLE IF NOT EXISTS nodes(
    id SERIAL PRIMARY KEY,
    parent_id INT,
    node_data TEXT,
    deleted BOOLEAN DEFAULT FALSE
);
