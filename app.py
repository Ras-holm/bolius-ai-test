import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Bolius Gap-Catcher", layout="centered")

st.title("🏠 Bolius Gap-Catcher")
api_key = st.sidebar.text_input("Indtast Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Vi bruger 'gemini-1.5-flash' da den er mest stabil til widgets
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        article_text = st.text_area("Indsæt artiklens tekst her:", height=200)
        user_query = st.text_input("Spørg om noget, artiklen (måske) ikke dækker:")

        if st.button("Tjek for videnshuller") and article_text and user_query:
            prompt = f"""
            Du er en fagekspert fra Bolius. Svar kun baseret på denne tekst: {article_text}
            Hvis teksten IKKE indeholder svaret på spørgsmålet "{user_query}", skal du svare: "GAP_FOUND".
            Ellers giv et kort svar.
            """
            response = model.generate_content(prompt)
            
            if "GAP_FOUND" in response.text:
                st.error("⚠️ Videnshul fundet! Dette spørgsmål kan artiklen ikke besvare.")
                st.info(f"Log: Bruger savner info om: {user_query}")
            else:
                st.success("Svar fundet i artiklen:")
                st.write(response.text)
                
    except Exception as e:
        st.error(f"Der opstod en teknisk fejl: {e}")
else:
    st.info("Start med at indsætte din API-nøgle i menuen til venstre.")
