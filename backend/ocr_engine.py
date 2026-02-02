"""
Motore OCR unificato per testi antichi.
Supporta Kraken (ottimo per manoscritti) e Tesseract (per stampati).
"""
import io
import tempfile
from typing import Dict, Tuple, Optional
from PIL import Image, ImageEnhance

# Kraken per testi antichi e manoscritti
try:
    from kraken import binarization, pageseg, rpred
    from kraken.lib import models
    KRAKEN_AVAILABLE = True
except ImportError:
    KRAKEN_AVAILABLE = False

# Tesseract per stampati più recenti
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

class AncientOCREngine:
    """Motore OCR specializzato per testi antici."""
    
    def __init__(self):
        self.kraken_models = self._load_kraken_models()
        
    def _load_kraken_models(self) -> Dict:
        """Carica i modelli pre-addestrati di Kraken."""
        models_dict = {}
        if not KRAKEN_AVAILABLE:
            return models_dict
            
        try:
            # Modello per latino antico (richiede download)
            # https://github.com/mittagessen/kraken-models
            models_dict['lat_antiqua'] = models.load_any('lat_antiqua.mlmodel')
        except:
            print("Modelli Kraken non trovati. Usa 'kraken get' per scaricarli.")
            
        return models_dict
    
    def _preprocess_image(self, image_data: bytes) -> Image.Image:
        """Pre-elaborazione dell'immagine per migliorare l'OCR."""
        image = Image.open(io.BytesIO(image_data))
        
        # Converti in scala di grigi se necessario
        if image.mode != 'L':
            image = image.convert('L')
            
        # Migliora contrasto
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Riduci rumore
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)
        
        return image
    
    def process_with_kraken(self, image: Image.Image, 
                          language: str = 'lat') -> Tuple[str, float]:
        """Elabora con Kraken (ideale per manoscritti)."""
        if not KRAKEN_AVAILABLE:
            return "Kraken non installato", 0.0
            
        # Binarizzazione (cruciale per manoscritti)
        bw_image = binarization.nlbin(image)
        
        # Segmentazione della pagina
        segments = pageseg.segment(bw_image)
        
        # Riconoscimento del testo
        model = self.kraken_models.get('lat_antiqua')
        if not model:
            return "Modello Kraken non disponibile", 0.0
            
        predictions = rpred.rpred(model, bw_image, segments)
        
        # Estrai testo e confidenza media
        text_lines = []
        confidences = []
        
        for pred in predictions:
            text_lines.append(pred.prediction)
            if hasattr(pred, 'confidence'):
                confidences.extend(pred.confidence)
        
        full_text = '\n'.join(text_lines)
        avg_confidence = sum(confidences)/len(confidences) if confidences else 0.85
        
        return full_text, avg_confidence
    
    def process_with_tesseract(self, image: Image.Image,
                             language: str = 'lat') -> Tuple[str, float]:
        """Elabora con Tesseract (per stampati)."""
        if not TESSERACT_AVAILABLE:
            return "Tesseract non installato", 0.0
            
        # Configurazione per testi antichi
        custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
        
        # Supporto multilinguaggio
        lang_map = {
            'lat': 'lat',
            'grc': 'grc',
            'heb': 'heb',
            'ara': 'ara',
            'default': 'lat'
        }
        
        tesseract_lang = lang_map.get(language, lang_map['default'])
        
        try:
            # Estrai testo con dati di confidenza
            data = pytesseract.image_to_data(
                image, 
                lang=tesseract_lang,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Ricostruisci testo con linee
            text_lines = {}
            confidences = []
            
            for i, word in enumerate(data['text']):
                if word.strip():
                    line_num = data['line_num'][i]
                    if line_num not in text_lines:
                        text_lines[line_num] = []
                    text_lines[line_num].append(word)
                    confidences.append(data['conf'][i])
            
            # Unisci le linee
            sorted_lines = [text_lines[key] for key in sorted(text_lines.keys())]
            full_text = '\n'.join([' '.join(line) for line in sorted_lines])
            
            # Calcola confidenza media (escludendo valori -1)
            valid_confs = [c for c in confidences if c > 0]
            avg_confidence = sum(valid_confs)/len(valid_confs)/100 if valid_confs else 0.7
            
        except Exception as e:
            return f"Errore Tesseract: {str(e)}", 0.0
            
        return full_text, avg_confidence
    
    def process_image(self, image_data: bytes, 
                     engine: str = 'auto',
                     language: str = 'lat') -> Dict:
        """
        Processa un'immagine e restituisce il testo riconosciuto.
        
        Args:
            image_data: Bytes dell'immagine
            engine: 'kraken', 'tesseract', o 'auto'
            language: Codice lingua ('lat', 'grc', etc.)
            
        Returns:
            Dizionario con testo, confidenza e metadati
        """
        # Pre-elaborazione
        image = self._preprocess_image(image_data)
        
        # Selezione automatica del motore
        if engine == 'auto':
            # Euristica: Kraken per immagini molto "sporche" (manoscritti)
            # In produzione, usa ML per classificare il tipo di documento
            width, height = image.size
            aspect_ratio = width / height
            
            if aspect_ratio > 2.5:  # Probabile rotolo/manoscritto
                engine = 'kraken'
            else:
                engine = 'tesseract'
        
        # Processa con il motore selezionato
        if engine == 'kraken' and KRAKEN_AVAILABLE:
            text, confidence = self.process_with_kraken(image, language)
            used_engine = 'kraken'
        else:
            text, confidence = self.process_with_tesseract(image, language)
            used_engine = 'tesseract'
        
        # Metadati dell'immagine
        metadata = {
            'dimensions': f"{image.width}x{image.height}",
            'mode': image.mode,
            'engine_used': used_engine,
            'language_requested': language
        }
        
        return {
            'text': text,
            'confidence': confidence,
            'metadata': metadata,
            'success': len(text.strip()) > 0
        }

# Istanziamento globale
ocr_engine = AncientOCREngine()