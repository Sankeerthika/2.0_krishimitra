"""
Knowledge Base Service - Handles data loading and caching for the Kisan AI assistant

This service is responsible for:
1. Loading and caching knowledge base data from JSON files
2. Providing structured access to different types of agricultural information
3. Refreshing data when needed
"""

import json
import os
import logging
import functools
import time
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """Service for managing agricultural knowledge data with efficient caching"""
    
    def __init__(self, data_dir=None):
        """Initialize the knowledge base service with configurable data directory"""
        # Base directory for data files (default to two levels up from services if not specified)
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            self.data_dir = current_dir.parent.parent / "data"
        
        # Dataset paths
        self.dataset_paths = {
            'general': self.data_dir / "kisan_knowledge_base.json",
            'diseases': self.data_dir / "crop_diseases.json",
            'market': self.data_dir / "market_prices.json",
            'schemes': self.data_dir / "government_schemes.json"
        }
        
        # In-memory cache
        self._cache = {}
        self._cache_timestamp = {}
        self._cache_ttl = 3600  # 1 hour TTL by default
        
        # Initial load
        self.load_all_datasets()
    
    def load_all_datasets(self):
        """Load all datasets into memory cache"""
        for dataset_name, path in self.dataset_paths.items():
            self.load_dataset(dataset_name)
    
    def load_dataset(self, dataset_name):
        """Load a specific dataset into memory cache"""
        if dataset_name not in self.dataset_paths:
            logger.error(f"Unknown dataset: {dataset_name}")
            return None
            
        path = self.dataset_paths[dataset_name]
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache[dataset_name] = data
                    self._cache_timestamp[dataset_name] = time.time()
                    logger.info(f"Loaded {dataset_name} dataset with {len(json.dumps(data))} bytes")
                    return data
            else:
                logger.warning(f"Dataset file not found: {path}")
                return None
        except Exception as e:
            logger.error(f"Error loading dataset {dataset_name}: {str(e)}")
            return None
    
    def get_dataset(self, dataset_name, force_refresh=False):
        """
        Get a dataset from cache or load it if needed
        
        Args:
            dataset_name (str): Name of the dataset to retrieve
            force_refresh (bool): Whether to force a refresh from disk
            
        Returns:
            dict: The dataset or None if not available
        """
        current_time = time.time()
        
        # Check if we need to refresh the cache
        if (dataset_name not in self._cache or 
            force_refresh or 
            current_time - self._cache_timestamp.get(dataset_name, 0) > self._cache_ttl):
            return self.load_dataset(dataset_name)
        
        return self._cache.get(dataset_name)
    
    def get_all_datasets(self, force_refresh=False):
        """Get all datasets combined into a single dictionary"""
        result = {}
        for dataset_name in self.dataset_paths.keys():
            data = self.get_dataset(dataset_name, force_refresh)
            if data:
                result[dataset_name] = data
        return result
    
    def get_crop_disease_info(self, crop_name=None, disease_name=None):
        """
        Get information about crop diseases
        
        Args:
            crop_name (str, optional): Filter by specific crop
            disease_name (str, optional): Filter by specific disease
            
        Returns:
            list: Matching disease records
        """
        diseases_data = self.get_dataset('diseases')
        if not diseases_data:
            return []
            
        records = diseases_data.get('diseases', [])
        
        # Apply filters if provided
        if crop_name:
            crop_name_lower = crop_name.lower()
            records = [r for r in records if r.get('crop', '').lower() == crop_name_lower]
            
        if disease_name:
            disease_name_lower = disease_name.lower()
            records = [r for r in records if disease_name_lower in r.get('name', '').lower()]
            
        return records
    
    def get_market_prices(self, commodity=None, market=None, max_days=30):
        """
        Get market prices for agricultural commodities
        
        Args:
            commodity (str, optional): Filter by specific commodity
            market (str, optional): Filter by specific market
            max_days (int): Maximum age of price data in days
            
        Returns:
            list: Matching price records
        """
        market_data = self.get_dataset('market')
        if not market_data:
            return []
            
        records = market_data.get('records', [])
        
        # Apply filters if provided
        if commodity:
            commodity_lower = commodity.lower()
            records = [r for r in records if r.get('commodity', '').lower() == commodity_lower]
            
        if market:
            market_lower = market.lower()
            records = [r for r in records if r.get('market', '').lower() == market_lower]
            
        # Sort by date if available
        records.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return records
    
    def get_government_schemes(self, category=None, keyword=None):
        """
        Get information about government agricultural schemes
        
        Args:
            category (str, optional): Filter by category
            keyword (str, optional): Filter by keyword
            
        Returns:
            list: Matching scheme records
        """
        schemes_data = self.get_dataset('schemes')
        if not schemes_data:
            return []
            
        schemes = schemes_data.get('schemes', [])
        
        # Apply filters if provided
        if category:
            category_lower = category.lower()
            schemes = [s for s in schemes if s.get('category', '').lower() == category_lower]
            
        if keyword:
            keyword_lower = keyword.lower()
            schemes = [s for s in schemes if (
                keyword_lower in s.get('name', '').lower() or
                keyword_lower in s.get('description', '').lower()
            )]
            
        return schemes
    
    def refresh_all(self):
        """Force refresh all datasets from disk"""
        for dataset_name in self.dataset_paths.keys():
            self.load_dataset(dataset_name)
        logger.info("Refreshed all knowledge base datasets")
    
    def set_cache_ttl(self, seconds):
        """Set the cache time-to-live in seconds"""
        self._cache_ttl = seconds
        logger.info(f"Set knowledge base cache TTL to {seconds} seconds")


# Create a singleton instance
knowledge_base = KnowledgeBaseService()
