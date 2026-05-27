# Support de presentation orale

## 1. Problematique metier

Le projet repond a une problematique e-commerce : mieux cibler les actions marketing en segmentant les clients selon leur comportement d'achat.

Objectif : identifier les clients les plus rentables, les clients fideles, les clients a risque et les profils a fort potentiel.

## 2. Modele de donnees

La base contient des clients, produits, commandes, lignes de commande, campagnes marketing et expositions aux campagnes.

Deux relations many-to-many sont modelisees :

- commandes et produits via `order_items`
- clients et campagnes via `customer_campaigns`

Cette structure permet d'analyser a la fois les ventes et les actions marketing.

## 3. Pipeline Python

Le pipeline :

1. se connecte a MySQL
2. recupere les commandes payees
3. enrichit les villes via l'API Adresse
4. calcule un score RFM avec Pandas
5. classe les clients en segments marketing
6. ecrit les resultats dans `rfm_scores`

## 4. Dashboard

Le dashboard montre :

- le nombre de clients
- le chiffre d'affaires total
- le panier moyen client
- la repartition des segments RFM
- le chiffre d'affaires par ville
- le revenu par canal d'acquisition

Le filtre par segment met a jour les KPIs et graphiques avec un callback Dash.

## 5. Element technique a montrer

Exemple SQL interessant :

```sql
SELECT p.category, COUNT(DISTINCT o.order_id) AS orders_count,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.order_status = 'paid'
GROUP BY p.category
ORDER BY revenue DESC;
```

Exemple Python interessant : la fonction `calculate_rfm()` dans `python/pipeline.py`.

