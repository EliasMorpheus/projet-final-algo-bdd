USE marketing_project;

INSERT INTO customers (first_name, last_name, email, city, signup_date, acquisition_channel)
WITH RECURSIVE seq AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < 60
)
SELECT
    ELT(1 + MOD(n, 12), 'Emma', 'Lucas', 'Jade', 'Hugo', 'Lea', 'Nathan', 'Chloe', 'Louis', 'Ines', 'Gabriel', 'Manon', 'Noah'),
    ELT(1 + MOD(n, 12), 'Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Richard', 'Petit', 'Durand', 'Leroy', 'Moreau', 'Simon', 'Laurent'),
    CONCAT('client', n, '@example.com'),
    ELT(1 + MOD(n, 10), 'Paris', 'Lyon', 'Marseille', 'Toulouse', 'Lille', 'Bordeaux', 'Nantes', 'Nice', 'Rennes', 'Strasbourg'),
    DATE_ADD('2024-01-01', INTERVAL MOD(n * 11, 650) DAY),
    ELT(1 + MOD(n, 5), 'SEO', 'Email', 'Paid Social', 'Influence', 'Referral')
FROM seq;

INSERT INTO products (product_name, category, unit_price, margin_rate)
WITH RECURSIVE seq AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < 35
)
SELECT
    CONCAT(ELT(1 + MOD(n, 7), 'Serum', 'Creme', 'Routine', 'Masque', 'Gel', 'Huile', 'Coffret'), ' ', n),
    ELT(1 + MOD(n, 5), 'Skincare', 'Haircare', 'Makeup', 'Wellness', 'Accessories'),
    ROUND(12 + MOD(n * 7, 85) + (MOD(n, 4) * 0.99), 2),
    ROUND(0.25 + (MOD(n, 6) * 0.06), 2)
FROM seq;

INSERT INTO campaigns (campaign_name, channel, start_date, end_date, budget)
WITH RECURSIVE seq AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < 30
)
SELECT
    CONCAT('Campagne ', ELT(1 + MOD(n, 6), 'Acquisition', 'Retention', 'Panier Moyen', 'Reactivation', 'VIP', 'Lancement'), ' ', n),
    ELT(1 + MOD(n, 5), 'Email', 'Meta Ads', 'Google Ads', 'TikTok', 'SMS'),
    DATE_ADD('2025-01-01', INTERVAL MOD(n * 9, 320) DAY),
    DATE_ADD(DATE_ADD('2025-01-01', INTERVAL MOD(n * 9, 320) DAY), INTERVAL 21 DAY),
    800 + MOD(n * 317, 6200)
FROM seq;

INSERT INTO orders (customer_id, order_date, order_status)
WITH RECURSIVE seq AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < 180
)
SELECT
    1 + MOD(n * 7, 60),
    DATE_ADD('2025-01-01', INTERVAL MOD(n * 5 + FLOOR(n / 3), 420) DAY),
    CASE WHEN MOD(n, 19) = 0 THEN 'cancelled' ELSE 'paid' END
FROM seq;

INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT
    o.order_id,
    1 + MOD(o.order_id * 3, 35),
    1 + MOD(o.order_id, 4),
    p.unit_price
FROM orders o
JOIN products p ON p.product_id = 1 + MOD(o.order_id * 3, 35);

INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT
    o.order_id,
    1 + MOD(o.order_id * 5 + 2, 35),
    1 + MOD(o.order_id + 1, 3),
    p.unit_price
FROM orders o
JOIN products p ON p.product_id = 1 + MOD(o.order_id * 5 + 2, 35)
WHERE MOD(o.order_id, 2) = 0
  AND 1 + MOD(o.order_id * 5 + 2, 35) <> 1 + MOD(o.order_id * 3, 35);

INSERT INTO customer_campaigns (customer_id, campaign_id, touch_date, converted)
WITH RECURSIVE seq AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < 180
)
SELECT
    1 + MOD(n - 1, 60),
    1 + MOD(MOD(n - 1, 60) * 11 + FLOOR((n - 1) / 60) * 7, 30),
    DATE_ADD('2025-01-05', INTERVAL MOD(n * 4, 360) DAY),
    MOD(n, 4) = 0
FROM seq;
