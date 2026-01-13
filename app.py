import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions

st.set_page_config(page_title="Bolius Gap-Catcher", layout="wide")

# Sidebar
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

# Initialisér hukommelse (Session State) så vi ikke mister data ved refresh
if 'smart_header' not in st.session_state:
    st.session_state.smart_header = ""
if 'gap_result' not in st.session_state:
    st.session_state.gap_result = ""
if 'gaps' not in st.session_state:
    st.session_state.gaps = []

st.title("🏠 Bolius Videns-Widget")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Vi bruger den mest stabile model fra din liste
        model = genai.GenerativeModel('gemini-2.0-flash')

        article_text = st.text_area("Indsæt artiklens tekst:", height=200)

        # --- DEL 1: SMART HEADER (KUN ved klik) ---
        if st.button("Generér Smart Header"):
            if article_text:
                try:
                    with st.spinner("Tænker..."):
                        res = model.generate_content(f"Giv 3 korte pointer og 3 FAQ baseret på: {article_text}")
                        st.session_state.smart_header = res.text
                except exceptions.ResourceExhausted:
                    st.error("Kvote nået. Vent 60 sekunder.")

        if st.session_state.smart_header:
            st.info(st.session_state.smart_header)

        st.divider()

        # --- DEL 2: GAP-CATCHER (KUN ved klik) ---
        user_query = st.text_input("Hvad vil du gerne vide?")
        if st.button("Tjek for svar"):
            if article_text and user_query:
                try:
                    with st.spinner("Søger i teksten..."):
                        res = model.generate_content(f"Svar kort på '{user_query}' baseret på: {article_text}. Hvis svaret mangler, svar KUN 'GAP_DETECTED'.").text
                        if "GAP_DETECTED" in res:
                            st.session_state.gap_result = "⚠️ Videnshul fundet!"
                            if user_query not in st.session_state.gaps:
                                st.session_state.gaps.append(user_query)
                        else:
                            st.session_state.gap_result = res
                except exceptions.ResourceExhausted:
                    st.error("Kvote nået.")

        if st.session_state.gap_result:
            if "⚠️" in st.session_state.gap_result:
                st.error(st.session_state.gap_result)
            else:
                st.success(st.session_state.gap_result)

        # --- DEL 3: REDAKTIONEL LOG ---
        if st.session_state.gaps:
            with st.expander("📋 Se opsamlede videnshuller"):
                for gap in st.session_state.gaps:
                    st.write(f"• {gap}")

    except Exception as e:
        st.error(f"Teknisk fejl: {e}")
else:
    st.info("Indtast API-nøgle i menuen til venstre.")
