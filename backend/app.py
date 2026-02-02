"""
API principale di Philologica.
Espone endpoint RESTful per l'elaborazione di testi antichi.
"""
import os
import tempfile
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ocr_engine import ocr_engine

# Modelli di richiesta/risposta
class OCRRequest(BaseModel):
    language: str = "lat"
    engine: str = "auto"
    preprocess: bool = True

class AnalysisRequest(BaseModel):
    text: str
    analysis_type: str = "all"  # 'stats', 'pos', 'entities'

# Inizializza app
app = FastAPI(
    title="Philologica API",
    description="Piattaforma open-source per l'analisi di testi antichi",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS per il frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specifica gli origini
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint di salute
@app.get("/")
async def root():
    return {
        "name": "Philologica",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "ocr": "/api/ocr",
            "analyze": "/api/analyze",
            "languages": "/api/languages",
            "engines": "/api/engines"
        }
    }

# Endpoint OCR
@app.post("/api/ocr")
async def process_ocr(
    file: UploadFile = File(...),
    language: str = Query("lat", description="Codice lingua"),
    engine: str = Query("auto", description="Motore OCR: 'kraken', 'tesseract', o 'auto'")
):
    """
    Processa un'immagine contenente testo antico.
    
    Supporta: latino (lat), greco antico (grc), ebraico (heb), arabo (ara).
    """
    # Controlla estensione file
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Formato non supportato. Usa: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Leggi file
        contents = await file.read()
        
        # Processa con il motore OCR
        result = ocr_engine.process_image(
            image_data=contents,
            engine=engine,
            language=language
        )
        
        # Aggiungi metadati file
        result['filename'] = file.filename
        result['file_size'] = len(contents)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint analisi testuale
@app.post("/api/analyze")
async def analyze_text(request: AnalysisRequest):
    """
    Analizza un testo estratto.
    
    Tipi di analisi:
    - 'stats': statistiche testuali
    - 'pos': Part-of-Speech tagging
    - 'entities': riconoscimento entità
    - 'all': tutto
    """
    # Per ora, implementazione base
    # In futuro: integrare spaCy, NLTK, etc.
    
    text = request.text
    
    # Statistiche di base
    stats = {
        'characters': len(text),
        'characters_no_spaces': len(text.replace(' ', '')),
        'words': len(text.split()),
        'lines': len(text.splitlines()),
        'avg_word_length': sum(len(w) for w in text.split())/len(text.split()) if text.split() else 0
    }
    
    return {
        'analysis_type': request.analysis_type,
        'statistics': stats,
        'language_detected': 'la',  # Da implementare
        'timestamp': datetime.now().isoformat()
    }

# Endpoint lingue supportate
@app.get("/api/languages")
async def get_supported_languages():
    """Restituisce le lingue supportate dall'OCR."""
    return {
        "tesseract": ["lat", "grc", "heb", "ara", "eng", "fra", "deu", "ita"],
        "kraken": ["lat_antiqua", "default"],  # Kraken usa modelli specifici
        "recommended": {
            "manuscripts": "kraken",
            "printed_latin": "tesseract:lat",
            "greek_papyri": "tesseract:grc"
        }
    }

# Endpoint motori disponibili
@app.get("/api/engines")
async def get_available_engines():
    """Restituisce i motori OCR disponibili e il loro stato."""
    return {
        "kraken": {
            "available": ocr_engine.KRAKEN_AVAILABLE,
            "specialization": "Manoscritti, testi antichi, layout complessi",
            "models": list(ocr_engine.kraken_models.keys())
        },
        "tesseract": {
            "available": ocr_engine.TESSERACT_AVAILABLE,
            "specialization": "Testi stampati, lingue moderne",
            "languages": ["lat", "grc", "heb", "ara"]
        }
    }

# Endpoint per download risultati
@app.get("/api/export/{format}")
async def export_results(
    text: str,
    format: str = Query("txt", regex="^(txt|xml|tei|json)$")
):
    """Esporta il testo in vari formati."""
    if format == "txt":
        content = text
        media_type = "text/plain"
    elif format == "json":
        content = json.dumps({"text": text, "version": "1.0"})
        media_type = "application/json"
    elif format == "tei":
        # Base TEI XML - da espandere
        content = f"""<?xml version="1.0"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <p>{text}</p>
    </body>
  </text>
</TEI>"""
        media_type = "application/xml"
    
    # Crea file temporaneo
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=f".{format}") as f:
        f.write(content)
        temp_path = f.name
    
    return FileResponse(
        temp_path,
        media_type=media_type,
        filename=f"philologica_export.{format}"
    )

# Middleware per logging
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    print(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response

# Punto di ingresso
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True  # Per sviluppo
    )