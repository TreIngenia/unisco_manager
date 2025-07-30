import json
import os
import csv
from datetime import datetime
from typing import List, Union, Dict, Any, Optional
from collections import defaultdict
import re
import hashlib
import logging
from pathlib import Path
from app.utils.env_manager import *

# json_file_name = f"cdr_data_{datetime.now().strftime('%Y_%m')}.json"
# processed_files = f"processed_files_{datetime.now().strftime('%Y_%m')}.json"
# aggregate_files = f"aggregate_files_{datetime.now().strftime('%Y_%m')}.json"

# json_file_name = JSON_FILE_NAME
# processed_files = PROCESSED_FILE
aggregate_files = AGGREGATE_FILES

class CDRProcessor:
    """
    Processore per file CDR (Call Detail Records)
    Converte file di testo separati da punto e virgola in JSON strutturato
    """
    
    def __init__(self, output_json_path):
        """
        Inizializza il processore CDR
        
        Args:
            output_json_path: Percorso del file JSON di output
            processed_files_path: Percorso del file che traccia i file già processati
        """
        # self.output_json_path = Path(ARCHIVE_DIRECTORY) / CDR_JSON_FOLDER / output_json_path
        # self.processed_files_path = Path(ARCHIVE_DIRECTORY) / CDR_JSON_FOLDER / processed_files
        self.logger = self._setup_logger()

        first_file = Path(ARCHIVE_DIRECTORY) / CDR_FTP_FOLDER / output_json_path
        anno_mese = self.extract_year_month_from_cdr(first_file)
        self.json_file_name = JSON_FILE_NAME+anno_mese+".json"
        self.processed_files = PROCESSED_FILE+anno_mese+".json"

        self.output_json_path = Path(ARCHIVE_DIRECTORY) / CDR_JSON_FOLDER / self.json_file_name
        self.processed_files_path = Path(ARCHIVE_DIRECTORY) / CDR_JSON_FOLDER / self.processed_files
            
        # Definizione delle colonne del CDR
        self.cdr_columns = [
            "data_ora",
            "numero_cliente", 
            "numero_chiamato",
            "durata_secondi",
            "tipo_chiamata",
            "operatore",
            "costo_euro",
            "codice_contratto",
            "codice_servizio",
            "cliente_finale",
            "comune",
            "prefisso_chiamato"
        ]
    
    def _setup_logger(self) -> logging.Logger:
        """Configura il logger per il processore"""
        logger = logging.getLogger('CDRProcessor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def extract_year_month_from_cdr(self, file_path):
        """
        Legge la prima riga di un file CDR, estrae la data e restituisce anno_mese.
        
        Args:
            file_path (str): Percorso del file CDR da analizzare
            
        Returns:
            str: Anno e mese nel formato "YYYY_MM" (es: "2025_07")
            None: Se si verifica un errore o il formato non è valido
            
        Raises:
            FileNotFoundError: Se il file non esiste
            ValueError: Se il formato della data non è corretto
        """
        try:
            # Apre il file e legge solo la prima riga
            with open(file_path, 'r', encoding='latin1') as file:
                first_line = file.readline().strip()
            
            # Controlla che la riga non sia vuota
            if not first_line:
                raise ValueError("Il file è vuoto o la prima riga è vuota")
            
            # Divide la riga per il delimitatore ";"
            fields = first_line.split(';')
            
            # Controlla che ci sia almeno un campo
            if not fields or not fields[0]:
                raise ValueError("Primo campo della riga vuoto")
            
            # Estrae la data (primo campo)
            date_string = fields[0]
            
            # Verifica il formato della data: YYYY-MM-DD-HH.MM.SS
            date_parts = date_string.split('-')
            
            if len(date_parts) < 3:
                raise ValueError(f"Formato data non valido: {date_string}")
            
            # Estrae anno e mese
            year = date_parts[0]
            month = date_parts[1]
            
            # Verifica che anno e mese siano numerici e validi
            if not (year.isdigit() and month.isdigit()):
                raise ValueError(f"Anno o mese non numerici: {year}-{month}")
            
            if len(year) != 4 or len(month) != 2:
                raise ValueError(f"Formato anno/mese non valido: {year}-{month}")
            
            # Restituisce nel formato richiesto
            return f"{year}_{month}"
            
        except FileNotFoundError:
            print(f"Errore: File '{file_path}' non trovato")
            return None
        except ValueError as e:
            print(f"Errore formato: {e}")
            return None
        except Exception as e:
            print(f"Errore imprevisto: {e}")
            return None
            
    def _get_file_hash(self, file_path: str) -> str:
        """
        Calcola l'hash MD5 di un file per identificare se è già stato processato
        
        Args:
            file_path: Percorso del file
            
        Returns:
            Hash MD5 del file
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        except FileNotFoundError:
            self.logger.error(f"File non trovato: {file_path}")
            return ""
        except Exception as e:
            self.logger.error(f"Errore nel calcolo hash per {file_path}: {e}")
            return ""
        
        return hash_md5.hexdigest()
    
    def _load_processed_files(self) -> Dict[str, str]:
        """
        Carica l'elenco dei file già processati
        
        Returns:
            Dizionario con nome_file: hash_file
        """
        if not os.path.exists(self.processed_files_path):
            return {}
        
        try:
            with open(self.processed_files_path, 'r', encoding='latin1') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Errore nel caricamento file processati: {e}")
            return {}
    
    def _save_processed_files(self, processed_files: Dict[str, str]):
        """
        Salva l'elenco dei file processati
        
        Args:
            processed_files: Dizionario con nome_file: hash_file
        """
        try:
            with open(self.processed_files_path, 'w', encoding='utf-8') as f:
                json.dump(processed_files, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Errore nel salvataggio file processati: {e}")
    
    def _load_existing_json(self) -> List[Dict[str, Any]]:
        """
        Carica il JSON esistente se presente
        
        Returns:
            Lista dei record CDR esistenti
        """
        if not os.path.exists(self.output_json_path):
            return []
        
        try:
            with open(self.output_json_path, 'r', encoding='latin1') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            self.logger.error(f"Errore nel caricamento JSON esistente: {e}")
            return []
    
    def _save_json(self, data: List[Dict[str, Any]]):
        """
        Salva i dati in formato JSON
        
        Args:
            data: Lista dei record CDR da salvare
        """
        try:
            with open(self.output_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Salvati {len(data)} record in {self.output_json_path}")
        except Exception as e:
            self.logger.error(f"Errore nel salvataggio JSON: {e}")
    
    def _parse_cdr_line(self, line: str) -> Dict[str, Any]:
        """
        Converte una riga CDR in dizionario
        
        Args:
            line: Riga del file CDR
            
        Returns:
            Dizionario con i dati strutturati
        """
        parts = line.strip().split(';')
        if len(parts)-1 != len(self.cdr_columns):
            self.logger.warning(f"Riga con numero colonne non valido: {len(parts)} vs {len(self.cdr_columns)}")
            return None
        
        try:
            # Costruisce il record strutturato
            record = {}
            
            for i, column in enumerate(self.cdr_columns):
                value = parts[i].strip()
                
                # Conversione tipi specifici
                if column == "data_ora":
                    # Converte la data in formato ISO
                    try:
                        dt = datetime.strptime(value, "%Y-%m-%d-%H.%M.%S")
                        record[column] = dt.isoformat()
                    except ValueError:
                        record[column] = value
                        
                elif column == "durata_secondi":
                    try:
                        record[column] = int(value)
                    except ValueError:
                        record[column] = 0
                        
                elif column == "costo_euro":
                    try:
                        record[column] = float(value.replace(',', '.'))
                    except ValueError:
                        record[column] = 0.0
                        
                elif column in ["codice_contratto", "codice_servizio"]:
                    try:
                        record[column] = int(value)
                    except ValueError:
                        record[column] = 0
                        
                else:
                    record[column] = value
                
                if(record.get('costo_euro') is not None and record.get('costo_euro') != 0.0):
                    record['costo_euro_with_markup'] = self._calculate_markup_price(
                        record.get('tipo_chiamata', ''), 
                        record.get('durata_secondi', 0)
                    )
            
            return record
            
        except Exception as e:
            self.logger.error(f"Errore nel parsing riga: {line[:50]}... - {e}")
            return None
    
    def _process_single_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Processa un singolo file CDR
        
        Args:
            file_path: Percorso del file da processare
            
        Returns:
            Lista dei record estratti dal file
        """
        if not os.path.exists(file_path):
            self.logger.error(f"File non trovato: {file_path}")
            return []
        
        records = []
        
        try:
            with open(file_path, 'r', encoding='latin1') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():  # Ignora righe vuote
                        record = self._parse_cdr_line(line)
                        if record:
                            # Aggiunge metadati del file
                            record['_source_file'] = os.path.basename(file_path)
                            record['_line_number'] = line_num
                            record['_processed_at'] = datetime.now().isoformat()
                            records.append(record)
            
            self.logger.info(f"Processati {len(records)} record da {file_path}")
            
        except Exception as e:
            self.logger.error(f"Errore nel processamento file {file_path}: {e}")
        
        return records
    
    

    def process_files(self, files: Union[str, List[str]], riprocessa: bool = True) -> Dict[str, Any]:
        """
        Processa uno o più file CDR e li converte in JSON
        
        Args:
            files: Nome file singolo o lista di nomi file
            riprocessa: Se True, riprocessa tutti i file da zero sovrascrivendo i dati esistenti
            
        Returns:
            Dizionario con statistiche del processamento
        """
        # Normalizza input a lista
        if isinstance(files, str):
            file_list = [files]
        else:
            file_list = files
        
        # Carica file già processati e JSON esistente
        if riprocessa:
            # Se riprocessa è True, inizializza tutto da zero
            processed_files = {}
            existing_data = []
            self.logger.info("Modalità riprocessamento: inizializzazione da zero")
        else:
            # Carica file già processati
            processed_files = self._load_processed_files()
            # Carica JSON esistente
            existing_data = self._load_existing_json()
        
        # Statistiche
        stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'records_added': 0,
            'total_records': len(existing_data),
            'errors': []
        }
        
        # Processa ogni file
        for file_name in file_list:
            try:
                # Calcola hash del file
                file_path = Path(ARCHIVE_DIRECTORY) / CDR_FTP_FOLDER / file_name
                file_hash = self._get_file_hash(file_path)
                file_name = os.path.basename(file_path)
                
                if not file_hash:
                    stats['errors'].append(f"Impossibile calcolare hash per {file_path}")
                    continue
                
                # Controlla se il file è già stato processato (solo se riprocessa è False)
                if not riprocessa and file_name in processed_files and processed_files[file_name] == file_hash:
                    self.logger.info(f"File già processato, salto: {file_path}")
                    stats['files_skipped'] += 1
                    continue
                
                # Processa il file
                new_records = self._process_single_file(file_path)
                
                if new_records:
                    existing_data.extend(new_records)
                    processed_files[file_name] = file_hash
                    stats['files_processed'] += 1
                    stats['records_added'] += len(new_records)
                    
                    self.logger.info(f"Processato {file_path}: {len(new_records)} nuovi record")
                else:
                    stats['errors'].append(f"Nessun record valido trovato in {file_path}")
                    
            except Exception as e:
                error_msg = f"Errore processamento {file_path}: {e}"
                self.logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        # Salva i risultati
        if stats['records_added'] > 0:
            self._save_json(existing_data)
            self._save_processed_files(processed_files)
        
        stats['total_records'] = len(existing_data)
        
        # Log statistiche finali
        self.logger.info(f"Processamento completato:")
        self.logger.info(f"  - File processati: {stats['files_processed']}")
        self.logger.info(f"  - File saltati: {stats['files_skipped']}")
        self.logger.info(f"  - Record aggiunti: {stats['records_added']}")
        self.logger.info(f"  - Record totali: {stats['total_records']}")
        
        if stats['errors']:
            self.logger.warning(f"  - Errori: {len(stats['errors'])}")
        
        return json.dumps({'stats': stats, 'nome_file': self.json_file_name})
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Restituisce statistiche sui dati processati
        
        Returns:
            Dizionario con statistiche
        """
        data = self._load_existing_json()
        processed_files = self._load_processed_files()
        
        if not data:
            return {
                'total_records': 0,
                'processed_files': 0,
                'date_range': None,
                'operators': [],
                'call_types': []
            }
        
        # Analisi dati
        operators = set()
        call_types = set()
        dates = []
        
        for record in data:
            if 'operatore' in record:
                operators.add(record['operatore'])
            if 'tipo_chiamata' in record:
                call_types.add(record['tipo_chiamata'])
            if 'data_ora' in record:
                dates.append(record['data_ora'])
        
        return {
            'total_records': len(data),
            'processed_files': len(processed_files),
            'date_range': {
                'from': min(dates) if dates else None,
                'to': max(dates) if dates else None
            },
            'operators': sorted(list(operators)),
            'call_types': sorted(list(call_types)),
            'files': list(processed_files.keys())
        }
    
    def _load_categories(self) -> Dict[str, Any]:
        """
        Carica le categorie dal file cdr_categories.json
        
        Returns:
            Dizionario con le categorie
        """
        categories_file = Path(ARCHIVE_DIRECTORY) / CATEGORIES_FOLDER / CATEGORIES_FILE
        
        if not os.path.exists(categories_file):
            self.logger.warning(f"File categorie non trovato: {categories_file}")
            return {}
        
        try:
            with open(categories_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Errore nel caricamento categorie: {e}")
            return {}

    def _calculate_markup_price(self, tipo_chiamata: str, durata_secondi: int) -> float:
        """
        Calcola il prezzo con markup basato su tipo_chiamata e durata
        
        Args:
            tipo_chiamata: Tipo di chiamata dal record CDR
            durata_secondi: Durata della chiamata in secondi
            
        Returns:
            Prezzo calcolato con markup in euro
        """
        if durata_secondi <= 0:
            return 0.0
        
        # Carica le categorie
        categories = self._load_categories()
        
        if not categories:
            return 0.0
        
        # Cerca il pattern corrispondente
        tipo_chiamata_upper = tipo_chiamata.upper().strip()
        
        for category_name, category_data in categories.items():
            if not category_data.get('is_active', True):
                continue
                
            patterns = category_data.get('patterns', [])
            
            # Controlla se il tipo_chiamata corrisponde a uno dei pattern
            for pattern in patterns:
                if pattern.upper() in tipo_chiamata_upper:
                    # Calcola il prezzo: (durata_secondi / 60) * price_with_markup
                    price_with_markup = category_data.get('price_with_markup', 0.0)
                    durata_minuti = durata_secondi / 60.0
                    prezzo_calcolato = durata_minuti * price_with_markup
                    
                    self.logger.debug(f"Tipo: {tipo_chiamata} -> Categoria: {category_name} -> "
                                    f"Durata: {durata_minuti:.2f}min -> Prezzo: {prezzo_calcolato:.4f}€")
                    return round(prezzo_calcolato, 4)
        
        # Se non trova corrispondenze, ritorna 0
        self.logger.debug(f"Nessuna categoria trovata per tipo_chiamata: {tipo_chiamata}")
        return 0.0


class CDRAggregator:
    """
    Aggregatore per dati CDR (Call Detail Records)
    Aggrega i dati per codice_contratto e tipo_chiamata
    """
    
    def __init__(self):
        """Inizializza l'aggregatore CDR"""
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configura il logger per l'aggregatore"""
        logger = logging.getLogger('CDRAggregator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def extract_year_month_from_filename(self, filename):
        """
        Estrae anno e mese da un nome file nel formato 'cdr_data_YYYY_MM.json'.
        
        Args:
            filename (str): Nome del file o percorso completo (es: "cdr_data_2025_07.json")
            
        Returns:
            str: Anno e mese nel formato "YYYY_MM" (es: "2025_07")
            None: Se il formato non è riconosciuto o non valido
            
        Examples:
            >>> extract_year_month_from_filename("cdr_data_2025_07.json")
            "2025_07"
            >>> extract_year_month_from_filename("/path/to/cdr_data_2024_12.json")
            "2024_12"
            >>> extract_year_month_from_filename("invalid_file.json")
            None
        """
        try:
            # Estrae solo il nome del file se è un percorso completo
            basename = os.path.basename(filename)
            
            # Pattern regex per identificare il formato cdr_data_YYYY_MM.json
            # Cerca: cdr_data_ seguito da 4 cifre (anno), underscore, 2 cifre (mese), .json
            pattern = r'cdr_data_(\d{4})_(\d{2})\.json$'
            
            match = re.search(pattern, basename, re.IGNORECASE)
            
            if not match:
                print(f"Formato filename non riconosciuto: {basename}")
                return None
            
            year = match.group(1)
            month = match.group(2)
            
            # Validazione base del mese (01-12)
            month_int = int(month)
            if month_int < 1 or month_int > 12:
                print(f"Mese non valido: {month}")
                return None
            
            # Validazione base dell'anno (deve essere ragionevole)
            year_int = int(year)
            # if year_int < 2000 or year_int > 2100:
            #     print(f"Anno non valido: {year}")
            #     return None
            
            return [ year, month ]#f"{year}_{month}"
            
        except Exception as e:
            print(f"Errore nell'elaborazione del filename '{filename}': {e}")
            return None    

    def extract_year_month_from_filename_flexible(self, filename):
        """
        Versione più flessibile che cerca qualsiasi pattern YYYY_MM nel filename.
        
        Args:
            filename (str): Nome del file o percorso completo
            
        Returns:
            str: Primo pattern "YYYY_MM" trovato nel filename
            None: Se non viene trovato alcun pattern valido
            
        Examples:
            >>> extract_year_month_from_filename_flexible("cdr_data_2025_07.json")
            "2025_07"
            >>> extract_year_month_from_filename_flexible("backup_2024_03_old.txt")
            "2024_03"
            >>> extract_year_month_from_filename_flexible("file_without_date.txt")
            None
        """
        try:
            # Estrae solo il nome del file se è un percorso completo
            basename = os.path.basename(filename)
            
            # Pattern più generico per trovare YYYY_MM ovunque nel filename
            pattern = r'(\d{4})_(\d{2})'
            
            match = re.search(pattern, basename)
            
            if not match:
                print(f"Nessun pattern anno_mese trovato in: {basename}")
                return None
            
            year = match.group(1)
            month = match.group(2)
            
            # Validazione del mese (01-12)
            month_int = int(month)
            if month_int < 1 or month_int > 12:
                print(f"Mese non valido: {month}")
                return None
            
            # Validazione dell'anno
            year_int = int(year)
            # if year_int < 2000 or year_int > 2100:
            #     print(f"Anno non valido: {year}")
            #     return None
            
            return [ year, month ] #f"{year}_{month}"
            
        except Exception as e:
            print(f"Errore nell'elaborazione del filename '{filename}': {e}")
            return None
            
    def _load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Carica un singolo file JSON
        
        Args:
            file_path: Percorso del file JSON
            
        Returns:
            Lista dei record CDR
        """
        file_path = Path(ARCHIVE_DIRECTORY) / CDR_JSON_FOLDER / file_path
        if not os.path.exists(file_path):
            self.logger.error(f"File non trovato: {file_path}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                self.logger.error(f"Il file {file_path} non contiene una lista")
                return []
                
            self.logger.info(f"Caricati {len(data)} record da {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Errore nel parsing JSON di {file_path}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Errore nel caricamento di {file_path}: {e}")
            return []
    
    def _load_all_data(self, files: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """
        Carica tutti i dati dai file specificati
        
        Args:
            files: File singolo o lista di file JSON
            
        Returns:
            Lista unificata di tutti i record CDR
        """
        # Normalizza input a lista
        if isinstance(files, str):
            file_list = [files]
        else:
            file_list = files
        
        all_data = []
        
        for file_path in file_list:
            data = self._load_json_file(file_path)
            all_data.extend(data)
        
        self.logger.info(f"Caricati in totale {len(all_data)} record da {len(file_list)} file")
        return all_data
    
    def _aggregate_by_contract_and_type(self, data: List[Dict[str, Any]]) -> Dict[int, Dict[str, Dict[str, Any]]]:

        """
        Aggrega i dati per codice_contratto e tipo_chiamata
        
        Args:
            data: Lista dei record CDR
            
        Returns:
            Dizionario strutturato: {codice_contratto: {tipo_chiamata: {aggregati}}}
        """
        # Struttura: {codice_contratto: {tipo_chiamata: {durata_totale, costo_totale, count, record_sample}}}
        aggregated = defaultdict(lambda: defaultdict(lambda: {
            'durata_secondi_totale': 0,
            'costo_euro_totale': 0.0,
            'costo_euro_totale_with_markup': 0.0,
            'numero_chiamate': 0,
            'record_sample': None
        }))
        
        for record in data:
            try:
                # Estrai i campi necessari
                codice_contratto = record.get('codice_contratto')
                tipo_chiamata = record.get('tipo_chiamata', 'N.D.')
                durata_secondi = record.get('durata_secondi', 0)
                costo_euro = record.get('costo_euro', 0.0)
                costo_euro_with_markup = record.get('costo_euro_with_markup', 0.0)

                # Verifica che codice_contratto sia presente
                if codice_contratto is None:
                    self.logger.warning(f"Record senza codice_contratto saltato: {record.get('_source_file', 'unknown')}")
                    continue
                
                # Converte i tipi se necessario
                if isinstance(durata_secondi, str):
                    durata_secondi = int(durata_secondi) if durata_secondi.isdigit() else 0
                if isinstance(costo_euro, str):
                    costo_euro = float(costo_euro.replace(',', '.')) if costo_euro else 0.0
                if isinstance(costo_euro_with_markup, str):
                    costo_euro_with_markup = float(costo_euro_with_markup.replace(',', '.')) if costo_euro_with_markup else 0.0
                if isinstance(codice_contratto, str):
                    codice_contratto = int(codice_contratto) if codice_contratto.isdigit() else 0
                
                # Aggrega i dati
                agg_data = aggregated[codice_contratto][tipo_chiamata]
                agg_data['durata_secondi_totale'] += durata_secondi
                agg_data['costo_euro_totale'] += costo_euro
                agg_data['costo_euro_totale_with_markup'] += costo_euro_with_markup
                agg_data['numero_chiamate'] += 1
                
                # Salva un record di esempio per mantenere i metadati
                if agg_data['record_sample'] is None:
                    agg_data['record_sample'] = record.copy()
                
            except Exception as e:
                self.logger.error(f"Errore nell'aggregazione del record: {e}")
                continue
        
        return dict(aggregated)
    
    def _create_contract_structure(self, aggregated_data: Dict[int, Dict[str, Dict[str, Any]]], original_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Crea la struttura finale organizzata per codice_contratto
        
        Args:
            aggregated_data: Dati aggregati per contratto e tipo chiamata
            original_data: Dati originali per creare lista_chiamate
            
        Returns:
            Dizionario strutturato per codice_contratto
        """
        result_structure = {}
        
        # Organizza i record originali per codice_contratto
        original_by_contract = defaultdict(list)
        for record in original_data:
            codice_contratto = record.get('codice_contratto')
            if codice_contratto is not None:
                # Converte in int se necessario
                if isinstance(codice_contratto, str) and codice_contratto.isdigit():
                    codice_contratto = int(codice_contratto)
                original_by_contract[codice_contratto].append(record)
        
        for codice_contratto, types_data in aggregated_data.items():
            # Calcola i totali generali per il contratto
            durata_generale = 0
            costo_generale = 0.0
            costo_generale_with_markup = 0.0
            chiamate_totali = 0
            
            # Record di esempio per i metadati del contratto
            contract_sample = None
            aggregated_records = []
            
            # Crea record per ogni tipo di chiamata
            for tipo_chiamata, agg_data in types_data.items():
                sample_record = agg_data['record_sample']
                
                if contract_sample is None:
                    contract_sample = sample_record
                
                # Crea record aggregato per tipo chiamata
                type_record = {
                    'codice_contratto': codice_contratto,
                    'data_ora': sample_record.get('data_ora', ''),  # Aggiunto campo data_ora
                    'tipo_chiamata': tipo_chiamata,
                    'durata_secondi_totale': agg_data['durata_secondi_totale'],
                    'costo_euro_totale': round(agg_data['costo_euro_totale'], 3),
                    'costo_euro_totale_with_markup': round(agg_data['costo_euro_totale_with_markup'], 3),
                    'numero_chiamate': agg_data['numero_chiamate'],
                    'aggregation_type': 'per_tipo_chiamata',
                    
                    # Mantieni alcuni metadati dal record di esempio
                    'cliente_finale': sample_record.get('cliente_finale', ''),
                    'numero_cliente': sample_record.get('numero_cliente', ''),
                    'codice_servizio': sample_record.get('codice_servizio', ''),
                    'comune': sample_record.get('comune', ''),
                    'operatore': sample_record.get('operatore', ''),
                    
                    # Metadati di aggregazione
                    '_aggregated_at': sample_record.get('_processed_at', ''),
                    '_source_files': list(set([sample_record.get('_source_file', '')])),
                }
                
                aggregated_records.append(type_record)
                
                # Accumula per il totale generale
                durata_generale += agg_data['durata_secondi_totale']
                costo_generale += agg_data['costo_euro_totale']
                costo_generale_with_markup += agg_data['costo_euro_totale_with_markup']
                chiamate_totali += agg_data['numero_chiamate']
            
            # Crea record aggregato generale per il contratto
            if contract_sample:
                general_record = {
                    'codice_contratto': codice_contratto,
                    'data_ora': contract_sample.get('data_ora', ''),  # Aggiunto campo data_ora
                    'tipo_chiamata': 'TOTALE_GENERALE',
                    'durata_secondi_generale': durata_generale,
                    'costo_euro_generale': round(costo_generale, 3),
                    'costo_euro_generale_with_markup': round(costo_generale_with_markup, 3),
                    'numero_chiamate_totali': chiamate_totali,
                    'numero_tipi_chiamata': len(types_data),
                    'aggregation_type': 'totale_generale',
                    
                    # Metadati del contratto
                    'cliente_finale': contract_sample.get('cliente_finale', ''),
                    'numero_cliente': contract_sample.get('numero_cliente', ''),
                    'codice_servizio': contract_sample.get('codice_servizio', ''),
                    'comune': contract_sample.get('comune', ''),
                    
                    # Metadati di aggregazione
                    '_aggregated_at': contract_sample.get('_processed_at', ''),
                    '_source_files': list(set([contract_sample.get('_source_file', '')])),
                }
                
                aggregated_records.append(general_record)
            
            # Crea la struttura per questo contratto
            contract_key = str(codice_contratto)
            result_structure[contract_key] = {
                'aggregated_records': aggregated_records,
                'lista_chiamate': original_by_contract[codice_contratto],
                'contract_info': {
                    'codice_contratto': codice_contratto,
                    'data_ora': contract_sample.get('data_ora', '') if contract_sample else '',  # Aggiunto campo data_ora
                    'cliente_finale': contract_sample.get('cliente_finale', '') if contract_sample else '',
                    'numero_cliente': contract_sample.get('numero_cliente', '') if contract_sample else '',
                    'codice_servizio': contract_sample.get('codice_servizio', '') if contract_sample else '',
                    'comune': contract_sample.get('comune', '') if contract_sample else '',
                    'durata_totale_secondi': durata_generale,
                    'costo_totale_euro': round(costo_generale, 3),
                    'costo_totale_euro_with_markup': round(costo_generale_with_markup, 3),
                    'numero_chiamate_totali': chiamate_totali,
                    'numero_tipi_chiamata': len(types_data)
                }
            }
        
        return result_structure
    # def _create_contract_structure(self, aggregated_data: Dict[int, Dict[str, Dict[str, Any]]], original_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    #     """
    #     Crea la struttura finale organizzata per codice_contratto
        
    #     Args:
    #         aggregated_data: Dati aggregati per contratto e tipo chiamata
    #         original_data: Dati originali per creare lista_chiamate
            
    #     Returns:
    #         Dizionario strutturato per codice_contratto
    #     """
    #     result_structure = {}
        
    #     # Organizza i record originali per codice_contratto
    #     original_by_contract = defaultdict(list)
    #     for record in original_data:
    #         codice_contratto = record.get('codice_contratto')
    #         if codice_contratto is not None:
    #             # Converte in int se necessario
    #             if isinstance(codice_contratto, str) and codice_contratto.isdigit():
    #                 codice_contratto = int(codice_contratto)
    #             original_by_contract[codice_contratto].append(record)
        
    #     for codice_contratto, types_data in aggregated_data.items():
    #         # Calcola i totali generali per il contratto
    #         durata_generale = 0
    #         costo_generale = 0.0
    #         costo_generale_with_markup = 0.0
    #         chiamate_totali = 0
            
    #         # Record di esempio per i metadati del contratto
    #         contract_sample = None
    #         aggregated_records = []
            
    #         # Crea record per ogni tipo di chiamata
    #         for tipo_chiamata, agg_data in types_data.items():
    #             sample_record = agg_data['record_sample']
                
    #             if contract_sample is None:
    #                 contract_sample = sample_record
                
    #             # Crea record aggregato per tipo chiamata
    #             type_record = {
    #                 'codice_contratto': codice_contratto,
    #                 'tipo_chiamata': tipo_chiamata,
    #                 'durata_secondi_totale': agg_data['durata_secondi_totale'],
    #                 'costo_euro_totale': round(agg_data['costo_euro_totale'], 3),
    #                 'costo_euro_totale_with_markup': round(agg_data['costo_euro_totale_with_markup'], 3),
    #                 'numero_chiamate': agg_data['numero_chiamate'],
    #                 'aggregation_type': 'per_tipo_chiamata',
                    
    #                 # Mantieni alcuni metadati dal record di esempio
    #                 'cliente_finale': sample_record.get('cliente_finale', ''),
    #                 'numero_cliente': sample_record.get('numero_cliente', ''),
    #                 'codice_servizio': sample_record.get('codice_servizio', ''),
    #                 'comune': sample_record.get('comune', ''),
    #                 'operatore': sample_record.get('operatore', ''),
                    
    #                 # Metadati di aggregazione
    #                 '_aggregated_at': sample_record.get('_processed_at', ''),
    #                 '_source_files': list(set([sample_record.get('_source_file', '')])),
    #             }
                
    #             aggregated_records.append(type_record)
                
    #             # Accumula per il totale generale
    #             durata_generale += agg_data['durata_secondi_totale']
    #             costo_generale += agg_data['costo_euro_totale']
    #             costo_generale_with_markup += agg_data['costo_euro_totale_with_markup']
    #             chiamate_totali += agg_data['numero_chiamate']
            
    #         # Crea record aggregato generale per il contratto
    #         if contract_sample:
    #             general_record = {
    #                 'codice_contratto': codice_contratto,
    #                 'tipo_chiamata': 'TOTALE_GENERALE',
    #                 'durata_secondi_generale': durata_generale,
    #                 'costo_euro_generale': round(costo_generale, 3),
    #                 'costo_euro_generale_with_markup': round(costo_generale_with_markup, 3),
    #                 'numero_chiamate_totali': chiamate_totali,
    #                 'numero_tipi_chiamata': len(types_data),
    #                 'aggregation_type': 'totale_generale',
                    
    #                 # Metadati del contratto
    #                 'cliente_finale': contract_sample.get('cliente_finale', ''),
    #                 'numero_cliente': contract_sample.get('numero_cliente', ''),
    #                 'codice_servizio': contract_sample.get('codice_servizio', ''),
    #                 'comune': contract_sample.get('comune', ''),
                    
    #                 # Metadati di aggregazione
    #                 '_aggregated_at': contract_sample.get('_processed_at', ''),
    #                 '_source_files': list(set([contract_sample.get('_source_file', '')])),
    #             }
                
    #             aggregated_records.append(general_record)
            
    #         # Crea la struttura per questo contratto
    #         contract_key = str(codice_contratto)
    #         result_structure[contract_key] = {
    #             'aggregated_records': aggregated_records,
    #             'lista_chiamate': original_by_contract[codice_contratto],
    #             'contract_info': {
    #                 'codice_contratto': codice_contratto,
    #                 'cliente_finale': contract_sample.get('cliente_finale', '') if contract_sample else '',
    #                 'numero_cliente': contract_sample.get('numero_cliente', '') if contract_sample else '',
    #                 'codice_servizio': contract_sample.get('codice_servizio', '') if contract_sample else '',
    #                 'comune': contract_sample.get('comune', '') if contract_sample else '',
    #                 'durata_totale_secondi': durata_generale,
    #                 'costo_totale_euro': round(costo_generale, 3),
    #                 'costo_totale_euro_with_markup': round(costo_generale_with_markup, 3),
    #                 'numero_chiamate_totali': chiamate_totali,
    #                 'numero_tipi_chiamata': len(types_data)
    #             }
    #         }
        
    #     return result_structure
    
    def aggregate_cdr_data(self, files: Union[str, List[str]] = None, output_file: str = None) -> Dict[str, Any]:
        """
        Aggrega i dati CDR dai file specificati
        
        Args:
            files: File JSON singolo o lista di file JSON (se None usa il default)
            output_file: File di output per salvare i risultati aggregati (se None usa il default)
            
        Returns:
            Dizionario con i risultati aggregati strutturati per codice_contratto
        """
        # Nomi file predefiniti
        # default_input_file = "cdr_data.json"
        # default_output_file = "cdr_aggregated.json"
              
        data_mese = self.extract_year_month_from_filename_flexible(files)
        anno = data_mese[0]
        mese = data_mese[1]

        if output_file is None:
            nome_file = str(AGGREGATE_FILES)+str(anno)+'_'+str(mese)+'.json'
            output_file = Path(ANALYTICS_OUTPUT_FOLDER) / anno / nome_file
            output_file.parent.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Usando file di output predefinito: {output_file}")
        
        # Carica tutti i dati
        all_data = self._load_all_data(files)
        
        if not all_data:
            self.logger.warning("Nessun dato da aggregare")
            return {
                'contracts': {},
                'statistics': {
                    'total_input_records': 0,
                    'total_contracts': 0,
                    'call_types_found': [],
                    'total_duration': 0,
                    'total_cost': 0.0
                }
            }
        
        # Aggrega i dati
        self.logger.info("Inizio aggregazione dati...")
        aggregated_data = self._aggregate_by_contract_and_type(all_data)
        
        # Crea la struttura finale organizzata per contratto
        contracts_structure = self._create_contract_structure(aggregated_data, all_data)
        
        # Calcola statistiche
        call_types = set()
        total_duration = 0
        total_cost = 0.0

        # Dizionari per aggregare per tipo di chiamata
        call_type_durations = {}
        call_type_costs = {}

        for contract_data in contracts_structure.values():
            contract_info = contract_data['contract_info']
            total_duration += contract_info['durata_totale_secondi']
            total_cost += contract_info['costo_totale_euro']
            
            # Aggrega i dati per tipo di chiamata
            for record in contract_data['aggregated_records']:
                if record.get('aggregation_type') == 'per_tipo_chiamata':
                    call_type = record['tipo_chiamata']
                    call_types.add(call_type)
                    
                    # Aggrega durata per tipo di chiamata
                    if call_type not in call_type_durations:
                        call_type_durations[call_type] = 0
                    call_type_durations[call_type] += record.get('durata_secondi_totale', 0)
                    
                    # Aggrega costi per tipo di chiamata
                    if call_type not in call_type_costs:
                        call_type_costs[call_type] = 0.0
                    call_type_costs[call_type] += record.get('costo_euro_totale', 0.0)

        # Arrotonda i costi per tipo di chiamata
        call_type_costs = {k: round(v, 3) for k, v in call_type_costs.items()}

        statistics = {
            'total_input_records': len(all_data),
            'total_contracts': len(contracts_structure),
            'call_types_found': sorted(list(call_types)),
            'total_duration': total_duration,
            'total_cost': round(total_cost, 3),
            'call_type_statistics': {
                'durations_by_type': call_type_durations,
                'costs_by_type': call_type_costs
            }
        }
        
        # Prepara il risultato finale
        result = {
            'contracts': contracts_structure,
            'statistics': statistics,
            'file_name': str(output_file)
        }
        
        # Salva i risultati
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Risultati aggregati salvati in {output_file}")
        except Exception as e:
            self.logger.error(f"Errore nel salvataggio in {output_file}: {e}")
        
        # Log statistiche
        self.logger.info(f"Aggregazione completata:")
        self.logger.info(f"  - Record originali: {statistics['total_input_records']}")
        self.logger.info(f"  - Contratti processati: {statistics['total_contracts']}")
        self.logger.info(f"  - Tipi chiamata trovati: {len(statistics['call_types_found'])}")
        
        return result

    
    def split_aggregate_to_contracts(self,source_file_path, output_directory=None):
        """
        Divide un file JSON aggregato in file separati per ogni contratto.
        
        Args:
            source_file_path (str): Percorso del file JSON sorgente
            output_directory (str, optional): Directory di output. Se None, usa una cartella 'contract_reports'
        
        Returns:
            dict: Dizionario con risultati dell'operazione
        """
        
        try:
            # Verifica esistenza file sorgente
            if not os.path.exists(source_file_path):
                raise FileNotFoundError(f"File sorgente non trovato: {source_file_path}")
            
            # Leggi il file JSON
            with open(source_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Verifica struttura dati
            if 'contracts' not in data:
                raise ValueError("Il file JSON non contiene la chiave 'contracts'")
            
            contracts = data['contracts']
            
            data_mese = self.extract_year_month_from_filename_flexible(source_file_path)
            anno = data_mese[0]
            mese = data_mese[1]

            # Crea directory di output se non specificata
            if output_directory is None:
                base_dir = Path(ANALYTICS_OUTPUT_FOLDER) / str(anno)
                output_directory = os.path.join(base_dir, str(mese)+'_detail')
            
            # Crea la directory se non esiste
            os.makedirs(output_directory, exist_ok=True)
            
            results = {
                'success': True,
                'files_created': [],
                'errors': [],
                'total_contracts': len(contracts),
                'statistics': data.get('statistics', {}),
                'timestamp': datetime.now().isoformat()
            }
            
            # Elabora ogni contratto
            for contract_id, contract_data in contracts.items():
                try:
                    # Crea il nome del file
                    filename = f"{contract_id}_reports.json"
                    output_path = os.path.join(output_directory, filename)
                    
                    # Prepara i dati del contratto con metadati aggiuntivi
                    contract_report = {
                        'contract_id': int(contract_id),
                        'generated_at': datetime.now().isoformat(),
                        'source_file': os.path.basename(source_file_path),
                        'contract_info': contract_data.get('contract_info', {}),
                        'aggregated_records': contract_data.get('aggregated_records', []),
                        'lista_chiamate': contract_data.get('lista_chiamate', []),
                        'summary': {
                            'numero_chiamate_totali': contract_data.get('contract_info', {}).get('numero_chiamate_totali', 0),
                            'durata_totale_secondi': contract_data.get('contract_info', {}).get('durata_totale_secondi', 0),
                            'costo_totale_euro': contract_data.get('contract_info', {}).get('costo_totale_euro', 0),
                            'costo_totale_euro_with_markup': contract_data.get('contract_info', {}).get('costo_totale_euro_with_markup', 0),
                            'numero_tipi_chiamata': contract_data.get('contract_info', {}).get('numero_tipi_chiamata', 0),
                            'cliente_finale': contract_data.get('contract_info', {}).get('cliente_finale', ''),
                            'numero_cliente': contract_data.get('contract_info', {}).get('numero_cliente', '')
                        }
                    }
                    
                    # Scrivi il file JSON
                    with open(output_path, 'w', encoding='utf-8') as output_file:
                        json.dump(contract_report, output_file, indent=2, ensure_ascii=False)
                    
                    results['files_created'].append({
                        'contract_id': contract_id,
                        'filename': filename,
                        'path': output_path,
                        'size_bytes': os.path.getsize(output_path),
                        'calls_count': len(contract_data.get('lista_chiamate', [])),
                        'client': contract_data.get('contract_info', {}).get('cliente_finale', 'N/A')
                    })
                    
                    logging.info(f"Creato file per contratto {contract_id}: {filename}")
                    
                except Exception as e:
                    error_msg = f"Errore durante l'elaborazione del contratto {contract_id}: {str(e)}"
                    results['errors'].append({
                        'contract_id': contract_id,
                        'error': error_msg
                    })
                    logging.error(error_msg)
            
            # Log dei risultati
            logging.info(f"Elaborazione completata: {len(results['files_created'])} file creati, {len(results['errors'])} errori")
            
            # Crea un file di riepilogo
            summary_path = os.path.join(output_directory, '_elaboration_summary.json')
            with open(summary_path, 'w', encoding='utf-8') as summary_file:
                json.dump(results, summary_file, indent=2, ensure_ascii=False)
            
            return results
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            logging.error(f"Errore durante l'elaborazione: {str(e)}")
            return error_result
         

class CDRContractsGenerator:
    def __init__(self, source_file_path: str):
        """
        Inizializza il generatore di contratti CDR
        
        Args:
            source_file_path: Percorso del file CDR JSON da processare
        """
        self.source_file_path = Path(ARCHIVE_DIRECTORY) / CDR_JSON_FOLDER / source_file_path
        self.contracts_data = {}
        self.metadata = {}
        self.output_path = Path(ARCHIVE_DIRECTORY) / CONTACTS_FOLDER / CONTACT_FILE
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configura il logger per l'aggregatore"""
        logger = logging.getLogger('CDRAggregator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def extract_year_month_from_filename(filename):
        """
        Estrae anno e mese da un nome file nel formato 'cdr_data_YYYY_MM.json'.
        
        Args:
            filename (str): Nome del file o percorso completo (es: "cdr_data_2025_07.json")
            
        Returns:
            str: Anno e mese nel formato "YYYY_MM" (es: "2025_07")
            None: Se il formato non è riconosciuto o non valido
            
        Examples:
            >>> extract_year_month_from_filename("cdr_data_2025_07.json")
            "2025_07"
            >>> extract_year_month_from_filename("/path/to/cdr_data_2024_12.json")
            "2024_12"
            >>> extract_year_month_from_filename("invalid_file.json")
            None
        """
        try:
            # Estrae solo il nome del file se è un percorso completo
            basename = os.path.basename(filename)
            
            # Pattern regex per identificare il formato cdr_data_YYYY_MM.json
            # Cerca: cdr_data_ seguito da 4 cifre (anno), underscore, 2 cifre (mese), .json
            pattern = r'cdr_data_(\d{4})_(\d{2})\.json$'
            
            match = re.search(pattern, basename, re.IGNORECASE)
            
            if not match:
                print(f"Formato filename non riconosciuto: {basename}")
                return None
            
            year = match.group(1)
            month = match.group(2)
            
            # Validazione base del mese (01-12)
            month_int = int(month)
            if month_int < 1 or month_int > 12:
                print(f"Mese non valido: {month}")
                return None
            
            # Validazione base dell'anno (deve essere ragionevole)
            year_int = int(year)
            if year_int < 2000 or year_int > 2100:
                print(f"Anno non valido: {year}")
                return None
            
            return f"{year}_{month}"
            
        except Exception as e:
            print(f"Errore nell'elaborazione del filename '{filename}': {e}")
            return None
                
    def load_cdr_data(self) -> List[Dict]:
        """
        Carica i dati CDR dal file JSON
        
        Returns:
            Lista dei record CDR
        """
        try:
            with open(self.source_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                print(f"Caricati {len(data)} record CDR da {self.source_file_path}")
                return data
        except FileNotFoundError:
            raise FileNotFoundError(f"File non trovato: {self.source_file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Errore nel parsing JSON: {e}")
    
    def load_existing_contracts(self) -> Dict:
        """
        Carica i contratti esistenti dal file contracts.json se presente
        
        Returns:
            Dizionario con i contratti esistenti, vuoto se file non esiste
        """
        try:
            if self.output_path.exists():
                with open(self.output_path, 'r', encoding='utf-8') as file:
                    existing_data = json.load(file)
                    existing_contracts = existing_data.get('contracts', {})
                    existing_metadata = existing_data.get('metadata', {})
                    print(f"Caricati {len(existing_contracts)} contratti esistenti")
                    return existing_data
            else:
                print("Nessun file contracts.json esistente trovato. Creazione nuovo file.")
                return {}
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Errore nel caricamento file esistente: {e}. Creazione nuovo file.")
            return {}
        
    def extract_contracts_from_cdr(self, cdr_records: List[Dict]) -> Dict:
        """
        Estrae i contratti dai record CDR
        
        Args:
            cdr_records: Lista dei record CDR
            
        Returns:
            Dizionario con i contratti estratti
        """
        contracts = {}
        contract_stats = defaultdict(lambda: {
            'phone_numbers': set(),
            'files': set(),
            'first_seen': None,
            'last_seen': None,
            'total_calls': 0,
            'cliente_finale': None
        })
        
        # Processa ogni record CDR
        for record in cdr_records:
            contract_code = str(record.get('codice_contratto', ''))
            if not contract_code:
                continue
                
            stats = contract_stats[contract_code]
            
            # Aggiorna statistiche
            stats['phone_numbers'].add(record.get('numero_cliente', ''))
            stats['files'].add(record.get('_source_file', ''))
            stats['total_calls'] += 1
            
            # Cliente finale (prende l'ultimo visto)
            if record.get('cliente_finale'):
                stats['cliente_finale'] = record.get('cliente_finale')
            
            # Date di primo e ultimo avvistamento
            processed_date = record.get('_processed_at')
            if processed_date:
                if not stats['first_seen'] or processed_date < stats['first_seen']:
                    stats['first_seen'] = processed_date
                if not stats['last_seen'] or processed_date > stats['last_seen']:
                    stats['last_seen'] = processed_date
        
        # Converte le statistiche in formato contracts.json
        for contract_code, stats in contract_stats.items():
            # Estrae nome contratto dal cliente_finale
            contract_name = self._extract_contract_name(stats['cliente_finale'])
            
            contracts[contract_code] = {
                "contract_code": contract_code,
                "contract_name": None,
                "odoo_client_id": "",  # Da compilare manualmente
                "first_seen_file": sorted(list(stats['files']))[0] if stats['files'] else "",
                "first_seen_date": stats['first_seen'] or "",
                "last_seen_file": sorted(list(stats['files']))[-1] if stats['files'] else "",
                "last_seen_date": stats['last_seen'] or "",
                "total_calls_found": stats['total_calls'],
                "files_found_in": sorted(list(stats['files'])),
                "notes": "",
                "phone_numbers": sorted(list(stats['phone_numbers'])),
                "total_unique_numbers": len(stats['phone_numbers']),
                "cliente_finale_comune": stats['cliente_finale'] or "",
                "contract_type": "",  # Da compilare manualmente
                "last_updated": datetime.now().isoformat()
            }
        
        return contracts
    
    def merge_contracts(self, existing_contracts: Dict, new_contracts: Dict) -> Dict:
        """
        Merge dei contratti esistenti con quelli nuovi
        
        Args:
            existing_contracts: Contratti già presenti nel file
            new_contracts: Contratti estratti dai nuovi dati CDR
            
        Returns:
            Dizionario con contratti uniti
        """
        merged_contracts = existing_contracts.copy()
        new_contracts_added = 0
        updated_contracts = 0
        
        for contract_code, new_contract in new_contracts.items():
            if contract_code in merged_contracts:
                # Contratto esistente: aggiorna solo i dati calcolati
                existing_contract = merged_contracts[contract_code]
                
                # Mantieni i dati manuali esistenti
                preserved_fields = {
                    'contract_name': existing_contract.get('contract_name'),
                    'odoo_client_id': existing_contract.get('odoo_client_id', ''),
                    'notes': existing_contract.get('notes', ''),
                    'contract_type': existing_contract.get('contract_type', '')
                }
                
                # Merge delle liste e dati calcolati
                merged_phone_numbers = set(existing_contract.get('phone_numbers', []))
                merged_phone_numbers.update(new_contract['phone_numbers'])
                
                merged_files = set(existing_contract.get('files_found_in', []))
                merged_files.update(new_contract['files_found_in'])
                
                # Aggiorna il contratto esistente
                merged_contracts[contract_code].update({
                    # Mantieni i campi manuali se valorizzati, altrimenti usa i nuovi
                    'contract_name': preserved_fields['contract_name'] if preserved_fields['contract_name'] else new_contract['contract_name'],
                    'odoo_client_id': preserved_fields['odoo_client_id'],
                    'notes': preserved_fields['notes'],
                    'contract_type': preserved_fields['contract_type'],
                    
                    # Aggiorna i campi calcolati
                    'phone_numbers': sorted(list(merged_phone_numbers)),
                    'total_unique_numbers': len(merged_phone_numbers),
                    'files_found_in': sorted(list(merged_files)),
                    'total_calls_found': existing_contract.get('total_calls_found', 0) + new_contract['total_calls_found'],
                    
                    # Aggiorna date se più recenti
                    'first_seen_date': min(existing_contract.get('first_seen_date', new_contract['first_seen_date']), new_contract['first_seen_date']) if existing_contract.get('first_seen_date') else new_contract['first_seen_date'],
                    'first_seen_file': existing_contract.get('first_seen_file', new_contract['first_seen_file']),
                    'last_seen_date': max(existing_contract.get('last_seen_date', new_contract['last_seen_date']), new_contract['last_seen_date']) if existing_contract.get('last_seen_date') else new_contract['last_seen_date'],
                    'last_seen_file': new_contract['last_seen_file'],  # Prendi sempre l'ultimo
                    
                    # Aggiorna cliente finale se non presente o vuoto
                    'cliente_finale_comune': existing_contract.get('cliente_finale_comune') if existing_contract.get('cliente_finale_comune') else new_contract['cliente_finale_comune'],
                    
                    'last_updated': datetime.now().isoformat()
                })
                
                updated_contracts += 1
                print(f"📝 Aggiornato contratto esistente: {contract_code}")
                
            else:
                # Nuovo contratto: aggiungi completamente
                merged_contracts[contract_code] = new_contract
                new_contracts_added += 1
                print(f"➕ Aggiunto nuovo contratto: {contract_code}")
        
        print(f"📊 Merge completato: {new_contracts_added} nuovi, {updated_contracts} aggiornati")
        return merged_contracts
    
    def _extract_contract_name(self, cliente_finale: str) -> str:
        """
        Estrae il nome del contratto dal campo cliente_finale
        
        Args:
            cliente_finale: Campo cliente finale completo
            
        Returns:
            Nome contratto estratto
        """
        if not cliente_finale:
            return ""
        
        # Rimuove la città (parte dopo l'ultimo " - ")
        if " - " in cliente_finale:
            name_part = cliente_finale.rsplit(" - ", 1)[0]
        else:
            name_part = cliente_finale
        
        return name_part.strip()
    
    def generate_metadata(self, contracts: Dict, cdr_records: List[Dict], existing_metadata: Dict = None) -> Dict:
        """
        Genera i metadati per il file contracts.json
        
        Args:
            contracts: Dizionario dei contratti
            cdr_records: Record CDR originali
            existing_metadata: Metadati esistenti se presenti
            
        Returns:
            Metadati del file
        """
        now = datetime.now().isoformat()
        
        # Conta i file unici processati
        files_processed = set()
        for record in cdr_records:
            if record.get('_source_file'):
                files_processed.add(record['_source_file'])
        
        if existing_metadata:
            # Aggiorna metadati esistenti
            extraction_runs = existing_metadata.get('extraction_runs', 0) + 1
            manual_updates = existing_metadata.get('manual_updates', 0)
            created_date = existing_metadata.get('created_date', now)
        else:
            # Nuovi metadati
            extraction_runs = 1
            manual_updates = 0
            created_date = now
        
        return {
            "version": "1.0",
            "created_date": created_date,
            "last_updated": now,
            "total_contracts": len(contracts),
            "extraction_source": "CDR_File_Processing",
            "manual_updates": manual_updates,
            "extraction_runs": extraction_runs,
            "last_extraction_added_contracts": len([c for c in contracts.values() if c.get('last_updated', '') == now or not existing_metadata]),
            "description": "Configurazione codici contratto estratti da file CDR"
        }
    
    def generate_last_extraction_info(self, contracts: Dict, cdr_records: List[Dict], existing_contracts_count: int = 0) -> Dict:
        """
        Genera le informazioni sull'ultima estrazione
        
        Args:
            contracts: Dizionario dei contratti
            cdr_records: Record CDR originali
            existing_contracts_count: Numero di contratti esistenti prima del merge
            
        Returns:
            Informazioni ultima estrazione
        """
        files_processed = set()
        for record in cdr_records:
            if record.get('_source_file'):
                files_processed.add(record['_source_file'])
        
        new_contracts_added = len(contracts) - existing_contracts_count
        
        return {
            "timestamp": datetime.now().isoformat(),
            "files_processed": len(files_processed),
            "records_processed": len(cdr_records),
            "new_contracts_added": max(0, new_contracts_added),
            "existing_contracts_preserved": existing_contracts_count,
            "total_contracts_after": len(contracts)
        }
    
    def generate_contracts_json(self) -> Dict:
        """
        Genera il file contracts.json completo con merge dei dati esistenti
        
        Returns:
            Struttura completa del file contracts.json
        """
        print("🔄 Inizio generazione contracts.json con merge...")
        
        # Carica dati esistenti
        existing_data = self.load_existing_contracts()
        existing_contracts = existing_data.get('contracts', {})
        existing_metadata = existing_data.get('metadata', {})
        existing_contracts_count = len(existing_contracts)
        
        # Carica dati CDR
        cdr_records = self.load_cdr_data()
        
        # Estrae contratti dai nuovi dati
        new_contracts = self.extract_contracts_from_cdr(cdr_records)
        print(f"📊 Estratti {len(new_contracts)} contratti dai dati CDR")
        
        # Merge dei contratti
        merged_contracts = self.merge_contracts(existing_contracts, new_contracts)
        
        # Genera metadata aggiornati
        metadata = self.generate_metadata(merged_contracts, cdr_records, existing_metadata)
        
        # Genera info ultima estrazione
        last_extraction = self.generate_last_extraction_info(merged_contracts, cdr_records, existing_contracts_count)
        
        # Struttura finale
        contracts_json = {
            "metadata": metadata,
            "contracts": merged_contracts,
            "last_extraction": last_extraction
        }
        
        return contracts_json
    
    # def save_contracts_json(self) -> None:
    #     """
    #     Salva il file contracts.json con merge dei dati esistenti
    #     """
        
    #     try:
    #         if self.output_path.exists():
    #             backup_file = Path(str(self.output_path) + f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    #             import shutil
    #             shutil.copy2(self.output_path, backup_file)
    #             self.logger.info(f"Backup categorie creato: {backup_file}")
            
    #         contracts_data = {}
    #         contracts_data = self.generate_contracts_json()
            
    #         with open(self.output_path, 'w', encoding='utf-8') as f:
    #             json.dump(contracts_data, f, indent=2, ensure_ascii=False)
            
    #         self.logger.info(f"Categorie salvate in {self.output_path}")
    #         return True
            
    #     except Exception as e:
    #         self.logger.error(f"Errore salvataggio categorie: {e}")
    #         return False
        
    #     # contracts_data = self.generate_contracts_json()
        
    #     # # Crea directory se non esiste
    #     # self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
    #     # with open(self.output_path, 'w', encoding='utf-8') as file:
    #     #     json.dump(contracts_data, file, indent=2, ensure_ascii=False)
        
    #     # print(f"✅ File contracts.json salvato in: {self.output_path}")
    #     # print(f"📊 Contratti totali: {len(contracts_data['contracts'])}")
    #     # print(f"📈 Record processati: {contracts_data['last_extraction']['records_processed']}")
    #     # print(f"➕ Nuovi contratti aggiunti: {contracts_data['last_extraction']['new_contracts_added']}")
    #     # print(f"📝 Contratti esistenti preservati: {contracts_data['last_extraction']['existing_contracts_preserved']}")
        
    #     # return contracts_data

    def save_contracts_json(self) -> bool:
        """
        Salva il file contracts.json con merge dei dati esistenti.
        Mantiene al massimo 5 file di backup.
        """
        import shutil
        import glob

        try:
            # Se esiste il file, crea backup
            if self.output_path.exists():
                backup_file = Path(str(self.output_path) + f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                shutil.copy2(self.output_path, backup_file)
                self.logger.info(f"Backup categorie creato: {backup_file}")

                # ✅ Limita i backup a massimo 5
                backup_pattern = str(self.output_path) + ".backup.*"
                backup_files = sorted(
                    Path(p) for p in glob.glob(backup_pattern)
                )
                if len(backup_files) > 5:
                    files_to_delete = backup_files[:-5]
                    for old_file in files_to_delete:
                        try:
                            old_file.unlink()
                            self.logger.info(f"Backup vecchio eliminato: {old_file}")
                        except Exception as e:
                            self.logger.warning(f"Impossibile eliminare {old_file}: {e}")

            # Genera dati da salvare
            contracts_data = self.generate_contracts_json()

            # Salva file JSON principale
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(contracts_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Categorie salvate in {self.output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Errore salvataggio categorie: {e}")
            return False

class JSONFileManager:
    """
    Classe per la trasformazione dei dati CDR aggregati.
    
    Trasforma i dati raggruppando per codice_contratto con:
    - Totali generali a livello contratto
    - Dettagli per ogni tipo di chiamata
    """
    
    def __init__(self):
        """
        Inizializza il trasformatore.
        
        Args:
            logger: Logger opzionale per il tracking delle operazioni
        """
        self.logger = self._setup_logger()
        self._last_transformation_stats = {}


    def _setup_logger(self) -> logging.Logger:
        """Configura il logger per il processore"""
        logger = logging.getLogger('CDRProcessor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def transform_from_dict(self, input_data: Dict) -> Dict:
        """
        Trasforma i dati CDR da dizionario Python raggruppando per codice_contratto.
        """
        try:
            self.logger.debug("Inizio trasformazione dati CDR raggruppati per contratto")
            
            # Validazione input
            if not isinstance(input_data, dict):
                raise ValueError("I dati di input devono essere un dizionario")
            
            if "contracts" not in input_data:
                raise ValueError("Sezione 'contracts' mancante nei dati di input")
            
            # Inizializza la struttura di output
            output = {
                "data": [],
                "statistics": input_data.get("statistics", {})
            }
            
            # Estrae i contratti dalla sezione "contracts"
            contracts = input_data.get("contracts", {})
            
            # Contatori per statistiche di trasformazione
            total_contracts = len(contracts)
            total_records_processed = 0
            skipped_records = 0
            
            # *** AGGIUNGI QUI: Variabili per calcolare i totali reali con markup ***
            total_cost_with_markup_sum = 0.0
            costs_by_type_with_markup = {}
            
            # Dizionario per raggruppare i dati per codice_contratto
            contracts_data = {}
            
            # Itera attraverso ogni contratto
            for contract_id, contract_data in contracts.items():
                self.logger.debug(f"Elaborazione contratto {contract_id}")
                
                # Estrae i record aggregati
                aggregated_records = contract_data.get("aggregated_records", [])
                
                for record in aggregated_records:
                    total_records_processed += 1
                    
                    codice_contratto = record.get("codice_contratto")
                    aggregation_type = record.get("aggregation_type")
                    
                    # Inizializza il record del contratto se non esiste
                    if codice_contratto not in contracts_data:
                        contracts_data[codice_contratto] = {
                            "codice_contratto": codice_contratto,
                            "cliente_finale": record.get("cliente_finale"),
                            # Inizializza i totali generali (verranno sovrascritti dai dati reali)
                            "durata_secondi_totale": 0,
                            "costo_euro_totale": 0.0,
                            "costo_euro_totale_with_markup": 0.0,
                            "numero_chiamate": 0,
                            "tipi_chiamata": {}
                        }
                    
                    # Se è un record "TOTALE_GENERALE", aggiorna i totali del contratto
                    if aggregation_type == "totale_generale":
                        contracts_data[codice_contratto].update({
                            "durata_secondi_totale": record.get("durata_secondi_generale", 0),
                            "costo_euro_totale": record.get("costo_euro_generale", 0.0),
                            "costo_euro_totale_with_markup": record.get("costo_euro_generale_with_markup", 0.0),
                            "numero_chiamate": record.get("numero_chiamate_totali", 0)
                        })
                        
                        # *** AGGIUNGI QUI: Somma al totale generale con markup ***
                        total_cost_with_markup_sum += record.get("costo_euro_generale_with_markup", 0.0)
                        continue
                    
                    # Altrimenti è un record per tipo di chiamata
                    tipo_chiamata = record.get("tipo_chiamata")
                    costo_with_markup = record.get("costo_euro_totale_with_markup", 0.0)
                    
                    # *** AGGIUNGI QUI: Somma per tipo di chiamata con markup ***
                    if tipo_chiamata:
                        if tipo_chiamata not in costs_by_type_with_markup:
                            costs_by_type_with_markup[tipo_chiamata] = 0.0
                        costs_by_type_with_markup[tipo_chiamata] += costo_with_markup
                    
                    # Aggiunge i dati per questo tipo di chiamata
                    contracts_data[codice_contratto]["tipi_chiamata"][tipo_chiamata] = {
                        "durata_secondi_totale": record.get("durata_secondi_totale", 0),
                        "costo_euro_totale": record.get("costo_euro_totale", 0.0),
                        "costo_euro_totale_with_markup": costo_with_markup,
                        "numero_chiamate": record.get("numero_chiamate", 0)
                    }
            
            # *** AGGIUNGI QUI: Aggiorna le statistiche con i valori reali calcolati ***
            if "statistics" in output and isinstance(output["statistics"], dict):
                # Aggiorna total_cost_with_markup con la somma reale
                output["statistics"]["total_cost_with_markup"] = round(total_cost_with_markup_sum, 2)
                
                # Aggiorna call_type_statistics con i costi reali per tipo
                if "call_type_statistics" in output["statistics"]:
                    call_type_stats = output["statistics"]["call_type_statistics"]
                    
                    # Arrotonda i valori per tipo
                    costs_by_type_with_markup_rounded = {
                        call_type: round(cost, 2) 
                        for call_type, cost in costs_by_type_with_markup.items()
                    }
                    
                    call_type_stats["costs_by_type_with_markup"] = costs_by_type_with_markup_rounded
            
            # Converte in lista per l'output finale
            output["data"] = list(contracts_data.values())
            
            # Salva statistiche di trasformazione
            self._last_transformation_stats = {
                "total_contracts": total_contracts,
                "total_records_processed": total_records_processed,
                "contracts_in_output": len(output["data"]),
                "skipped_records": skipped_records
            }
            
            self.logger.info(
                f"Trasformazione completata: {total_contracts} contratti, "
                f"{len(output['data'])} contratti in output, "
                f"{skipped_records} record saltati"
            )
            
            return output
            
        except Exception as e:
            self.logger.error(f"Errore durante la trasformazione: {str(e)}")
            raise
        
    
    def transform_from_dict_flat(self, input_data: Dict) -> Dict:
        """
        Versione alternativa che crea una struttura "piatta" con campi separati per tipo.
        Mantiene i totali generali + campi specifici per tipo con prefisso.
        
        Args:
            input_data: Dizionario contenente i dati CDR aggregati originali
            
        Returns:
            dict: Dizionario con struttura piatta
        """
        try:
            self.logger.debug("Inizio trasformazione dati CDR (versione piatta)")
            
            # Validazione input
            if not isinstance(input_data, dict):
                raise ValueError("I dati di input devono essere un dizionario")
            
            if "contracts" not in input_data:
                raise ValueError("Sezione 'contracts' mancante nei dati di input")
            
            # Inizializza la struttura di output
            output = {
                "data": [],
                "statistics": input_data.get("statistics", {})
            }
            
            # Estrae i contratti dalla sezione "contracts"
            contracts = input_data.get("contracts", {})
            
            # Dizionario per raggruppare i dati per codice_contratto
            contracts_data = {}
            
            # Itera attraverso ogni contratto
            for contract_id, contract_data in contracts.items():
                self.logger.debug(f"Elaborazione contratto {contract_id}")
                
                # Estrae i record aggregati
                aggregated_records = contract_data.get("aggregated_records", [])
                
                for record in aggregated_records:
                    codice_contratto = record.get("codice_contratto")
                    aggregation_type = record.get("aggregation_type")
                    
                    # Inizializza il record del contratto se non esiste
                    if codice_contratto not in contracts_data:
                        contracts_data[codice_contratto] = {
                            "codice_contratto": codice_contratto,
                            "cliente_finale": record.get("cliente_finale"),
                            # Totali generali
                            "durata_secondi_totale": 0,
                            "costo_euro_totale": 0.0,
                            "costo_euro_totale_with_markup": 0.0,
                            "numero_chiamate": 0
                        }
                    
                    # Se è un record "TOTALE_GENERALE", aggiorna i totali del contratto
                    if aggregation_type == "totale_generale":
                        contracts_data[codice_contratto].update({
                            "durata_secondi_totale": record.get("durata_secondi_generale", 0),
                            "costo_euro_totale": record.get("costo_euro_generale", 0.0),
                            "costo_euro_totale_with_markup": record.get("costo_euro_generale_with_markup", 0.0),
                            "numero_chiamate": record.get("numero_chiamate_totali", 0)
                        })
                        continue
                    
                    # Altrimenti è un record per tipo di chiamata
                    tipo_chiamata = record.get("tipo_chiamata")
                    
                    # Aggiunge i dati per questo tipo di chiamata con prefisso
                    prefix = tipo_chiamata.lower()
                    contracts_data[codice_contratto].update({
                        f"{prefix}_durata_secondi_totale": record.get("durata_secondi_totale", 0),
                        f"{prefix}_costo_euro_totale": record.get("costo_euro_totale", 0.0),
                        f"{prefix}_costo_euro_totale_with_markup": record.get("costo_euro_totale_with_markup", 0.0),
                        f"{prefix}_numero_chiamate": record.get("numero_chiamate", 0)
                    })
            
            # Converte in lista per l'output finale
            output["data"] = list(contracts_data.values())
            
            return output
            
        except Exception as e:
            self.logger.error(f"Errore durante la trasformazione piatta: {str(e)}")
            raise
    
    def transform_from_file(self, file_path: Union[str, Path], flat_format: bool = False) -> Dict:
        """
        Trasforma i dati CDR da file JSON.
        
        Args:
            file_path: Percorso del file JSON contenente i dati CDR
            flat_format: Se True usa la struttura piatta, altrimenti struttura nidificata
            
        Returns:
            dict: Dizionario con struttura semplificata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File non trovato: {file_path}")
        
        self.logger.info(f"Caricamento dati da: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                input_data = json.load(file)
            
            if flat_format:
                return self.transform_from_dict_flat(input_data)
            else:
                return self.transform_from_dict(input_data)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Errore nel parsing JSON: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Errore nel caricamento file: {str(e)}")
            raise
    
    def transform_from_string(self, json_string: str, flat_format: bool = False) -> Dict:
        """
        Trasforma i dati CDR da stringa JSON.
        
        Args:
            json_string: Stringa contenente i dati JSON CDR
            flat_format: Se True usa la struttura piatta, altrimenti struttura nidificata
            
        Returns:
            dict: Dizionario con struttura semplificata
            
        Raises:
            ValueError: Se la stringa JSON non è valida
            Exception: Per altri errori durante la trasformazione
        """
        if not json_string or not json_string.strip():
            raise ValueError("La stringa JSON non può essere vuota")
        
        self.logger.info("Trasformazione dati da stringa JSON")
        
        try:
            input_data = json.loads(json_string)
            
            if flat_format:
                return self.transform_from_dict_flat(input_data)
            else:
                return self.transform_from_dict(input_data)
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Errore nel parsing JSON: {str(e)}")
            raise ValueError(f"JSON non valido: {str(e)}")
        except Exception as e:
            self.logger.error(f"Errore nella trasformazione: {str(e)}")
            raise
        
    def transform_and_save(self, input_file: Union[str, Path], 
                          output_file: Union[str, Path],
                          flat_format: bool = False) -> Dict:
        """
        Trasforma i dati CDR e salva il risultato su file.
        
        Args:
            input_file: Percorso del file JSON di input
            output_file: Percorso del file JSON di output
            flat_format: Se True usa la struttura piatta
            
        Returns:
            dict: Dizionario con struttura semplificata
        """
        # Trasforma i dati
        transformed_data = self.transform_from_file(input_file, flat_format)
        
        # Salva il risultato
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(transformed_data, file, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Dati trasformati salvati in: {output_path}")
        
        return transformed_data
    
    def get_transformation_stats(self) -> Dict:
        """
        Restituisce le statistiche dell'ultima trasformazione eseguita.
        
        Returns:
            dict: Statistiche di trasformazione
        """
        return self._last_transformation_stats.copy()
    
    def transform_from_multiple_files(self, file_paths: List[Union[str, Path]], flat_format: bool = False) -> Dict:
        """
        Trasforma e unisce i dati CDR da più file JSON.
        
        Args:
            file_paths: Lista dei percorsi dei file JSON da unire
            flat_format: Se True usa la struttura piatta, altrimenti struttura nidificata
            
        Returns:
            dict: Dizionario con struttura unificata contenente tutti i dati
        """
        try:
            self.logger.info(f"Inizio trasformazione e unione di {len(file_paths)} file")
            
            if not file_paths:
                raise ValueError("La lista dei file non può essere vuota")
            
            # Inizializza strutture per l'unione
            unified_contracts = {}
            unified_statistics = {
                "total_input_records": 0,
                "total_contracts": 0,
                "call_types_found": set(),
                "total_duration": 0,
                "total_cost": 0.0,
                "total_cost_with_markup": 0.0,  # Questo campo deve essere presente
                "call_type_statistics": {
                    "durations_by_type": {},
                    "costs_by_type": {},
                    "costs_by_type_with_markup": {},  # Questo campo è importante
                    "calls_by_type": {}
                }
            }
            
            total_files_processed = 0
            
            # Elabora ogni file
            for file_path in file_paths:
                file_path = Path(file_path)
                
                if not file_path.exists():
                    self.logger.warning(f"File non trovato, saltato: {file_path}")
                    continue
                    
                self.logger.debug(f"Elaborazione file: {file_path}")
                
                try:
                    # Carica i dati dal file
                    with open(file_path, 'r', encoding='utf-8') as file:
                        file_data = json.load(file)
                    
                    # Estrae i contratti
                    contracts = file_data.get("contracts", {})
                    
                    # Unisce i contratti per codice_contratto
                    for contract_id, contract_data in contracts.items():
                        if contract_id not in unified_contracts:
                            # Primo file per questo contratto - copia tutto
                            unified_contracts[contract_id] = {
                                "aggregated_records": contract_data.get("aggregated_records", []).copy(),
                                "lista_chiamate": contract_data.get("lista_chiamate", []).copy(),
                                "contract_info": contract_data.get("contract_info", {}).copy()
                            }
                        else:
                            # Contratto già esistente - unisci i dati
                            existing_contract = unified_contracts[contract_id]
                            
                            # 1. Unisci aggregated_records
                            new_aggregated = contract_data.get("aggregated_records", [])
                            existing_aggregated = existing_contract.get("aggregated_records", [])
                            
                            # Crea un dizionario per aggregare per tipo di chiamata
                            aggregated_by_type = {}
                            totale_generale_data = None
                            
                            # Processa record esistenti
                            for record in existing_aggregated:
                                aggregation_type = record.get("aggregation_type")
                                if aggregation_type == "totale_generale":
                                    totale_generale_data = record.copy()
                                else:
                                    tipo_chiamata = record.get("tipo_chiamata")
                                    if tipo_chiamata:
                                        aggregated_by_type[tipo_chiamata] = record.copy()
                            
                            # Processa nuovi record
                            for record in new_aggregated:
                                aggregation_type = record.get("aggregation_type")
                                if aggregation_type == "totale_generale":
                                    # Unisci totali generali
                                    if totale_generale_data:
                                        totale_generale_data["durata_secondi_generale"] += record.get("durata_secondi_generale", 0)
                                        totale_generale_data["costo_euro_generale"] += record.get("costo_euro_generale", 0.0)
                                        totale_generale_data["costo_euro_generale_with_markup"] += record.get("costo_euro_generale_with_markup", 0.0)
                                        totale_generale_data["numero_chiamate_totali"] += record.get("numero_chiamate_totali", 0)
                                        # Aggiorna il numero di tipi di chiamata
                                        tipi_esistenti = set()
                                        for tipo_record in list(aggregated_by_type.values()):
                                            tipi_esistenti.add(tipo_record.get("tipo_chiamata"))
                                        totale_generale_data["numero_tipi_chiamata"] = len(tipi_esistenti)
                                    else:
                                        totale_generale_data = record.copy()
                                else:
                                    # Unisci per tipo di chiamata
                                    tipo_chiamata = record.get("tipo_chiamata")
                                    if tipo_chiamata:
                                        if tipo_chiamata in aggregated_by_type:
                                            # Somma i valori esistenti
                                            existing_record = aggregated_by_type[tipo_chiamata]
                                            existing_record["durata_secondi_totale"] += record.get("durata_secondi_totale", 0)
                                            existing_record["costo_euro_totale"] += record.get("costo_euro_totale", 0.0)
                                            existing_record["costo_euro_totale_with_markup"] += record.get("costo_euro_totale_with_markup", 0.0)
                                            existing_record["numero_chiamate"] += record.get("numero_chiamate", 0)
                                            
                                            # Unisci source files
                                            existing_sources = set(existing_record.get("_source_files", []))
                                            new_sources = set(record.get("_source_files", []))
                                            existing_record["_source_files"] = list(existing_sources.union(new_sources))
                                        else:
                                            aggregated_by_type[tipo_chiamata] = record.copy()
                            
                            # Ricostruisci la lista aggregated_records
                            unified_aggregated = list(aggregated_by_type.values())
                            if totale_generale_data:
                                unified_aggregated.append(totale_generale_data)
                            
                            existing_contract["aggregated_records"] = unified_aggregated
                            
                            # 2. Unisci lista_chiamate
                            new_calls = contract_data.get("lista_chiamate", [])
                            existing_contract["lista_chiamate"].extend(new_calls)
                            
                            # 3. Aggiorna contract_info con i totali
                            if totale_generale_data:
                                contract_info = existing_contract.get("contract_info", {})
                                contract_info.update({
                                    "durata_totale_secondi": totale_generale_data.get("durata_secondi_generale", 0),
                                    "costo_totale_euro": totale_generale_data.get("costo_euro_generale", 0.0),
                                    "costo_totale_euro_with_markup": totale_generale_data.get("costo_euro_generale_with_markup", 0.0),
                                    "numero_chiamate_totali": totale_generale_data.get("numero_chiamate_totali", 0),
                                    "numero_tipi_chiamata": totale_generale_data.get("numero_tipi_chiamata", 0)
                                })
                                existing_contract["contract_info"] = contract_info
                    
                    # Unisce le statistiche
                    file_stats = file_data.get("statistics", {})
                    if file_stats:
                        unified_statistics["total_input_records"] += file_stats.get("total_input_records", 0)
                        unified_statistics["total_cost"] += file_stats.get("total_cost", 0.0)
                        unified_statistics["total_cost_with_markup"] += file_stats.get("total_cost_with_markup", 0.0)
                        unified_statistics["total_duration"] += file_stats.get("total_duration", 0)
                        
                        # Unisci call_types_found (usa set per evitare duplicati)
                        file_call_types = file_stats.get("call_types_found", [])
                        unified_statistics["call_types_found"].update(file_call_types)
                        
                        # Unisce le statistiche per tipo di chiamata
                        file_call_type_stats = file_stats.get("call_type_statistics", {})
                        
                        # Mappa corretta dei campi delle statistiche
                        stat_mapping = {
                            "durations_by_type": "durations_by_type",
                            "costs_by_type": "costs_by_type", 
                            "costs_by_type_with_markup": "costs_by_type_with_markup",
                            "calls_by_type": "calls_by_type"
                        }
                        
                        for unified_key, file_key in stat_mapping.items():
                            file_type_data = file_call_type_stats.get(file_key, {})
                            for call_type, value in file_type_data.items():
                                if call_type not in unified_statistics["call_type_statistics"][unified_key]:
                                    unified_statistics["call_type_statistics"][unified_key][call_type] = 0
                                unified_statistics["call_type_statistics"][unified_key][call_type] += value
                    
                    total_files_processed += 1
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Errore nel parsing JSON del file {file_path}: {str(e)}")
                    continue
                except Exception as e:
                    self.logger.error(f"Errore nell'elaborazione del file {file_path}: {str(e)}")
                    continue
            
            if total_files_processed == 0:
                raise ValueError("Nessun file valido è stato elaborato")
            
            # Finalizza le statistiche unificate
            unified_statistics["total_contracts"] = len(unified_contracts)
            unified_statistics["call_types_found"] = list(unified_statistics["call_types_found"])  # Converte set in lista
            
            # Crea la struttura unificata per la trasformazione
            unified_input_data = {
                "contracts": unified_contracts,
                "statistics": unified_statistics
            }
            
            # *** PUNTO CHIAVE: APPLICA LA TRASFORMAZIONE ***
            # Applica la trasformazione normale sui dati unificati
            if flat_format:
                result = self.transform_from_dict_flat(unified_input_data)
            else:
                result = self.transform_from_dict(unified_input_data)
            
            # Aggiorna le statistiche di trasformazione
            self._last_transformation_stats.update({
                "files_processed": total_files_processed,
                "files_requested": len(file_paths),
                "files_skipped": len(file_paths) - total_files_processed
            })
            
            self.logger.info(
                f"Unione completata: {total_files_processed}/{len(file_paths)} file elaborati, "
                f"{len(result['data'])} contratti nel risultato finale"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Errore durante l'unione dei file: {str(e)}")
            raise

    def transform_and_save_multiple(self, input_files: List[Union[str, Path]], 
                                output_file: Union[str, Path],
                                flat_format: bool = False) -> Dict:
        """
        Trasforma e unisce più file CDR e salva il risultato su file.
        
        Args:
            input_files: Lista dei percorsi dei file JSON di input
            output_file: Percorso del file JSON di output
            flat_format: Se True usa la struttura piatta
            
        Returns:
            dict: Dizionario con struttura unificata
        """
        # Trasforma e unisce i dati
        unified_data = self.transform_from_multiple_files(input_files, flat_format)
        
        # Salva il risultato
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(unified_data, file, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Dati unificati salvati in: {output_path}")
        
        return unified_data
    

class JSONAggregator:
    """
    Classe per l'aggregazione di file JSON contenenti dati di contratti CDR.
    
    Questa classe gestisce la lettura, l'aggregazione e l'unione di più file JSON
    che contengono dati di contratti telefonici, mantenendo la struttura originale
    e aggregando le statistiche.
    """
    
    def __init__(self):
        """
        Inizializza l'aggregatore JSON.
        
        Args:
            logger (Optional[logging.Logger]): Logger personalizzato. Se None, usa il logger di default.
        """
        self.logger = self._setup_logger()
        self.processed_files: List[str] = []
        self.aggregated_data: Dict[str, Any] = {}
        
    def _setup_logger(self) -> logging.Logger:
        """Configura il logger per il processore"""
        logger = logging.getLogger('CDRProcessor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_aggregated_structure(self) -> Dict[str, Any]:
        """
        Inizializza la struttura dati per l'aggregazione.
        
        Returns:
            Dict[str, Any]: Struttura dati inizializzata
        """
        return {
            "contracts": {},
            "statistics": {
                "total_input_records": 0,
                "total_contracts": 0,
                "call_types_found": set(),
                "total_duration": 0,
                "total_cost": 0.0,
                "call_type_statistics": {
                    "durations_by_type": defaultdict(int),
                    "costs_by_type": defaultdict(float)
                }
            },
            "file_name": ""
        }
    
    def aggregate_files(self, folder_path: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Legge tutti i file JSON da una cartella e li unisce per codice_contratto.
        
        Args:
            folder_path (str): Percorso della cartella contenente i file JSON
            output_file (Optional[str]): Percorso del file di output. Se None, non salva su file
            
        Returns:
            Dict[str, Any]: Dizionario aggregato con lo stesso schema dell'input
            
        Raises:
            FileNotFoundError: Se la cartella non esiste
            ValueError: Se non ci sono file JSON nella cartella
        """
        self.logger.info(f"Inizio aggregazione file dalla cartella: {folder_path}")
        
        # Inizializza la struttura di output
        self.aggregated_data = self._initialize_aggregated_structure()
        self.processed_files = []
        
        # Verifica che la cartella esista
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"La cartella {folder_path} non esiste")
        
        # Elenca tutti i file JSON nella cartella
        json_files = self._get_json_files(folder_path)
        
        if not json_files:
            raise ValueError(f"Nessun file JSON trovato nella cartella {folder_path}")
        
        self.logger.info(f"Trovati {len(json_files)} file JSON da processare")
        
        # Processa ogni file JSON
        for filename in json_files:
            file_path = os.path.join(folder_path, filename)
            success = self._process_single_file(file_path, filename)
            
            if success:
                self.processed_files.append(filename)
        
        # Post-processing
        self._finalize_aggregation()
        
        # Salva su file se richiesto
        if output_file:
            self.save_to_file(output_file)
        
        self.logger.info(
            f"Aggregazione completata. Processati {len(self.processed_files)} file, "
            f"trovati {self.aggregated_data['statistics']['total_contracts']} contratti"
        )
        
        return self.aggregated_data
    
    def _get_json_files(self, folder_path: str) -> List[str]:
        """
        Ottiene la lista dei file JSON nella cartella principale.
        
        Args:
            folder_path (str): Percorso della cartella
            
        Returns:
            List[str]: Lista dei nomi dei file JSON
        """
        return [
            f for f in os.listdir(folder_path) 
            if f.endswith('.json') and os.path.isfile(os.path.join(folder_path, f))
        ]
    
    def _process_single_file(self, file_path: str, filename: str) -> bool:
        """
        Processa un singolo file JSON.
        
        Args:
            file_path (str): Percorso completo del file
            filename (str): Nome del file
            
        Returns:
            bool: True se il file è stato processato con successo, False altrimenti
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.logger.info(f"Processando file: {filename}")
                
                # Aggrega i contratti
                self._aggregate_contracts(data)
                
                # Aggrega le statistiche
                self._aggregate_statistics(data)
                
                return True
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Errore nel parsing del file {filename}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Errore nel processamento del file {filename}: {e}")
            return False
    
    def _aggregate_contracts(self, data: Dict[str, Any]) -> None:
        """
        Aggrega i dati dei contratti.
        
        Args:
            data (Dict[str, Any]): Dati del file JSON corrente
        """
        if "contracts" not in data:
            return
        
        for codice_contratto, contract_data in data["contracts"].items():
            if codice_contratto not in self.aggregated_data["contracts"]:
                # Primo inserimento del contratto
                self.aggregated_data["contracts"][codice_contratto] = {
                    "aggregated_records": [],
                    "lista_chiamate": [],
                    "contract_info": contract_data.get("contract_info", {})
                }
            
            # Unisce aggregated_records
            if "aggregated_records" in contract_data:
                self.aggregated_data["contracts"][codice_contratto]["aggregated_records"].extend(
                    contract_data["aggregated_records"]
                )
            
            # Unisce lista_chiamate
            if "lista_chiamate" in contract_data:
                self.aggregated_data["contracts"][codice_contratto]["lista_chiamate"].extend(
                    contract_data["lista_chiamate"]
                )
            
            # Aggiorna contract_info se presente
            if "contract_info" in contract_data:
                self.aggregated_data["contracts"][codice_contratto]["contract_info"].update(
                    contract_data["contract_info"]
                )
    
    def _aggregate_statistics(self, data: Dict[str, Any]) -> None:
        """
        Aggrega le statistiche.
        
        Args:
            data (Dict[str, Any]): Dati del file JSON corrente
        """
        if "statistics" not in data:
            return
        
        stats = data["statistics"]
        agg_stats = self.aggregated_data["statistics"]
        
        # Somma i valori numerici
        agg_stats["total_input_records"] += stats.get("total_input_records", 0)
        agg_stats["total_duration"] += stats.get("total_duration", 0)
        agg_stats["total_cost"] += stats.get("total_cost", 0.0)
        
        # Unisce call_types_found (set)
        if "call_types_found" in stats:
            agg_stats["call_types_found"].update(stats["call_types_found"])
        
        # Aggrega call_type_statistics
        self._aggregate_call_type_statistics(stats)
    
    def _aggregate_call_type_statistics(self, stats: Dict[str, Any]) -> None:
        """
        Aggrega le statistiche per tipo di chiamata.
        
        Args:
            stats (Dict[str, Any]): Statistiche del file corrente
        """
        if "call_type_statistics" not in stats:
            return
        
        call_stats = stats["call_type_statistics"]
        agg_call_stats = self.aggregated_data["statistics"]["call_type_statistics"]
        
        # Durations by type
        if "durations_by_type" in call_stats:
            for call_type, duration in call_stats["durations_by_type"].items():
                agg_call_stats["durations_by_type"][call_type] += duration
        
        # Costs by type
        if "costs_by_type" in call_stats:
            for call_type, cost in call_stats["costs_by_type"].items():
                agg_call_stats["costs_by_type"][call_type] += cost
    
    def _finalize_aggregation(self) -> None:
        """
        Finalizza l'aggregazione con post-processing.
        """
        # Converte il set in lista per call_types_found
        self.aggregated_data["statistics"]["call_types_found"] = list(
            self.aggregated_data["statistics"]["call_types_found"]
        )
        
        # Calcola total_contracts
        self.aggregated_data["statistics"]["total_contracts"] = len(
            self.aggregated_data["contracts"]
        )
        
        # Converte defaultdict in dict normali
        call_stats = self.aggregated_data["statistics"]["call_type_statistics"]
        call_stats["durations_by_type"] = dict(call_stats["durations_by_type"])
        call_stats["costs_by_type"] = dict(call_stats["costs_by_type"])
        
        # Imposta il file_name con l'elenco dei file processati
        self.aggregated_data["file_name"] = f"Aggregated from: {', '.join(self.processed_files)}"
        
        # Ricomputa i totali per ogni contratto
        self.recalculate_contract_totals()
    
    def recalculate_contract_totals(self) -> None:
        """
        Ricalcola i totali per ogni contratto basandosi sui dati aggregati.
        """
        for codice_contratto, contract_data in self.aggregated_data["contracts"].items():
            if "contract_info" not in contract_data:
                contract_data["contract_info"] = {}
            
            # Calcola totali dalla lista chiamate
            total_duration = 0
            total_cost = 0.0
            total_cost_with_markup = 0.0
            total_calls = 0
            call_types = set()
            
            for call in contract_data.get("lista_chiamate", []):
                total_duration += call.get("durata_secondi", 0)
                total_cost += call.get("costo_euro", 0.0)
                total_cost_with_markup += call.get("costo_euro_with_markup", 0.0)
                total_calls += 1
                if "tipo_chiamata" in call:
                    call_types.add(call["tipo_chiamata"])
            
            # Aggiorna contract_info
            contract_data["contract_info"].update({
                "durata_totale_secondi": total_duration,
                "costo_totale_euro": round(total_cost, 3),
                "costo_totale_euro_with_markup": round(total_cost_with_markup, 3),
                "numero_chiamate_totali": total_calls,
                "numero_tipi_chiamata": len(call_types)
            })
    
    def merge_aggregated_records_by_type(self) -> None:
        """
        Unisce gli aggregated_records per tipo_chiamata per evitare duplicati.
        Gestisce anche il campo data_ora presente nella nuova struttura.
        """
        for codice_contratto, contract_data in self.aggregated_data["contracts"].items():
            if "aggregated_records" not in contract_data:
                continue
            
            # Raggruppa per tipo_chiamata e aggregation_type
            grouped_records = defaultdict(lambda: defaultdict(list))
            
            for record in contract_data["aggregated_records"]:
                tipo_chiamata = record.get("tipo_chiamata", "N.D.")
                aggregation_type = record.get("aggregation_type", "unknown")
                grouped_records[tipo_chiamata][aggregation_type].append(record)
            
            # Crea nuovi record aggregati
            new_aggregated_records = []
            
            for tipo_chiamata, by_agg_type in grouped_records.items():
                for aggregation_type, records in by_agg_type.items():
                    if len(records) == 1:
                        new_aggregated_records.append(records[0])
                    else:
                        # Merge multiple records
                        merged_record = self._merge_records(records)
                        new_aggregated_records.append(merged_record)
            
            contract_data["aggregated_records"] = new_aggregated_records
            
            self.logger.info(
                f"Contratto {codice_contratto}: uniti record duplicati, "
                f"ora {len(new_aggregated_records)} record aggregati"
            )
    
    def _merge_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Unisce più record dello stesso tipo.
        
        Args:
            records (List[Dict[str, Any]]): Lista di record da unire
            
        Returns:
            Dict[str, Any]: Record unito
        """
        merged_record = records[0].copy()
        
        # Somma i valori numerici
        merged_record["durata_secondi_totale"] = sum(
            r.get("durata_secondi_totale", 0) for r in records
        )
        merged_record["costo_euro_totale"] = sum(
            r.get("costo_euro_totale", 0.0) for r in records
        )
        merged_record["costo_euro_totale_with_markup"] = sum(
            r.get("costo_euro_totale_with_markup", 0.0) for r in records
        )
        merged_record["numero_chiamate"] = sum(
            r.get("numero_chiamate", 0) for r in records
        )
        
        # Gestisce data_ora - prende la più recente
        data_ora_list = [r.get("data_ora") for r in records if r.get("data_ora")]
        if data_ora_list:
            # Ordina e prende la più recente
            merged_record["data_ora"] = max(data_ora_list)
        
        # Unisce source_files
        source_files = set()
        for r in records:
            source_files.update(r.get("_source_files", []))
        merged_record["_source_files"] = list(source_files)
        
        # Aggiorna timestamp di aggregazione
        merged_record["_aggregated_at"] = datetime.now().isoformat()
        
        return merged_record
    
    def save_to_file(self, output_file: str) -> None:
        """
        Salva i dati aggregati su file.
        
        Args:
            output_file (str): Percorso del file di output
            
        Raises:
            IOError: Se non riesce a scrivere il file
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.aggregated_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"File aggregato salvato in: {output_file}")
        except IOError as e:
            self.logger.error(f"Errore nel salvare il file {output_file}: {e}")
            raise
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """
        Restituisce un riassunto delle statistiche aggregate.
        
        Returns:
            Dict[str, Any]: Riassunto delle statistiche
        """
        if not self.aggregated_data:
            return {}
        
        stats = self.aggregated_data.get("statistics", {})
        return {
            "total_contracts": stats.get("total_contracts", 0),
            "total_calls": stats.get("total_input_records", 0),
            "total_duration_seconds": stats.get("total_duration", 0),
            "total_duration_hours": round(stats.get("total_duration", 0) / 3600, 2),
            "total_cost_euro": round(stats.get("total_cost", 0.0), 3),
            "call_types": stats.get("call_types_found", []),
            "processed_files_count": len(self.processed_files),
            "processed_files": self.processed_files
        }
    
    def get_contract_info(self, codice_contratto: str) -> Optional[Dict[str, Any]]:
        """
        Restituisce le informazioni di un contratto specifico.
        
        Args:
            codice_contratto (str): Codice del contratto
            
        Returns:
            Optional[Dict[str, Any]]: Informazioni del contratto o None se non trovato
        """
        if not self.aggregated_data or codice_contratto not in self.aggregated_data.get("contracts", {}):
            return None
        
        return self.aggregated_data["contracts"][codice_contratto]
    
    def list_contracts(self) -> List[str]:
        """
        Restituisce la lista dei codici contratto presenti.
        
        Returns:
            List[str]: Lista dei codici contratto
        """
        if not self.aggregated_data:
            return []
        
        return list(self.aggregated_data.get("contracts", {}).keys())







########################################
# Funzione di utilità per uso semplice #
########################################
def process_cdr_files(files: Union[str, List[str]], 
                     output_path) -> Dict[str, Any]:
    """
    Funzione di utilità per processare file CDR
    
    Args:
        files: File o lista di file da processare
        output_path: Percorso del file JSON di output
        
    Returns:
        Statistiche del processamento
    """

    processor = CDRProcessor(output_json_path=output_path)
    return processor.process_files(files)


def aggregate_cdr_files(files: Union[str, List[str]] = None, 
                       output_file: str = None) -> Dict[str, Any]:
    """
    Funzione di utilità per aggregare file CDR
    
    Args:
        files: File JSON singolo o lista di file JSON (se None usa il default)
        output_file: File di output per salvare i risultati (se None usa il default)
        
    Returns:
        Risultati dell'aggregazione strutturati per contratto
    """
    aggregator = CDRAggregator()
    return aggregator.aggregate_cdr_data(files, output_file)

def get_contract_summary(self, files: Union[str, List[str]] = None) -> Dict[int, Dict[str, Any]]:
        """
        Restituisce un riassunto per contratto
        
        Args:
            files: File JSON singolo o lista di file JSON (se None usa il default)
            
        Returns:
            Dizionario con riassunto per ogni contratto
        """
        # Nome file predefinito
        default_input_file = "cdr_data.json"
        
        # Usa il file predefinito se non specificato
        if files is None:
            files = default_input_file
            self.logger.info(f"Usando file di input predefinito: {default_input_file}")
        
        all_data = self._load_all_data(files)
        aggregated_data = self._aggregate_by_contract_and_type(all_data)
        
        summary = {}
        
        for codice_contratto, types_data in aggregated_data.items():
            contract_info = None
            total_duration = 0
            total_cost = 0.0
            total_calls = 0
            
            for tipo_data in types_data.values():
                if contract_info is None:
                    sample = tipo_data['record_sample']
                    contract_info = {
                        'cliente_finale': sample.get('cliente_finale', ''),
                        'numero_cliente': sample.get('numero_cliente', ''),
                        'codice_servizio': sample.get('codice_servizio', '')
                    }
                
                total_duration += tipo_data['durata_secondi_totale']
                total_cost += tipo_data['costo_euro_totale']
                total_calls += tipo_data['numero_chiamate']
            
            summary[codice_contratto] = {
                **contract_info,
                'total_duration_seconds': total_duration,
                'total_cost_euro': round(total_cost, 3),
                'total_calls': total_calls,
                'call_types': list(types_data.keys())
            }
        
        return summary


# Configura il logging
def get_contract_summar1(self, files: Union[str, List[str]] = None) -> Dict[int, Dict[str, Any]]:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Crea un'istanza dell'aggregatore
    aggregator = JSONAggregator()
    
    # Esempio di utilizzo
    folder_path = "path/to/json/files"  # Sostituisci con il percorso reale
    output_file = "aggregated_data.json"  # File di output opzionale
    
    try:
        # Aggrega i file
        result = aggregator.aggregate_files(folder_path, output_file)
        
        # Opzionale: unisce record duplicati
        aggregator.merge_aggregated_records_by_type()
        
        # Mostra statistiche
        summary = aggregator.get_statistics_summary()
        print(f"Aggregazione completata con successo!")
        print(f"Totale contratti: {summary['total_contracts']}")
        print(f"Totale chiamate: {summary['total_calls']}")
        print(f"Durata totale: {summary['total_duration_hours']} ore")
        print(f"Costo totale: {summary['total_cost_euro']} euro")
        print(f"Tipi di chiamata: {', '.join(summary['call_types'])}")
        
        # Lista contratti
        contracts = aggregator.list_contracts()
        print(f"Contratti trovati: {contracts}")
        
    except Exception as e:
        print(f"Errore durante l'aggregazione: {e}")    
    

# Esempio di utilizzo
if __name__ == "__main__":
    # Esempi di utilizzo
    
    # Processare un singolo file
    # stats = process_cdr_files("RIV_20943_2025-07-17-13.18.53.CDR")
    
    # Processare più file
    # stats = process_cdr_files([
    #     "RIV_20943_2025-07-17-13.18.53.CDR",
    #     "RIV_20943_2025-07-18-13.18.53.CDR"
    # ])
    
    # Uso avanzato con configurazione personalizzata
    # processor = CDRProcessor(
    #     output_json_path="data/cdr_unified.json",
    #     processed_files_path="data/processed_files.json"
    # )
    
    # Processare file
    # stats = processor.process_files("esempio.CDR")
    
    # Ottenere statistiche
    # stats = processor.get_stats()
    # print(json.dumps(stats, indent=2))
    
    print("CDR Processor pronto per l'utilizzo!")



    #######################################################


    # Esempi di utilizzo
    
    # Aggregare un singolo file
    # results = aggregate_cdr_files("cdr_data_2025_07.json", "aggregated_cdr.json")
    
    # Aggregare più file
    # results = aggregate_cdr_files([
    #     "cdr_data_2025_07.json",
    #     "cdr_data_2025_08.json"
    # ], "aggregated_multiple.json")
    
    # Uso avanzato
    # aggregator = CDRAggregator()
    
    # Aggrega i dati
    # results = aggregator.aggregate_cdr_data("cdr_data_2025_07.json")
    
    # Ottieni riassunto per contratto
    # summary = aggregator.get_contract_summary("cdr_data_2025_07.json")
    
    print("CDR Aggregator pronto per l'utilizzo!")