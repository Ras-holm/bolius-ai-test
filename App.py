import streamlit as st
import google.generativeai as genai
import datetime

# --- Konfiguration & UI ---
st.set_page_config(page_title="BO - Bolius AI Sidebar", layout="wide")

# Styling af sidebaren for at simulere Bolius-look
st.markdown("""
    <style>
    .stSidebar { background-color: #f9f9f9; border-left: 1px solid #ddd; }
    .gap-warning { color: #d9534f; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 1. API Opsætning
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception:
    st.error("API-nøgle mangler! Tilføj GOOGLE_API_KEY i Streamlit Secrets.")
    st.stop()

# 2. BO's Grundlov (System Instruction)
BO_SYSTEM_INSTRUCTION = """
Du er BO, en uvildig AI-assistent for Bolius. 
Din opgave er at hjælpe brugere baseret på de udleverede dokumenter.

REGLER FOR SVAR:
1. KILDE-HIERARKI: 
   - Prioritér altid "PRIMÆR_ARTIKEL". Hvis svaret findes her, giv et kort og præcist resumé.
   - Hvis svaret ikke er i primær artikel, søg i "EMNE_CLUSTER". Hvis svaret findes her, giv ét kort svar (max 1 linje) efterfulgt af: "Læs mere her: [Link]".
   - Hvis svaret IKKE findes i hverken primær artikel eller emne-cluster, skal du svare præcis: "GAP_DETECTED".

2. TONE & STIL:
   - Svar professionelt, neutralt og faktuelt på dansk.
   - Undgå at anbefale specifikke mærker.
   - Brug korrekte byggetekniske termer.

3. BEGRÆNSNINGER:
   - Brug ALDRIG din egen viden uden for kontekst.
   - Ved tvivl, svar altid "GAP_DETECTED".
"""

# --- App Layout ---
st.title("BO - Bolius AI Sidebar (MVP)")

# Tabs til administration vs. brugeroplevelse
tab1, tab2 = st.tabs(["🖥️ Brugerflade (Demo)", "⚙️ Datagrundlag (Admin)"])

with tab2:
    st.subheader("Indlæs viden til BO")
    primær_tekst = st.text_area("Primær artikel (den brugeren læser lige nu):", height=200, placeholder="Indsæt tekst her...")
    cluster_tekst = st.text_area("Emne-cluster (relateret viden):", height=300, placeholder="Indsæt tekst og links fra relaterede artikler her...")

with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.info("👈 Indlæs data under fanen 'Datagrundlag' for at starte.")
        st.markdown("### Simuleret Artikel-visning")
        if primær_tekst:
            st.markdown(primær_tekst[:500] + "...")
        else:
            st.write("Ingen artikel indlæst.")

    # SIDEBAR - Her bor BO
    with st.sidebar:
        st.header("🤖 Spørg BO")
        user_input = st.text_input("Hvad vil du vide om emnet?", key="bo_input")
        
        if st.button("Spørg BO"):
            if not primær_tekst:
                st.warning("Indlæs venligst data først.")
            else:
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-pro",
                    system_instruction=BO_SYSTEM_INSTRUCTION
                )
                
                full_prompt = f"""
                PRIMÆR_ARTIKEL:
                {primær_tekst}
                
                EMNE_CLUSTER:
                {cluster_tekst}
                
                BRUGER_SPØRGSMÅL:
                {user_input}
                """
                
                with st.spinner("BO kigger i arkivet..."):
                    response = model.generate_content(full_prompt)
                    svar = response.text
                    
                    if "GAP_DETECTED" in svar:
                        st.error("BO kunne ikke finde svaret i Bolius' viden.")
                        st.markdown("<p class='gap-warning'>Spørgsmålet er logget til redaktionen.</p>", unsafe_allow_html=True)
                        
                        # Gapcatcher logning (simuleret via session state i demo)
                        if 'gap_logs' not in st.session_state:
                            st.session_state.gap_logs = []
                        st.session_state.gap_logs.append({
                            "tid": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "spørgsmål": user_input
                        })
                    else:
                        st.success("Svar fra BO:")
                        st.write(svar)

        # Visning af Gapcatcher logs (kun for dig i demo-fasen)
        if st.checkbox("Vis Gapcatcher logs (Admin)"):
            if 'gap_logs' in st.session_state and st.session_state.gap_logs:
                st.write(st.session_state.gap_logs)
            else:
                st.write("Ingen ubesvarede spørgsmål endnu.")
