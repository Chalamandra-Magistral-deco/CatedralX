"""
Advanced transparent sentiment engine — domain-aware lexicon with intensifiers
Chalamandra Magistral DecoX · CatedralX

Mejoras sobre la versión básica:
  ✅ Palabras con peso diferente (no todas valen lo mismo)
  ✅ Intensificadores: "sube mucho" pesa más que "sube"
  ✅ Negaciones: "no sube" invierte el significado
  ✅ Emojis y signos de exclamación aumentan intensidad
  ✅ Puntuación desglosada + confianza
"""
from __future__ import annotations
import re

# Palabras con peso de sentimiento [-1.0, 1.0]
LEXICON = {
    # Positivas
    "sube": 0.3, "alcista": 0.4, "crece": 0.3, "positivo": 0.5,
    "recupera": 0.4, "fuerte": 0.4, "gana": 0.3, "estable": 0.25,
    "confianza": 0.45, "oportunidad": 0.35, "crecimiento": 0.4,
    "rentable": 0.5, "exitoso": 0.55, "sólido": 0.4, "mejora": 0.35,
    # Negativas
    "baja": -0.3, "bajista": -0.4, "cae": -0.4, "negativo": -0.5,
    "riesgo": -0.35, "débil": -0.4, "pierde": -0.35, "inestable": -0.45,
    "peligro": -0.6, "pérdida": -0.55, "incertidumbre": -0.3,
    "volatilidad": -0.25, "corrección": -0.3, "pánico": -0.7,
}

# Intensificadores: multiplican el peso de la siguiente palabra
INTENSIFIERS = {
    "muy": 1.5, "mucho": 1.4, "significativamente": 1.6,
    "claramente": 1.3, "definitivamente": 1.4, "fuerte": 1.4,
    "levemente": 0.6, "ligeramente": 0.7, "poco": 0.6,
}

# Negaciones: invierten el signo de la siguiente palabra
NEGATIONS = {"no", "ni", "nunca", "jamás", "sin", "menos"}

# Emojis de mercado
EMOJI_SENTIMENT = {
    "📈": 0.3, "🟢": 0.25, "✅": 0.2, "🚀": 0.4, "💰": 0.25,
    "📉": -0.3, "🔴": -0.25, "⚠️": -0.2, "⛔": -0.35, "💥": -0.5,
}


def analizar_sentimiento(texto: str) -> dict:
    """
    Analiza el sentimiento del texto con soporte para:
    - léxico ponderado
    - intensificadores
    - negaciones
    - emojis
    - puntuación de confianza
    """
    if not isinstance(texto, str):
        raise ValueError("texto must be a string")

    emojis_encontrados = {}
    for emoji, valor in EMOJI_SENTIMENT.items():
        if emoji in texto:
            emojis_encontrados[emoji] = texto.count(emoji) * valor

    texto_sin_emoji = re.sub(r"[^\w\s¡¿!?.,;:]", " ", texto.lower())
    tokens = re.findall(r"\b\w+\b", texto_sin_emoji)

    score_total = 0.0
    palabras_contadas = 0
    intensificador_activo = 1.0
    negacion_activa = False
    intensidad_exclamacion = 1.0

    exclamaciones = texto.count("!") + texto.count("¡")
    if exclamaciones >= 3:
        intensidad_exclamacion = 1.3
    elif exclamaciones >= 1:
        intensidad_exclamacion = 1.15

    for token in tokens:
        if token in NEGATIONS:
            negacion_activa = True
            intensificador_activo = 1.0
            continue

        if token in INTENSIFIERS:
            intensificador_activo = INTENSIFIERS[token]
            continue

        if token in LEXICON:
            valor = LEXICON[token] * intensificador_activo * intensidad_exclamacion
            if negacion_activa:
                valor = -valor
            score_total += valor
            palabras_contadas += 1

        intensificador_activo = 1.0
        negacion_activa = False

    emoji_score = sum(emojis_encontrados.values())
    score_total += emoji_score

    if palabras_contadas > 0 or emojis_encontrados:
        score_final = score_total / max(palabras_contadas + len(emojis_encontrados), 1)
        score_final = max(-1.0, min(1.0, score_final))
    else:
        score_final = 0.0

    if score_final > 0.15:
        tono = "positivo"
        confianza = min(1.0, abs(score_final) * 1.2)
    elif score_final < -0.15:
        tono = "negativo"
        confianza = min(1.0, abs(score_final) * 1.2)
    else:
        tono = "neutral"
        confianza = 0.0

    return {
        "score": round(score_final, 6),
        "tono": tono,
        "confianza": round(confianza, 6),
        "palabras_contadas": palabras_contadas,
        "emojis_detectados": list(emojis_encontrados.keys()),
        "metodo": "advanced_lexicon_engine",
        "is_trained_model": False,
    }
