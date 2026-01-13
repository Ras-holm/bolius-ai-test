import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions
import requests
from bs4 import BeautifulSoup
import os

st.set_page_config(page_title="Bolius URL-Widget", layout="wide")

api_key = st.sidebar.text_input("Gemini API Key:", type="password")

# --- Hjælpefunktion: Scraper ---
def scrape_bolius(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Forsøger at ramme selve brødteksten og fjerne støj (menuer, reklamer)
        article = soup.find('article') or soup.find('main')
        if article:
            # Fjern script og style elementer
            for script in article(["script", "style"]):
                script.extract()
            return article.get_text(separator=' ', strip=True)
        return "Kunne ikke finde hovedindholdet på siden."
    except Exception as e:
        return f"Fejl ved hentning af URL: {e}"

# --- Interface ---
st.title("🏠 Bolius URL-Widget & Gap-Catcher")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    url_input = st.text_input("Indsæt Bolius-URL her:", placeholder="https://www.bolius.dk/...")

    if url_input:
        if 'last_url' not in st.session_state or st.session_state.last_url != url_input:
            with st.spinner("Læser artiklen..."):
                st.session_state.article_text = scrape_bolius(url_input)
                st.session_state.last_url = url_input
                st.session_state.smart_header = "" # Nulstil ved ny URL

        if st.session_state.article_text:
            # Vis et lille uddrag af den læste tekst for kontrol
            with st.expander("Se indlæst tekst"):
                st.write(st.session_state.article_text[:1000] + "...")

            # Smart Header & FAQ
            if st.button("Generér Smart Header & FAQ"):
                try:
                    res = model.generate_content(f"Giv 3 pointer og 3 FAQ baseret på: {st.session_state.article_text}")
                    st.session_state.smart_header = res.text
                except exceptions.ResourceExhausted:
                    st.error("Kvote nået. Vent 60 sek.")

            if st.session_state.smart_header:
                st.info(st.session_state.smart_header)

            st.divider()

            # Gap-Catcher
            user_query = st.text_input("Stil et uddybende spørgsmål:")
            if st.button("Søg efter svar") and user_query:
                try:
                    prompt = f"Svar på '{user_query}' baseret på teksten. Hvis svaret mangler, svar KUN 'GAP_DETECTED'. Tekst: {st.session_state.article_text}"
                    res = model.generate_content(prompt).text
                    if "GAP_DETECTED" in res:
                        st.error("⚠️ Videnshul fundet!")
                        # Logning til fil
                        with open("gaps.txt", "a") as f:
                            f.write(f"URL: {url_input} | Spørgsmål: {user_query}\n")
                    else:
                        st.success(res)
                except exceptions.ResourceExhausted:
                    st.error("Kvote nået.")

    # Vis loggen til admin
    if os.path.exists("gaps.txt"):
        with st.expander("📊 Log (Admin)"):
            with open("gaps.txt", "r") as f:
                st.text(f.read())
else:
    st.info("Indtast API-nøgle.")
