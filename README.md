# Projet final Algo & Bases de Donnees

## Sujet

Ce projet traite une problematique data marketing e-commerce :

**Comment segmenter les clients pour identifier les clients fideles, les clients a risque et les profils a fort potentiel marketing ?**

Le pipeline construit une base MySQL, enrichit les villes via une API externe, calcule un scoring RFM avec Python/Pandas, puis affiche les resultats dans un dashboard interactif Plotly Dash.

## Stack technique

- MySQL 8
- Python 3.12
- Pandas
- API Adresse `api-adresse.data.gouv.fr`
- Plotly Dash

## Structure

```text
.
├── assets/
│   └── styles.css
├── dashboard/
│   └── app.py
├── python/
│   ├── config.py
│   └── pipeline.py
├── scripts/
│   ├── setup_database.ps1
│   └── start_mysql.ps1
├── sql/
│   ├── 01_create_database.sql
│   ├── 02_insert_data.sql
│   ├── 03_queries.sql
│   ├── 04_views_functions.sql
│   └── dbdiagram.dbml
├── .env.example
├── requirements.txt
└── README.md
```

## Modele de donnees

Le modele contient les tables suivantes :

- `customers`
- `products`
- `orders`
- `order_items`
- `campaigns`
- `customer_campaigns`
- `city_enrichment`
- `rfm_scores`

Relations many-to-many :

- `orders` <-> `products` via `order_items`
- `customers` <-> `campaigns` via `customer_campaigns`

Le fichier `sql/dbdiagram.dbml` peut etre copie dans dbdiagram.io pour generer le schema. La capture du schema doit ensuite etre placee dans `assets/schema_db.png`.

## Installation

Installer les dependances Python :

```powershell
python -m pip install -r requirements.txt
```

Copier `.env.example` vers `.env`, puis renseigner les identifiants MySQL.

Exemple local utilise pour ce projet :

```env
DB_HOST=127.0.0.1
DB_PORT=3307
DB_USER=projet_algo
DB_PASSWORD=your_password
DB_NAME=marketing_project
```

Le fichier `.env` est ignore par Git.

## Lancer MySQL local

Sur cette machine, une instance locale MySQL dediee au projet peut etre demarree avec :

```powershell
.\scripts\start_mysql.ps1
```

## Initialiser la base et lancer le pipeline

```powershell
.\scripts\setup_database.ps1
```

Ce script execute :

1. creation de la base et des tables
2. insertion des donnees
3. creation de la vue et de la fonction SQL
4. calcul du scoring RFM via Python
5. insertion des resultats dans `rfm_scores`

## Lancer le dashboard

```powershell
python dashboard\app.py
```

Puis ouvrir :

```text
http://127.0.0.1:8050
```

## Algorithme marketing

Le pipeline calcule un scoring RFM :

- `R` : recence du dernier achat
- `F` : frequence d'achat
- `M` : montant total depense

Chaque client obtient un score RFM et un segment :

- Champions
- Clients fideles
- Clients a risque
- Nouveaux clients
- Fort potentiel
- A developper

## API externe

Le script `python/pipeline.py` appelle l'API Adresse pour enrichir les villes clients avec latitude et longitude :

```text
https://api-adresse.data.gouv.fr/search/
```

Les resultats sont stockes dans `city_enrichment`.

## Dashboard

Le dashboard contient :

- 4 KPIs : nombre de clients, chiffre d'affaires total, panier moyen client, recence moyenne
- graphique des clients par segment
- graphique du chiffre d'affaires par ville
- graphique du revenu par canal d'acquisition
- graphique RFM frequence vs valeur client
- filtre interactif par segment
- callback Dash mettant a jour les KPIs et graphiques
- tableau des clients prioritaires selon le score RFM

## Requetes SQL importantes

Le fichier `sql/03_queries.sql` contient :

- une requete avec `WHERE`, `ORDER BY`, `LIMIT`
- une requete avec `GROUP BY` et `HAVING`
- une jointure sur 4 tables
- une sous-requete
- un CTE

Le fichier `sql/04_views_functions.sql` contient :

- la vue `v_customer_revenue`
- la fonction `customer_lifetime_value(customer_id)`

## Checklist cahier des charges

- [x] Schema dbdiagram.io fourni en DBML
- [x] Au moins 3 tables avec relations
- [x] Relation many-to-many
- [x] Fichier SQL de creation et insertion
- [x] FOREIGN KEY
- [x] NOT NULL et UNIQUE
- [x] 5 requetes SELECT differentes
- [x] Jointure sur 3 tables ou plus
- [x] Sous-requete et CTE
- [x] Vue SQL
- [x] Fonction SQL
- [x] Connexion Python a MySQL
- [x] Manipulation Pandas
- [x] Appel API externe
- [x] Algorithme marketing RFM
- [x] Ecriture dans une nouvelle table MySQL
- [x] Code Python structure avec fonctions
- [x] Dashboard Plotly Dash
- [x] 3 KPIs
- [x] 2 graphiques minimum
- [x] Filtre interactif
- [x] Callback Dash
