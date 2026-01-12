import streamlit as st
import google.generativeai as genai

# Konfiguration af siden
st.set_page_config(page_title="Bolius Smart Header MVP", layout="centered")

# Overskrift og Bolius-branding (simuleret)
st.title("🏠 Bolius Smart Header")
st.subheader("AI-drevet resumé og spørgehjørne")

# Indtast din Gemini API nøgle i sidebar (til testbrug)
api_key = st.sidebar.text_input("Indtast Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')

    # Input: Her indsætter du artiklens tekst (senere kan vi automatisere dette)
    article_text = st.text_area("Indsæt artiklens tekst her:", height=200, placeholder="Kopiér teksten fra en Bolius-artikel...")

    if article_text:
        # Step 1: Generér Smart Header
        if st.button("Generér Smart Header"):
            prompt = f"""
            Analysér følgende artikel fra Bolius og giv:
            1. Et ultra-kort resumé (max 3 bullets) med de vigtigste pointer for boligejeren.
            2. Tre spørgsmål, som artiklen giver svar på.
            3. Identificér ét punkt, som artiklen IKKE dækker, men som er relevant for emnet.
            
            Artikel: {article_text}
            """
            response = model.generate_content(prompt)
            st.markdown("---")
            st.markdown("### ⚡ Lyn-overblik")
            st.write(response.text)

        # Step 2: Spørgsmål og Gap-analyse
        st.markdown("---")
        user_question = st.text_input("Spørg om noget, artiklen ikke dækker:")
        
        if user_question:
            gap_prompt = f"""
            Baseret KUN på denne artikel: {article_text}
            Svar på spørgsmålet: {user_question}
            Hvis svaret ikke findes i artiklen, skal du svare: "Svaret findes ikke i artiklen."
            """
            answer = model.generate_content(gap_prompt)
            
            if "Svaret findes ikke i artiklen" in answer.text:
                st.warning("Dette er et videns-hul! Vi har logget dit spørgsmål til redaktionen.")
                # Her logger vi "hullet" (i denne MVP viser vi det bare på skærmen)
                st.info(f"Logget spørgsmål: {user_question}")
            else:
                st.success("Svar fundet i artiklen:")
                st.write(answer.text)
else:
    st.info("Indtast din API-nøgle i venstre side for at starte.")
