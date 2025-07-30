from app import create_app
from dotenv import load_dotenv
import os

# Carica variabili d'ambiente da app/.env
load_dotenv(os.path.join(os.path.dirname(__file__), 'app', '.env'))

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, 
            host='0.0.0.0', 
            port=int(os.environ.get('PORT', 5000)),
            )