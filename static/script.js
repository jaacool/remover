document.addEventListener('DOMContentLoaded', function() {
    // UI-Elemente
    const inputText = document.getElementById('input-text');
    const outputText = document.getElementById('output-text');
    const cleanBtn = document.getElementById('clean-btn');
    const translateBtn = document.getElementById('translate-btn');
    const copyBtn = document.getElementById('copy-btn');
    const copyNotification = document.getElementById('copy-notification');
    const langDe = document.getElementById('lang-de');
    const langEn = document.getElementById('lang-en');
    
    // Status-Variablen
    let detectedWatermarks = {};
    let isShowingDetection = false;
    
    // Spracheinstellungen
    const translations = {
        'de': {
            'main-title': 'ChatGPT Wasserzeichenentfernung',
            'input-label': 'KI-Text mit Wasserzeichen einfügen:',
            'output-label': 'Bereinigter Text:',
            'clean-btn': 'Wasserzeichen entfernen',
            'translate-btn': 'Übersetzen',
            'copy-btn': 'Kopieren',
            'copy-notification': 'Kopiert!',
            'footer-text': 'Diese App entfernt unsichtbare Wasserzeichen aus KI-generierten Texten.',
            'translation-note': 'Hinweis: Für die Übersetzungsfunktion wird ein API-Key benötigt.',
            'input-placeholder': 'Füge hier deinen Text ein...'
        },
        'en': {
            'main-title': 'ChatGPT Watermark Removal',
            'input-label': 'Insert AI text with watermarks:',
            'output-label': 'Cleaned Text:',
            'clean-btn': 'Remove Watermarks',
            'translate-btn': 'Translate',
            'copy-btn': 'Copy',
            'copy-notification': 'Copied!',
            'footer-text': 'This app removes invisible watermarks from AI-generated texts.',
            'translation-note': 'Note: An API key is required for the translation function.',
            'input-placeholder': 'Paste your text here...'
        }
    };
    
    // Aktuelle Sprache
    let currentLanguage = 'de';
    
    // Funktion zum Wechseln der Sprache
    function changeLanguage(lang) {
        currentLanguage = lang;
        
        // Aktive Klasse für Sprachbuttons aktualisieren
        if (lang === 'de') {
            langDe.classList.add('active');
            langEn.classList.remove('active');
        } else {
            langEn.classList.add('active');
            langDe.classList.remove('active');
        }
        
        // UI-Texte aktualisieren
        for (const [id, text] of Object.entries(translations[lang])) {
            const element = document.getElementById(id);
            if (element) {
                if (element.tagName === 'BUTTON' || element.tagName === 'DIV') {
                    element.textContent = text;
                } else {
                    element.textContent = text;
                }
            }
        }
        
        // Placeholder aktualisieren
        inputText.placeholder = translations[lang]['input-placeholder'];
    }
    
    // Wasserzeichen erkennen und anzeigen
    async function detectWatermarks() {
        const text = inputText.value.trim();
        if (!text) return;
        
        try {
            const response = await fetch('/detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text
                })
            });
            
            const data = await response.json();
            detectedWatermarks = data.watermark_stats;
            
            // Wenn Wasserzeichen gefunden wurden, zeige sie an
            if (Object.keys(detectedWatermarks).length > 0) {
                // Aktualisiere den Button-Text basierend auf der Sprache
                cleanBtn.textContent = currentLanguage === 'de' ? 'Wasserzeichen entfernen' : 'Remove Watermarks';
                
                // Zeige markierten Text und Statistiken an
                outputText.innerHTML = data.marked_text;
                
                // Erstelle eine Zusammenfassung der gefundenen Wasserzeichen
                let summary = currentLanguage === 'de' ? 
                    '<div class="watermark-summary"><h3>Gefundene Wasserzeichen:</h3><ul>' : 
                    '<div class="watermark-summary"><h3>Detected Watermarks:</h3><ul>';
                
                for (const [char, info] of Object.entries(detectedWatermarks)) {
                    summary += `<li><span class="watermark-code">${info.unicode}</span>: ${info.description} - ${info.count}x</li>`;
                }
                
                summary += '</ul></div>';
                
                // Füge die Zusammenfassung zum Ausgabetext hinzu
                outputText.innerHTML = summary + outputText.innerHTML;
                
                isShowingDetection = true;
            } else {
                // Keine Wasserzeichen gefunden
                outputText.innerHTML = currentLanguage === 'de' ? 
                    '<div class="no-watermarks">Keine Wasserzeichen gefunden!</div>' : 
                    '<div class="no-watermarks">No watermarks found!</div>';
            }
        } catch (error) {
            console.error('Fehler beim Erkennen der Wasserzeichen:', error);
            outputText.innerHTML = '';
            outputText.textContent = currentLanguage === 'de' ? 
                'Fehler beim Erkennen der Wasserzeichen. Bitte versuche es erneut.' : 
                'Error detecting watermarks. Please try again.';
        }
    }
    
    // Text bereinigen
    async function cleanText() {
        // Wenn wir gerade die Erkennung anzeigen, entferne die Wasserzeichen
        if (isShowingDetection) {
            const text = inputText.value.trim();
            if (!text) return;
            
            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text: text,
                        action: 'clean'
                    })
                });
                
                const data = await response.json();
                // Wichtig: Hier muss .innerHTML verwendet werden, nicht .value
                outputText.innerHTML = '';
                outputText.textContent = data.result;
                
                // Aktualisiere den Button-Text basierend auf der Sprache
                cleanBtn.textContent = currentLanguage === 'de' ? 'Erneut prüfen' : 'Check Again';
                
                isShowingDetection = false;
            } catch (error) {
                console.error('Fehler beim Bereinigen des Textes:', error);
                outputText.innerHTML = '';
                outputText.textContent = currentLanguage === 'de' ? 
                    'Fehler beim Verarbeiten des Textes. Bitte versuche es erneut.' : 
                    'Error processing text. Please try again.';
            }
        } else {
            // Sonst zeige die Erkennung an
            detectWatermarks();
        }
    }
    
    // Text übersetzen
    async function translateText() {
        const text = inputText.value.trim();
        if (!text) return;
        
        // Zielsprache basierend auf aktueller UI-Sprache
        const targetLanguage = currentLanguage === 'de' ? 'en' : 'de';
        
        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    action: 'translate',
                    target_language: targetLanguage
                })
            });
            
            const data = await response.json();
            // Wichtig: Hier muss .innerHTML und .textContent verwendet werden, nicht .value
            outputText.innerHTML = '';
            outputText.textContent = data.result;
        } catch (error) {
            console.error('Fehler beim Übersetzen des Textes:', error);
            const errorMessage = currentLanguage === 'de' 
                ? 'Fehler beim Übersetzen des Textes. Bitte versuche es erneut.' 
                : 'Error translating text. Please try again.';
            outputText.innerHTML = '';
            outputText.textContent = errorMessage;
        }
    }
    
    // Text in die Zwischenablage kopieren
    function copyToClipboard() {
        // Erstelle einen temporären Textbereich für den reinen Text
        const tempTextarea = document.createElement('textarea');
        
        // Wenn wir die Erkennung anzeigen, kopiere nur den bereinigten Text
        if (isShowingDetection) {
            // Hole den Text ohne HTML-Tags
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = outputText.innerHTML;
            // Entferne die Zusammenfassung, falls vorhanden
            const summary = tempDiv.querySelector('.watermark-summary');
            if (summary) summary.remove();
            // Entferne alle Wasserzeichen-Markierungen
            const watermarks = tempDiv.querySelectorAll('.watermark');
            watermarks.forEach(mark => {
                mark.parentNode.removeChild(mark);
            });
            tempTextarea.value = tempDiv.textContent;
        } else {
            // Normaler Text
            tempTextarea.value = outputText.textContent || outputText.innerText;
        }
        
        document.body.appendChild(tempTextarea);
        tempTextarea.select();
        document.execCommand('copy');
        document.body.removeChild(tempTextarea);
        
        // Benachrichtigung anzeigen
        copyNotification.classList.remove('hidden');
        setTimeout(() => {
            copyNotification.classList.add('hidden');
        }, 2000);
    }
    
    // Event-Listener
    cleanBtn.addEventListener('click', cleanText);
    translateBtn.addEventListener('click', translateText);
    copyBtn.addEventListener('click', copyToClipboard);
    langDe.addEventListener('click', () => changeLanguage('de'));
    langEn.addEventListener('click', () => changeLanguage('en'));
    
    // Keine automatische Bereinigung bei Eingabe mehr, da wir jetzt einen zweistufigen Prozess haben
});
