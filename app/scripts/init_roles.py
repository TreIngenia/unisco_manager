from app import create_app, db
from app.models.role import Role
from app.models.user import User

def init_roles():
    """Inizializza i ruoli di default nel database"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Inizializzazione ruoli nel database...")
        
        # Crea i ruoli di default
        Role.create_default_roles()
        
        print("✅ Ruoli creati con successo!")
        
        # Mostra ruoli esistenti
        roles = Role.query.all()
        print(f"📋 Ruoli disponibili ({len(roles)}):")
        for role in roles:
            print(f"  - {role.name}: {role.description}")
        
        # Assegna ruolo user a tutti gli utenti senza ruoli
        users_without_roles = User.query.filter(~User.roles.any()).all()
        if users_without_roles:
            print(f"👥 Assegnazione ruolo 'user' a {len(users_without_roles)} utenti...")
            default_role = Role.get_default_role()
            for user in users_without_roles:
                user.add_role(default_role)
            db.session.commit()
            print("✅ Ruoli assegnati!")

def create_admin_user(email, password):
    """Crea un utente admin"""
    app = create_app()
    
    with app.app_context():
        # Controlla se esiste già
        existing_user = User.find_by_username(email)
        if existing_user:
            print(f"❌ Utente {email} esiste già!")
            return
        
        # Crea utente
        admin_user = User(
            username=email,
            email=email,
            is_active=True,
            is_email_confirmed=True  # Admin confermato automaticamente
        )
        admin_user.set_password(password)
        
        db.session.add(admin_user)
        db.session.flush()
        
        # Assegna ruolo admin
        admin_role = Role.get_admin_role()
        if admin_role:
            admin_user.add_role(admin_role)
        
        db.session.commit()
        
        print(f"✅ Utente admin creato: {email}")
        print(f"   Ruoli: {', '.join(admin_user.get_role_names())}")

def make_user_admin(email):
    """Rende un utente esistente admin"""
    app = create_app()
    
    with app.app_context():
        user = User.find_by_username(email)
        if not user:
            print(f"❌ Utente {email} non trovato!")
            return
        
        if user.is_admin():
            print(f"ℹ️  {email} è già admin!")
            return
        
        admin_role = Role.get_admin_role()
        if not admin_role:
            print("❌ Ruolo admin non trovato! Esegui prima 'init'")
            return
        
        user.add_role(admin_role)
        db.session.commit()
        
        print(f"✅ {email} è ora admin!")
        print(f"   Ruoli: {', '.join(user.get_role_names())}")

def remove_user_admin(email):
    """Rimuove il ruolo admin da un utente"""
    app = create_app()
    
    with app.app_context():
        user = User.find_by_username(email)
        if not user:
            print(f"❌ Utente {email} non trovato!")
            return
        
        if not user.is_admin():
            print(f"ℹ️  {email} non è admin!")
            return
        
        admin_role = Role.get_admin_role()
        if admin_role:
            user.remove_role(admin_role)
            db.session.commit()
            
            print(f"✅ Ruolo admin rimosso da {email}")
            print(f"   Ruoli rimanenti: {', '.join(user.get_role_names())}")

def add_user_role(email, role_name):
    """Aggiunge un ruolo a un utente"""
    app = create_app()
    
    with app.app_context():
        user = User.find_by_username(email)
        if not user:
            print(f"❌ Utente {email} non trovato!")
            return
        
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            print(f"❌ Ruolo '{role_name}' non trovato!")
            available_roles = [r.name for r in Role.query.all()]
            print(f"   Ruoli disponibili: {', '.join(available_roles)}")
            return
        
        if user.has_role(role_name):
            print(f"ℹ️  {email} ha già il ruolo '{role_name}'!")
            return
        
        user.add_role(role)
        db.session.commit()
        
        print(f"✅ Ruolo '{role_name}' aggiunto a {email}")
        print(f"   Tutti i ruoli: {', '.join(user.get_role_names())}")

def show_users_and_roles():
    """Mostra tutti gli utenti e i loro ruoli"""
    app = create_app()
    
    with app.app_context():
        users = User.query.all()
        
        print(f"👥 Utenti registrati ({len(users)}):")
        print("-" * 80)
        
        for user in users:
            status = "✅" if user.is_active and user.is_email_confirmed else "❌"
            admin_badge = "🔴 ADMIN" if user.is_admin() else ""
            roles = ', '.join(user.get_role_names()) or 'Nessun ruolo'
            
            print(f"{status} {user.email} {admin_badge}")
            print(f"   Ruoli: {roles}")
            print(f"   Creato: {user.created_at.strftime('%d/%m/%Y %H:%M')}")
            if user.last_login:
                print(f"   Ultimo login: {user.last_login.strftime('%d/%m/%Y %H:%M')}")
            print()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("🛠️  GESTIONE UTENTI E RUOLI")
        print("=" * 50)
        print("Uso:")
        print("  python -m app.scripts.init_roles init")
        print("  python -m app.scripts.init_roles admin EMAIL PASSWORD")
        print("  python -m app.scripts.init_roles make-admin EMAIL")
        print("  python -m app.scripts.init_roles remove-admin EMAIL") 
        print("  python -m app.scripts.init_roles add-role EMAIL ROLE")
        print("  python -m app.scripts.init_roles show")
        print()
        print("Esempi:")
        print("  python -m app.scripts.init_roles make-admin user@example.com")
        print("  python -m app.scripts.init_roles add-role user@example.com moderator")
        print("  python -m app.scripts.init_roles remove-admin admin@example.com")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'init':
        init_roles()
    elif command == 'admin':
        if len(sys.argv) != 4:
            print("❌ Uso: python -m app.scripts.init_roles admin EMAIL PASSWORD")
            sys.exit(1)
        email = sys.argv[2]
        password = sys.argv[3]
        create_admin_user(email, password)
    elif command == 'make-admin':
        if len(sys.argv) != 3:
            print("❌ Uso: python -m app.scripts.init_roles make-admin EMAIL")
            sys.exit(1)
        email = sys.argv[2]
        make_user_admin(email)
    elif command == 'remove-admin':
        if len(sys.argv) != 3:
            print("❌ Uso: python -m app.scripts.init_roles remove-admin EMAIL")
            sys.exit(1)
        email = sys.argv[2]
        remove_user_admin(email)
    elif command == 'add-role':
        if len(sys.argv) != 4:
            print("❌ Uso: python -m app.scripts.init_roles add-role EMAIL ROLE")
            sys.exit(1)
        email = sys.argv[2]
        role_name = sys.argv[3]
        add_user_role(email, role_name)
    elif command == 'show':
        show_users_and_roles()
    else:
        print(f"❌ Comando sconosciuto: {command}")
        sys.exit(1)