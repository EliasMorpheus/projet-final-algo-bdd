DROP DATABASE IF EXISTS marketing_project;
CREATE DATABASE marketing_project CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE marketing_project;

CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    city VARCHAR(80) NOT NULL,
    signup_date DATE NOT NULL,
    acquisition_channel VARCHAR(40) NOT NULL
);

CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(120) NOT NULL,
    category VARCHAR(60) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    margin_rate DECIMAL(4, 2) NOT NULL
);

CREATE TABLE campaigns (
    campaign_id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_name VARCHAR(120) NOT NULL UNIQUE,
    channel VARCHAR(40) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    budget DECIMAL(10, 2) NOT NULL
);

CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE customer_campaigns (
    customer_id INT NOT NULL,
    campaign_id INT NOT NULL,
    touch_date DATE NOT NULL,
    converted BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (customer_id, campaign_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
);

CREATE TABLE city_enrichment (
    city VARCHAR(80) PRIMARY KEY,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    api_source VARCHAR(80) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rfm_scores (
    customer_id INT PRIMARY KEY,
    recency_days INT NOT NULL,
    frequency_orders INT NOT NULL,
    monetary_value DECIMAL(12, 2) NOT NULL,
    r_score INT NOT NULL,
    f_score INT NOT NULL,
    m_score INT NOT NULL,
    rfm_score INT NOT NULL,
    segment VARCHAR(60) NOT NULL,
    city VARCHAR(80) NOT NULL,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

