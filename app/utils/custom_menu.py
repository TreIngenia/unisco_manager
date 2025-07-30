# custom_menu.py
from flask import g
from .menu_structure import get_menu_structure
from .menu import MenuManager

class CustomMenuManager:
# Aggiungi questi menu predefiniti che includono i sottomenu
    PREDEFINED_MENUS = {
        'admin_quick': ['admin.admin_dashboard', 'admin.manage_users', 'config_page', 'logs'],
        'user_dashboard': ['web.dashboard', 'listino', 'gestione_fatture', 'web.profile'],
        'gestione_base': ['listino', 'gestione_fatture', 'gestione_contratti'],
        'categorie_complete': ['cdr_categories_dashboard', 'cdr_categories_edit', 'cdr_categories_page_new'],
        'amministrazione': ['admin.admin_dashboard', 'admin.manage_users', 'admin.manage_roles', 'config_page', 'logs', 'status_page', 'admin.cdr_categories'],
        'sistema_admin': ['admin.admin_dashboard', 'config_page', 'logs', 'status_page'],  # Solo i sottomenu di "Sistema"
        'sistema_completo': ['children:Sistema']  # Usa la nuova sintassi per includere tutti i figli
    }
    
    @staticmethod
    def get_menu_item_by_endpoint(endpoint):
        """Trova un item del menu principale per endpoint"""
        def search_items(items):
            for item in items:
                if item.get('endpoint') == endpoint:
                    return item
                if 'children' in item:
                    found = search_items(item['children'])
                    if found:
                        return found
            return None
        
        menu_items = get_menu_structure()
        return search_items(menu_items)
    
    @staticmethod
    def create_custom_menu_from_endpoints(endpoints, validate_permissions=True, validate_endpoints=True, include_children=False):
        """Crea un menu personalizzato da una lista di endpoint"""
        custom_menu = []
        user_roles = []
        
        if hasattr(g, 'user') and g.user:
            user_roles = g.user.get_role_names()
        
        for endpoint in endpoints:
            # Se l'endpoint contiene "children:", gestisci il caso speciale
            if isinstance(endpoint, str) and endpoint.startswith('children:'):
                parent_title = endpoint.replace('children:', '')
                children = CustomMenuManager.get_children_by_parent_title(parent_title)
                for child in children:
                    if validate_permissions:
                        if not MenuManager.has_permission(child.get('roles', []), user_roles):
                            continue
                    if validate_endpoints:
                        if not MenuManager.endpoint_exists(child.get('endpoint', '')):
                            continue
                    custom_menu.append(child.copy())
                continue
            
            menu_item = CustomMenuManager.get_menu_item_by_endpoint(endpoint)
            
            if not menu_item:
                if not validate_endpoints or MenuManager.endpoint_exists(endpoint):
                    custom_menu.append({
                        'endpoint': endpoint,
                        'title': endpoint.replace('_', ' ').replace('.', ' ').title(),
                        'icon': 'ki-outline ki-arrow-right fs-2',
                        'roles': [],
                        'custom': True
                    })
                continue
            
            if validate_permissions:
                if not MenuManager.has_permission(menu_item.get('roles', []), user_roles):
                    continue
            
            if validate_endpoints:
                if not MenuManager.endpoint_exists(endpoint):
                    continue
            
            # Se include_children è True e l'item ha figli, aggiungili
            if include_children and 'children' in menu_item:
                custom_menu.append(menu_item.copy())
                for child in menu_item['children']:
                    if validate_permissions:
                        if not MenuManager.has_permission(child.get('roles', []), user_roles):
                            continue
                    if validate_endpoints:
                        if not MenuManager.endpoint_exists(child.get('endpoint', '')):
                            continue
                    custom_menu.append(child.copy())
            else:
                custom_menu.append(menu_item.copy())
        
        return custom_menu
    
    @staticmethod
    def get_children_by_parent_title(parent_title):
        """Trova i figli di un item del menu per titolo del parent"""
        def search_items(items):
            for item in items:
                if item.get('title') == parent_title and 'children' in item:
                    return item['children']
                if 'children' in item:
                    found = search_items(item['children'])
                    if found:
                        return found
            return []
        
        menu_items = get_menu_structure()
        return search_items(menu_items)
    
    @staticmethod
    def get_predefined_menu(menu_name, validate_permissions=True, validate_endpoints=True):
        """Ottiene un menu predefinito"""
        if menu_name not in CustomMenuManager.PREDEFINED_MENUS:
            return []
        
        endpoints = CustomMenuManager.PREDEFINED_MENUS[menu_name]
        return CustomMenuManager.create_custom_menu_from_endpoints(
            endpoints, validate_permissions, validate_endpoints
        )


# Funzioni helper per i template
def get_custom_menu(endpoints, validate_permissions=True, validate_endpoints=True):
    return CustomMenuManager.create_custom_menu_from_endpoints(
        endpoints, validate_permissions, validate_endpoints
    )

def get_predefined_menu(menu_name):
    return CustomMenuManager.get_predefined_menu(menu_name)

# def get_children_menu(parent_title):
#     """Funzione helper per template - ottiene children di un parent"""
#     return CustomMenuManager.get_children_by_parent_title(parent_title)

def get_children_menu(endpoints_or_titles, validate_permissions=True, validate_endpoints=True):
    """
    Funzione avanzata per template - gestisce endpoint singoli e titoli parent
    
    Comportamento:
    - Se è un endpoint singolo -> restituisce solo i dati di quell'endpoint
    - Se è un titolo parent -> restituisce solo i children di quel parent
    """
    if isinstance(endpoints_or_titles, str):
        endpoints_or_titles = [endpoints_or_titles]
    
    result_items = []
    user_roles = []
    
    if hasattr(g, 'user') and g.user:
        user_roles = g.user.get_role_names()
    
    def find_item_by_endpoint(target_endpoint, items):
        """Trova un item specifico per endpoint (ricerca ricorsiva)"""
        for item in items:
            # Salta le sezioni
            if item.get('type') == 'section':
                continue
                
            # Controlla l'endpoint corrente
            if item.get('endpoint') == target_endpoint:
                return item
            
            # Cerca nei children se esistono
            if 'children' in item:
                found = find_item_by_endpoint(target_endpoint, item['children'])
                if found:
                    return found
        return None
    
    def find_item_by_title(target_title, items):
        """Trova un item specifico per titolo (ricerca ricorsiva)"""
        for item in items:
            # Salta le sezioni
            if item.get('type') == 'section':
                continue
                
            # Controlla il titolo corrente
            if item.get('title') == target_title:
                return item
            
            # Cerca nei children se esistono
            if 'children' in item:
                found = find_item_by_title(target_title, item['children'])
                if found:
                    return found
        return None
    
    def validate_item(item):
        """Valida un item secondo i parametri di validazione"""
        if validate_permissions:
            if not MenuManager.has_permission(item.get('roles', []), user_roles):
                return False
        
        if validate_endpoints and item.get('endpoint'):
            if not MenuManager.endpoint_exists(item.get('endpoint')):
                return False
                
        return True
    
    menu_items = get_menu_structure()
    
    for search_term in endpoints_or_titles:
        # Prima prova a trovare per endpoint
        found_item = find_item_by_endpoint(search_term, menu_items)
        
        # Se non trovato per endpoint, prova per titolo
        if not found_item:
            found_item = find_item_by_title(search_term, menu_items)
        
        if not found_item:
            continue
            
        # Se l'item ha children (è un parent), aggiungi solo il parent completo
        if 'children' in found_item and found_item['children']:
            # Aggiungi il parent COMPLETO (con children inclusi)
            parent_complete = found_item.copy()
            
            # Filtra i children del parent se necessario
            if validate_permissions or validate_endpoints:
                filtered_children = []
                for child in parent_complete['children']:
                    if validate_item(child):
                        filtered_children.append(child)
                parent_complete['children'] = filtered_children
            
            # Aggiungi solo il parent con children (se non è vuoto dopo il filtraggio)
            if not validate_permissions or MenuManager.has_permission(parent_complete.get('roles', []), user_roles):
                result_items.append(parent_complete)
        
        # Se l'item non ha children, aggiungilo direttamente
        else:
            if validate_item(found_item):
                result_items.append(found_item.copy())
    
    return result_items
    
    return result_items