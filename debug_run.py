# debug_run.py - File specifico per il debug con VS Code
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Configura il path del progetto
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Carica variabili d'ambiente da app/.env
env_path = PROJECT_ROOT / 'app' / '.env'
load_dotenv(dotenv_path=env_path)

# Configurazione debug
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '0'  # Disabilita debug Flask per evitare conflitti

# Importa dopo aver configurato il path
from app import create_app

def main():
    """Funzione principale per avviare l'app in modalità debug"""
    
    print("🔧 Modalità Debug VS Code")
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"📄 ENV file: {env_path}")
    print(f"🐍 Python: {sys.executable}")
    print("-" * 50)
    
    try:
        # Crea l'applicazione Flask
        app = create_app()
        
        # Configurazione debug-friendly
        app.config['TESTING'] = False
        app.config['DEBUG'] = False  # VS Code gestisce il debug
        
        print("✅ App creata con successo")
        print(f"🌐 Server: http://localhost:5000")
        print(f"🎯 Breakpoint pronti!")
        print("-" * 50)
        
        # Avvia il server
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=False,        # VS Code debugger
            use_reloader=False, # Evita conflitti
            use_debugger=False, # VS Code debugger
            threaded=True,      # Threading abilitato
            load_dotenv=False   # Già caricato manualmente
        )
        
    except Exception as e:
        print(f"❌ Errore durante l'avvio: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)