"""
DISC Translation Service

Provides LLM-based translation with placeholder preservation for DISC assessment content.
Translates Portuguese to English while maintaining {PLACEHOLDERS} intact.
"""
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class DISCTranslator:
    """Translate DISC assessment content while preserving placeholders."""

    # Common placeholders to preserve
    PLACEHOLDER_PATTERN = re.compile(r'\{[A-Z_]+\}')

    def __init__(self, llm_client=None):
        """
        Initialize translator.

        Args:
            llm_client: LLM client for translation (optional, will use simple logic if None)
        """
        self.llm_client = llm_client
        self.cache = {}  # Simple cache for identical strings

    def translate(self, text: str, target_lang: str = 'en') -> str:
        """
        Translate text while preserving placeholders.

        Args:
            text: Text to translate (Portuguese)
            target_lang: Target language code ('en' for English)

        Returns:
            Translated text with placeholders intact
        """
        if not text or not text.strip():
            return ''

        # Check cache
        cache_key = f"{text}:{target_lang}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Extract placeholders
        placeholders = self._extract_placeholders(text)

        # Replace placeholders with tokens
        tokenized_text, placeholder_map = self._tokenize_placeholders(text, placeholders)

        # Translate
        if target_lang == 'en':
            translated = self._translate_pt_to_en(tokenized_text)
        else:
            translated = tokenized_text

        # Restore placeholders
        restored = self._restore_placeholders(translated, placeholder_map)

        # Cache result
        self.cache[cache_key] = restored

        return restored

    def _extract_placeholders(self, text: str) -> List[str]:
        """Extract all {PLACEHOLDER} patterns from text."""
        return self.PLACEHOLDER_PATTERN.findall(text)

    def _tokenize_placeholders(self, text: str, placeholders: List[str]) -> Tuple[str, Dict]:
        """Replace placeholders with numbered tokens."""
        placeholder_map = {}
        tokenized = text

        for i, placeholder in enumerate(placeholders):
            token = f"__PLACEHOLDER_{i}__"
            placeholder_map[token] = placeholder
            tokenized = tokenized.replace(placeholder, token)

        return tokenized, placeholder_map

    def _restore_placeholders(self, text: str, placeholder_map: Dict[str, str]) -> str:
        """Restore original placeholders from tokens."""
        restored = text

        for token, placeholder in placeholder_map.items():
            restored = restored.replace(token, placeholder)

        return restored

    def _translate_pt_to_en(self, text: str) -> str:
        """
        Translate Portuguese to English.

        Uses LLM if available, otherwise returns text with simple replacements.
        """
        if not text.strip():
            return text

        # If LLM client available, use it
        if self.llm_client:
            return self._translate_with_llm(text)

        # Fallback: basic word replacements (not ideal, but better than nothing)
        return self._simple_translate_pt_to_en(text)

    def _translate_with_llm(self, text: str) -> str:
        """Translate using LLM."""
        try:
            prompt = f"""Translate the following Portuguese text to English.
Requirements:
- Maintain a professional, corporate tone
- Use clear, inclusive language (6th-8th grade reading level)
- Keep any tokens like __PLACEHOLDER_N__ exactly as they are
- Preserve formatting and punctuation
- Do NOT translate letter codes like D, I, S, C when they stand alone
- Be concise and accurate

Portuguese text:
{text}

English translation:"""

            # Call LLM (implementation depends on your LLM client)
            response = self.llm_client.generate(prompt, max_tokens=500)

            translated = response.strip()

            # Clean up common issues
            translated = self._clean_translation(translated)

            return translated

        except Exception as e:
            logger.error(f"LLM translation failed: {e}")
            return self._simple_translate_pt_to_en(text)

    def _simple_translate_pt_to_en(self, text: str) -> str:
        """Simple word-by-word translation for fallback."""
        # Common DISC-related translations
        translations = {
            # Factor names
            'Dominância': 'Dominance',
            'Influência': 'Influence',
            'Estabilidade': 'Steadiness',
            'Conformidade': 'Compliance',
            'Cautela': 'Caution',

            # Common assessment terms
            'Concordo totalmente': 'Strongly agree',
            'Concordo parcialmente': 'Somewhat agree',
            'Neutro': 'Neutral',
            'Discordo parcialmente': 'Somewhat disagree',
            'Discordo totalmente': 'Strongly disagree',

            'sempre': 'always',
            'frequentemente': 'frequently',
            'às vezes': 'sometimes',
            'raramente': 'rarely',
            'nunca': 'never',

            'muito': 'very',
            'moderadamente': 'moderately',
            'pouco': 'slightly',

            'alto': 'high',
            'médio': 'medium',
            'baixo': 'low',

            'força': 'strength',
            'fraqueza': 'weakness',
            'oportunidade': 'opportunity',
            'desafio': 'challenge',

            'comportamento': 'behavior',
            'personalidade': 'personality',
            'estilo': 'style',
            'perfil': 'profile',

            # Common verbs
            'Eu sou': 'I am',
            'Eu tenho': 'I have',
            'Eu gosto': 'I like',
            'Eu prefiro': 'I prefer',
            'Eu costumo': 'I usually',

            # Adjectives
            'decisivo': 'decisive',
            'assertivo': 'assertive',
            'comunicativo': 'communicative',
            'sociável': 'sociable',
            'paciente': 'patient',
            'confiável': 'reliable',
            'metódico': 'methodical',
            'analítico': 'analytical',
            'direto': 'direct',
            'entusiasta': 'enthusiastic',
            'calmo': 'calm',
            'preciso': 'precise',
        }

        result = text
        for pt, en in translations.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(pt), re.IGNORECASE)
            result = pattern.sub(en, result)

        return result

    def _clean_translation(self, text: str) -> str:
        """Clean up translation artifacts."""
        # Remove common prefixes that LLMs might add
        prefixes_to_remove = [
            'English translation:',
            'Translation:',
            'Here is the translation:',
            'The translation is:',
        ]

        cleaned = text.strip()
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()

        return cleaned

    def batch_translate(self, texts: List[str], target_lang: str = 'en') -> List[str]:
        """
        Translate multiple texts efficiently.

        Args:
            texts: List of texts to translate
            target_lang: Target language code

        Returns:
            List of translated texts
        """
        return [self.translate(text, target_lang) for text in texts]


# Singleton instance for easy access
_translator_instance = None


def get_translator(llm_client=None) -> DISCTranslator:
    """Get or create translator instance."""
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = DISCTranslator(llm_client)
    return _translator_instance


def translate_text(text: str, target_lang: str = 'en') -> str:
    """Convenience function for translation."""
    translator = get_translator()
    return translator.translate(text, target_lang)
