"""
Sistema di cache semplice per le route Odoo esistenti - VERSIONE SEMPLIFICATA
"""
from functools import wraps
import hashlib
import json
import time
from flask import request
import logging

logger = logging.getLogger(__name__)

# Cache in memoria semplice
_memory_cache = {}
_cache_timestamps = {}
CACHE_TIMEOUT = 300  # 5 minuti default

class SimpleCache:
    """Cache semplice solo in memoria"""
    
    @staticmethod
    def _generate_cache_key(prefix, *args, **kwargs):
        """Genera chiave cache univoca"""
        key_data = {
            'prefix': prefix,
            'args': args,
            'kwargs': kwargs,
            'query_params': dict(request.args) if request else {}
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:12]
        return f"{prefix}_{key_hash}"
    
    @staticmethod
    def get(key):
        """Recupera dalla cache"""
        try:
            if key in _memory_cache:
                timestamp = _cache_timestamps.get(key, 0)
                if time.time() - timestamp < CACHE_TIMEOUT:
                    return _memory_cache[key]
                else:
                    # Scaduto, rimuovi
                    _memory_cache.pop(key, None)
                    _cache_timestamps.pop(key, None)
            return None
        except Exception as e:
            logger.warning(f"Cache GET error: {e}")
            return None
    
    @staticmethod
    def set(key, value, timeout=None):
        """Imposta in cache"""
        try:
            _memory_cache[key] = value
            _cache_timestamps[key] = time.time()
            
            # Pulizia automatica (mantieni solo 100 elementi)
            if len(_memory_cache) > 100:
                # Rimuovi i 20 più vecchi
                oldest_keys = sorted(_cache_timestamps.items(), key=lambda x: x[1])[:20]
                for old_key, _ in oldest_keys:
                    _memory_cache.pop(old_key, None)
                    _cache_timestamps.pop(old_key, None)
                    
        except Exception as e:
            logger.warning(f"Cache SET error: {e}")

def cached_route(timeout=300, key_prefix="odoo_api"):
    """
    Decorator per aggiungere cache alle route esistenti
    """
    global CACHE_TIMEOUT
    CACHE_TIMEOUT = timeout  # Imposta il timeout globalmente
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Genera chiave cache
            cache_key = SimpleCache._generate_cache_key(
                f"{key_prefix}_{f.__name__}", *args, **kwargs
            )
            
            # Prova a recuperare dalla cache
            cached_result = SimpleCache.get(cache_key)
            if cached_result is not None:
                logger.info(f"🚀 Cache HIT: {cache_key}")
                return cached_result
            
            # Esegui la funzione originale
            logger.info(f"⏳ Cache MISS: {cache_key} - Executing...")
            start_time = time.time()
            
            result = f(*args, **kwargs)
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Executed in {execution_time:.3f}s - Caching result")
            
            # Salva in cache
            SimpleCache.set(cache_key, result, timeout)
            
            return result
        return decorated_function
    return decorator

def cached_route_with_retry(timeout=300, key_prefix="odoo_api", max_retries=2):
    """
    Cache con retry automatico per errori di connessione
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = SimpleCache._generate_cache_key(
                f"{key_prefix}_{f.__name__}", *args, **kwargs
            )
            
            # Prova cache
            cached_result = SimpleCache.get(cache_key)
            if cached_result is not None:
                logger.info(f"🚀 Cache HIT: {cache_key}")
                return cached_result
            
            # Esegui con retry
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    logger.info(f"⏳ Cache MISS: {cache_key} - Attempt {attempt + 1}")
                    start_time = time.time()
                    
                    result = f(*args, **kwargs)
                    
                    execution_time = time.time() - start_time
                    logger.info(f"✅ Executed in {execution_time:.3f}s - Caching result")
                    
                    # Salva in cache solo se successo
                    SimpleCache.set(cache_key, result, timeout)
                    return result
                    
                except Exception as e:
                    last_error = e
                    if "ODOO_CONNECTION_ERROR" in str(e) and attempt < max_retries:
                        logger.warning(f"🔄 Tentativo {attempt + 1} fallito, riprovo...")
                        time.sleep(1)  # Pausa prima del retry
                        continue
                    else:
                        raise e
            
            # Se arriva qui, tutti i tentativi sono falliti
            raise last_error
            
        return decorated_function
    return decorator

def clear_cache_pattern(pattern=""):
    """Pulisce la cache per pattern specifico"""
    try:
        if pattern:
            keys_to_remove = [key for key in _memory_cache.keys() if pattern in key]
        else:
            keys_to_remove = list(_memory_cache.keys())
            
        for key in keys_to_remove:
            _memory_cache.pop(key, None)
            _cache_timestamps.pop(key, None)
        
        logger.info(f"🧹 Cache cleared for pattern: '{pattern}' - {len(keys_to_remove)} keys removed")
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return False

def get_cache_stats():
    """Statistiche della cache"""
    try:
        return {
            "cache_type": "Memory",
            "cache_size": len(_memory_cache),
            "cache_keys": list(_memory_cache.keys())[:10],  # Prime 10 chiavi
            "oldest_entry": min(_cache_timestamps.values()) if _cache_timestamps else None,
            "newest_entry": max(_cache_timestamps.values()) if _cache_timestamps else None
        }
    except Exception as e:
        return {"error": str(e)}