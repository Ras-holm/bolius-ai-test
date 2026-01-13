import streamlit as st
import google.generativeai as genai

st.title("🛠 Gemini Diagnose")
api_key = st.sidebar.text_input("API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    try:
        st.write("Dine tilgængelige modeller:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                st.code(m.name) # Dette er det navn, du skal bruge i koden
    except Exception as e:
        st.error(f"Fejl ved opslag: {e}")
