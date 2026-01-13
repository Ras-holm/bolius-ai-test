import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Bolius Scraper Fix", layout="wide")

# Sidebar
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

def scrape_bolius_v2(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hent titel for at verificere
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Ingen titel fundet"
        
        # Find brødteksten - Bolius bruger ofte specifikke tags eller classes
        # Vi prøver at fange de primære tekst-containere
        content_parts = []
        # Finder typisk tekst i 'article' men undgår sidebar
        main_content = soup.find('article')
        if main_content:
            paragraphs = main_content.find_all(['p', 'h2', 'h3'])
            for p in paragraphs:
                content_parts.append(p.get_text(strip=True))
        
        full_text = " ".join(content_parts)
        return title, full_text
    except Exception as e:
        return "Fejl", f"Kunne ikke hente siden: {e}"

st.title("🏠 Bolius Videns-Widget v2.0")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    url_input = st.text_input("Indsæt Bolius-URL:", key="url_field")

    if st.button("Hent og analysér artikel"):
        with st.spinner("Henter indhold..."):
            title, text = scrape_bolius_v2(url_input)
            st.session_state.current_title = title
            st.session_state.current_text = text
            # Nulstil resultater ved ny artikel
            st.session_state.smart_res = ""

    if 'current_title' in st.session_state:
        st.subheader(f"Indlæst: {st.session_state.current_title}")
        
        # Her tjekker vi om titlen rent faktisk passer med din URL
        if "skægkræ" in st.session_state.current_title.lower() and "tilbygning" in url_input.lower():
            st.error("FEJL: Scraperen har fat i en forkert artikel (sandsynligvis fra en sidebar).")
        
        with st.expander("Se den indlæste tekst"):
            st.write(st.session_state.current_text[:1500] + "...")

        if st.button("Generér Smart Header"):
            res = model.generate_content(f"Lav resumé og 3 FAQ baseret på: {st.session_state.current_text}")
            st.session_state.smart_res = res.text
        
        if 'smart_res' in st.session_state and st.session_state.smart_res:
            st.info(st.session_state.smart_res)

        # Gap-Catcher
        query = st.text_input("Spørg artiklen:")
        if query:
            res = model.generate_content(f"Svar kort på '{query}' ud fra teksten. Svar 'GAP_DETECTED' hvis info mangler. Tekst: {st.session_state.current_text}")
            if "GAP_DETECTED" in res.text:
                st.warning("Videnshul fundet!")
            else:
                st.success(res.text)
else:
    st.info("Indtast API-nøgle")
