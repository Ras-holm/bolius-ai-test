import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import os

# --- 1. KONFIGURATION & SCRAPER ---
st.set_page_config(page_title="Bolius Cluster-Catcher", layout="wide")

def scrape_content(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Titel
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Ingen titel"
        
        # Metadata (Keywords)
        meta = soup.find("meta", attrs={"itemprop": "keywords"})
        keywords = [k.strip() for k in meta["content"].split(",")] if meta else []

        # Find alle interne links i brødteksten
        links = []
        for a in soup.select('article a[href*="bolius.dk"]'):
            if a['href'].startswith('http') and len(a.get_text(strip=True)) > 2:
                links.append({'title': a.get_text(strip=True), 'url': a['href']})
        
        # Rens brødtekst
        for noise in soup(["script", "style", "nav", "footer", "aside", "form"]):
            noise.extract()
        paragraphs = soup.find_all(['p', 'h2', 'h3'])
        text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40])
        
        return title, text, links, keywords
    except Exception as e:
        return "Fejl", str(e), [], []

# --- 2. UI & API OPSÆTNING ---
st.title("🏠 Bolius Cluster-Catcher PoC")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    url_input = st.text_input("Indlæs primær artikel URL:", placeholder="https://www.bolius.dk/...")

    if url_input:
        # Hent primær artikel hvis den ikke er hentet før
        if 'main_url' not in st.session_state or st.session_state.main_url != url_input:
            with st.spinner("Henter primær artikel..."):
                title, text, links, keywords = scrape_content(url_input)
                st.session_state.main_url = url_input
                st.session_state.main_title = title
                st.session_state.main_text = f"KILDE URL: {url_input}\nINDHOLD:\n{text}"
                st.session_state.found_links = links
                st.session_state.cluster_text = st.session_state.main_text # Start med kun én artikel
        
        st.subheader(f"📍 {st.session_state.main_title}")

        # --- 3. CLUSTER BYGNING ---
        if st.session_state.found_links:
            with st.expander("🔗 Findes svaret i en af disse relaterede artikler? (Vælg for at inkludere)"):
                # Vi bruger en form til at vælge links
                selected_urls = []
                for i, link in enumerate(st.session_state.found_links[:10]): # Vis top 10 links
                    if st.checkbox(f"{link['title']}", key=f"link_{i}"):
                        selected_urls.append(link['url'])
                
                if st.button("Opdatér AI-hukommelse med valgte artikler"):
                    combined_text = st.session_state.main_text
                    for l_url in selected_urls:
                        with st.spinner(f"Læser: {l_url}..."):
                            _, l_text, _, _ = scrape_content(l_url)
                            combined_text += f"\n\n---\nKILDE URL: {l_url}\nINDHOLD:\n{l_text}"
                    st.session_state.cluster_text = combined_text
                    st.success(f"AI kender nu {len(selected_urls) + 1} artikler.")

        st.divider()

        # --- 4. SPØRGSMÅL & CITERING ---
        query = st.text_input("Stil et spørgsmål (AI søger i alle valgte artikler):")
        
        if query:
            # Prompten der tvinger citation
            prompt = f"""
            Du er en fagekspert fra Bolius. Svar kort og præcist på: '{query}'
            
            Brug KUN den leverede tekst som kilde. 
            Hvis du finder svaret, SKAL du afslutte dit svar med at skrive: 
            "Læs mere her: [Indsæt den relevante KILDE URL fra teksten]".
            
            Hvis svaret ikke findes i teksten, skal du svare KUN: GAP_DETECTED.
            
            TEKSTGRUNDLAG:
            {st.session_state.cluster_text}
            """
            
            with st.spinner("Søger efter svar..."):
                response = model.generate_content(prompt).text
                
                if "GAP_DETECTED" in response:
                    st.error("⚠️ Videnshul: Svaret findes ikke i de valgte artikler.")
                    with open("gaps.txt", "a", encoding="utf-8") as f:
                        f.write(f"Cluster-start: {url_input} | Spørgsmål: {query}\n")
                else:
                    st.success(response)

else:
    st.info("Indtast venligst din API-nøgle i sidebaren.")
