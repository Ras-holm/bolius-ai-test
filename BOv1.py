import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# --- Konfiguration ---

# 1. Definer BO's "hjerne" (System Prompt)
BO_SYSTEM_INSTRUCTION = """
Du er BO, en hjælpsom AI-assistent fra Bolius.dk.
Din opgave er at besvare brugernes spørgsmål om bolig og have.

REGLER FOR DINE SVAR:
1. Du må KUN basere dit svar på den viden, du får udleveret i 'KONTEKST'.
2. Hvis svaret IKKE findes i den leverede 'KONTEKST', skal du svare præcist: "Jeg kan desværre ikke finde svaret i min nuværende viden."
3. Du må IKKE bruge generel viden eller information uden for 'KONTEKST'.
4. Hold dine svar korte og præcise, og referér kun til informationen fra 'KONTEKST'.
5. Tal dansk i en faglig, men letforståelig tone.
"""

# 2. Opsæt Gemini API-nøgle (Husk at sætte din miljøvariabel)
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("Fejl: GOOGLE_API_KEY er ikke sat. Afslutter.")
    exit()

# 3. Definer kilde og spørgsmål for denne test
URL_KILDE = "https://www.bolius.dk/saadan-mindsker-du-stoej-og-skjuler-varmepumpen-98283"
BRUGER_SPØRGSMÅL = "Min nabos varmepumpe larmer. Har du nogle gode tips til hvad man kan gøre?"


# --- Trin 1: RETRIEVAL (Hent data) ---

def fetch_article_text(url: str) -> str | None:
    """
    Henter alt tekstindhold fra en given URL.
    Simpel version til MVP - fjerner HTML-tags.
    """
    print(f"Henter indhold fra: {url}...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Stopper hvis der er fejl (f.eks. 404)
        
        # Brug BeautifulSoup til at "rense" HTML og kun få teksten
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # For Bolius.dk er hovedindholdet ofte i <article> tagget. Dette giver renere data.
        main_content = soup.find('article')
        if main_content:
            return main_content.get_text(separator=' ', strip=True)
        else:
            # Fallback hvis <article> ikke findes
            return soup.get_text(separator=' ', strip=True)

    except requests.RequestException as e:
        print(f"Fejl under hentning af URL: {e}")
        return None


# --- Hovedlogik ---

if __name__ == "__main__":
    
    # Kør Trin 1: Hent den relevante tekst fra Bolius.dk
    kontekst_tekst = fetch_article_text(URL_KILDE)

    if not kontekst_tekst:
        print("Kunne ikke hente kontekst. Processen stopper.")
    else:
        print(f"Hentede succesfuldt {len(kontekst_tekst)} tegn som kontekst.\n")

        # Initialiser Gemini-modellen med vores systeminstruktion
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=BO_SYSTEM_INSTRUCTION
        )

        # --- Trin 2: AUGMENTATION (Byg prompt) ---
        final_prompt = f"""
        KONTEKST:
        ---
        {kontekst_tekst}
        ---

        SPØRGSMÅL: {BRUGER_SPØRGSMÅL}
        """
        
        print("--- Sender følgende til Gemini (forkortet) ---")
        print(f"SYSTEM INSTRUCTION: {BO_SYSTEM_INSTRUCTION[:100]}...")
        print(f"KONTEKST: {kontekst_tekst[:200]}...")
        print(f"SPØRGSMÅL: {BRUGER_SPØRGSMÅL}\n")


        # --- Trin 3: GENERATION (Få svar fra AI) ---
        print("--- BO's Svar ---")
        try:
            response = model.generate_content(final_prompt)
            print(response.text)
        except Exception as e:
            print(f"Der opstod en fejl under kald til Gemini API: {e}")
