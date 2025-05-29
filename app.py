from flask import Flask, render_template, request, jsonify
import re
import html
import requests
import os

app = Flask(__name__)

# Gemeinsame Liste der bekannten Wasserzeichen und Ersetzungen
def get_watermark_definitions():
    # Ersetze spezielle Anführungszeichen und Gedankenstriche durch ihre normalen Entsprechungen
    replacements = {
        '\u2019': "'",  # Right Single Quotation Mark
        '\u2018': "'",  # Left Single Quotation Mark
        '\u201D': '"',  # Right Double Quotation Mark
        '\u201E': '"',  # Double Low-9 Quotation Mark
        '\u2013': "-",  # En Dash
        '\u2014': "-",  # Em Dash
    }
    
    # Erweiterte Liste aller bekannten Wasserzeichen
    chatgpt_watermarks = {
        # Spezifische ChatGPT-Wasserzeichen
        '\u00A0': "Non-breaking Space (geschütztes Leerzeichen)",
        '\u00AD': "Soft Hyphen (weiches Trennzeichen)",
        '\u200B': "Zero Width Space (Nullbreiten-Leerzeichen)",
        '\u200C': "Zero Width Non-Joiner (ZWNJ)",
        '\u200D': "Zero Width Joiner (ZWJ)",
        '\u202F': "Narrow No-Break Space (schmales geschütztes Leerzeichen)",
        '\u2060': "Word Joiner",
        '\u2020': "Kreuz (Dagger)",
        '\u2021': "Doppelkreuz (Double Dagger)",
        '\u2022': "Aufzählungszeichen (Bullet Point)",
        '\u2023': "Dreieckiges Aufzählungszeichen",
        '\u2043': "Hyphen Bullet",
        '\u204C': "Schwarzes Aufzählungszeichen",
        '\u204D': "Weißes Aufzählungszeichen",
        '\uFEFF': "Byte Order Mark (BOM)",
        # Anführungszeichen
        '\u201D': "Right Double Quotation Mark",
        '\u201E': "Double Low-9 Quotation Mark",
        '\u201C': "Left Double Quotation Mark",
        '\u201F': "Double High-Reversed-9 Quotation Mark",
        '\u2018': "Left Single Quotation Mark",
        '\u2019': "Right Single Quotation Mark",
        '\u201A': "Single Low-9 Quotation Mark",
        '\u201B': "Single High-Reversed-9 Quotation Mark",
        # Gedankenstriche und Bindestriche
        '\u2013': "En Dash",
        '\u2014': "Em Dash",
        '\u2015': "Horizontal Bar",
        '\u2010': "Hyphen",
        '\u2011': "Non-Breaking Hyphen",
        '\u2012': "Figure Dash",
        # Zusätzliche mögliche Wasserzeichen
        '\u2000': "En-Quadrat",
        '\u2001': "Em-Quadrat",
        '\u2002': "En-Leerzeichen",
        '\u2003': "Em-Leerzeichen",
        '\u2004': "Drittel-Em-Leerzeichen",
        '\u2005': "Viertel-Em-Leerzeichen",
        '\u2006': "Sechstel-Em-Leerzeichen",
        '\u2007': "Zahlen-Leerzeichen",
        '\u2008': "Interpunktions-Leerzeichen",
        '\u2009': "Dünnes Leerzeichen",
        '\u200A': "Haar-Leerzeichen",
        '\u200E': "Links-nach-Rechts-Markierung",
        '\u200F': "Rechts-nach-Links-Markierung",
        '\u2028': "Zeilentrenner",
        '\u2029': "Absatztrenner",
        '\u202A': "Links-nach-Rechts-Einbettung",
        '\u202B': "Rechts-nach-Links-Einbettung",
        '\u202C': "Richtungsformatierung beenden",
        '\u202D': "Links-nach-Rechts-Überschreibung",
        '\u202E': "Rechts-nach-Links-Überschreibung",
        '\u205F': "Mittleres mathematisches Leerzeichen",
        '\u2061': "Funktionsanwendung",
        '\u2062': "Unsichtbares Malzeichen",
        '\u2063': "Unsichtbarer Trenner",
        '\u2064': "Unsichtbares Pluszeichen",
        '\u2066': "Links-nach-Rechts-Isolierung",
        '\u2067': "Rechts-nach-Links-Isolierung",
        '\u2068': "Erste starke Isolierung",
        '\u2069': "Richtungsisolierung beenden",
        '\u206A': "Symmetrisches Tauschen verhindern (veraltet)",
        '\u206B': "Symmetrisches Tauschen aktivieren (veraltet)",
        '\u206C': "Arabische Formgestaltung verhindern (veraltet)",
        '\u206D': "Arabische Formgestaltung aktivieren (veraltet)",
        '\u206E': "Nationale Ziffernformen (veraltet)",
        '\u206F': "Nominale Ziffernformen (veraltet)",
        '\u3000': "Ideographisches Leerzeichen",
        '\u180E': "Mongolischer Vokaltrennzeichen",
        '\u061C': "Arabisches Buchstabenzeichen"
    }
    
    return replacements, chatgpt_watermarks

def detect_watermarks(text):
    """
    Identifiziert ChatGPT-Wasserzeichen im Text und markiert sie mit HTML-Tags.
    Gibt den markierten Text und ein Dictionary mit Informationen über die gefundenen Wasserzeichen zurück.
    """
    if not text:
        return "", {}
    
    # Hole die Definitionen
    replacements, chatgpt_watermarks = get_watermark_definitions()
    
    # Ersetze spezielle Anführungszeichen und Gedankenstriche
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Zähle und markiere die gefundenen Wasserzeichen
    watermark_stats = {}
    marked_text = text
    
    for char, description in chatgpt_watermarks.items():
        count = text.count(char)
        if count > 0:
            watermark_stats[char] = {
                "description": description,
                "count": count,
                "unicode": f"U+{ord(char):04X}"
            }
            
            # Markiere die unsichtbaren Zeichen im Text
            # Wir verwenden HTML-Span-Tags mit einer speziellen Klasse
            # Die tatsächlichen Zeichen werden durch den Unicode-Wert ersetzt
            unicode_value = f'U+{ord(char):04X}'
            marker = f'<span class="watermark" title="{description} ({unicode_value})">{unicode_value}</span>'
            marked_text = marked_text.replace(char, marker)
    
    return marked_text, watermark_stats

def remove_watermarks(text):
    """
    Entfernt ChatGPT-Wasserzeichen aus dem Text.
    Fokussiert sich auf die bekannten unsichtbaren Unicode-Zeichen, die von ChatGPT als Wasserzeichen verwendet werden,
    während normale Leerzeichen, Zeilenumbrüche und relevante Satzzeichen beibehalten werden.
    """
    if not text:
        return ""
    
    # Hole die Definitionen
    replacements, chatgpt_watermarks = get_watermark_definitions()
    
    # Ersetze spezielle Anführungszeichen und Gedankenstriche
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Ersetze ChatGPT-Wasserzeichen
    for char, description in chatgpt_watermarks.items():
        if char == '\u00A0':  # Geschütztes Leerzeichen durch normales Leerzeichen ersetzen
            text = text.replace(char, ' ')
        else:  # Andere Wasserzeichen komplett entfernen
            text = text.replace(char, '')
    
    # Zusätzliche Sicherheit: Entferne auch alle anderen potenziellen Unicode-Wasserzeichen-Zeichen
    # (Zeichen aus dem Private Use Area und andere unsichtbare Zeichen)
    text = re.sub(r'[\u0080-\u009F\uE000-\uF8FF\uFFF0-\uFFFF]', '', text)
    
    return text

def translate_text(text, target_language):
    """
    Einfache Übersetzungsfunktion, die eine grundlegende Übersetzung zwischen Deutsch und Englisch durchführt.
    In einer echten Anwendung würde hier eine API wie DeepL oder Google Translate verwendet werden.
    """
    if not text:
        return ""
    
    # Erkennen der Quellsprache (vereinfacht)
    source_language = "en" if any(word in text.lower() for word in ['the', 'and', 'is', 'are', 'to']) else "de"
    
    # Wenn Quell- und Zielsprache gleich sind, keine Übersetzung notwendig
    if source_language == target_language:
        return text + "\n\n[Keine Übersetzung notwendig, da Quell- und Zielsprache identisch sind.]"
    
    # Einfache Wörterbücher für die Übersetzung häufiger Wörter und Phrasen
    de_to_en = {
        'hallo': 'hello',
        'welt': 'world',
        'guten tag': 'good day',
        'wie geht es dir': 'how are you',
        'danke': 'thank you',
        'bitte': 'please',
        'ja': 'yes',
        'nein': 'no',
        'und': 'and',
        'oder': 'or',
        'ich': 'I',
        'du': 'you',
        'er': 'he',
        'sie': 'she',
        'es': 'it',
        'wir': 'we',
        'ihr': 'you',
        'sie': 'they'
    }
    
    en_to_de = {v: k for k, v in de_to_en.items()}
    
    # Hinweis zur Demo-Übersetzung
    result = text + "\n\n[Demo-Übersetzung: "
    
    # Einfache Ersetzung einiger Wörter als Demonstration
    if source_language == "de" and target_language == "en":
        for de_word, en_word in de_to_en.items():
            text = text.lower().replace(de_word, en_word)
        result += "Deutsch → Englisch"
    elif source_language == "en" and target_language == "de":
        for en_word, de_word in en_to_de.items():
            text = text.lower().replace(en_word, de_word)
        result += "Englisch → Deutsch"
    
    result += "]\n\nHinweis: Dies ist nur eine Demo-Übersetzung. Für eine vollständige Übersetzung wird eine API wie DeepL oder Google Translate benötigt."
    
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    data = request.get_json()
    input_text = data.get('text', '')
    
    # Wasserzeichen erkennen und markieren
    marked_text, watermark_stats = detect_watermarks(input_text)
    
    return jsonify({
        'marked_text': marked_text,
        'watermark_stats': watermark_stats
    })

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    input_text = data.get('text', '')
    action = data.get('action', 'clean')
    
    # Text bereinigen
    cleaned_text = remove_watermarks(input_text)
    
    # Bei Bedarf übersetzen
    if action == 'translate':
        target_language = data.get('target_language', 'en')
        result_text = translate_text(cleaned_text, target_language)
    else:
        result_text = cleaned_text
    
    return jsonify({'result': result_text})

if __name__ == '__main__':
    # In Produktion wird debug automatisch auf False gesetzt
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5002)))

# Diese Zeile wird für Gunicorn benötigt
app = app
