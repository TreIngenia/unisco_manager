from app import create_app, db
from app.models.user import User
import uuid

def migrate_users_to_uid():
    """Migra gli utenti esistenti aggiungendo UID"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Migrazione utenti esistenti...")
        
        users = User.query.filter_by(uid=None).all()
        
        for user in users:
            if not user.uid:
                user.uid = str(uuid.uuid4())
                print(f"✅ Aggiunto UID a {user.username}: {user.uid}")
        
        db.session.commit()
        print(f"🎉 Migrazione completata per {len(users)} utenti!")

if __name__ == '__main__':
    migrate_users_to_uid()