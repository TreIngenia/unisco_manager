from app.logger import get_logger
from app.voip_cdr.ftp_downloader import FTPDownloader
from flask import jsonify
from app.utils.env_manager import *

logger = get_logger(__name__)
# try:
#     from dotenv import load_dotenv
#     import os
#     load_dotenv()  # Carica variabili dal file .env
#     print("📁 File .env caricato")
#     FTP_HOST=os.getenv('FTP_HOST')
#     FTP_PORT=int(os.getenv('FTP_PORT'))
#     FTP_USER=os.getenv('FTP_USER')
#     FTP_PASSWORD=os.getenv('FTP_PASSWORD')
#     FTP_DIRECTORY=os.getenv('FTP_DIRECTORY')
#     SPECIFIC_FILENAME=os.getenv('SPECIFIC_FILENAME')
#     ARCHIVE_DIRECTORY=os.getenv('ARCHIVE_DIRECTORY')
    
# except ImportError:
#     print("⚠️ python-dotenv non installato - usando solo variabili d'ambiente del sistema")
    
def ftp_routes(app, secure_config):
    @app.route('/test_ftp')
    def test_ftp():
        ftp = FTPDownloader(secure_config)
        downloader = ftp.runftp("*", True)
        return downloader


    @app.route('/test_ftp_template')
    def test_ftp_template():
        downloader = FTPDownloader.runftp(SPECIFIC_FILENAME, True)
        return downloader


    @app.route('/test_ftp_template/')
    @app.route('/test_ftp_template/<string:get_template>')
    def test_ftp_template_manual(get_template="*"):
        downloader = FTPDownloader.runftp(get_template, True)
        return downloader


    @app.route('/download_ftp_template')
    def download_ftp_template():
        downloader = FTPDownloader.runftp(SPECIFIC_FILENAME, False)
        return downloader
    

    @app.route('/manual_run')
    def manual_run():
        """Esecuzione manuale del processo con gestione serializzazione JSON corretta"""
        try:

            # ✅ Istanzia il downloader
            downloader = FTPDownloader(secure_config)
            
            # ✅ Chiama il metodo sull'istanza
            ftp_response = downloader.process_files()
            if(ftp_response['success'] == True):
                from cdr_manager import complete_cdr_conversion
                files = ftp_response['files']
                conversion_result = complete_cdr_conversion(files, 'latin-1')
                print(conversion_result)
                
            return ftp_response
                
        except Exception as e:
            logger.error(f"Errore esecuzione manuale: {e}")
            return jsonify({
                'success': False, 
                'message': str(e),
                'error_type': type(e).__name__
            })