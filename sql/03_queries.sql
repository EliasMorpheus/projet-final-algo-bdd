USE marketing_project;

-- 1. WHERE + ORDER BY + LIMIT: derniers clients acquis via Email.
SELECT customer_id, first_name, last_name, email, city, signup_date
FROM customers
WHERE acquisition_channel = 'Email'
ORDER BY signup_date DESC
LIMIT 10;

-- 2. GROUP BY + HAVING: villes avec plus de 5 clients.
SELECT city, COUNT(*) AS customer_count
FROM customers
GROUP BY city
HAVING COUNT(*) > 5
ORDER BY customer_count DESC;

-- 3. Jointure sur 3 tables ou plus: CA par categorie produit.
SELECT p.category, COUNT(DISTINCT o.order_id) AS orders_count,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.order_status = 'paid'
GROUP BY p.category
ORDER BY revenue DESC;

-- 4. Sous-requete: clients au-dessus du panier moyen.
SELECT c.customer_id, c.first_name, c.last_name,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS customer_revenue
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.order_status = 'paid'
GROUP BY c.customer_id, c.first_name, c.last_name
HAVING customer_revenue > (
    SELECT AVG(order_total)
    FROM (
        SELECT o2.order_id, SUM(oi2.quantity * oi2.unit_price) AS order_total
        FROM orders o2
        JOIN order_items oi2 ON oi2.order_id = o2.order_id
        WHERE o2.order_status = 'paid'
        GROUP BY o2.order_id
    ) totals
)
ORDER BY customer_revenue DESC
LIMIT 15;

-- 5. CTE: performance des campagnes marketing.
WITH campaign_revenue AS (
    SELECT cc.campaign_id,
           COUNT(*) AS touches,
           SUM(cc.converted) AS conversions,
           SUM(CASE WHEN cc.converted THEN oi.quantity * oi.unit_price ELSE 0 END) AS attributed_revenue
    FROM customer_campaigns cc
    JOIN campaigns ca ON ca.campaign_id = cc.campaign_id
    LEFT JOIN orders o ON o.customer_id = cc.customer_id
        AND o.order_date BETWEEN cc.touch_date AND DATE_ADD(cc.touch_date, INTERVAL 30 DAY)
        AND o.order_status = 'paid'
    LEFT JOIN order_items oi ON oi.order_id = o.order_id
    GROUP BY cc.campaign_id
)
SELECT ca.campaign_name, ca.channel, touches, conversions,
       ROUND(conversions / touches * 100, 2) AS conversion_rate_pct,
       ROUND(attributed_revenue, 2) AS attributed_revenue,
       ROUND(attributed_revenue / ca.budget, 2) AS roas
FROM campaign_revenue cr
JOIN campaigns ca ON ca.campaign_id = cr.campaign_id
ORDER BY roas DESC
LIMIT 10;

