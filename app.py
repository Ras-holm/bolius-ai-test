import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Bolius Smart Header & Gap-Catcher", layout="wide")

# Sidebar
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

st.title("🏠 Bolius Videns-Widget")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    article_text = st.text_area("Indsæt artiklens tekst:", height=250)

    if article_text:
        # --- DEL 1: AUTOMATISK SMART HEADER ---
        if st.button("Generér Smart Header & FAQ"):
            with st.spinner("Analyserer artikel..."):
                header_prompt = f"""
                Analysér artiklen og giv:
                1. 3 korte bulletpoints med de vigtigste pointer.
                2. 3 FAQ-spørgsmål, som denne artikel giver svar på.
                
                Artikel: {article_text}
                """
                header_res = model.generate_content(header_prompt)
                
                st.markdown("### ⚡ Hurtigt overblik & FAQ")
                st.info(header_res.text)

        st.divider()

        # --- DEL 2: INTERAKTIV GAP-CATCHER ---
        st.subheader("🔍 Spørg artiklen (Gap-Catcher)")
        user_query = st.text_input("Hvad mangler du svar på?")

        if user_query:
            gap_prompt = f"""
            Svar på spørgsmålet baseret KUN på denne tekst: {article_text}
            Hvis svaret IKKE findes i teksten, svar præcis: "GAP_DETECTED".
            Ellers giv et kort svar.
            
            Spørgsmål: {user_query}
            """
            response = model.generate_content(gap_prompt)
            
            if "GAP_DETECTED" in response.text:
                st.error("⚠️ Videnshul! Dette emne dækkes ikke i artiklen.")
                st.session_state.setdefault('gaps', []).append(user_query)
            else:
                st.success("Svar fundet:")
                st.write(response.text)

        # --- DEL 3: REDAKTIONEL LOG ---
        if 'gaps' in st.session_state and st.session_state['gaps']:
            with st.expander("📋 Se opsamlede videnshuller (til redaktionen)"):
                for gap in st.session_state['gaps']:
                    st.write(f"• {gap}")
else:
    st.info("Indtast API-nøgle for at starte.")
