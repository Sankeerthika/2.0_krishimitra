"""
Translation Service for multilingual support
Handles language detection and translation for the Kisan AI assistant
"""
import logging
import re
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Set seed for consistent language detection results
DetectorFactory.seed = 0

class TranslationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def detect_language(self, text):
        """
        Detect the language of the input text with improved accuracy for Indian languages
        Returns language code (e.g., 'en', 'hi', 'bn', etc.)
        """
        try:
            # Clean the text for better detection
            cleaned_text = text.strip()
            if not cleaned_text:
                return 'en'  # Default to English for empty text
            
            # Handle common Indian greetings and words that might be misdetected
            indian_patterns = {
                'hi': ['नमस्ते', 'namaste', 'namaskar', 'नमस्कार', 'हैलो', 'हेलो', 'हिंदी', 'किसान', 'खेती', 'फसल', 'बाजार', 'मंडी', 'कीमत', 'भाव', 'बीज', 'खाद', 'पानी', 'सिंचाई', 'खरपतवार', 'बीमारी', 'कीड़े', 'दवा', 'उर्वरक', 'मिट्टी', 'करेला', 'टमाटर', 'प्याज', 'आलू', 'चावल', 'गेहूं', 'धान', 'मक्का', 'गन्ना', 'कपास'],
                'bn': ['হ্যালো', 'নমস্কার', 'আমি', 'দাম', 'কত', 'চাল', 'আলু', 'টমেটো', 'পেঁয়াজ', 'শসা', 'কৃষক', 'চাষ', 'বাজার', 'মূল্য'],
                'ta': ['வணக்கம்', 'நான்', 'விலை', 'என்ன', 'அரிசி', 'வெள்ளரி', 'தக்காளி', 'வெங்காயம்', 'உருளை', 'விவசாயி', 'சாகுபடி', 'சந்தை'],
                'te': ['నమస్కారం', 'హలో', 'నేను', 'ధర', 'ఎంత', 'బియ్యం', 'పుచ్చకాయ', 'టమాటో', 'ఉల్లిపాయ', 'బంగాళదుంప', 'రైతు', 'వ్యవసాయం', 'మార్కెట్'],
                'kn': ['ನಮಸ್ಕಾರ', 'ಹಲೋ', 'ನಾನು', 'ಬೆಲೆ', 'ಎಷ್ಟು', 'ಅಕ್ಕಿ', 'ಸೌತೆಕಾಯಿ', 'ಟೊಮೇಟೊ', 'ಈರುಳ್ಳಿ', 'ಆಲೂಗೆಡ್ಡೆ', 'ರೈತ', 'ಕೃಷಿ', 'ಮಾರುಕಟ್ಟೆ'],
                'gu': ['નમસ્તે', 'હેલો', 'હું', 'ભાવ', 'કેટલો', 'ચોખા', 'કાકડી', 'ટમેટા', 'ડુંગળી', 'બટાકા', 'ખેડૂત', 'ખેતી', 'બજાર'],
                'ml': ['നമസ്കാരം', 'ഹലോ', 'ഞാൻ', 'വില', 'എത്ര', 'അരി', 'വെള്ളരി', 'തക്കാളി', 'ഉള്ളി', 'ഉരുളക്കിഴങ്ങ്', 'കർഷകൻ', 'കൃഷി', 'മാർക്കറ്റ്'],
                'pa': ['ਨਮਸਤੇ', 'ਹੈਲੋ', 'ਮੈਂ', 'ਕੀਮਤ', 'ਕਿੰਨੀ', 'ਚਾਵਲ', 'ਖੀਰਾ', 'ਟਮਾਟਰ', 'ਪਿਆਜ਼', 'ਆਲੂ', 'ਕਿਸਾਨ', 'ਖੇਤੀ', 'ਮੰਡੀ']
            }
            
            text_lower = cleaned_text.lower()
            
            # Check for Indian language patterns first
            for lang_code, patterns in indian_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in text_lower or pattern in cleaned_text:
                        self.logger.info(f"Detected language: {lang_code} for text: {text[:50]}... (pattern match: {pattern})")
                        return lang_code
            
            # Use langdetect for detection if no pattern match
            detected_lang = detect(cleaned_text)
            
            # RESTRICTION: Only allow Indian languages and English
            allowed_languages = ['hi', 'bn', 'ta', 'te', 'kn', 'gu', 'ml', 'pa', 'or', 'as', 'mr', 'en']
            
            if detected_lang not in allowed_languages:
                # If detected language is not Indian/English, default to Hindi
                self.logger.info(f"Detected non-Indian language '{detected_lang}', defaulting to Hindi for: {text[:50]}...")
                return 'hi'
            
            # Override specific misdetections
            if detected_lang == 'et' and ('namaste' in text_lower or 'नमस्ते' in cleaned_text):
                detected_lang = 'hi'
                self.logger.info(f"Corrected Estonian->Hindi for: {text[:50]}...")
            elif detected_lang == 'lt' and any(hindi_char in cleaned_text for hindi_char in 'कखगघचछजझटठडढणतथदधनपफबभमयरलवशषसहािीुूृेैोौं्'):
                detected_lang = 'hi'
                self.logger.info(f"Corrected Lithuanian->Hindi for: {text[:50]}...")
            elif detected_lang == 'lv' and ('namaskar' in text_lower or 'namaste' in text_lower):
                detected_lang = 'hi'
                self.logger.info(f"Corrected Latvian->Hindi for: {text[:50]}...")
            
            self.logger.info(f"Detected language: {detected_lang} for text: {text[:50]}...")
            return detected_lang
            
        except LangDetectException as e:
            self.logger.warning(f"Language detection failed: {e}. Defaulting to Hindi for Indian context.")
            # In Indian farming context, default to Hindi instead of English
            return 'hi'
        except Exception as e:
            self.logger.error(f"Unexpected error in language detection: {e}")
            return 'hi'  # Default to Hindi for Indian farming context
    
    def _clean_text(self, text):
        """
        Clean corrupted or garbled text before processing
        """
        if not text:
            return text
        
        # First pass: remove extreme repetition patterns
        # Remove single words repeated 4+ times consecutively
        text = re.sub(r'\b(\w+)(\s+\1){3,}\b', r'\1', text)
        
        # Remove single characters or short patterns repeated excessively
        text = re.sub(r'(.{1,3})\1{5,}', r'\1', text)  # Remove patterns repeated 6+ times
        
        # Remove sequences like "की की की की की" or "के के के के के"
        text = re.sub(r'\b([क-ह्]{1,3})(\s+\1){4,}\b', r'\1', text)
        
        # Remove excessive repetition of common Hindi words
        text = re.sub(r'\b(में|की|के|का|को|से|पर|और|है|हैं|जो|यह|वह)(\s+\1){3,}\b', r'\1', text)
        
        # Remove patterns like "र र र र र" (single character repetitions)
        text = re.sub(r'\b(\S)\s+(\1\s+){2,}', r'\1', text)
        
        # Remove excessive character repetitions within words
        text = re.sub(r'(.)\1{3,}', r'\1', text)
        
        # Split into words for detailed cleaning
        words = text.split()
        cleaned_words = []
        word_counts = {}
        
        for word in words:
            # Skip very short words (they're probably fine)
            if len(word) <= 2:
                cleaned_words.append(word)
                continue
                
            # Skip completely broken words
            if len(word) > 25:  # Abnormally long words
                continue
                
            # Skip words with severe script mixing corruption
            if re.search(r'[a-zA-Z][क-ह्][a-zA-Z]|[क-ह्][a-zA-Z][क-ह्]', word):
                continue
                
            # Skip words that are mostly random characters/symbols
            if len(re.sub(r'[a-zA-Z\u0900-\u097F\s]', '', word)) > len(word) * 0.6:
                continue
                
            # Skip words with excessive case mixing (like "KANTA")
            if re.search(r'[A-Z]{3,}[a-z]|[a-z][A-Z]{3,}', word):
                continue
                
            # Skip words that look corrupted (random letter combinations)
            if re.search(r'^[a-z]{2,}[a-z]*[a-z]{3,}$', word) and len(word) > 6:
                # Check if it's a corrupted word by looking for vowel patterns
                vowel_ratio = len(re.findall(r'[aeiouAEIOU]', word)) / len(word)
                if vowel_ratio < 0.2 or vowel_ratio > 0.8:  # Too few or too many vowels
                    continue
            
            # Count word frequency to detect repetitive patterns
            word_lower = word.lower()
            word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
            
            # Keep the word if it seems fine
            cleaned_words.append(word)
        
        # Second pass: remove words that appear too frequently (likely repetition corruption)
        total_words = len(cleaned_words)
        if total_words > 10:  # Only apply this filter for longer texts
            filtered_words = []
            for word in cleaned_words:
                word_lower = word.lower()
                frequency = word_counts.get(word_lower, 0) / total_words
                if frequency <= 0.25:  # Word shouldn't appear more than 25% of the time
                    filtered_words.append(word)
            cleaned_words = filtered_words
        
        text = ' '.join(cleaned_words)
        
        # Final cleanup
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[*]{2,}', '*', text)  # Clean excessive asterisks
        text = re.sub(r'[\.]{3,}', '...', text)  # Clean excessive dots
        
        # If the cleaned text is too short compared to original, it was heavily corrupted
        if len(cleaned_words) < 3 or len(text) < 10:
            return ""  # Return empty for heavily corrupted text
        
        return text
    
    def translate_to_english(self, text, source_lang=None):
        """
        Translate text to English
        Args:
            text: Text to translate
            source_lang: Source language code (if known, otherwise auto-detect)
        Returns:
            Translated text in English
        """
        try:
            if not text or not text.strip():
                return text
                
            # Clean the text first - remove corrupted parts
            cleaned_text = self._clean_text(text)
            if len(cleaned_text) < len(text) * 0.5:  # If we lost more than 50% of text, it was too corrupted
                self.logger.warning(f"Text appears heavily corrupted, using simplified query")
                # Try to extract key meaningful words
                words = text.split()
                meaningful_words = [w for w in words if len(w) > 2 and not re.search(r'[a-zA-Z]{1}[क-ह]{1}[a-zA-Z]{1}', w)]
                cleaned_text = ' '.join(meaningful_words[:10])  # Take first 10 meaningful words
                
            if not cleaned_text.strip():
                return "farming question"  # Fallback for completely corrupted text
                
            # If source language is not provided, detect it
            if source_lang is None:
                source_lang = self.detect_language(cleaned_text)
            
            # If already in English, return as-is
            if source_lang == 'en':
                self.logger.info("Text is already in English, no translation needed")
                return cleaned_text
            
            # Translate to English using deep-translator
            translator = GoogleTranslator(source=source_lang, target='en')
            translated_text = translator.translate(cleaned_text)
            
            self.logger.info(f"Translated '{cleaned_text[:50]}...' from {source_lang} to English: '{translated_text[:50]}...'")
            return translated_text
            
        except Exception as e:
            self.logger.error(f"Translation to English failed: {e}. Using fallback.")
            # Try to extract at least the topic if possible
            if 'करेला' in text or 'bitter gourd' in text.lower():
                return "bitter gourd farming question"
            elif any(word in text for word in ['कीमत', 'दाम', 'price', 'cost']):
                return "price question"
            return "farming question"  # Ultimate fallback
    
    def translate_from_english(self, text, target_lang):
        """
        Translate text from English to target language
        Args:
            text: English text to translate
            target_lang: Target language code
        Returns:
            Translated text in target language
        """
        try:
            if not text or not text.strip():
                return text
                
            # If target is English, return as-is
            if target_lang == 'en':
                self.logger.info("Target language is English, no translation needed")
                return text
            
            # Translate from English to target language using deep-translator
            translator = GoogleTranslator(source='en', target=target_lang)
            translated_text = translator.translate(text)
            
            self.logger.info(f"Translated '{text[:50]}...' from English to {target_lang}: '{translated_text[:50]}...'")
            return translated_text
            
        except Exception as e:
            self.logger.error(f"Translation from English to {target_lang} failed: {e}. Returning original text.")
            return text  # Return original text if translation fails
    
    def translate_message(self, text):
        """
        Complete translation pipeline:
        1. Detect language of input
        2. Translate to English for processing
        3. Return both the English text and detected language
        """
        detected_lang = self.detect_language(text)
        english_text = self.translate_to_english(text, detected_lang)
        # Normalize simple greetings to English 'hello'
        text_lower = text.strip().lower()
        greetings = ['hi', 'hello', 'namaste', 'namaskar']
        if english_text.strip().lower() in greetings or text_lower in greetings:
            english_text = 'hello'
        return {
            'english_text': english_text,
            'detected_language': detected_lang,
            'original_text': text
        }
    
    def translate_response(self, english_response, target_lang):
        """
        Translate a response text to the target language.
        If the text is already in the target language, return as-is.
        Otherwise, ensure English intermediary for translation.
        """
        text = english_response
        if not text or not text.strip():
            return text
        # Detect source language of the response text
        try:
            src_lang = self.detect_language(text)
        except Exception:
            src_lang = 'en'
        # If text is already in desired language, return it
        if src_lang == target_lang:
            self.logger.info(f"Response detected as target language '{target_lang}', no translation needed")
            return text
        # If text is not English, translate to English first
        if src_lang != 'en':
            try:
                text = self.translate_to_english(text, src_lang)
            except Exception as e:
                self.logger.warning(f"Failed to translate response to English: {e}")
        # If target is English, return intermediary English text
        if target_lang == 'en':
            return text
        # Translate from English to target language
        try:
            translated = GoogleTranslator(source='en', target=target_lang).translate(text)
            self.logger.info(f"Translated response to {target_lang}: '{translated[:50]}...'")
            return translated
        except Exception as e:
            self.logger.error(f"Translation back to {target_lang} failed: {e}. Returning English text.")
            return text

# Global instance
translation_service = TranslationService()
