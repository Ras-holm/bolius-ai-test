import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions
import os

st.set_page_config(page_title="Bolius Prototype", layout="wide")

# Opsætning af API
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

# Funktion til logning af videnshuller
def log_gap(query):
    with open("videnshuller.txt", "a", encoding="utf-8") as f:
        f.write(f"{query}\n")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-lite')

        # Cache funktionen så vi sparer penge/kvote
        @st.cache_data
        def get_smart_header(text):
            prompt = f"Giv 3 korte pointer og 3 FAQ baseret på denne tekst: {text}"
            return model.generate_content(prompt).text

        article_text = st.text_area("Indsæt artiklens tekst:", height=200)

        if article_text:
            # 1. Smart Header (Gemmes i cache)
            if st.button("Generér/Vis Smart Header"):
                try:
                    header = get_smart_header(article_text)
                    st.info(header)
                except exceptions.ResourceExhausted:
                    st.error("Kvote nået. Vent 60 sek.")

            st.divider()

            # 2. Gap-Catcher
            user_query = st.text_input("Spørg artiklen:")
            if user_query:
                try:
                    res = model.generate_content(f"Svar kort på '{user_query}' baseret på: {article_text}. Hvis svaret mangler, svar 'GAP_DETECTED'.").text
                    if "GAP_DETECTED" in res:
                        st.error("⚠️ Videnshul fundet!")
                        log_gap(user_query) # Gemmer til filen
                        st.success(f"'{user_query}' er logget til redaktionen.")
                    else:
                        st.write(res)
                except exceptions.ResourceExhausted:
                    st.error("Kvote nået.")

            # 3. Vis loggen (til dit møde)
            if os.path.exists("videnshuller.txt"):
                with st.expander("📊 Se opsamlede data (kun for admin)"):
                    with open("videnshuller.txt", "r", encoding="utf-8") as f:
                        st.text(f.read())

    except Exception as e:
        st.error(f"Fejl: {e}")
else:
    st.info("Indtast API-nøgle.")
