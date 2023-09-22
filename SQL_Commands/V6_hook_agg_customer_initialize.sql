CREATE TABLE IF NOT EXISTS target_schema.agg_customer AS
(
    ID PRIMARY KEY SERIAL NOT NULL,
    customer_name TEXT,
    customer_lastname TEXT,
    customer_age INT,
    date_of_birth TIMESTAMP,
    updated_date TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customer_id ON target_schema.agg_customer(ID);