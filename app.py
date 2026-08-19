import os

import pandas as pd
import streamlit as st

import scraper

st.set_page_config(page_title='RoyScrap APP', layout='wide')

ACCENT = '#b8f14a'
MONO = 'ui-monospace, "Cascadia Mono", "SF Mono", Menlo, Consolas, monospace'

# liens des deux formulaires d'evaluation
LIEN_KOBO = 'https://ee.kobotoolbox.org/x/FQk5z6AK'
LIEN_GOOGLE_FORMS = ('https://docs.google.com/forms/d/e/'
                     '1FAIpQLSeLjHSJsApctZbLGzrWR-Gr6Px4_J3B9GdW9_RsfKM7B1QGyg/viewform')

ACCUEIL = '01  ACCUEIL'
COLLECTE = '02  COLLECTE'
BRUTES = '03  DONNÉES BRUTES'
DASHBOARD = '04  DASHBOARD'
EVALUATION = '05  ÉVALUATION'
PAGES = [ACCUEIL, COLLECTE, BRUTES, DASHBOARD, EVALUATION]

SOURCES = {
    'Books to Scrape': {
        'brut': 'data/books_toscrape_brut.csv',
        'propre': 'data/books_clean.csv',
        'table': 'books_clean',
        'site': 'https://books.toscrape.com'
        },
    'Dakar auto': {
        'brut': 'data/dakar_auto_brut.csv',
        'propre': 'data/dakar_auto_clean.csv',
        'table': 'dakar_auto_clean',
        'site': 'https://www.gaaraas.com/fr/users/dakar-auto'
        }
    }

st.markdown(f"""
<style>
[data-testid="stMetric"] {{ border-bottom: 2px solid {ACCENT}; padding: 0 0 .35rem 0; }}
[data-testid="stMetricValue"] {{ font-family: {MONO}; font-size: 1.8rem; }}
[data-testid="stMetricLabel"] p,
[data-testid="stSidebar"] [role="radiogroup"] p {{
    font-family: {MONO};
    text-transform: uppercase;
    font-size: .74rem;
    letter-spacing: .09em;
}}
.marque {{ font-family: {MONO}; font-size: 1.05rem; display: flex; gap: .5rem; }}
.marque i {{ width: .7rem; height: .7rem; background: {ACCENT}; display: inline-block; }}
.mono {{ font-family: {MONO}; color: #8b98a5; font-size: .78rem;
         letter-spacing: .08em; text-transform: uppercase; }}
/* p.titre et non .titre : Streamlit style deja les p du markdown */
p.titre {{ font-family: {MONO}; font-size: 2.6rem; line-height: 1.1; margin: 0; }}
p.titre b {{ color: {ACCENT}; }}
</style>
""", unsafe_allow_html=True)


def mono(texte):
    st.markdown(f'<div class="mono">{texte}</div>', unsafe_allow_html=True)


@st.cache_data
def charger(chemin):
    if os.path.exists(chemin):
        return pd.read_csv(chemin)
    return pd.DataFrame()


def aller(page):
    st.session_state['page'] = page


lignes_base = scraper.compter_lignes()

with st.sidebar:
    st.markdown('<div class="marque"><i></i>RoyScrap APP</div>', unsafe_allow_html=True)
    mono('collecte · nettoyage · dashboard')
    st.divider()

    page = st.radio('Navigation', PAGES, label_visibility='collapsed', key='page')

    st.divider()
    mono('base de données')
    if lignes_base:
        for table, n in lignes_base.items():
            st.caption(f'{table} · {n} lignes')
    else:
        st.caption('vide')


# ------------------------------------------------------------------ accueil

if page == ACCUEIL:
    st.markdown('<p class="titre">Roy<b>Scrap</b> APP</p>', unsafe_allow_html=True)
    mono('web scraping · nettoyage · visualisation')
    st.write('')
    st.write('Cette application collecte des données sur deux sites avec Selenium, '
             'les nettoie, les enregistre dans une base SQL et les présente dans un '
             'tableau de bord. Les données du scraping no-code sont téléchargeables '
             'sans nettoyage.')

    st.divider()

    a, b, c = st.columns(3)
    a.metric('Livres en base', lignes_base.get('books_clean', 0))
    b.metric('Annonces en base', lignes_base.get('dakar_auto_clean', 0))
    c.metric('Sources', len(SOURCES))

    st.divider()

    colonnes = st.columns(2)
    descriptions = ['titre, prix, disponibilité, note, description, catégorie, tax',
                    'marque, modèle, année, prix, kilométrage, boîte, région']
    for colonne, (nom, source), description in zip(colonnes, SOURCES.items(), descriptions):
        with colonne:
            mono(f'source {list(SOURCES).index(nom) + 1}')
            st.write(f'**{nom}**')
            st.caption(description)
            st.link_button('Voir le site', source['site'])

    st.divider()
    mono('accès rapide')

    a, b, c = st.columns(3)
    a.button('Collecter des données', on_click=aller, args=(COLLECTE,),
             use_container_width=True)
    b.button('Voir le dashboard', on_click=aller, args=(DASHBOARD,),
             use_container_width=True)
    c.button('Évaluer l’application', on_click=aller, args=(EVALUATION,),
             use_container_width=True)


# ------------------------------------------------------------------ collecte

elif page == COLLECTE:
    mono('02 · collecte')
    st.subheader('Scraper des données')
    st.write('La collecte se fait avec Selenium, page par page. '
             'Les données sont nettoyées puis enregistrées dans la base de données.')

    gauche, droite = st.columns([2, 1])
    with gauche:
        source = st.selectbox('Source', list(SOURCES))
    with droite:
        nb_pages = st.number_input('Nombre de pages', min_value=1, max_value=20, value=2)

    details = False
    if source == 'Books to Scrape':
        details = st.checkbox('Ouvrir la page de chaque livre '
                              '(description, catégorie, tax, nombre de reviews)')

    if st.button('Lancer la collecte', type='primary'):
        termine = False
        with st.status('Collecte en cours...', expanded=True) as etat:
            try:
                st.write(f'{nb_pages} page(s) de {source}')
                if source == 'Books to Scrape':
                    df = scraper.nettoyer_books(scraper.scraper_books(nb_pages, details))
                else:
                    df = scraper.nettoyer_autos(scraper.scraper_autos(nb_pages))

                st.write(f'{len(df)} lignes collectées')
                scraper.enregistrer(df, SOURCES[source]['table'])
                st.write(f"enregistrées dans la table {SOURCES[source]['table']}")
                etat.update(label='Collecte terminée', state='complete')
                st.session_state['resultat'] = df
                termine = True
            except Exception as erreur:
                etat.update(label='La collecte a échoué', state='error')
                st.error(erreur)
                st.info('Le navigateur Chrome/Chromium est nécessaire pour le scraping.')

        # relancer l'affichage pour mettre a jour les compteurs de la base
        if termine:
            st.rerun()

    if 'resultat' in st.session_state:
        df = st.session_state['resultat']
        st.divider()
        st.write(f'{df.shape[0]} lignes et {df.shape[1]} colonnes')
        st.dataframe(df, use_container_width=True)
        st.download_button('Télécharger ces données (csv)',
                           df.to_csv(index=False).encode('utf-8'),
                           'donnees_scrapees.csv', 'text/csv')


# ------------------------------------------------------------------ donnees brutes

elif page == BRUTES:
    mono('03 · données brutes')
    st.subheader('Données du scraping no-code')
    st.write("Données collectées avec l'extension Chrome Web Scraper, sans nettoyage.")

    for nom, source in SOURCES.items():
        st.divider()
        df = charger(source['brut'])
        st.write(f"**{nom}** — {source['site']}")

        if df.empty:
            st.warning(f"Fichier absent : {source['brut']}")
            continue

        fichier = os.path.basename(source['brut'])
        st.caption(f'{df.shape[0]} lignes et {df.shape[1]} colonnes')
        st.download_button(f'Télécharger {fichier}',
                           df.to_csv(index=False).encode('utf-8'),
                           fichier, 'text/csv', key=f'dl_{nom}')
        with st.expander('Aperçu'):
            st.dataframe(df.head(50), use_container_width=True)


# ------------------------------------------------------------------ dashboard

elif page == DASHBOARD:
    mono('04 · dashboard')
    st.subheader('Données nettoyées')
    st.write('Données collectées avec Selenium et nettoyées.')

    onglet_books, onglet_autos = st.tabs(['Books to Scrape', 'Dakar auto'])

    with onglet_books:
        df = charger(SOURCES['Books to Scrape']['propre'])
        if df.empty:
            df = scraper.lire_table('books_clean')

        if df.empty:
            st.warning('Aucune donnée : lancer une collecte ou déposer '
                       'books_clean.csv dans data/')
        else:
            a, b, c, d = st.columns(4)
            a.metric('Livres', len(df))
            b.metric('Prix moyen', f"{df['prix'].mean():.2f} £")
            c.metric('Note moyenne', f"{df['note'].mean():.1f} / 5")
            d.metric('En stock', int((df['disponibilite'] == 'En stock').sum()))

            st.divider()
            gauche, droite = st.columns(2)

            if 'type_produit' in df.columns and df['type_produit'].notna().any():
                with gauche:
                    mono('livres par catégorie')
                    st.bar_chart(df['type_produit'].value_counts().head(15), color=ACCENT)
                with droite:
                    mono('prix moyen par catégorie')
                    st.bar_chart(df.groupby('type_produit')['prix'].mean()
                                   .sort_values(ascending=False).head(15), color=ACCENT)
            else:
                with gauche:
                    mono('répartition des notes')
                    st.bar_chart(df['note'].value_counts().sort_index(), color=ACCENT)
                with droite:
                    mono('répartition des prix')
                    st.bar_chart(df['prix'].value_counts(bins=10).sort_index(), color=ACCENT)

            st.divider()
            notes = st.multiselect('Filtrer par note', sorted(df['note'].dropna().unique()))
            prix_max = st.slider('Prix maximum', float(df['prix'].min()),
                                 float(df['prix'].max()), float(df['prix'].max()))

            selection = df[df['prix'] <= prix_max]
            if notes:
                selection = selection[selection['note'].isin(notes)]

            st.caption(f'{len(selection)} livres')
            st.dataframe(selection, use_container_width=True)

    with onglet_autos:
        df = charger(SOURCES['Dakar auto']['propre'])
        if df.empty:
            df = scraper.lire_table('dakar_auto_clean')

        if df.empty:
            st.warning('Aucune donnée : lancer une collecte ou déposer '
                       'dakar_auto_clean.csv dans data/')
        else:
            a, b, c, d, e = st.columns(5)
            a.metric('Annonces', len(df))
            b.metric('Marques', df['marque'].nunique())
            c.metric('Prix moyen', f"{df['prix'].mean():,.0f} CFA".replace(',', ' '))
            d.metric('Kilométrage moyen', f"{df['kilometrage'].mean():,.0f} km".replace(',', ' '))
            e.metric('Année médiane', int(df['annee'].median()))

            st.divider()
            gauche, droite = st.columns(2)
            with gauche:
                mono('véhicules par marque')
                st.bar_chart(df['marque'].value_counts().head(15), color=ACCENT)
            with droite:
                mono('prix moyen par marque')
                st.bar_chart(df.groupby('marque')['prix'].mean()
                               .sort_values(ascending=False).head(15), color=ACCENT)

            gauche, droite = st.columns(2)
            with gauche:
                mono('boîte de vitesses')
                st.bar_chart(df['boite_vitesses'].value_counts(), color=ACCENT)
            with droite:
                mono('prix moyen par année')
                st.line_chart(df.dropna(subset=['annee']).groupby('annee')['prix'].mean(),
                              color=ACCENT)

            st.divider()
            gauche, milieu, droite = st.columns(3)
            with gauche:
                marques = st.multiselect('Marque', sorted(df['marque'].dropna().unique()))
            with milieu:
                boites = st.multiselect('Boîte', sorted(df['boite_vitesses'].dropna().unique()))
            with droite:
                regions = st.multiselect('Région', sorted(df['region'].dropna().unique()))

            selection = df.copy()
            if marques:
                selection = selection[selection['marque'].isin(marques)]
            if boites:
                selection = selection[selection['boite_vitesses'].isin(boites)]
            if regions:
                selection = selection[selection['region'].isin(regions)]

            st.caption(f'{len(selection)} annonces')
            st.dataframe(selection, use_container_width=True)


# ------------------------------------------------------------------ evaluation

else:
    mono('05 · évaluation')
    st.subheader("Évaluer l'application")
    st.write('Le même formulaire est disponible en deux versions.')

    gauche, droite = st.columns(2)
    with gauche:
        st.write('**KoboToolbox**')
        st.link_button('Ouvrir le formulaire Kobo', LIEN_KOBO, use_container_width=True)
    with droite:
        st.write('**Google Forms**')
        st.link_button('Ouvrir le formulaire Google Forms', LIEN_GOOGLE_FORMS,
                       use_container_width=True)
