# ############## #
# Procedure base #
# ############## #
Installare Python 3.11
https://www.python.org/downloads/release/python-3110/
https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe

#Eseguire lo Scripts
py -3.11 -m venv venv
venv\\Scripts\\activate     #windows
source venv/bin/activate    # su Linux/Mac 
pip install -r requirements.txt
python run.py


# ############### #
# Gestione utenti #
# ############### #
ddsf
# Windows
set FLASK_APP=run.py
# Linux/Mac  
export FLASK_APP=run.py

# Crea admin
flask create-admin admin@example.com password123
# Verifica
python -m app.scripts.init_roles show

# Elimina e ricrea le tabelle
flask db downgrade
flask db upgrade



