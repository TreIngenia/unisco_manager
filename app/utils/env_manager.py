from flask import Flask
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

def load_env_variables():
    # Carica le variabili dal file .env
    load_dotenv()

    # Ritorna un dizionario con tutte le variabili ambiente utili all'app
    return {
        'FLASK_CONFIG': os.getenv('FLASK_CONFIG'),
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'PORT': os.getenv('PORT'),

        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'DEV_DATABASE_URL': os.getenv('DEV_DATABASE_URL'),

        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY'),

        'SMTP_SERVER': os.getenv('SMTP_SERVER'),
        'SMTP_PORT': os.getenv('SMTP_PORT'),
        'SENDER_EMAIL': os.getenv('SENDER_EMAIL'),
        'SENDER_PASSWORD': os.getenv('SENDER_PASSWORD'),
        'SENDER_NAME': os.getenv('SENDER_NAME'),
        'SENDEER_CC': os.getenv('SENDEER_CC'),

        'UPLOAD_FOLDER': os.getenv('UPLOAD_FOLDER'),

        'AVATAR_FOLDER': os.getenv('AVATAR_FOLDER'),
    
        'FTP_HOST': os.getenv('FTP_HOST'),
        'FTP_PORT': os.getenv('FTP_PORT'),
        'FTP_USER': os.getenv('FTP_USER'),
        'FTP_PASSWORD': os.getenv('FTP_PASSWORD'),
        'FTP_DIRECTORY': os.getenv('FTP_DIRECTORY'),

        'DOWNLOAD_ALL_FILES': os.getenv('DOWNLOAD_ALL_FILES'),
        'SPECIFIC_FILENAME': os.getenv('SPECIFIC_FILENAME'),

}

#Carica correttamente il file .env ovunque venga richiamato.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(dotenv_path=DOTENV_PATH)

FLASK_CONFIG = os.getenv('FLASK_CONFIG')
SECRET_KEY = os.getenv('SECRET_KEY')
PORT = os.getenv('PORT')
DATABASE_URL = os.getenv('DATABASE_URL')
DEV_DATABASE_URL = os.getenv('DEV_DATABASE_URL')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = os.getenv('SMTP_PORT')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
SENDER_NAME = os.getenv('SENDER_NAME')
SENDEER_CC = os.getenv('SENDEER_CC')
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, os.getenv('UPLOAD_FOLDER_STATIC'))
AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, os.getenv('AVATAR_FOLDER'))
UPLOAD_URL = f"{os.getenv('UPLOAD_FOLDER')}"
AVATAR_URL = f"{UPLOAD_URL}/{os.getenv('AVATAR_FOLDER')}"

# Configurazione Server FTP
FTP_HOST=os.getenv('FTP_HOST')
FTP_PORT=os.getenv('FTP_PORT')
FTP_USER=os.getenv('FTP_USER')
FTP_PASSWORD=os.getenv('FTP_PASSWORD')
FTP_DIRECTORY=os.getenv('FTP_DIRECTORY')
FTP_TEST= os.getenv('FTP_TEST', 'False').lower() == 'true'


# Configurazione Download
DOWNLOAD_ALL_FILES=os.path.join(PROJECT_ROOT, os.getenv('DOWNLOAD_ALL_FILES'))
SPECIFIC_FILENAME=os.getenv('SPECIFIC_FILENAME')
ARCHIVE_DIRECTORY=os.path.join(PROJECT_ROOT, os.getenv('ARCHIVE_DIRECTORY'))
ANALYTICS_OUTPUT_FOLDER=os.path.join(ARCHIVE_DIRECTORY, os.getenv('ANALYTICS_OUTPUT_FOLDER'))
FILE_NAMING_PATTERN=os.getenv('FILE_NAMING_PATTERN')
CUSTOM_PATTERN=os.getenv('CUSTOM_PATTERN')
FILTER_PATTERN=os.getenv('FILTER_PATTERN')

LOGS=os.path.join(PROJECT_ROOT, os.getenv('LOGS')) 

CATEGORIES_FOLDER = os.path.join(ARCHIVE_DIRECTORY, os.getenv('CATEGORIES_FOLDER'))
CATEGORIES_FILE=os.getenv('CATEGORIES_FILE')

CDR_JSON_FOLDER = os.getenv('CDR_JSON_FOLDER')
CDR_FTP_FOLDER = os.getenv('CDR_FTP_FOLDER')
CONTACTS_FOLDER = os.getenv('CONTACTS_FOLDER')
CONTACT_FILE = os.path.join(ARCHIVE_DIRECTORY, CONTACTS_FOLDER,os.getenv('CONTACT_FILE')) 


# Odoo
ODOO_URL = os.getenv('ODOO_URL')
ODOO_DB = os.getenv('ODOO_DB')
ODOO_USERNAME = os.getenv('ODOO_USERNAME')
ODOO_API_KEY = os.getenv('ODOO_API_KEY')
# config/cdr_categories.json

# JSON_FILE_NAME  = f"cdr_data_{datetime.now().strftime('%Y_%m')}.json"
# PROCESSED_FILE  = f"processed_files_{datetime.now().strftime('%Y_%m')}.json"
# AGGREGATE_FILES = f"aggregate_files_{datetime.now().strftime('%Y_%m')}.json"

JSON_FILE_NAME  = f"cdr_data_"
PROCESSED_FILE  = f"processed_files_"
AGGREGATE_FILES = f"aggregate_files_"

#Listino voip
LISTINO_VOIP=os.getenv('LISTINO_VOIP')
# ARCHIVE_DIRECTORY CATEGORIES_FOLDER CATEGORIES_FILE



#os.path.join(ARCHIVE_DIRECTORY, LISTINO_VOIPO)