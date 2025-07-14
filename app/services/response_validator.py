"""
Response Validator - Ensures high-quality AI responses without corruption

This service is responsible for:
1. Detecting and rejecting corrupted text
2. Ensuring language consistency
3. Validating that responses meet quality standards
"""

import re
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ResponseValidator:
    """Service for validating AI-generated responses"""
    
    def __init__(self):
        """Initialize the response validator with default settings"""
        # Minimum acceptable response length
        self.min_response_length = 10
        
        # Maximum word repetition ratio (as percentage of total words)
        self.max_word_repetition = 0.2  # 20%
        
        # Maximum symbol ratio (as percentage of total characters)
        self.max_symbol_ratio = 0.08  # 8%
        
        # Maximum ratio of potentially corrupted words
        self.max_corrupted_word_ratio = 0.3  # 30%
        
        # Maximum ratio of very short words
        self.max_short_word_ratio = 0.7  # 70%
        
        logger.info("Response validator initialized")
    
    def validate_response(self, response_text, language='en'):
        """
        Validate that the response is not corrupted or garbled
        
        Args:
            response_text (str): The response text to validate
            language (str): The expected language code
            
        Returns:
            tuple: (is_valid, reason)
        """
        if not response_text or len(response_text.strip()) < self.min_response_length:
            return False, "Response too short"
        
        # Split into words for analysis
        words = response_text.split()
        if len(words) < 5:
            return True, "Short response accepted"  # Short responses are probably okay
        
        # Check for excessive repetitions
        word_counts = {}
        for word in words:
            word_lower = word.lower()
            word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
        
        # If any word appears more than the threshold, it's likely corrupted
        max_word_count = max(word_counts.values())
        max_word_frequency = max_word_count / len(words)
        if max_word_frequency > self.max_word_repetition:
            return False, f"Excessive word repetition (max freq: {max_word_frequency:.2f})"
        
        # Run language-specific checks
        if language.startswith('en'):
            return self._validate_english(response_text, words)
        elif language.startswith('hi'):
            return self._validate_hindi(response_text, words)
        else:
            # General validation for other languages
            return self._validate_general(response_text, words)
    
    def _validate_english(self, response_text, words):
        """Validate English text"""
        # Check for corrupted word patterns in English
        corrupted_words = 0
        for word in words:
            # Skip short words
            if len(word) <= 4:
                continue
                
            # Count words that look like corruption (random letters)
            if re.search(r'^[a-z]+$', word.lower()):
                vowel_count = len(re.findall(r'[aeiou]', word.lower()))
                vowel_ratio = vowel_count / len(word)
                
                # Words without enough vowels or too many vowels
                if vowel_ratio < 0.15 or vowel_ratio > 0.7:
                    corrupted_words += 1
        
        # If too many corrupted words, reject
        corrupted_ratio = corrupted_words / len(words)
        if corrupted_ratio > self.max_corrupted_word_ratio:
            return False, f"Too many corrupted words ({corrupted_words}/{len(words)})"
        
        # Check for excessive consecutive repetition of same word/phrase
        if re.search(r'\b(\w+)(\s+\1){4,}\b', response_text):
            return False, "Excessive consecutive word repetition"
        
        # Check for extremely fragmented text (too many very short words)
        short_words = sum(1 for word in words if len(word) <= 2)
        short_word_ratio = short_words / len(words)
        if short_word_ratio > self.max_short_word_ratio:
            return False, f"Text too fragmented ({short_word_ratio:.2f} short words)"
        
        # Check for excessive punctuation or symbols
        symbol_count = len(re.findall(r'[^\w\s]', response_text))
        symbol_ratio = symbol_count / len(response_text)
        if symbol_ratio > self.max_symbol_ratio:
            return False, f"Excessive symbols ({symbol_ratio:.2f})"
        
        return True, "Response passed validation"
    
    def _validate_hindi(self, response_text, words):
        """Validate Hindi text with special handling for Devanagari script"""
        # Check for script mixing corruption
        # Pattern 1: English letters mixed with Devanagari in unnatural ways
        if re.search(r'[a-zA-Z][क-ह्][a-zA-Z]|[क-ह्][a-zA-Z][क-ह्]', response_text):
            return False, "Corrupted script mixing detected (pattern 1)"
        
        # Pattern 2: Single English letters inserted randomly in Hindi words
        if re.search(r'[क-ह्][a-zA-Z][क-ह्]|[क-ह्][a-zA-Z]{1,2}[क-ह्]', response_text):
            return False, "Corrupted script mixing detected (pattern 2)"
        
        # Pattern 3: Mixed script within words (like "aखीrरे")
        if re.search(r'\b[a-zA-Z]*[क-ह्]+[a-zA-Z]+[क-ह्]*\b|\b[क-ह्]*[a-zA-Z]+[क-ह्]+[a-zA-Z]*\b', response_text):
            return False, "Corrupted script mixing detected (pattern 3)"
        
        # Check for excessive uppercase mixing (like "KANTA मंडी KANTA")
        if re.search(r'[A-Z]{3,}.*[क-ह्].*[A-Z]{3,}', response_text):
            return False, "Excessive uppercase/script mixing detected"
        
        # Check for excessive punctuation or symbols (excluding Hindi punctuation)
        symbol_count = len(re.findall(r'[^\w\s\u0900-\u097F।,!?.\-()]', response_text))
        symbol_ratio = symbol_count / len(response_text)
        if symbol_ratio > self.max_symbol_ratio:
            return False, f"Excessive symbols detected ({symbol_ratio:.2f})"
        
        return True, "Response passed validation"
    
    def _validate_general(self, response_text, words):
        """General validation for any language"""
        # Check for excessive consecutive repetition of same word/phrase
        if re.search(r'\b(\w+)(\s+\1){4,}\b', response_text):
            return False, "Excessive consecutive word repetition"
        
        # Check for extremely fragmented text (too many very short words)
        short_words = sum(1 for word in words if len(word) <= 2)
        short_word_ratio = short_words / len(words)
        if short_word_ratio > self.max_short_word_ratio:
            return False, f"Text too fragmented ({short_word_ratio:.2f} short words)"
        
        # Check for excessive punctuation or symbols
        symbol_count = len(re.findall(r'[^\w\s]', response_text))
        symbol_ratio = symbol_count / len(response_text)
        if symbol_ratio > self.max_symbol_ratio:
            return False, f"Excessive symbols ({symbol_ratio:.2f})"
        
        return True, "Response passed validation"


# Create a singleton instance
response_validator = ResponseValidator()
