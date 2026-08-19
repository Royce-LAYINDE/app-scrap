# Application Data Collection

Application Streamlit du projet d'examen. Quatre pages :

- **Scraper** : collecte avec Selenium sur plusieurs pages, nettoyage, enregistrement dans la base
- **Données brutes** : téléchargement des csv du scraping no-code Web Scraper, non nettoyés
- **Dashboard** : visualisation des données nettoyées des deux sources
- **Évaluation** : liens vers les formulaires Kobo et Google Forms

## Fichiers

| Fichier | Rôle |
|---|---|
| `app.py` | interface |
| `scraper.py` | collecte Selenium, nettoyage, base de données |
| `data/` | csv lus par l'application |
| `base/` | base sqlite créée automatiquement |
| `packages.txt` | chromium pour le serveur de déploiement |

## Lancer en local

```
pip install -r requirements.txt
streamlit run app.py
```

## Données attendues dans data/

| Fichier | Provenance |
|---|---|
| `books_clean.csv` | notebook Selenium |
| `dakar_auto_clean.csv` | notebook Selenium |
| `books_toscrape_brut.csv` | export Web Scraper |
| `dakar_auto_brut.csv` | export Web Scraper |

Les deux fichiers `_clean` presents sont des collectes partielles, a remplacer par les
exports complets du notebook. Les fichiers `_brut` restent a deposer : la page Données
brutes affiche un avertissement tant qu'ils sont absents.

## Deploiement

Streamlit Community Cloud, fichier principal `app.py`. Le fichier `packages.txt` installe
chromium et chromium-driver, necessaires au scraping depuis l'application.

## A completer

Les liens des deux formulaires sont en haut de `app.py` (`LIEN_KOBO`,
`LIEN_GOOGLE_FORMS`), a remplacer par les vrais liens.
