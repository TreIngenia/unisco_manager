from flask import g, url_for, current_app
import logging

# Definizione completa del menu con controllo ruoli
MENU_ITEMS = [
    {
        'type': 'section',
        'title': '',  # Sezione vuota per spaziatura
    },
    {
        'endpoint': 'web.dashboard',
        'title': 'Dashboard',
        'icon': 'ki-outline ki-element-11 fs-2',
        'roles': ['user', 'moderator', 'admin'],  # Tutti possono vedere
    },
    
    # ==================== SEZIONE GESTIONE UTENTI ====================
    {
        'type': 'section',
        'title': 'Gestione Utenti',
        'roles': ['admin', 'moderator'],  # Solo admin e moderator
    },
    {
        'endpoint': 'admin.manage_users',
        'title': 'Utenti',
        'icon': 'ki-outline ki-people fs-2',
        'roles': ['admin', 'moderator'],
    },
    {
        'endpoint': 'admin.manage_roles',
        'title': 'Ruoli',
        'icon': 'ki-outline ki-security-user fs-2',
        'roles': ['admin'],  # Solo admin
    },
    
    # ==================== SEZIONE LISTINI ====================
    {
        'type': 'section',
        'title': 'Listini',
        'roles': ['user', 'moderator', 'admin'],
    },
    {
        'endpoint': 'listino',
        'title': 'Listino prezzi',
        'icon': 'ki-outline ki-price-tag fs-2',
        'roles': ['user', 'moderator', 'admin'],
    },
    
    # ==================== SEZIONE CATEGORIE ====================
    {
        'type': 'section',
        'title': 'Categorie',
        'roles': ['user', 'moderator', 'admin'],
    },
    {
        'title': 'Gestione categorie',
        'icon': 'ki-outline ki-minus-folder fs-2',
        'roles': ['moderator', 'admin'],
        'children': [
            {
                'endpoint': 'cdr_categories_dashboard',
                'title': 'Dashboard categorie',
                'icon': 'ki-outline ki-element-11',
                'roles': ['moderator', 'admin'],
            },
            {
                'endpoint': 'cdr_categories_edit',
                'title': 'Gestione categorie',
                'icon': 'ki-outline ki-notepad-edit',
                'roles': ['moderator', 'admin'],
            },
            {
                'endpoint': 'cdr_categories_page_new',
                'title': 'Modifica categorie NEW',
                'icon': 'ki-outline ki-notepad-edit',
                'roles': ['admin'],  # Solo admin per funzioni avanzate
            }
        ]
    },
    
    # ==================== SEZIONE FATTURE ====================
    {
        'type': 'section',
        'title': 'Fatture',
        'roles': ['user', 'moderator', 'admin'],
    },
    {
        'endpoint': 'gestione_fatture',
        'title': 'Gestione Fatture',
        'icon': 'ki-outline ki-cheque fs-2',
        'roles': ['user', 'moderator', 'admin'],
    },
    
    # ==================== SEZIONE CONTRATTI ====================
    {
        'type': 'section',
        'title': 'Contratti',
        'roles': ['moderator', 'admin'],  # Solo moderator e admin
    },
    {
        'endpoint': 'gestione_contratti',
        'title': 'Gestione contratti',
        'icon': 'ki-outline ki-briefcase fs-2',
        'roles': ['moderator', 'admin'],
    },
    
    # ==================== SEZIONE PROFILO UTENTE ====================
    {
        'type': 'section',
        'title': 'Il Mio Account',
        'roles': ['user', 'moderator', 'admin'],
    },
    {
        'endpoint': 'web.profile',
        'title': 'Il Mio Profilo',
        'icon': 'ki-outline ki-profile-user fs-2',
        'roles': ['user', 'moderator', 'admin'],
    },
    {
        'endpoint': 'web.settings',
        'title': 'Preferenze',
        'icon': 'ki-outline ki-setting-3 fs-2',
        'roles': ['user', 'moderator', 'admin'],
    },
    
    # ==================== SEZIONE AMMINISTRAZIONE ====================
    {
        'type': 'section',
        'title': 'Amministrazione',
        'roles': ['admin'],  # Solo admin
    },
    {
        'title': 'Sistema',
        'icon': 'ki-outline ki-setting-2 fs-2',
        'roles': ['admin'],
        'children': [
            {
                'endpoint': 'admin.admin_dashboard',
                'title': 'Dashboard Admin',
                'icon': 'ki-outline ki-element-11',
                'roles': ['admin'],
            },
            {
                'endpoint': 'config_page',
                'title': 'Impostazioni Sistema',
                'icon': 'ki-outline ki-setting-2',
                'roles': ['admin'],
            },
            {
                'endpoint': 'logs',
                'title': 'Logs Sistema',
                'icon': 'ki-outline ki-devices',
                'roles': ['admin'],
            },
            {
                'endpoint': 'status_page',
                'title': 'Stato del Sistema',
                'icon': 'ki-outline ki-pulse',
                'roles': ['admin'],
            }
        ]
    },
]

class MenuManager:
    """Gestisce il menu dinamico basato sui ruoli utente"""
    
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
    def get_safe_url(endpoint_name, fallback_url='#'):
        """Genera un URL sicuro per un endpoint, con fallback se non esiste"""
        if not endpoint_name:
            return fallback_url
        
        try:
            return url_for(endpoint_name)
        except Exception as e:
            # Log dell'errore in modalità debug
            if current_app.debug:
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
    def filter_menu_item(item, user_roles, validate_endpoints=True):
        """Filtra un singolo item del menu basato sui ruoli e validazione endpoint"""
        # Controlla se l'utente può vedere questo item
        if not MenuManager.has_permission(item.get('roles', []), user_roles):
            return None
        
        # Se richiesto, valida l'endpoint
        if validate_endpoints and 'endpoint' in item:
            if not MenuManager.endpoint_exists(item['endpoint']):
                # Log dell'endpoint mancante
                if current_app.debug:
                    current_app.logger.warning(f"Endpoint '{item['endpoint']}' non esiste - item '{item.get('title', 'Unknown')}' rimosso dal menu")
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
    def get_menu_for_user(validate_endpoints=True):
        """Restituisce il menu filtrato per l'utente corrente"""
        # Ottieni i ruoli dell'utente corrente
        user_roles = []
        if hasattr(g, 'user') and g.user:
            user_roles = g.user.get_role_names()
        
        filtered_menu = []
        
        for item in MENU_ITEMS:
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
        
        def count_items(items):
            nonlocal total_items, sections, invalid_endpoints
            for item in items:
                if item.get('type') == 'section':
                    sections += 1
                else:
                    total_items += 1
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
            'user_roles': user_roles,
            'is_admin': 'admin' in user_roles,
            'is_moderator': 'moderator' in user_roles
        }
    
    @staticmethod
    def validate_all_endpoints():
        """Valida tutti gli endpoint nel menu e restituisce un report"""
        report = {
            'valid': [],
            'invalid': [],
            'total_checked': 0
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
                    
                    if MenuManager.endpoint_exists(endpoint):
                        report['valid'].append({
                            'endpoint': endpoint,
                            'title': full_title
                        })
                    else:
                        report['invalid'].append({
                            'endpoint': endpoint,
                            'title': full_title
                        })
                
                if 'children' in item:
                    check_items(item['children'], item.get('title', 'Unknown'))
        
        check_items(MENU_ITEMS)
        return report

# Funzioni di utilità per i template
def get_menu(validate_endpoints=True):
    """Funzione per ottenere il menu nei template"""
    return MenuManager.get_menu_for_user(validate_endpoints)

def get_menu_stats():
    """Funzione per ottenere le statistiche del menu nei template"""
    return MenuManager.get_user_menu_stats()

def get_safe_url(endpoint_name, fallback_url='#'):
    """Funzione per generare URL sicuri nei template"""
    return MenuManager.get_safe_url(endpoint_name, fallback_url)

def validate_menu_endpoints():
    """Funzione per validare tutti gli endpoint del menu"""
    return MenuManager.validate_all_endpoints()