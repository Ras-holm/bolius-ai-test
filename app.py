import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

def scrape_with_metadata(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Ekstraher Metadata (Keywords)
        keywords = []
        meta_keywords = soup.find("meta", attrs={"itemprop": "keywords"})
        if meta_keywords:
            keywords = [k.strip() for k in meta_keywords["content"].split(",")]
        
        # 2. Hent Titel og Brødtekst
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Ingen titel"
        
        for noise in soup(["script", "style", "nav", "footer", "aside"]):
            noise.extract()
            
        paragraphs = soup.find_all(['p', 'h2', 'h3'])
        text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40])
        
        return title, text, keywords
    except Exception as e:
        return "Fejl", str(e), []

st.title("🏠 Bolius Metadata & Cluster-Catcher")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    url_input = st.text_input("Indlæs Bolius-URL:")
    if st.button("Analysér Artikel"):
        with st.spinner("Henter data og keywords..."):
            title, text, keywords = scrape_with_metadata(url_input)
            st.session_state.current_title = title
            st.session_state.current_text = text
            st.session_state.current_keywords = keywords

    if 'current_title' in st.session_state:
        st.subheader(f"📍 {st.session_state.current_title}")
        
        # Vis Keywords som Tags
        if st.session_state.current_keywords:
            st.write("**Redaktionelle Keywords (Tags):**")
            cols = st.columns(len(st.session_state.current_keywords))
            for i, tag in enumerate(st.session_state.current_keywords):
                cols[i].button(tag, key=f"tag_{i}", disabled=True)
        
        # Brug keywords i prompten
        if st.button("Generér Smart Header baseret på tags"):
            tags_str = ", ".join(st.session_state.current_keywords)
            prompt = f"Du er ekspert i {tags_str}. Lav et resumé af denne tekst med fokus på disse emner: {st.session_state.current_text}"
            res = model.generate_content(prompt)
            st.info(res.text)

else:
    st.info("Indtast API-nøgle.")
