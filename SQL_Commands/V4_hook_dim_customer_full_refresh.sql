CREATE TABLE IF NOT EXISTS target_schema.dim_customer AS
(
    ID PRIMARY KEY SERIAL NOT NULL,
    customer_name TEXT,
    customer_lastname TEXT,
    customer_age INT,
    date_of_birth TIMESTAMP,
    updated_date TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customer_id ON target_schema.dim_customer(ID);
TRUNCATE TABLE IF EXISTS target_schema.dim_customer;
INSERT INTO target_schema.dim_customer 
(
    SELECT 
        id,
        name AS customer_name,
        lastname AS customer_lastname,
        age AS customer_age,
        dob AS date_of_birth,
        updated_date,
        'DVD_RENTAL' AS source_name
    FROM target_schema.stg_dvd_rental_customer
    UNION
    SELECT 
        id,
        customer_name,
        customer_lastname,
        customer_age,
        date_of_birth,
        updated_date,
        'ANOTHER_SOURCE' AS source_name
    FROM target_schema.stg_college_students
)

