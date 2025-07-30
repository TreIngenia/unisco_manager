"""
Definizione della struttura del menu dell'applicazione.
Questo file contiene solo la configurazione del menu, separata dalla logica.
"""

# Configurazione base del menu
MENU_CONFIG = {
    'validate_endpoints_by_default': True,
    'debug_missing_endpoints': True,
    'fallback_url': '#',
    'show_empty_sections': False
}

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
        'roles': ['user', 'moderator', 'admin'],
        'description': 'Panoramica generale del sistema'
    },
    
    # ==================== SEZIONE GESTIONE UTENTI ====================
    {
        'type': 'section',
        'title': 'Gestione Utenti',
        'roles': ['admin', 'moderator'],
        'description': 'Amministrazione utenti e permessi'
    },
    {
        'endpoint': 'admin.manage_companies',
        'title': 'Società',
        'icon': 'ki-outline ki-triangle fs-2',
        'roles': ['admin', 'moderator'],
        'description': 'Gestione delle società del sistema'
    },
    {
        'endpoint': 'admin.manage_users',
        'title': 'Utenti',
        'icon': 'ki-outline ki-people fs-2',
        'roles': ['admin', 'moderator'],
        'description': 'Gestione degli utenti del sistema'
    },
    {
        'endpoint': 'admin.manage_roles',
        'title': 'Ruoli',
        'icon': 'ki-outline ki-security-user fs-2',
        'roles': ['admin'],
        'description': 'Configurazione ruoli e permessi'
    },
    
    # ==================== SEZIONE LISTINI ====================
    {
        'type': 'section',
        'title': 'Listini',
        'roles': ['user', 'moderator', 'admin'],
        'description': 'Gestione prezzi e listini'
    },
    {
        'endpoint': 'listino',
        'title': 'Listino prezzi',
        'icon': 'ki-outline ki-price-tag fs-2',
        'roles': ['user', 'moderator', 'admin'],
        'description': 'Visualizza e gestisci i listini prezzi'
    },
    
    # ==================== SEZIONE CATEGORIE ====================
    {
        'type': 'section',
        'title': 'Categorie',
        'roles': ['user', 'moderator', 'admin'],
        'description': 'Organizzazione e categorizzazione'
    },
    {
        'title': 'Gestione categorie',
        'icon': 'ki-outline ki-minus-folder fs-2',
        'roles': ['moderator', 'admin'],
        'description': 'Strumenti per la gestione delle categorie',
        'children': [
            {
                'endpoint': 'cdr_categories_dashboard',
                'title': 'Dashboard categorie',
                'icon': 'ki-outline ki-element-11',
                'roles': ['moderator', 'admin'],
                'description': 'Panoramica delle categorie'
            },
            {
                'endpoint': 'cdr_categories_edit',
                'title': 'Gestione categorie',
                'icon': 'ki-outline ki-notepad-edit',
                'roles': ['moderator', 'admin'],
                'description': 'Modifica e organizza le categorie'
            },
            {
                'endpoint': 'cdr_categories_page_new',
                'title': 'Modifica categorie NEW',
                'icon': 'ki-outline ki-notepad-edit',
                'roles': ['admin'],
                'description': 'Nuova interfaccia di gestione categorie',
                'badge': 'NEW',
                'badge_class': 'badge-success'
            }
        ]
    },
    
    # ==================== SEZIONE FATTURE ====================
    {
        'type': 'section',
        'title': 'Fatture',
        'roles': ['user', 'moderator', 'admin'],
        'description': 'Gestione documentale e fatturazione'
    },
    {
        'endpoint': 'gestione_fatture',
        'title': 'Gestione Fatture',
        'icon': 'ki-outline ki-cheque fs-2',
        'roles': ['user', 'moderator', 'admin'],
        'description': 'Crea e gestisci le fatture'
    },
    
    # ==================== SEZIONE CONTRATTI ====================
    {
        'type': 'section',
        'title': 'Contratti',
        'roles': ['moderator', 'admin'],
        'description': 'Gestione contratti e accordi'
    },
    {
        'endpoint': 'gestione_contratti',
        'title': 'Gestione contratti',
        'icon': 'ki-outline ki-briefcase fs-2',
        'roles': ['moderator', 'admin'],
        'description': 'Amministra contratti e accordi commerciali'
    },
    
    # ==================== SEZIONE PROFILO UTENTE ====================
    {
        'type': 'section',
        'title': 'Il Mio Account',
        'roles': ['user', 'moderator', 'admin'],
        'description': 'Impostazioni personali'
    },
    {
        'endpoint': 'web.profile',
        'title': 'Il Mio Profilo',
        'icon': 'ki-outline ki-profile-user fs-2',
        'roles': ['user', 'moderator', 'admin'],
        'description': 'Gestisci le tue informazioni personali'
    },
    {
        'endpoint': 'web.settings',
        'title': 'Preferenze',
        'icon': 'ki-outline ki-setting-3 fs-2',
        'roles': ['user', 'moderator', 'admin'],
        'description': 'Configura le tue preferenze'
    },
    
    # ==================== SEZIONE AMMINISTRAZIONE ====================
    {
        'type': 'section',
        'title': 'Amministrazione',
        'roles': ['admin'],
        'description': 'Strumenti di amministrazione del sistema'
    },
    {
        'title': 'Sistema',
        'icon': 'ki-outline ki-setting-2 fs-2',
        'roles': ['admin'],
        'description': 'Strumenti di amministrazione avanzata',
        'children': [
            {
                'endpoint': 'admin.admin_dashboard',
                'title': 'Dashboard Admin',
                'icon': 'ki-outline ki-element-11',
                'roles': ['admin'],
                'description': 'Pannello di controllo amministrativo'
            },
            {
                'endpoint': 'config_page',
                'title': 'Impostazioni Sistema',
                'icon': 'ki-outline ki-setting-2',
                'roles': ['admin'],
                'description': 'Configurazione generale del sistema'
            },
            {
                'endpoint': 'logs',
                'title': 'Logs Sistema',
                'icon': 'ki-outline ki-devices',
                'roles': ['admin'],
                'description': 'Visualizza i log del sistema'
            },
            {
                'endpoint': 'status_page',
                'title': 'Stato del Sistema',
                'icon': 'ki-outline ki-pulse',
                'roles': ['admin'],
                'description': 'Monitoraggio stato e performance',
                'badge': 'BETA',
                'badge_class': 'badge-warning'
            }
        ]
    },
    
    # ==================== SEZIONE FATTURE ====================
    {
        'type': 'section',
        'title': 'VoIP & CDR',
        'roles': ['moderator', 'admin'],
        'description': 'Gestione categorie CDR'
    },
    {
        'endpoint': 'admin_voip_cdr.listino',
        'title': 'Listino',
        'icon': 'ki-outline ki-cheque fs-2',
        'roles': ['moderator', 'admin'],
        'description': 'Mostra il listino prezzi'
    },
    {
        'endpoint': 'admin_voip_cdr.clienti_traffico_voip',
        'title': 'Clienti traffico VoIP',
        'icon': 'ki-outline ki-cheque fs-2',
        'roles': ['moderator', 'admin'],
        'description': 'Mostra un riassunto del traffico voip dei clienti'
    },
    {
        'endpoint': 'admin_voip_cdr.cdr_categories',
        'title': 'Gestione categorie',
        'icon': 'ki-outline ki-cheque fs-2',
        'roles': ['moderator', 'admin'],
        'description': 'Crea e gestisci le categorei del CDR'
    },
    {
        'endpoint': 'admin_voip_cdr.contratti_voip',
        'title': 'Gestione contratti',
        'icon': 'ki-outline ki-cheque fs-2',
        'roles': ['moderator', 'admin'],
        'description': 'Gestisce i contratti tra wic e odoo'
    },
]

# Funzioni di utilità per la gestione della struttura
def get_menu_structure():
    """Restituisce la struttura completa del menu"""
    return MENU_ITEMS

def get_menu_config():
    """Restituisce la configurazione del menu"""
    return MENU_CONFIG

def get_endpoints_list():
    """Estrae tutti gli endpoint definiti nel menu"""
    endpoints = []
    
    def extract_endpoints(items):
        for item in items:
            if item.get('type') == 'section':
                continue
            
            if 'endpoint' in item:
                endpoints.append({
                    'endpoint': item['endpoint'],
                    'title': item['title'],
                    'roles': item.get('roles', [])
                })
            
            if 'children' in item:
                extract_endpoints(item['children'])
    
    extract_endpoints(MENU_ITEMS)
    return endpoints

def get_roles_list():
    """Estrae tutti i ruoli utilizzati nel menu"""
    roles = set()
    
    def extract_roles(items):
        for item in items:
            if 'roles' in item:
                roles.update(item['roles'])
            
            if 'children' in item:
                extract_roles(item['children'])
    
    extract_roles(MENU_ITEMS)
    return sorted(list(roles))