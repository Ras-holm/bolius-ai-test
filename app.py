import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import os

st.set_page_config(page_title="Bolius Gap-Catcher v5.0", layout="wide")

# --- Hjælpefunktion: Robust Scraper ---
def scrape_bolius_final(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            return None, f"Fejl: Modtog status {response.status_code}"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hent titel
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Ingen titel fundet"

        # Rens uønskede elementer (menuer, fodnoter osv.)
        for noise in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            noise.extract()

        # Find tekst i paragraffer (p) og overskrifter (h2, h3)
        # Vi filtrerer korte bidder fra for at undgå knapper og smålinks
        text_elements = soup.find_all(['p', 'h2', 'h3'])
        text_content = [el.get_text(strip=True) for el in text_elements if len(el.get_text(strip=True)) > 40]
        
        full_text = "\n\n".join(text_content)
        
        if len(full_text) < 200:
            return title, "ADVARSEL: Kunne ikke finde nok brødtekst. Tjek om URL'en er korrekt."
            
        return title, full_text
    except Exception as e:
        return "Fejl", str(e)

# --- UI Opsætning ---
st.title("🏠 Bolius Videns-Widget & Gap-Catcher")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    # URL Input Form
    with st.form("url_input_form"):
        url_input = st.text_input("Indsæt Bolius-URL:")
        submit_url = st.form_submit_button("Indlæs artikel")

    if submit_url and url_input:
        with st.spinner("Henter indhold..."):
            title, text = scrape_bolius_final(url_input)
            st.session_state.current_title = title
            st.session_state.current_text = text
            st.session_state.smart_res = "" # Nulstil ved ny artikel

    # Vis resultater hvis data er indlæst
    if 'current_title' in st.session_state and st.session_state.current_title:
        st.subheader(f"📍 {st.session_state.current_title}")
        
        with st.expander("Se indlæst tekst (debug)"):
            st.write(st.session_state.current_text)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Generér Smart Header & FAQ"):
                with st.spinner("Analyserer..."):
                    prompt = f"Giv 3 korte bullets og 3 FAQ baseret på denne tekst: {st.session_state.current_text}"
                    res = model.generate_content(prompt)
                    st.session_state.smart_res = res.text
            
            if 'smart_res' in st.session_state and st.session_state.smart_res:
                st.info(st.session_state.smart_res)

        with col2:
            query = st.text_input("Stil spørgsmål til artiklen (Gap-Catcher):")
            if st.button("Tjek for svar"):
                if query:
                    with st.spinner("Søger..."):
                        prompt = f"Svar på '{query}' ud fra teksten. Hvis info mangler, svar KUN 'GAP_DETECTED'. Tekst: {st.session_state.current_text}"
                        res = model.generate_content(prompt).text
                        if "GAP_DETECTED" in res:
                            st.error("⚠️ Videnshul fundet! Spørgsmålet er logget.")
                            # Log til fil
                            with open("gaps.txt", "a", encoding="utf-8") as f:
                                f.write(f"URL: {url_input} | Gap: {query}\n")
                        else:
                            st.success(res)

    # Admin log sektion
    if os.path.exists("gaps.txt"):
