# setup_db.py - Script per inizializzare il database
import os
import sys

def setup_database():
    """Setup iniziale del database"""
    print("🔧 Inizializzazione database...")
    
    # Controlla se esiste la cartella migrations
    if os.path.exists('migrations'):
        print("⚠️  Cartella migrations esistente. Vuoi cancellarla e ricrearla? (y/n)")
        if input().lower() == 'y':
            import shutil
            shutil.rmtree('migrations')
            print("✅ Cartella migrations cancellata")
    
    # Imposta variabile d'ambiente
    os.environ['FLASK_APP'] = 'run.py'
    
    # Comandi da eseguire
    commands = [
        'flask db init',
        'flask db migrate -m "Initial migration with users table"',
        'flask db upgrade'
    ]
    
    for cmd in commands:
        print(f"🔄 Eseguendo: {cmd}")
        result = os.system(cmd)
        if result != 0:
            print(f"❌ Errore durante l'esecuzione di: {cmd}")
            return False
        print(f"✅ Completato: {cmd}")
    
    print("🎉 Database inizializzato con successo!")
    return True

if __name__ == '__main__':
    setup_database()