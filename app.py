import streamlit as st
from PIL import Image
import pytesseract
from kraken import binarization, rpred
import requests
import io

st.title("Toolkit Filologico per Testi Antichi")
st.write("Strumento semplice per digitalizzare, analizzare e tradurre testi in lingue semitiche, greco, latino e medievali europee.")

tool = st.sidebar.selectbox("Scegli funzione", ["Digitalizzazione (OCR/HTR)", "Analisi Testuale", "Traduzione", "Identificazione"])

if tool == "Digitalizzazione (OCR/HTR)":
    uploaded_file = st.file_uploader("Carica immagine di manoscritto (PNG/JPG/PDF)", type=["png", "jpg", "pdf"])
    lang = st.selectbox("Lingua", ["grc (Greco antico)", "lat (Latino)", "heb (Ebraico semitico)", "deu_frak (Gotico medievale)", "eng (Inglese antico)"])  # Aggiungi altre
    if uploaded_file:
        image = Image.open(uploaded_file)
        # Tesseract OCR semplice
        text = pytesseract.image_to_string(image, lang=lang.split()[0])
        st.write("Testo estratto (Tesseract):", text)
        # Kraken HTR avanzato (per manoscritti)
        try:
            bw_image = binarization.nlbin(image)
            pred = rpred.rpred(model='generic.mlmodel', im=bw_image)  # Usa modello generico; scarica specifici da Kraken repo
            st.write("Testo estratto (Kraken):", pred.prediction)
        except:
            st.write("Kraken non pronto; usa Tesseract.")

if tool == "Analisi Testuale":
    text_input = st.text_area("Inserisci testo estratto")
    if text_input:
        # Embed Voyant Tools (web-based)
        voyant_url = f"https://voyant-tools.org/?input={text_input}"
        st.components.v1.html(f'<iframe src="{voyant_url}" width="100%" height="600"></iframe>')

if tool == "Traduzione":
    text = st.text_area("Testo da tradurre")
    lang_from = st.selectbox("Da", ["grc|eng (Greco>Inglese)", "lat|eng (Latino>Inglese)", "heb|eng (Ebraico>Inglese)"])  # Espandi
    if text:
        # Apertium API (free)
        pair = lang_from.split('|')[0] + '|' + lang_from.split('|')[1]
        response = requests.get(f"https://www.apertium.org/apy/translate?langpair={pair}&q={text}")
        if response.status_code == 200:
            st.write("Traduzione:", response.json()["responseData"]["translatedText"])
        else:
            st.write("Errore traduzione; riprova.")

if tool == "Identificazione":
    text_fragment = st.text_area("Inserisci frammento testo")
    if text_fragment:
        # Esempio semplice con Perseus API (adatta per Ithaca/Perseus)
        perseus_url = f"http://www.perseus.tufts.edu/hopper/text?doc={text_fragment}"
        st.write("Link a Perseus per identificazione:", perseus_url)
        st.components.v1.html(f'<iframe src="{perseus_url}" width="100%" height="600"></iframe>')