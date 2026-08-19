import os
import shutil
import sqlite3
import time

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

CHEMIN_DB = 'base/examen_data_collection.db'


# ---------------------------------------------------------------- navigateur

def lancer_navigateur():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    # sur le serveur de deploiement le navigateur s'appelle chromium
    navigateur = shutil.which('chromium') or shutil.which('chromium-browser')
    if navigateur:
        options.binary_location = navigateur

    driver = shutil.which('chromedriver')
    if driver:
        return webdriver.Chrome(service=Service(driver), options=options)
    return webdriver.Chrome(options=options)


# ---------------------------------------------------------------- source 1

def scraper_books(nb_pages, details=False):
    driver = lancer_navigateur()
    liste_livres = []

    try:
        for i in range(1, nb_pages + 1):
            url = f'https://books.toscrape.com/catalogue/page-{i}.html'
            driver.get(url)

            try:
                nombre_produits = driver.find_element(By.CSS_SELECTOR, 'form.form-horizontal strong').text
            except:
                nombre_produits = None

            containers = driver.find_elements(By.CSS_SELECTOR, 'article.product_pod')

            for container in containers:
                try:
                    lien = container.find_element(By.CSS_SELECTOR, 'h3 a')
                    dic = {
                        'titre': lien.get_attribute('title'),
                        'prix': container.find_element(By.CSS_SELECTOR, 'p.price_color').text,
                        'disponibilite': container.find_element(By.CSS_SELECTOR, 'p.availability').text,
                        'nombre_produits': nombre_produits,
                        'note': container.find_element(By.CSS_SELECTOR, 'p.star-rating').get_attribute('class'),
                        'lien': lien.get_attribute('href')
                        }
                    liste_livres.append(dic)
                except:
                    pass

        df = pd.DataFrame(liste_livres)

        # la description, la categorie, la tax et le nombre de reviews sont sur la page du livre
        if details and len(df) > 0:
            liste_details = []

            for livre in liste_livres:
                driver.get(livre['lien'])

                try:
                    description = driver.find_element(By.CSS_SELECTOR, '#product_description ~ p').text
                except:
                    description = None

                infos = {}
                for ligne in driver.find_elements(By.CSS_SELECTOR, 'table.table-striped tr'):
                    try:
                        infos[ligne.find_element(By.TAG_NAME, 'th').text] = ligne.find_element(By.TAG_NAME, 'td').text
                    except:
                        pass

                try:
                    type_produit = driver.find_elements(By.CSS_SELECTOR, 'ul.breadcrumb li')[2].text
                except:
                    type_produit = None

                liste_details.append({
                    'lien': livre['lien'],
                    'nombre_reviews': infos.get('Number of reviews'),
                    'description': description,
                    'type_produit': type_produit,
                    'tax': infos.get('Tax'),
                    'upc': infos.get('UPC'),
                    'stock_detail': infos.get('Availability')
                    })

            df = pd.merge(df, pd.DataFrame(liste_details), on='lien', how='left')
    finally:
        driver.quit()

    return df


def nettoyer_description(texte):
    texte = str(texte).strip()

    if texte.endswith('...more'):
        texte = texte[:-len('...more')].strip()

    # le site affiche le debut de la description puis le texte complet
    position = texte.find(texte[:30], 1)
    if position > 0:
        texte = texte[position:]

    return texte


def nettoyer_books(df_brut):
    df = df_brut.copy()

    if 'description' in df.columns:
        df['description'] = df['description'].apply(
            lambda texte: None if pd.isna(texte) else nettoyer_description(texte))

    for colonne in ['prix', 'tax']:
        if colonne in df.columns:
            df[colonne] = (df[colonne].astype(str)
                                      .str.replace('Â', '', regex=False)
                                      .str.replace('£', '', regex=False)
                                      .str.strip())
            df[colonne] = pd.to_numeric(df[colonne], errors='coerce')

    notes = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
    df['note'] = df['note'].str.split().str[-1].map(notes)

    if 'stock_detail' in df.columns:
        df['quantite_stock'] = df['stock_detail'].astype(str).str.extract(r'\((\d+) available\)')[0]
        df['quantite_stock'] = pd.to_numeric(df['quantite_stock'], errors='coerce').astype('Int64')
        df = df.drop(columns=['stock_detail'])

    df['disponibilite'] = np.where(df['disponibilite'].str.contains('In stock', na=False),
                                   'En stock', 'Rupture de stock')

    for colonne in ['nombre_produits', 'nombre_reviews']:
        if colonne in df.columns:
            df[colonne] = df[colonne].astype(str).str.replace(r'[^0-9]', '', regex=True)
            df[colonne] = pd.to_numeric(df[colonne], errors='coerce').astype('Int64')

    df['note'] = df['note'].astype('Int64')

    for colonne in ['titre', 'description', 'type_produit']:
        if colonne in df.columns:
            df[colonne] = (df[colonne].astype(str)
                                      .str.replace(r'\s+', ' ', regex=True)
                                      .str.strip()
                                      .replace({'None': None, 'nan': None}))

    df = df.drop_duplicates(subset='lien').drop(columns=['lien'])
    return df.reset_index(drop=True)


# ---------------------------------------------------------------- source 2

def scraper_autos(nb_pages):
    driver = lancer_navigateur()
    liste_annonces = []

    try:
        for i in range(1, nb_pages + 1):
            url = f'https://www.gaaraas.com/fr/users/dakar-auto?page={i}'
            driver.get(url)
            time.sleep(1)

            containers = driver.find_elements(By.CSS_SELECTOR, 'a.common-ad-card')

            # les dernieres pages ne contiennent plus d'annonces
            if len(containers) == 0:
                break

            for container in containers:
                try:
                    dic = {
                        'titre': container.find_element(By.TAG_NAME, 'h4').get_attribute('title'),
                        'prix': container.find_element(By.CSS_SELECTOR, 'div.ad-vehicle-price div.value').text,
                        'kilometrage': container.find_element(By.CSS_SELECTOR, 'div.ad-vehicle-mileage div.value').text,
                        'boite_vitesses': container.find_element(By.CSS_SELECTOR, 'div.transmission span').text,
                        'region': container.find_element(By.CSS_SELECTOR, 'div.location').text,
                        'lien': container.get_attribute('href')
                        }
                    liste_annonces.append(dic)
                except:
                    pass
    finally:
        driver.quit()

    return pd.DataFrame(liste_annonces)


marques_composees = ['Land Rover', 'Alfa Romeo', 'Aston Martin', 'Mercedes Benz',
                     'Great Wall', 'Rolls Royce', 'DS Automobiles']


def decouper_titre(titre):
    morceaux = str(titre).strip().split()

    annee = None
    if morceaux and morceaux[0].isdigit() and len(morceaux[0]) == 4:
        annee = int(morceaux[0])
        morceaux = morceaux[1:]

    reste = ' '.join(morceaux)

    for marque in marques_composees:
        if reste.lower().startswith(marque.lower()):
            modele = reste[len(marque):].strip()
            return pd.Series([marque, modele if modele else None, annee])

    if not morceaux:
        return pd.Series([None, None, annee])

    modele = ' '.join(morceaux[1:])
    return pd.Series([morceaux[0], modele if modele else None, annee])


def nettoyer_autos(df_brut):
    df = df_brut.copy()

    df[['marque', 'modele', 'annee']] = df['titre'].apply(decouper_titre)

    for colonne in ['prix', 'kilometrage']:
        df[colonne] = df[colonne].astype(str).str.replace(r'[^0-9]', '', regex=True)
        df[colonne] = pd.to_numeric(df[colonne], errors='coerce').astype('Int64')

    df['annee'] = df['annee'].astype('Int64')

    df['boite_vitesses'] = (df['boite_vitesses'].astype(str)
                                                .str.strip()
                                                .str.capitalize()
                                                .replace({'': None, 'None': None, 'N/a': None}))
    df['region'] = (df['region'].astype(str)
                                .str.replace(r'\s+', ' ', regex=True)
                                .str.strip()
                                .str.title())

    df = df.drop_duplicates(subset='lien')
    df = df[['marque', 'modele', 'annee', 'prix', 'kilometrage', 'boite_vitesses', 'region']]
    return df.reset_index(drop=True)


# ---------------------------------------------------------------- base de donnees

def enregistrer(df, table):
    os.makedirs('base', exist_ok=True)

    # on ajoute a la suite des collectes precedentes, meme si les colonnes ont change
    ancien = lire_table(table)
    if not ancien.empty:
        df = pd.concat([ancien, df], ignore_index=True)

    conn = sqlite3.connect(CHEMIN_DB)
    df.to_sql(table, conn, index=False, if_exists='replace')
    conn.commit()
    conn.close()


def lire_table(table):
    if not os.path.exists(CHEMIN_DB):
        return pd.DataFrame()
    conn = sqlite3.connect(CHEMIN_DB)
    try:
        df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df


def compter_lignes():
    if not os.path.exists(CHEMIN_DB):
        return {}
    conn = sqlite3.connect(CHEMIN_DB)
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
    resultat = {}
    for nom in tables['name']:
        resultat[nom] = pd.read_sql_query(f'SELECT COUNT(*) AS n FROM {nom}', conn)['n'].iloc[0]
    conn.close()
    return resultat
