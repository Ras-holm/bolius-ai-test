import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

def scrape_bolius(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Metadata & Titel
        meta = soup.find("meta", attrs={"itemprop": "keywords"})
        keywords = [k.strip() for k in meta["content"].split(",")] if meta else []
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Ingen titel"
        
        # Rens brødtekst
        for noise in soup(["script", "style", "nav", "footer", "aside"]):
            noise.extract()
        text = "\n\n".join([p.get_text(strip=True) for p in soup.find_all(['p', 'h2', 'h3']) if len(p.get_text()) > 40])
        
        return title, text, keywords
    except Exception as e:
        return None, str(e), []

def search_bolius_cluster(keyword):
    search_url = f"https://www.bolius.dk/soeg?q={keyword}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Finder typisk overskrifter i søgeresultater
        results = []
        for a in soup.select('.search-results__item a')[:3]: # De 3 øverste resultater
            results.append({'title': a.get_text(strip=True), 'url': a['href']})
        return results
    except:
        return []

st.title("🏠 Bolius Cluster-Search & FAQ")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    url_input = st.text_input("Indlæs artikel-URL:")
    if url_input:
        title, text, keywords = scrape_bolius(url_input)
        st.session_state.current_text = text
        
        # --- SEKTION 1: 3 FAQ ---
        st.subheader("💡 3 hurtige svar fra artiklen")
        if st.button("Generér FAQ"):
            res = model.generate_content(f"Lav præcis 3 FAQ (spørgsmål/svar) baseret på: {text}")
            st.write(res.text)

        st.divider()

        # --- SEKTION 2: CLUSTER SØGNING ---
        st.subheader("🔍 Find relateret viden (Cluster)")
        if keywords:
            target_keyword = keywords[-1] # Vi tager det mest specifikke (sidste) tag
            if st.button(f"Søg efter mere om '{target_keyword}'"):
                results = search_bolius_cluster(target_keyword)
                for rel in results:
                    st.write(f"- [{rel['title']}]({rel['url']})")
        
        # --- SEKTION 3: GAP-CATCHER ---
        st.subheader("❓ Spørg artiklen")
        query = st.text_input("Stil et spørgsmål:")
        if query:
            res = model.generate_content(f"Svar kort på '{query}' ud fra: {text}. Svar 'GAP_DETECTED' hvis info mangler.").text
            if "GAP_DETECTED" in res:
                st.error("Videnshul logget.")
            else:
                st.success(res)
