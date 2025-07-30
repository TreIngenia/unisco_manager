# ===============================================
# COMANDI FLASK CLI PER GESTIONE ADMIN
# ===============================================
# 🆕 CREARE NUOVO ADMIN (se non esiste)
flask create-admin admin@example.com password123

# 🔴 RENDERE UTENTE ESISTENTE ADMIN
flask make-admin user@example.com

# ➕ AGGIUNGERE RUOLO A UTENTE  
flask add-role user@example.com moderator

# ➖ RIMUOVERE RUOLO DA UTENTE
flask remove-role user@example.com admin

# ❌ RIMUOVERE RUOLO ADMIN
flask remove-admin admin@example.com

# 👥 LISTA TUTTI GLI UTENTI E RUOLI
flask list-users

# 🎭 LISTA TUTTI I RUOLI DISPONIBILI
flask list-roles

# 🆕 CREARE NUOVO ADMIN (se non esiste)
flask create-admin admin@example.com password123

# 🔧 INIZIALIZZARE RUOLI DEFAULT
flask init-roles

# ===============================================
# COMANDI SCRIPT PYTHON (ALTERNATIVA)
# ===============================================

# 🔴 RENDERE UTENTE ADMIN
python -m app.scripts.init_roles make-admin user@example.com

# ➕ AGGIUNGERE RUOLO
python -m app.scripts.init_roles add-role user@example.com moderator

# ❌ RIMUOVERE ADMIN
python -m app.scripts.init_roles remove-admin admin@example.com

# 👥 MOSTRA UTENTI
python -m app.scripts.init_roles show

# 🆕 CREA ADMIN
python -m app.scripts.init_roles admin admin@example.com password123

# 🔧 INIZIALIZZA RUOLI
python -m app.scripts.init_roles init

# ===============================================
# ESEMPI PRATICI
# ===============================================

# Scenario 1: Hai un utente registrato che vuoi rendere admin
flask make-admin mario.rossi@example.com

# Scenario 2: Vuoi aggiungere ruolo moderatore a qualcuno
flask add-role mario.rossi@example.com moderator

# Scenario 3: Rimuovere privilegi admin
flask remove-admin ex-admin@example.com

# Scenario 4: Vedere chi sono gli admin attuali
flask list-users

# Scenario 5: Vedere tutti i ruoli disponibili
flask list-roles

# ===============================================
# OUTPUT ESEMPI
# ===============================================

# flask make-admin user@example.com
# ✅ user@example.com è ora admin!
#    Ruoli: admin, user

# flask list-users
# 👥 Utenti registrati (3):
# --------------------------------
# ✅ 🔴 admin@example.com
#    Ruoli: admin, user
#    Creato: 08/07/2025 14:30
# 
# ✅ user@example.com  
#    Ruoli: user
#    Creato: 08/07/2025 15:45