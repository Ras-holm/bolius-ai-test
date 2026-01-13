import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

def scrape_content_aggressive(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Hent Titel
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Ingen titel"

        # 2. Find ALLE links og filtrer bagefter
        all_links = soup.find_all('a', href=True)
        found_links = []
        
        for a in all_links:
            href = a['href']
            link_text = a.get_text(strip=True)
            
            # Lav relative links til absolutte
            if href.startswith('/'):
                href = "https://www.bolius.dk" + href
            
            # KRITERIER FOR AT KOMME MED I LISTEN:
            # - Skal indeholde bolius.dk
            # - Teksten skal være længere end 5 tegn (for at fange 'Byggetilladelse' osv.)
            # - Må ikke være den side, vi allerede er på
            if "bolius.dk" in href and len(link_text) > 5 and url not in href:
                # Fjern kendt støj
                noise = ['kontakt', 'nyhedsbrev', 'cookie', 'om-os', 'facebook', 'instagram', 'linkedin']
                if not any(x in href.lower() for x in noise):
                    if href not in [l['url'] for l in found_links]: # Undgå dubletter
                        found_links.append({'title': link_text, 'url': href})

        # 3. Rens og hent brødtekst
        # Vi gemmer en kopi af teksten til AI'en
        temp_soup = BeautifulSoup(response.text, 'html.parser')
        for noise in temp_soup(["script", "style", "nav", "footer", "aside", "form"]):
            noise.extract()
        paragraphs = temp_soup.find_all(['p', 'h2', 'h3'])
        text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40])
        
        return title, text, found_links[:20] # Vi tager de første 20 links
    except Exception as e:
        return "Fejl", str(e), []

# --- UI ---
st.title("🏠 Bolius Cluster-Catcher v6.3")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    url_input = st.text_input("Indlæs artikel-URL:", key="url_input")

    if url_input:
        if 'main_url' not in st.session_state or st.session_state.main_url != url_input:
            with st.spinner("Scraper siden..."):
                title, text, links = scrape_content_aggressive(url_input)
                st.session_state.main_url = url_input
                st.session_state.main_title = title
                st.session_state.main_text = text
                st.session_state.found_links = links
                st.session_state.cluster_data = []

        st.subheader(f"📍 {st.session_state.main_title}")
        
        # --- DEBUG INFO ---
        st.write(f"🔍 Scraperen har fundet **{len(st.session_state.found_links)}** potentielle links.")

        # --- CLUSTER SEKTION ---
        if st.session_state.found_links:
            with st.expander("🔗 Vælg artikler til AI-cluster (Klik for at åbne)", expanded=True):
                for i, link in enumerate(st.session_state.found_links):
                    # Vi viser titlen og en bid af URL'en så man kan se hvad det er
                    if st.checkbox(f"{link['title']} (..{link['url'][-20:]})", key=f"link_{i}"):
                        if link['url'] not in [d['url'] for d in st.session_state.cluster_data]:
                            with st.spinner(f"Tilføjer {link['title']}..."):
                                _, l_text, _ = scrape_content_aggressive(link['url'])
                                st.session_state.cluster_data.append({'url': link['url'], 'text': l_text})
            
            st.info(f"AI-hukommelse: {len(st.session_state.cluster_data) + 1} artikler indlæst.")

        # --- GAP-CATCHER ---
        query = st.text_input("Spørg artiklen/clusteret:")
        if query:
            context = f"PRIMÆR KILDE ({url_input}):\n{st.session_state.main_text}\n\n"
            for extra in st.session_state.cluster_data:
                context += f"UDDYBENDE KILDE ({extra['url']}):\n{extra['text']}\n\n"

            prompt = f"""
            Du er fagekspert fra Bolius. Svar kort på: '{query}'
            Brug KUN den leverede tekst. 
            Hvis svaret er i en UDDYBENDE KILDE, skal du afslutte med: "Læs mere her: [URL]".
            Hvis svaret mangler, svar KUN: GAP_DETECTED.
            
            KONTEKST:
            {context}
            """
            res = model.generate_content(prompt).text
            if "GAP_DETECTED" in res:
                st.error("⚠️ Videnshul fundet.")
            else:
                st.success(res)
