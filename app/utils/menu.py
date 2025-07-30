# menu.py
"""
Menu Manager - Gestisce il menu dinamico basato sui ruoli utente.
La struttura del menu è definita in menu_structure.py
"""

from flask import g, url_for, current_app
import logging
from .menu_structure import get_menu_structure, get_menu_config as get_menu_structure_config

class MenuManager:
    """Gestisce il menu dinamico basato sui ruoli utente"""
    
    def __init__(self):
        self.menu_items = get_menu_structure()
        self.config = get_menu_structure_config()
    
    @staticmethod
    def endpoint_exists(endpoint_name):
        """Verifica se un endpoint esiste nell'applicazione Flask"""
        if not endpoint_name:
            return False
        
        try:
            # Prova a generare l'URL per l'endpoint
            url_for(endpoint_name)
            return True
        except:
            # Se fallisce, l'endpoint non esiste
            return False
    
    @staticmethod
    def get_safe_url(endpoint_name, fallback_url=None):
        """Genera un URL sicuro per un endpoint, con fallback se non esiste"""
        if fallback_url is None:
            fallback_url = get_menu_structure_config().get('fallback_url', '#')
            
        if not endpoint_name:
            return fallback_url
        
        try:
            return url_for(endpoint_name)
        except Exception as e:
            # Log dell'errore in modalità debug
            config = get_menu_structure_config()
            if config.get('debug_missing_endpoints', False) and current_app.debug:
                current_app.logger.warning(f"Endpoint '{endpoint_name}' non trovato: {e}")
            return fallback_url
    
    @staticmethod
    def has_permission(item_roles, user_roles):
        """Verifica se l'utente ha i permessi per vedere un item del menu"""
        if not item_roles:  # Se non ci sono ruoli specificati, mostra a tutti
            return True
        
        if not user_roles:  # Se l'utente non ha ruoli, non mostra niente con restrizioni
            return False
        
        # Controlla se almeno uno dei ruoli dell'utente è nei ruoli richiesti
        return bool(set(user_roles) & set(item_roles))
    
    @staticmethod
    def filter_menu_item(item, user_roles, validate_endpoints=None):
        """Filtra un singolo item del menu basato sui ruoli e validazione endpoint"""
        if validate_endpoints is None:
            validate_endpoints = get_menu_structure_config().get('validate_endpoints_by_default', True)
        
        # Controlla se l'utente può vedere questo item
        if not MenuManager.has_permission(item.get('roles', []), user_roles):
            return None
        
        # Se richiesto, valida l'endpoint
        if validate_endpoints and 'endpoint' in item:
            if not MenuManager.endpoint_exists(item['endpoint']):
                # Log dell'endpoint mancante
                config = get_menu_structure_config()
                if config.get('debug_missing_endpoints', False) and current_app.debug:
                    current_app.logger.warning(
                        f"Endpoint '{item['endpoint']}' non esiste - item '{item.get('title', 'Unknown')}' rimosso dal menu"
                    )
                return None
        
        # Se l'item ha figli, filtra anche quelli
        if 'children' in item:
            filtered_children = []
            for child in item['children']:
                filtered_child = MenuManager.filter_menu_item(child, user_roles, validate_endpoints)
                if filtered_child:
                    filtered_children.append(filtered_child)
            
            # Se non ci sono figli visibili, non mostrare il parent
            if not filtered_children:
                return None
            
            # Crea una copia dell'item con i figli filtrati
            filtered_item = item.copy()
            filtered_item['children'] = filtered_children
            return filtered_item
        
        return item
    
    @staticmethod
    def get_menu_for_user(validate_endpoints=None):
        """Restituisce il menu filtrato per l'utente corrente"""
        if validate_endpoints is None:
            validate_endpoints = get_menu_structure_config().get('validate_endpoints_by_default', True)
            
        # Ottieni i ruoli dell'utente corrente
        user_roles = []
        if hasattr(g, 'user') and g.user:
            user_roles = g.user.get_role_names()
        
        filtered_menu = []
        menu_items = get_menu_structure()
        
        for item in menu_items:
            # Gestisci le sezioni
            if item.get('type') == 'section':
                # Controlla se la sezione ha restrizioni di ruolo
                if MenuManager.has_permission(item.get('roles', []), user_roles):
                    filtered_menu.append(item)
                continue
            
            # Filtra gli item normali
            filtered_item = MenuManager.filter_menu_item(item, user_roles, validate_endpoints)
            if filtered_item:
                filtered_menu.append(filtered_item)
        
        # Rimuovi sezioni consecutive vuote
        return MenuManager.clean_empty_sections(filtered_menu)
    
    @staticmethod
    def clean_empty_sections(menu_items):
        """Rimuove sezioni vuote o consecutive dal menu"""
        config = get_menu_structure_config()
        if config.get('show_empty_sections', False):
            return menu_items
            
        cleaned_menu = []
        last_was_section = False
        
        for item in menu_items:
            is_section = item.get('type') == 'section'
            
            # Non aggiungere sezioni consecutive
            if is_section and last_was_section:
                continue
            
            cleaned_menu.append(item)
            last_was_section = is_section
        
        # Rimuovi sezione finale se presente
        if cleaned_menu and cleaned_menu[-1].get('type') == 'section':
            cleaned_menu.pop()
        
        return cleaned_menu
    
    @staticmethod
    def get_user_menu_stats():
        """Restituisce statistiche sul menu dell'utente corrente"""
        menu = MenuManager.get_menu_for_user()
        
        total_items = 0
        sections = 0
        invalid_endpoints = 0
        items_with_badges = 0
        
        def count_items(items):
            nonlocal total_items, sections, invalid_endpoints, items_with_badges
            for item in items:
                if item.get('type') == 'section':
                    sections += 1
                else:
                    total_items += 1
                    
                    # Conta badge
                    if item.get('badge'):
                        items_with_badges += 1
                    
                    # Verifica endpoint se presente
                    if 'endpoint' in item and not MenuManager.endpoint_exists(item['endpoint']):
                        invalid_endpoints += 1
                    
                    if 'children' in item:
                        count_items(item['children'])
        
        count_items(menu)
        
        user_roles = []
        if hasattr(g, 'user') and g.user:
            user_roles = g.user.get_role_names()
        
        return {
            'total_items': total_items,
            'sections': sections,
            'invalid_endpoints': invalid_endpoints,
            'items_with_badges': items_with_badges,
            'user_roles': user_roles,
            'is_admin': 'admin' in user_roles,
            'is_moderator': 'moderator' in user_roles,
            'is_user': 'user' in user_roles
        }
    
    @staticmethod
    def validate_all_endpoints():
        """Valida tutti gli endpoint nel menu e restituisce un report"""
        report = {
            'valid': [],
            'invalid': [],
            'total_checked': 0,
            'by_role': {}
        }
        
        def check_items(items, parent_title=''):
            for item in items:
                if item.get('type') == 'section':
                    continue
                
                if 'endpoint' in item:
                    report['total_checked'] += 1
                    endpoint = item['endpoint']
                    title = item.get('title', 'Unknown')
                    full_title = f"{parent_title} > {title}" if parent_title else title
                    roles = item.get('roles', [])
                    
                    endpoint_info = {
                        'endpoint': endpoint,
                        'title': full_title,
                        'roles': roles,
                        'description': item.get('description', '')
                    }
                    
                    if MenuManager.endpoint_exists(endpoint):
                        report['valid'].append(endpoint_info)
                    else:
                        report['invalid'].append(endpoint_info)
                    
                    # Raggruppa per ruolo
                    for role in roles:
                        if role not in report['by_role']:
                            report['by_role'][role] = {'valid': 0, 'invalid': 0}
                        
                        if MenuManager.endpoint_exists(endpoint):
                            report['by_role'][role]['valid'] += 1
                        else:
                            report['by_role'][role]['invalid'] += 1
                
                if 'children' in item:
                    check_items(item['children'], item.get('title', 'Unknown'))
        
        menu_items = get_menu_structure()
        check_items(menu_items)
        return report
    
    @staticmethod
    def get_menu_item_by_endpoint(endpoint_name):
        """Trova un item del menu per il suo endpoint"""
        def search_items(items):
            for item in items:
                if item.get('endpoint') == endpoint_name:
                    return item
                
                if 'children' in item:
                    found = search_items(item['children'])
                    if found:
                        return found
            return None
        
        menu_items = get_menu_structure()
        return search_items(menu_items)
    
    @staticmethod
    # def get_breadcrumb_for_endpoint(endpoint_name):
    #     """Genera il breadcrumb per un endpoint specifico"""
    #     def search_items(items, path=[]):
    #         for item in items:
    #             current_path = path + [item.get('title', '')]
                
    #             if item.get('endpoint') == endpoint_name:
    #                 return current_path
                
    #             if 'children' in item:
    #                 found = search_items(item['children'], current_path)
    #                 if found:
    #                     return found
    #         return None
        
    #     menu_items = get_menu_structure()
    #     breadcrumb = search_items(menu_items)
    #     return [item for item in breadcrumb if item] if breadcrumb else []
    def get_breadcrumb_for_endpoint(endpoint_name):
        def search_items(items, path=[]):
            for item in items:
                current_path = path + [item]
                if item.get('endpoint') == endpoint_name:
                    return current_path
                if 'children' in item:
                    found = search_items(item['children'], current_path)
                    if found:
                        return found
            return None

        menu_items = get_menu_structure()
        breadcrumb_items = search_items(menu_items)
        if not breadcrumb_items:
            return []

        breadcrumb = []
        for i, item in enumerate(breadcrumb_items):
            breadcrumb.append({
                'title': item.get('title', 'Untitled'),
                'url': MenuManager.get_safe_url(item.get('endpoint')) if i < len(breadcrumb_items) - 1 else None,
                'is_active': i == len(breadcrumb_items) - 1
            })
        return breadcrumb

# Funzioni di utilità per i template
def get_menu(validate_endpoints=None):
    """Funzione per ottenere il menu nei template"""
    return MenuManager.get_menu_for_user(validate_endpoints)

def get_menu_stats():
    """Funzione per ottenere le statistiche del menu nei template"""
    return MenuManager.get_user_menu_stats()

def get_safe_url(endpoint_name, fallback_url=None):
    """Funzione per generare URL sicuri nei template"""
    return MenuManager.get_safe_url(endpoint_name, fallback_url)

def validate_menu_endpoints():
    """Funzione per validare tutti gli endpoint del menu"""
    return MenuManager.validate_all_endpoints()

def get_menu_config():
    """Funzione per ottenere la configurazione del menu"""
    return get_menu_structure_config()

def find_menu_item(endpoint_name):
    """Trova un item del menu per endpoint"""
    return MenuManager.get_menu_item_by_endpoint(endpoint_name)

def get_breadcrumb(endpoint_name):
    """Genera breadcrumb per un endpoint"""
    return MenuManager.get_breadcrumb_for_endpoint(endpoint_name)

def register_template_functions(app):
    """Registra le funzioni helper per i template"""
    
    @app.template_global()
    def get_custom_menu(endpoints, validate_permissions=True, validate_endpoints=True):
        """Crea un menu personalizzato da lista di endpoint - disponibile nei template"""
        from custom_menu import CustomMenuManager
        return CustomMenuManager.create_custom_menu_from_endpoints(
            endpoints, validate_permissions, validate_endpoints
        )
    
    @app.template_global()
    def get_predefined_menu(menu_name):
        """Ottiene un menu predefinito - disponibile nei template"""
        from custom_menu import CustomMenuManager
        return CustomMenuManager.get_predefined_menu(menu_name)