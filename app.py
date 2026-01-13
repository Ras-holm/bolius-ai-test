def scrape_bolius_final(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hent titel
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Ingen titel"

        # Rens uønskede elementer før vi udtrækker tekst
        for noise in soup(["script", "style", "nav", "footer", "header", "aside"]):
            noise.extract()

        # Find alt tekst i paragraffer
        paragraphs = soup.find_all('p')
        text_content = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40]
        
        full_text = "\n\n".join(text_content)
        return title, full_text
    except Exception as e:
        return "Fejl", str(e)
