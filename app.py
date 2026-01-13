import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

def scrape_content(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Find brødtekst-containeren (Bolius bruger ofte specifikke klasser)
        content_area = soup.find(['article', 'main']) or soup.body
        
        # 2. Find links KUN i brødteksten
        links = []
        if content_area:
            for a in content_area.find_all('a', href=True):
                link_url = a['href']
                link_text = a.get_text(strip=True)
                
                # Filtrering: Kun Bolius-links, ingen PDF, ingen kontakt, ingen korte tekster
                if 'bolius.dk' in link_url and len(link_text) > 10:
                    if link_url.startswith('/'): link_url = "https://www.bolius.dk" + link_url
                    # Fjern støj-ord
                    noise = ['kontakt', 'nyhedsbrev', 'cookie', 'om-os', 'privatliv']
                    if not any(x in link_url.lower() for x in noise) and url not in link_url:
                        links.append({'title': link_text, 'url': link_url})

        # 3. Rens og hent tekst
        for noise in soup(["script", "style", "nav", "footer", "aside", "form"]):
            noise.extract()
        paragraphs = soup.find_all(['p', 'h2', 'h3'])
        text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40])
        
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Ingen titel"
        return title, text, links[:10]
    except Exception as e:
        return "Fejl", str(e), []

# --- UI LOGIK ---
st.title("🏠 Bolius Cluster-Catcher v6.2")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    url_input = st.text_input("Indlæs primær artikel URL:")

    if url_input:
        if 'main_url' not in st.session_state or st.session_state.main_url != url_input:
            title, text, links = scrape_content(url_input)
            st.session_state.main_url = url_input
            st.session_state.main_title = title
            st.session_state.main_text = text
            st.session_state.found_links = links
            st.session_state.cluster_data = [] # Liste over ekstra artikler

        st.subheader(f"📍 {st.session_state.main_title}")

        # --- CLUSTER SEKTION ---
        if st.session_state.found_links:
            with st.expander("🔗 Relevante uddybende artikler fundet"):
                for i, link in enumerate(st.session_state.found_links):
                    if st.checkbox(f"{link['title']}", key=f"link_{i}"):
                        if link['url'] not in [d['url'] for d in st.session_state.cluster_data]:
                            with st.spinner(f"Henter {link['title']}..."):
                                _, l_text, _ = scrape_content(link['url'])
                                st.session_state.cluster_data.append({'url': link['url'], 'text': l_text})
            st.write(f"Cluster-størrelse: {len(st.session_state.cluster_data) + 1} artikler.")

        # --- GAP-CATCHER ---
        query = st.text_input("Stil et spørgsmål:")
        if query:
            # Opbyg kontekst med tydelige kildemarkører
            context = f"PRIMÆR ARTIKEL ({url_input}):\n{st.session_state.main_text}\n\n"
            for extra in st.session_state.cluster_data:
                context += f"UDDYBENDE ARTIKEL ({extra['url']}):\n{extra['text']}\n\n"

            prompt = f"""
            Du er fagekspert fra Bolius. Svar kort på: '{query}'
            Brug KUN den leverede tekst. 
            
            REGLER FOR CITERING:
            1. Hvis svaret findes i den PRIMÆRE ARTIKEL, skal du bare svare.
            2. Hvis svaret findes i en UDDYBENDE ARTIKEL, skal du svare og afslutte med: "Læs mere her: [URL]".
            3. Hvis svaret slet ikke findes, svar KUN: GAP_DETECTED.
            
            KONTEKST:
            {context}
            """
            res = model.generate_content(prompt).text
            if "GAP_DETECTED" in res:
                st.error("⚠️ Videnshul fundet.")
            else:
                st.success(res)
