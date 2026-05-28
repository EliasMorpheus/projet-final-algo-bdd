# Script de presentation - Projet final Algo & BDD

## Avant de commencer

Ouvrir ces elements avant la presentation :

- le repo GitHub
- le dashboard : `http://127.0.0.1:8050`
- le schema dbdiagram ou l'image `assets/schema_db.png`
- le fichier `sql/03_queries.sql`
- le fichier `python/pipeline.py`

---

## 1. Introduction du projet

**A montrer a l'ecran : le dashboard, vue generale.**

Bonjour, je vais vous presenter mon projet final d'algorithme et bases de donnees.

J'ai choisi une problematique data marketing e-commerce :

**Comment segmenter les clients pour identifier les meilleurs clients, les clients fideles, les clients a risque et les profils a fort potentiel ?**

L'objectif est de construire un outil d'aide a la decision CRM. Le dashboard permet a une equipe marketing de savoir quels clients cibler, avec quelle priorite, et sur quels segments concentrer les actions.

Le projet suit le pipeline demande dans les consignes :

- une base MySQL relationnelle
- des requetes SQL avancees
- un pipeline Python avec Pandas
- un enrichissement via API externe
- un algorithme marketing RFM
- un dashboard interactif Plotly Dash

---

## 2. Donnees et modele SQL

**A montrer a l'ecran : le schema dbdiagram ou `assets/schema_db.png`.**

La base de donnees s'appelle `marketing_project`.

Elle simule un cas e-commerce avec plusieurs tables :

- `customers` pour les clients
- `products` pour les produits
- `orders` pour les commandes
- `order_items` pour les produits contenus dans chaque commande
- `campaigns` pour les campagnes marketing
- `customer_campaigns` pour les contacts entre clients et campagnes
- `city_enrichment` pour les donnees enrichies par API
- `rfm_scores` pour les resultats du scoring marketing

La modelisation contient deux relations many-to-many.

La premiere est entre `orders` et `products`, via la table `order_items`. Une commande peut contenir plusieurs produits, et un produit peut apparaitre dans plusieurs commandes.

La deuxieme est entre `customers` et `campaigns`, via `customer_campaigns`. Un client peut etre touche par plusieurs campagnes, et une campagne peut toucher plusieurs clients.

J'ai aussi ajoute des contraintes SQL :

- des `PRIMARY KEY`
- des `FOREIGN KEY`
- des contraintes `NOT NULL`
- des contraintes `UNIQUE`, par exemple sur l'email client et le nom de campagne

---

## 3. Creation et alimentation de la base

**A montrer a l'ecran : `sql/01_create_database.sql`, puis `sql/02_insert_data.sql`.**

Le projet contient un script SQL de creation de base.

Dans `01_create_database.sql`, je cree la base, les tables et les relations.

Dans `02_insert_data.sql`, j'insere les donnees. Les donnees sont generees pour reproduire un cas e-commerce realiste, avec au moins 30 lignes par table principale, comme demande dans les consignes.

Les donnees couvrent :

- des clients repartis par ville et canal d'acquisition
- des produits avec categories, prix et taux de marge
- des commandes payees ou annulees
- des lignes de commande
- des campagnes marketing et des contacts campagne-client

---

## 4. Requetes SQL avancees

**A montrer a l'ecran : `sql/03_queries.sql`.**

Le fichier `03_queries.sql` contient les requetes demandees dans le cahier des charges.

Il y a par exemple :

- une requete avec `WHERE`, `ORDER BY` et `LIMIT`
- une requete avec `GROUP BY` et `HAVING`
- une jointure sur plus de trois tables
- une sous-requete
- un CTE avec `WITH`

La requete que je trouve interessante est celle du chiffre d'affaires par categorie produit.

Elle relie les commandes, les lignes de commandes, les produits et les clients. Elle permet d'identifier les categories qui generent le plus de revenu.

**Phrase a dire en montrant la requete :**

Cette requete montre l'interet de la modelisation relationnelle : les donnees sont separees proprement dans plusieurs tables, mais les jointures permettent de reconstruire une analyse business exploitable.

---

## 5. Vue SQL et fonction SQL

**A montrer a l'ecran : `sql/04_views_functions.sql`.**

J'ai aussi cree une vue SQL et une fonction.

La vue s'appelle `v_customer_revenue`.

Elle resume pour chaque client :

- le nombre de commandes payees
- le chiffre d'affaires total
- la date de derniere commande

Cela evite de reecrire les memes jointures a chaque analyse.

La fonction s'appelle `customer_lifetime_value(customer_id)`.

Elle estime la valeur client en calculant une marge a partir des commandes, des prix, des quantites et du taux de marge produit.

---

## 6. Pipeline Python

**A montrer a l'ecran : `python/pipeline.py`.**

La deuxieme partie du projet est le pipeline Python.

Le script se connecte a MySQL avec les identifiants stockes dans un fichier `.env`.

Ensuite, il charge les commandes payees dans un DataFrame Pandas.

Il appelle aussi une API externe : l'API Adresse de data.gouv.fr. Cette API permet d'enrichir les villes avec des coordonnees latitude et longitude.

Les resultats sont stockes dans la table `city_enrichment`.

Ensuite, Python calcule le scoring RFM.

RFM signifie :

- `R` pour recence : depuis combien de temps le client n'a pas achete
- `F` pour frequence : combien de commandes le client a passees
- `M` pour montant : combien le client a depense

Chaque client recoit un score R, F et M, puis un segment marketing :

- Champions
- Clients fideles
- Fort potentiel
- Nouveaux clients
- A developper
- Clients a risque

Les resultats sont ecrits dans une nouvelle table MySQL : `rfm_scores`.

---

## 7. Dashboard interactif

**A montrer a l'ecran : le dashboard.**

Le dashboard a ete construit avec Plotly Dash.

Il affiche quatre KPIs :

- le nombre de clients
- le chiffre d'affaires total
- le chiffre d'affaires moyen par client
- la recence moyenne

Il contient aussi plusieurs visualisations :

- un graphique de portefeuille clients par segment
- un graphique RFM avec frequence et valeur client
- une repartition par canal d'acquisition
- un graphique par ville
- un tableau des clients prioritaires

La partie interactive fonctionne comme un dashboard BI.

On peut filtrer avec :

- les segments
- les canaux d'acquisition
- les villes
- une plage de score RFM
- une plage de chiffre d'affaires client

**A faire a l'ecran : selectionner un canal, par exemple `SEO`.**

Quand je filtre sur un canal, tous les KPIs, graphiques et tableaux se mettent a jour.

**A faire a l'ecran : cliquer sur une barre du graphique des segments, par exemple `Champions`.**

On peut aussi cliquer directement sur un graphique. Par exemple, si je clique sur le segment `Champions`, tout le dashboard se filtre sur ce segment. C'est le meme principe que dans Power BI : les graphiques communiquent entre eux.

**A montrer : le panneau Decision CRM.**

Le panneau de droite donne une recommandation marketing selon la vue active. Par exemple, pour les Champions, la recommandation est de travailler sur un programme VIP, des ventes privees ou du parrainage.

---

## 8. Securite et repo GitHub

**A montrer a l'ecran : le repo GitHub ou `.gitignore` et `.env.example`.**

Pour respecter les consignes, je n'ai pas mis mon mot de passe MySQL dans GitHub.

Les identifiants sont stockes dans un fichier `.env`, qui est ignore par Git avec `.gitignore`.

Le repo contient seulement un fichier `.env.example`, qui montre la structure attendue sans exposer de vrai mot de passe.

Le repo GitHub contient tout le projet :

- les scripts SQL
- le pipeline Python
- le dashboard
- le README
- le schema de base de donnees
- le support de presentation

---

## 9. Conclusion

**A montrer a l'ecran : le dashboard final.**

Pour conclure, ce projet couvre l'ensemble des consignes.

J'ai construit une base relationnelle MySQL avec contraintes, relations et many-to-many.

J'ai ajoute des requetes SQL avancees, une vue et une fonction.

J'ai cree un pipeline Python qui se connecte a MySQL, utilise Pandas, appelle une API externe et calcule un algorithme marketing RFM.

Enfin, les resultats sont exploites dans un dashboard interactif qui permet de filtrer, cliquer sur les graphiques et identifier les clients prioritaires pour les actions CRM.

Le livrable final est donc un pipeline complet, de la base de donnees jusqu'a la visualisation marketing.

---

## Questions probables et reponses courtes

### Pourquoi le RFM ?

Parce que c'est une methode classique en marketing client. Elle transforme des donnees transactionnelles en segments directement exploitables pour le CRM.

### Pourquoi une relation many-to-many ?

Parce qu'une commande peut contenir plusieurs produits, et un produit peut etre present dans plusieurs commandes. C'est exactement le role de `order_items`.

### Pourquoi utiliser une API ?

Pour enrichir les donnees internes avec une source externe. Ici, l'API Adresse ajoute les coordonnees geographiques des villes.

### Quelle table contient le resultat final ?

La table `rfm_scores`. Elle contient les scores RFM, le segment marketing et les coordonnees enrichies.

### Qu'est-ce que le dashboard apporte au metier ?

Il permet d'identifier rapidement les clients a prioriser et d'adapter les actions marketing selon le segment, le canal ou la ville.

### Quelle partie technique est la plus importante ?

Le pipeline Python, parce qu'il fait le lien entre les donnees SQL brutes, l'enrichissement API, l'algorithme RFM et la table finale exploitee par le dashboard.

