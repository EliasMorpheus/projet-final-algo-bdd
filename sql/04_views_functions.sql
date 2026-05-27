USE marketing_project;

CREATE OR REPLACE VIEW v_customer_revenue AS
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.city,
    c.acquisition_channel,
    COUNT(DISTINCT CASE WHEN o.order_status = 'paid' THEN o.order_id END) AS paid_orders,
    COALESCE(ROUND(SUM(CASE WHEN o.order_status = 'paid' THEN oi.quantity * oi.unit_price ELSE 0 END), 2), 0) AS total_revenue,
    MAX(CASE WHEN o.order_status = 'paid' THEN o.order_date END) AS last_order_date
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
LEFT JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email, c.city, c.acquisition_channel;

DROP FUNCTION IF EXISTS customer_lifetime_value;

DELIMITER //
CREATE FUNCTION customer_lifetime_value(p_customer_id INT)
RETURNS DECIMAL(12, 2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total DECIMAL(12, 2);

    SELECT COALESCE(ROUND(SUM(oi.quantity * oi.unit_price * p.margin_rate), 2), 0)
    INTO total
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.customer_id = p_customer_id
      AND o.order_status = 'paid';

    RETURN total;
END //
DELIMITER ;

SELECT customer_id, first_name, last_name, customer_lifetime_value(customer_id) AS estimated_margin
FROM customers
ORDER BY estimated_margin DESC
LIMIT 10;

