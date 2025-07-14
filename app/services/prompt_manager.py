"""
Prompt Manager - Handles prompt engineering for better AI responses

This service is responsible for:
1. Generating optimized prompts for different use cases
2. Incorporating context from the knowledge base
3. Managing prompt structure and length constraints
"""

import json
import logging
import datetime

# Set up logging
logger = logging.getLogger(__name__)

class PromptManager:
    """Service for managing AI prompts with improved context handling"""
    
    def __init__(self):
        """Initialize the prompt manager with default templates"""
        # Maximum context length for knowledge base inclusion
        self.max_context_length = 3000
        
        # Current date for contextual information
        self.current_date = datetime.datetime.now().strftime("%B %d, %Y")
        
        logger.info("Prompt manager initialized")
    
    def create_system_prompt(self, farmer_name, query, knowledge_base=None, language='en'):
        """
        Create an optimized system prompt for agricultural queries
        
        Args:
            farmer_name (str): Name of the farmer
            query (str): The farmer's query
            knowledge_base (dict): Knowledge base data
            language (str): Source language code
            
        Returns:
            str: Optimized system prompt
        """
        # Base system prompt template
        base_prompt = f"""You are Project Kisan, an AI assistant specifically designed to help Indian farmers. Today is {self.current_date}. 

You are having a conversation with farmer {farmer_name} in {self._get_language_name(language)}.

Core principles:
- Provide accurate, practical farming advice tailored to Indian agriculture
- Be specific and actionable in your recommendations
- Include relevant market prices when available 
- Mention specific government schemes that can help when applicable
- Keep responses concise but thorough
- Always be respectful and helpful
- Format prices in rupees (₹) where applicable
- Consider the current season in your advice

Farmer's query: {query}
"""
        
        # Add knowledge base if available
        if knowledge_base:
            kb_json = self._format_knowledge_base(knowledge_base)
            base_prompt += f"\nAvailable Knowledge Base:\n{kb_json}\n"
        
        # Add seasonal context
        seasonal_context = self._get_seasonal_context()
        base_prompt += f"\nSeasonal Context: {seasonal_context}\n"
        
        # Add response guidance
        base_prompt += """
Please provide a helpful response focusing on practical advice related to the query.
Format your response well with appropriate sections and bullet points where relevant.
"""
        
        logger.info(f"Created system prompt with {len(base_prompt)} characters")
        return base_prompt
    
    def create_image_analysis_prompt(self, farmer_name, query=None, language='en'):
        """
        Create a prompt for image analysis
        
        Args:
            farmer_name (str): Name of the farmer
            query (str): The farmer's query/caption (optional)
            language (str): Source language code
            
        Returns:
            str: Image analysis prompt
        """
        # Default query if none provided
        if not query:
            query = "What do you see in this image? I need advice about it."
        
        prompt = f"""You are Project Kisan, an agricultural vision assistant for Indian farmers. Today is {self.current_date}.

You are analyzing an image sent by farmer {farmer_name} in {self._get_language_name(language)}.

The farmer asks: "{query}"

As an agricultural expert, please:
1. Identify the crop, plant, or agricultural scene in the image
2. Look for any visible issues (disease, pests, deficiencies) 
3. Assess the condition of what you see
4. Provide specific, actionable advice based on your analysis
5. Include treatment recommendations if a problem is detected

Be specific and practical in your analysis, focusing on helping the farmer with their immediate concern.
"""
        
        logger.info(f"Created image analysis prompt with {len(prompt)} characters")
        return prompt
    
    def create_fallback_prompt(self, language='en'):
        """
        Create a prompt for generating a fallback response
        
        Args:
            language (str): Target language code
            
        Returns:
            str: Fallback prompt
        """
        prompt = f"""Generate a polite fallback message for an Indian farmer in {self._get_language_name(language)}, explaining that:
1. You didn't understand their query or encountered a technical issue
2. They should try asking their question again in a different way
3. You can help with farming questions, market prices, crop advice, etc.

Keep the message short, friendly, and encouraging.
"""
        
        return prompt
    
    def _format_knowledge_base(self, knowledge_base):
        """Format knowledge base data for inclusion in prompts"""
        if not knowledge_base:
            return "{}"
            
        # Try to extract just the most relevant parts to fit within max length
        try:
            kb_json = json.dumps(knowledge_base, ensure_ascii=False, indent=2)
            
            # Truncate if too long
            if len(kb_json) > self.max_context_length:
                kb_json = kb_json[:self.max_context_length] + "...(truncated)"
                
            return kb_json
        except Exception as e:
            logger.error(f"Error formatting knowledge base: {str(e)}")
            return "{}"
    
    def _get_language_name(self, language_code):
        """Get the human-readable name of a language from its code"""
        language_names = {
            'en': 'English',
            'hi': 'Hindi',
            'bn': 'Bengali',
            'ta': 'Tamil',
            'te': 'Telugu',
            'kn': 'Kannada',
            'gu': 'Gujarati',
            'ml': 'Malayalam',
            'pa': 'Punjabi',
            'mr': 'Marathi',
            'or': 'Oriya',
            'as': 'Assamese'
        }
        
        return language_names.get(language_code, 'their language')
    
    def _get_seasonal_context(self):
        """Get seasonal context based on current date"""
        now = datetime.datetime.now()
        month = now.month
        
        # Indian agricultural seasons
        if 6 <= month <= 10:  # June to October
            return "Current Season: Kharif (Monsoon) - Main crops include rice, maize, cotton, sugarcane, and pulses."
        elif 11 <= month <= 12 or 1 <= month <= 3:  # November to March
            return "Current Season: Rabi (Winter) - Main crops include wheat, barley, mustard, gram, and peas."
        else:  # April and May
            return "Current Season: Zaid (Summer) - Main crops include vegetables, fruits, and fodder crops."


# Create a singleton instance
prompt_manager = PromptManager()
