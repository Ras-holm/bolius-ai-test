import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Bolius Scraper Fix", layout="wide")

# Sidebar
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

def scrape_bolius_v3(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, f"Fejl: Modtog statuskode {response.status_code} fra Bolius."
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Prøv at finde den specifikke artikel-titel
        title = "Ingen titel fundet"
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
            
        # 2. Målrettet scraping af brødtekst
        # Vi leder efter 'article' og fjerner kendte støj-elementer
        article_tag = soup.find('article')
        if not article_tag:
            article_tag = soup.find('main')
            
        if article_tag:
            # Fjern sidebars, relaterede artikler og menuer inde i artiklen
            for extra in article_tag.select(".related-articles, .sidebar, .ad-container, nav, footer, script, style"):
                extra.decompose()
            
            # Hent kun tekst fra paragraffer og overskrifter i selve artiklen
            paragraphs = article_tag.find_all(['p', 'h2', 'h3'])
            text = " ".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text()) > 20])
            
            if len(text) < 100:
                return title, "ADVARSEL: Kunne ikke finde nok tekst. Måske er indholdet bag en betalingsvæg eller blokeret."
            
            return title, text
        
        return title, "Kunne ikke finde artikel-indholdet på siden."
    except Exception as e:
        return None, f"Kritisk fejl: {e}"

st.title("🏠 Bolius Videns-Widget v3.0")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    # Vi bruger en FORM for at sikre, at URL'en bliver sendt korrekt
    with st.form("url_form"):
        url_input = st.text_input("Indsæt Bolius-URL:")
        submitted = st.form_submit_button("Hent Artikel")

    if submitted and url_input:
        # RENS hukommelsen før nyt opslag
        if "current_text" in st.session_state:
            del st.session_state.current_text
            del st.session_state.current_title
            
        with st.spinner("Scraper Bolius..."):
            title, text = scrape_bolius_v3(url_input)
            st.session_state.current_title = title
            st.session_state.current_text = text

    # Vis kun resultater hvis vi har en titel/tekst i hukommelsen
    if 'current_title' in st.session_state and st.session_state.current_title:
        st.subheader(f"📍 Indlæst: {st.session_state.current_title}")
        
        # DEBUG CHECK: Fortæl brugeren hvis det ligner den forkerte artikel
        if "skægkræ" in st.session_state.current_title.lower() and "tilbygning" in url_input.lower():
            st.warning("⚠️ Bemærk: Titlen matcher ikke din URL. Scraperen ramte sandsynligvis en anbefalet artikel i siden.")

        with st.expander("Se rå tekst (Første 1000 tegn)"):
            st.write(st.session_state.current_text[:1000])

        if st.button("Generér Smart Header"):
            with st.spinner("Analyserer..."):
                res = model.generate_content(f"Lav resumé og 3 FAQ baseret på: {st.session_state.current_text}")
                st.info(res.text)

        query = st.text_input("Spørg artiklen:")
        if query:
            res = model.generate_content(f"Svar på '{query}' ud fra teksten. Svar 'GAP_DETECTED' hvis info mangler. Tekst: {st.session_state.current_text}")
            if "GAP_DETECTED" in res.text:
                st.error("Videnshul fundet!")
            else:
                st.success(res.text)
else:
    st.info("Indtast API-nøgle i sidebaren.")
