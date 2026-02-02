/**
 * Philologica OCR - Frontend Logic
 * Gestione delle chiamate API e visualizzazione risultati
 */

const API_BASE = 'http://localhost:8000/api';  // Cambia in produzione

class PhilologicaOCR {
    constructor() {
        this.currentImage = null;
        this.currentResults = null;
    }
    
    /**
     * Processa un'immagine tramite l'API
     */
    async processImage(imageFile, language = 'lat', engine = 'auto') {
        const processBtn = document.getElementById('processBtn');
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        // Disabilita bottone e mostra progresso
        processBtn.disabled = true;
        processBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i> Processamento...';
        progressContainer.style.display = 'block';
        
        // Animazione progresso
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 2;
            if (progress > 90) progress = 90;
            progressBar.style.width = `${progress}%`;
            progressText.textContent = `${progress}%`;
        }, 200);
        
        try {
            // Crea FormData
            const formData = new FormData();
            formData.append('file', imageFile);
            formData.append('language', language);
            formData.append('engine', engine);
            
            // Chiamata API
            const response = await fetch(`${API_BASE}/ocr`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Aggiorna UI con risultati
            this.displayResults(result);
            
            // Completa progresso
            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            
            // Salva risultati
            this.currentResults = result;
            
            return result;
            
        } catch (error) {
            console.error('OCR Error:', error);
            this.showError(error.message);
            return null;
            
        } finally {
            // Ripristina bottone
            setTimeout(() => {
                processBtn.disabled = false;
                processBtn.innerHTML = '<i class="bi bi-magic me-2"></i> Processa OCR';
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                    progressBar.style.width = '0%';
                    progressText.textContent = '0%';
                }, 1000);
            }, 500);
        }
    }
    
    /**
     * Visualizza i risultati nella UI
     */
    displayResults(data) {
        // Nascondi empty state
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('resultsArea').style.display = 'block';
        
        // Testo trascritto
        const textOutput = document.getElementById('textOutput');
        textOutput.value = data.text || '';
        
        // Confidenza
        const confidence = data.confidence || 0;
        const confidenceValue = document.getElementById('confidenceValue');
        const confidenceFill = document.getElementById('confidenceFill');
        
        confidenceValue.textContent = `${(confidence * 100).toFixed(1)}%`;
        confidenceFill.style.width = `${confidence * 100}%`;
        
        // Colore in base alla confidenza
        confidenceFill.className = 'confidence-fill ';
        if (confidence < 0.7) {
            confidenceFill.classList.add('confidence-low');
        } else if (confidence < 0.85) {
            confidenceFill.classList.add('confidence-medium');
        } else {
            confidenceFill.classList.add('confidence-high');
        }
        
        // Metadati
        document.getElementById('engineUsed').textContent = 
            data.metadata?.engine_used || 'sconosciuto';
        document.getElementById('imageDimensions').textContent = 
            data.metadata?.dimensions || 'sconosciute';
        
        // Aggiorna contatori
        this.updateTextCounters();
    }
    
    /**
     * Aggiorna contatori di caratteri e parole
     */
    updateTextCounters() {
        const text = document.getElementById('textOutput').value;
        document.getElementById('charCount').textContent = text.length;
        document.getElementById('wordCount').textContent = 
            text.split(/\s+/).filter(w => w.length > 0).length;
    }
    
    /**
     * Mostra errore
     */
    showError(message) {
        // Crea alert Bootstrap
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            <i class="bi bi-exclamation-triangle-fill me-2"></i>
            <strong>Errore:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Inserisci all'inizio del container principale
        const container = document.querySelector('.container.py-5');
        container.insertBefore(alert, container.firstChild);
        
        // Rimuovi automaticamente dopo 10 secondi
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 10000);
    }
    
    /**
     * Verifica lo stato dell'API
     */
    async checkAPIStatus() {
        try {
            const response = await fetch(`${API_BASE}/`);
            return response.ok;
        } catch (error) {
            return false;
        }
    }
    
    /**
     * Ottiene lingue supportate
     */
    async getSupportedLanguages() {
        try {
            const response = await fetch(`${API_BASE}/languages`);
            return await response.json();
        } catch (error) {
            return { tesseract: [], kraken: [] };
        }
    }
    
    /**
     * Ottiene motori disponibili
     */
    async getAvailableEngines() {
        try {
            const response = await fetch(`${API_BASE}/engines`);
            return await response.json();
        } catch (error) {
            return { kraken: { available: false }, tesseract: { available: false } };
        }
    }
}

// Istanza globale
const philologicaOCR = new PhilologicaOCR();

// Funzione globale per processare immagine
async function processImage() {
    const fileInput = document.getElementById('imageInput');
    const languageBadge = document.querySelector('.language-badge.active');
    const engineRadio = document.querySelector('input[name="engine"]:checked');
    
    if (!fileInput.files.length) {
        alert('Per favore, seleziona un\'immagine prima di processare.');
        return;
    }
    
    const language = languageBadge?.dataset.code || 'lat';
    const engine = engineRadio?.value || 'auto';
    
    await philologicaOCR.processImage(fileInput.files[0], language, engine);
}

// Esporta per uso globale
window.philologicaOCR = philologicaOCR;
window.processImage = processImage;