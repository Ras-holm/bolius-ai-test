import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import os

st.set_page_config(page_title="Bolius Cluster-Catcher v6.0", layout="wide")

# --- 1. SCRAPER LOGIK ---
def scrape_content(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Metadata & Titel
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Ingen titel"
        meta = soup.find("meta", attrs={"itemprop": "keywords"})
        keywords = [k.strip() for k in meta["content"].split(",")] if meta else []

        # Bredere link-ekstraktion
        links = []
        for a in soup.find_all('a', href=True):
            link_url = a['href']
            link_text = a.get_text(strip=True)
            # Rens og filtrer links
            if 'bolius.dk' in link_url and len(link_text) > 3:
                if link_url.startswith('/'): link_url = "https://www.bolius.dk" + link_url
                if link_url not in [l['url'] for l in links] and url not in link_url:
                    if not any(x in link_url for x in ['/om-bolius/', 'nyhedsbrev', 'facebook']):
                        links.append({'title': link_text, 'url': link_url})
        
        # Rens tekst
        for noise in soup(["script", "style", "nav", "footer", "aside", "form"]):
            noise.extract()
        paragraphs = soup.find_all(['p', 'h2', 'h3'])
        text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40])
        
        return title, text, links[:15], keywords # Top 15 links
    except Exception as e:
        return "Fejl", str(e), [], []

# --- 2. UI & INITIALISERING ---
st.title("🏠 Bolius Cluster-Catcher")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    url_input = st.text_input("Indlæs primær artikel URL:")

    if url_input:
        if 'main_url' not in st.session_state or st.session_state.main_url != url_input:
            with st.spinner("Henter data..."):
                title, text, links, keywords = scrape_content(url_input)
                st.session_state.main_url = url_input
                st.session_state.main_title = title
                st.session_state.main_text = f"KILDE URL: {url_input}\nINDHOLD:\n{text}"
                st.session_state.found_links = links
                st.session_state.cluster_text = st.session_state.main_text
                st.session_state.keywords = keywords

        st.subheader(f"📍 {st.session_state.main_title}")
        if st.session_state.keywords:
            st.caption(f"Tags: {', '.join(st.session_state.keywords)}")

        # --- 3. CLUSTER SEKTION ---
        st.write("---")
        st.subheader("🔗 Udvid vidensgrundlag (Cluster)")
        if st.session_state.found_links:
            with st.expander("Findes svaret i en af disse relaterede artikler?"):
                selected_urls = []
                for i, link in enumerate(st.session_state.found_links):
                    if st.checkbox(f"{link['title']}", key=f"link_{i}"):
                        selected_urls.append(link['url'])
                
                if st.button("Opdatér AI-hukommelse"):
                    combined_text = st.session_state.main_text
                    for l_url in selected_urls:
                        with st.spinner(f"Læser: {l_url}..."):
                            _, l_text, _, _ = scrape_content(l_url)
                            combined_text += f"\n\n---\nKILDE URL: {l_url}\nINDHOLD:\n{l_text}"
                    st.session_state.cluster_text = combined_text
                    st.success(f"AI kender nu {len(selected_urls) + 1} artikler.")
        else:
            st.warning("Ingen relevante interne links fundet.")

        # --- 4. GAP-CATCHER ---
        st.write("---")
        query = st.text_input("Spørg artiklen (AI søger i hele clusteret):")
        
        if query:
            prompt = f"""
            Du er fagekspert fra Bolius. Svar kort på: '{query}'
            Brug KUN den leverede tekst. 
            Hvis svaret findes, SKAL du afslutte med: "Læs mere her: [KILDE URL]".
            Hvis svaret mangler, svar KUN: GAP_DETECTED.
            
            TEKSTGRUNDLAG:
            {st.session_state.cluster_text}
            """
            with st.spinner("Søger..."):
                res = model.generate_content(prompt).text
                if "GAP_DETECTED" in res:
                    st.error("⚠️ Videnshul fundet i clusteret.")
                else:
                    st.success(res)
else:
    st.info("Indtast API-nøgle i sidebaren.")
