from flask import request, jsonify, render_template, redirect, url_for, flash, g
from app.models.user import User
from app.models.role import Role
from app.models.company import Company
from app.auth.decorators import admin_required, api_admin_required, moderator_required
from app import db
from app.auth.unified_decorators import unified_api_admin_required, unified_api_moderator_required
import base64
import os
from datetime import datetime
from app.utils.env_manager import *
from app.logger import get_logger       
from app.voip_cdr.cdr_categories import CDRAnalyticsEnhanced
import json
from pathlib import Path
logger = get_logger(__name__)


def register_api_voip_cdr_routes(api_voip_cdr):
    # ############################# #
    # CATEGORIE CDR ############### #
    # #### ######################## #  
    out_directory = ARCHIVE_DIRECTORY
    analytics = CDRAnalyticsEnhanced(output_directory=out_directory)
    categories_manager = analytics.get_categories_manager()
    
    #Legge
    @api_voip_cdr.route('categories', methods=['GET'])
    @unified_api_admin_required
    def get_categories():
        """API per ottenere tutte le categorie con informazioni pricing"""
        try:
            categories_data = categories_manager.get_all_categories_with_pricing()
            
            return jsonify({
                'success': True,
                'categories': categories_data,
                'stats': categories_manager.get_statistics(),
                'global_markup_percent': categories_manager.global_markup_percent
            })
            
        except Exception as e:
            logger.error(f"Errore API get categories: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    

    #INSERISCE
    @api_voip_cdr.route('categories', methods=['POST'])
    @unified_api_admin_required
    def create_category():
        """API per creare una nuova categoria con markup personalizzabile"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'Dati non validi'}), 400
            
            # Validazione dati richiesti
            required_fields = ['name', 'display_name', 'price_per_minute', 'patterns']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'success': False, 'message': f'Campo {field} obbligatorio'}), 400
            
            # Estrai dati
            name = data['name'].strip().upper()
            display_name = data['display_name'].strip()
            price_per_minute = float(data['price_per_minute'])
            patterns = [p.strip() for p in data['patterns'] if p.strip()]
            currency = data.get('currency', 'EUR')
            description = data.get('description', '').strip()
            
            # Gestione markup personalizzato
            custom_markup_percent = None
            if 'custom_markup_percent' in data and data['custom_markup_percent'] not in [None, '', 'null']:
                try:
                    custom_markup_percent = float(data['custom_markup_percent'])
                    if custom_markup_percent < -100:
                        return jsonify({'success': False, 'message': 'Markup non può essere inferiore a -100%'}), 400
                    if custom_markup_percent > 1000:
                        return jsonify({'success': False, 'message': 'Markup troppo alto (massimo 1000%)'}), 400
                except (ValueError, TypeError):
                    return jsonify({'success': False, 'message': 'Valore markup non valido'}), 400
            
            # Validazioni aggiuntive
            if price_per_minute < 0:
                return jsonify({'success': False, 'message': 'Il prezzo deve essere positivo'}), 400
            
            if not patterns:
                return jsonify({'success': False, 'message': 'Almeno un pattern è obbligatorio'}), 400
            
            # Crea categoria con markup
            success = categories_manager.add_category(
                name=name,
                display_name=display_name,
                price_per_minute=price_per_minute,
                patterns=patterns,
                currency=currency,
                description=description,
                custom_markup_percent=custom_markup_percent
            )
            
            if success:
                logger.info(f"Categoria {name} creata con successo")
                # Restituisci info pricing complete
                new_category = categories_manager.get_category(name)
                from dataclasses import asdict
                category_data = asdict(new_category)
                category_data['pricing_info'] = new_category.get_pricing_info(categories_manager.global_markup_percent)
                
                return jsonify({
                    'success': True,
                    'message': f'Categoria {name} creata con successo',
                    'category_name': name,
                    'category_data': category_data
                })
            else:
                return jsonify({'success': False, 'message': 'Errore nella creazione della categoria'}), 500
                
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Errore API create category: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
        
    #AGGIORNA
    @api_voip_cdr.route('categories/<category_name>', methods=['PUT'])
    @unified_api_admin_required
    def update_category(category_name):
        """API per aggiornare una categoria esistente con supporto markup"""
        try:
            
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'Dati non validi'}), 400
            
            # Verifica esistenza categoria
            if not categories_manager.get_category(category_name):
                return jsonify({'success': False, 'message': 'Categoria non trovata'}), 404
            
            # Prepara aggiornamenti
            updates = {}
            
            if 'display_name' in data:
                updates['display_name'] = data['display_name'].strip()
            
            if 'price_per_minute' in data:
                price = float(data['price_per_minute'])
                if price < 0:
                    return jsonify({'success': False, 'message': 'Il prezzo deve essere positivo'}), 400
                updates['price_per_minute'] = price
            
            if 'patterns' in data:
                patterns = [p.strip() for p in data['patterns'] if p.strip()]
                if not patterns:
                    return jsonify({'success': False, 'message': 'Almeno un pattern è obbligatorio'}), 400
                updates['patterns'] = patterns
            
            if 'currency' in data:
                updates['currency'] = data['currency']
            
            if 'description' in data:
                updates['description'] = data['description'].strip()
            
            if 'is_active' in data:
                updates['is_active'] = bool(data['is_active'])
            
            # Gestione aggiornamento markup personalizzato
            if 'custom_markup_percent' in data:
                markup_value = data['custom_markup_percent']
                
                if markup_value in [None, '', 'null', 'reset']:
                    # Reset a markup globale
                    updates['custom_markup_percent'] = None
                else:
                    try:
                        custom_markup = float(markup_value)
                        if custom_markup < -100:
                            return jsonify({'success': False, 'message': 'Markup non può essere inferiore a -100%'}), 400
                        if custom_markup > 1000:
                            return jsonify({'success': False, 'message': 'Markup troppo alto (massimo 1000%)'}), 400
                        updates['custom_markup_percent'] = custom_markup
                    except (ValueError, TypeError):
                        return jsonify({'success': False, 'message': 'Valore markup non valido'}), 400
            
            # Aggiorna categoria
            success = categories_manager.update_category(category_name, **updates)
            
            if success:
                logger.info(f"Categoria {category_name} aggiornata con successo")
                # Restituisci dati aggiornati con pricing
                updated_category = categories_manager.get_category(category_name)
                from dataclasses import asdict
                category_data = asdict(updated_category)
                category_data['pricing_info'] = updated_category.get_pricing_info(categories_manager.global_markup_percent)
                
                return jsonify({
                    'success': True,
                    'message': f'Categoria {category_name} aggiornata con successo',
                    'category_data': category_data
                })
            else:
                return jsonify({'success': False, 'message': 'Errore nell\'aggiornamento della categoria'}), 500
                
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Errore API update category {category_name}: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500


    #ELIMINA        
    @api_voip_cdr.route('categories/<category_name>', methods=['DELETE'])
    @unified_api_admin_required
    def delete_category(category_name):
        """API per eliminare una categoria"""
        try:
            # Verifica esistenza categoria
            if not categories_manager.get_category(category_name):
                return jsonify({'success': False, 'message': 'Categoria non trovata'}), 404
            
            # Elimina categoria
            success = categories_manager.delete_category(category_name)
            
            if success:
                logger.info(f"Categoria {category_name} eliminata con successo")
                return jsonify({
                    'success': True,
                    'message': f'Categoria {category_name} eliminata con successo'
                })
            else:
                return jsonify({'success': False, 'message': 'Errore nell\'eliminazione della categoria'}), 500
                
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Errore API delete category {category_name}: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
        

    @api_voip_cdr.route('categories/conflicts', methods=['GET'])
    @unified_api_admin_required
    def get_pattern_conflicts():
        """API per ottenere conflitti tra pattern delle categorie"""
        try:
            conflicts = categories_manager.validate_patterns_conflicts()
            
            return jsonify({
                'success': True,
                'conflicts': conflicts,
                'has_conflicts': len(conflicts) > 0
            })
            
        except Exception as e:
            logger.error(f"Errore API conflicts: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    

    @api_voip_cdr.route('categories/statistics', methods=['GET'])
    @unified_api_admin_required
    def get_categories_statistics():
        """API per ottenere statistiche delle categorie con info markup"""
        try:
            stats = categories_manager.get_statistics()
            
            return jsonify({
                'success': True,
                'statistics': stats
            })
            
        except Exception as e:
            logger.error(f"Errore API statistics: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
        
    @api_voip_cdr.route('categories/health', methods=['GET'])
    @unified_api_admin_required
    def check_categories_health():
        """API per controllo salute sistema categorie"""
        try:
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'checks': {},
                'warnings': [],
                'errors': []
            }
            
            # Check file configurazione
            try:
                if categories_manager.config_file.exists():
                    health_status['checks']['config_file_exists'] = True
                    
                    # Check permessi
                    if os.access(categories_manager.config_file, os.R_OK):
                        health_status['checks']['config_file_readable'] = True
                    else:
                        health_status['checks']['config_file_readable'] = False
                        health_status['errors'].append('File configurazione non leggibile')
                    
                    if os.access(categories_manager.config_file, os.W_OK):
                        health_status['checks']['config_file_writable'] = True
                    else:
                        health_status['checks']['config_file_writable'] = False
                        health_status['warnings'].append('File configurazione non scrivibile')
                else:
                    health_status['checks']['config_file_exists'] = False
                    health_status['warnings'].append('File configurazione non esiste')
            except Exception as e:
                health_status['checks']['config_file_check'] = False
                health_status['errors'].append(f'Errore controllo file: {str(e)}')
            
            # Check categorie caricate
            try:
                categories_count = len(categories_manager.get_all_categories())
                active_count = len(categories_manager.get_active_categories())
                
                health_status['checks']['categories_loaded'] = categories_count > 0
                health_status['checks']['active_categories'] = active_count > 0
                
                if categories_count == 0:
                    health_status['errors'].append('Nessuna categoria caricata')
                elif active_count == 0:
                    health_status['warnings'].append('Nessuna categoria attiva')
                    
            except Exception as e:
                health_status['checks']['categories_check'] = False
                health_status['errors'].append(f'Errore controllo categorie: {str(e)}')
            
            # Check conflitti pattern
            try:
                conflicts = categories_manager.validate_patterns_conflicts()
                health_status['checks']['no_pattern_conflicts'] = len(conflicts) == 0
                
                if conflicts:
                    health_status['warnings'].append(f'{len(conflicts)} conflitti pattern rilevati')
                    
            except Exception as e:
                health_status['checks']['conflicts_check'] = False
                health_status['errors'].append(f'Errore controllo conflitti: {str(e)}')
            
            # Determina stato generale
            if health_status['errors']:
                health_status['status'] = 'unhealthy'
            elif health_status['warnings']:
                health_status['status'] = 'degraded'
            
            return jsonify(health_status)
            
        except Exception as e:
            logger.error(f"Errore API health check: {e}")
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    @api_voip_cdr.route('categories/validate', methods=['POST'])
    @unified_api_admin_required
    def validate_category():
        """API per validare una categoria"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'Dati non validi'}), 400
            
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Validazioni base
            if not data.get('name'):
                validation_result['errors'].append('Nome categoria mancante')
            
            if not data.get('display_name'):
                validation_result['errors'].append('Nome visualizzato mancante')
            
            try:
                price = float(data.get('price_per_minute', 0))
                if price < 0:
                    validation_result['errors'].append('Prezzo non può essere negativo')
                elif price > 100:
                    validation_result['warnings'].append('Prezzo molto alto')
            except (ValueError, TypeError):
                validation_result['errors'].append('Prezzo non valido')
            
            patterns = data.get('patterns', [])
            if not patterns:
                validation_result['errors'].append('Almeno un pattern è obbligatorio')
            elif len(patterns) > 20:
                validation_result['warnings'].append('Molti pattern potrebbero rallentare il matching')
            
            # Validazione markup
            custom_markup = data.get('custom_markup_percent')
            if custom_markup is not None:
                try:
                    markup = float(custom_markup)
                    if markup < -100:
                        validation_result['errors'].append('Markup non può essere inferiore a -100%')
                    elif markup > 1000:
                        validation_result['errors'].append('Markup troppo alto')
                    elif markup > 500:
                        validation_result['warnings'].append('Markup molto alto')
                except (ValueError, TypeError):
                    validation_result['errors'].append('Valore markup non valido')
            
            validation_result['valid'] = len(validation_result['errors']) == 0
            
            return jsonify({
                'success': True,
                'validation': validation_result
            })
            
        except Exception as e:
            logger.error(f"Errore API validate: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
        
        
    @api_voip_cdr.route('categories/test-classification', methods=['POST'])
    @unified_api_admin_required
    def test_classification():
        """API per testare la classificazione di tipi di chiamata con markup"""
        try:
            data = request.get_json()
            if not data or 'call_types' not in data:
                return jsonify({'success': False, 'message': 'Dati non validi'}), 400
            
            call_types = data['call_types']
            duration_seconds = int(data.get('duration_seconds', 300))  # Default 5 minuti
            
            results = []
            
            for call_type in call_types:
                # Testa con markup
                classification = categories_manager.calculate_call_cost(call_type, duration_seconds)
                
                results.append({
                    'call_type': call_type,
                    'category_name': classification['category_name'],
                    'category_display': classification['category_display_name'],
                    'matched': classification['matched'],
                    'price_per_minute_base': classification.get('price_per_minute_base', 0),
                    'price_per_minute_with_markup': classification.get('price_per_minute_with_markup', 0),
                    'price_per_minute_used': classification.get('price_per_minute_used', 0),
                    'markup_percent': classification.get('markup_percent_applied', 0),
                    'markup_source': classification.get('markup_source', 'none'),
                    'markup_applied': classification.get('markup_applied', False),
                    'cost_calculated': classification['cost_calculated'],
                    'currency': classification['currency']
                })
            
            return jsonify({
                'success': True,
                'test_duration_seconds': duration_seconds,
                'global_markup_percent': categories_manager.global_markup_percent,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Errore API test classification: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # ############################# #
    # CONTRATTI     ############### #
    # #### ######################## #  

    @api_voip_cdr.route('contracts', methods=['GET'])
    @unified_api_admin_required
    def get_contracts_config():
        """
        API per ottenere la configurazione contratti salvata
        
        Returns:
            JSON con configurazione contratti corrente
        """
        try:
            contracts_file = Path(CONTACT_FILE)
            print(contracts_file)
            if not contracts_file.exists():
                return jsonify({
                    'success': False,
                    'message': 'File configurazione contratti non trovato',
                    'suggestion': 'Esegui prima estrazione codici contratto'
                })
            
            with open(contracts_file, 'r', encoding='utf-8') as f:
                contracts_data = json.load(f)
            
            return jsonify({
                'success': True,
                'config_file': str(contracts_file),
                'contracts_count': len(contracts_data.get('contracts', {})),
                'last_updated': contracts_data.get('metadata', {}).get('last_updated'),
                'data': contracts_data
            })
            
        except Exception as e:
            logger.error(f"Errore lettura configurazione: {e}")
            return jsonify({
                'success': False,
                'message': f'Errore lettura configurazione: {str(e)}'
            }), 500
        
    @api_voip_cdr.route('contracts/datatable/ajax', methods=['GET'])
    @unified_api_admin_required
    def contracts_datatable_ajax():
        """
        Endpoint per DataTables in modalità AJAX
        Restituisce tutti i dati in formato oggetto JSON
        """
           # Import del servizio (da aggiungere all'inizio del file contratti_routes.py)
        from app.voip_cdr.contratti import create_contracts_service
        
        # Crea istanza del servizio usando l'app Flask corrente
        contracts_service = create_contracts_service()
        try:
            logger.info("📋 Richiesta dati contratti per DataTables AJAX")
            
            # Recupera dati dal servizio
            data = contracts_service.get_contracts_for_ajax()
            
            if 'data' not in data:
                logger.error("Formato dati non valido dal servizio")
                return jsonify({
                    'data': [],
                    'error': 'Formato dati non valido'
                }), 500
            
            logger.info(f"✅ Restituiti {len(data['data'])} contratti in formato AJAX")
            # with open('output/contracts_output.json', 'w', encoding='utf-8') as f:
            #     json.dump(data, f, ensure_ascii=False, indent=2)
            return jsonify(data)
            
        except Exception as e:
            logger.error(f"❌ Errore endpoint AJAX: {e}")
            return jsonify({
                'data': [],
                'error': str(e)
            }), 500
        
    @api_voip_cdr.route('update_contract', methods=['POST'])
    @unified_api_admin_required
    def update_contract_info():
        """
        API per aggiornare informazioni di un contratto specifico
        
        Body JSON:
        {
            "contract_code": "12345",
            "contract_name": "Nome Cliente",
            "odoo_client_id": 8378,
            "contract_type": "A CONSUMO",
            "notes": "Note aggiuntive"
        }
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Dati non validi'
                }), 400
            
            contract_code = data.get('contract_code')
            if not contract_code:
                return jsonify({
                    'success': False,
                    'message': 'Codice contratto obbligatorio'
                }), 400
            
            # Carica configurazione esistente
            contracts_file = Path(CONTACT_FILE)
            
            if not contracts_file.exists():
                return jsonify({
                    'success': False,
                    'message': 'File configurazione contratti non trovato'
                }), 404
            
            with open(contracts_file, 'r', encoding='utf-8') as f:
                contracts_data = json.load(f)
            
            # Verifica esistenza contratto
            if str(contract_code) not in contracts_data.get('contracts', {}):
                return jsonify({
                    'success': False,
                    'message': f'Codice contratto {contract_code} non trovato'
                }), 404
            
            # Aggiorna informazioni contratto
            contract = contracts_data['contracts'][str(contract_code)]
            
            if 'contract_name' in data:
                contract['contract_name'] = data['contract_name'].strip() if data['contract_name'] is not None else None
            if 'odoo_client_id' in data:
                contract['odoo_client_id'] = data['odoo_client_id'].strip()
            if 'contract_type' in data:
                contract['contract_type'] = data['contract_type'].strip()
            if 'payment_term' in data:
                contract['payment_term'] = data['payment_term'].strip()
            if 'notes' in data:
                contract['notes'] = data['notes'].strip()
            
            contract['last_updated'] = datetime.now().isoformat()
            
            # Aggiorna metadata
            contracts_data['metadata']['last_updated'] = datetime.now().isoformat()
            contracts_data['metadata']['manual_updates'] = contracts_data['metadata'].get('manual_updates', 0) + 1
            
            # Salva configurazione aggiornata
            with open(contracts_file, 'w', encoding='utf-8') as f:
                json.dump(contracts_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Contratto {contract_code} aggiornato")
            
            return jsonify({
                'success': True,
                'message': f'Contratto {contract_code} aggiornato con successo',
                'updated_contract': contract
            })
            
        except Exception as e:
            logger.error(f"Errore aggiornamento contratto: {e}")
            return jsonify({
                'success': False,
                'message': f'Errore aggiornamento: {str(e)}'
            }), 500
        

    # Traffico VoIP clienti
    # @api_voip_cdr.route('clienti_traffico_voip/datatable/ajax', defaults={'periodo': None}, methods=['GET'])
    # @api_voip_cdr.route('clienti_traffico_voip/datatable/ajax/<periodo>', methods=['GET'])
    # @unified_api_admin_required
    # def clienti_traffico_voip(periodo):
    #     """
    #     Recupero dal file json aggregato le informazioni necessarie per popolare la tabella clienti
    #     """
    #     from app.voip_cdr.cdr_processor import CDRProcessor, CDRAggregator, CDRContractsGenerator, JSONFileManager, JSONAggregator
    #     if not periodo:
    #         nome_file = f"aggregate_files_{datetime.now().strftime('%Y_%m')}.json"
    #     else:
    #         nome_file = f"aggregate_files_{periodo}.json"
    #     try:
    #         logger.info("📋 Richiesta dati cliente per DataTables AJAX")
    #         print(f"Apro il file {nome_file}")
    #         aggregate_json_file = Path(ANALYTICS_OUTPUT_FOLDER) / datetime.now().strftime('%Y') / nome_file
    #         json_manager = JSONFileManager()
    #         datatables_json = json_manager.transform_from_multiple_files([aggregate_json_file])
            
    #         # with open('output/contracts_output.json', 'w', encoding='utf-8') as f:
    #         #     json.dump(data, f, ensure_ascii=False, indent=2)
    #         # return json.dumps(datatables_json, indent=4)
    #         return jsonify(datatables_json)

        
    #     except Exception as e:
    #         logger.error(f"❌ Errore endpoint AJAX: {e}")
    #         return jsonify({
    #             'data': [],
    #             'error': str(e)
    #         }), 500    
    @api_voip_cdr.route('clienti_traffico_voip/datatable/ajax', defaults={'periodo': None}, methods=['GET'])
    @api_voip_cdr.route('clienti_traffico_voip/datatable/ajax/<periodo>', methods=['GET'])
    @unified_api_admin_required
    # @admin_required
    def clienti_traffico_voip(periodo):
        """
        Recupera dati cliente per DataTables da JSON aggregati, filtrando per anno o anno+mese.
        """
        from app.voip_cdr.cdr_processor import (
            JSONFileManager,
            JSONAggregator,
        )
        now = datetime.now()

        try:
            if not periodo:
                # Nessun parametro → mese corrente
                anno = now.strftime('%Y')
                mese = now.strftime('%m')
                file_path = Path(ANALYTICS_OUTPUT_FOLDER) / anno / f"aggregate_files_{anno}_{mese}.json"

                logger.info(f"📋 Richiesta dati cliente per mese corrente: {anno}_{mese}")
                json_manager = JSONFileManager()
                datatables_json = json_manager.transform_from_multiple_files([file_path])
                return jsonify(datatables_json)

            parts = periodo.split("_")

            if len(parts) == 1:
                # ✅ Solo anno → aggregazione dinamica dei file annuali
                anno = parts[0]
                path = Path(ANALYTICS_OUTPUT_FOLDER) / anno

                logger.info(f"📋 Richiesta aggregata per l'anno intero: {anno}")
                aggregator = JSONAggregator()
                result = aggregator.aggregate_files(path)

                json_manager = JSONFileManager()
                datatables_json = json_manager.transform_from_string(json.dumps(result, indent=4))
                return jsonify(datatables_json)

            elif len(parts) == 2:
                # ✅ Anno e mese → singolo file
                anno, mese = parts

                if not mese.isdigit() or not (1 <= int(mese) <= 12):
                    return jsonify({"data": [], "error": f"Mese non valido: {mese}"}), 400

                nome_file = f"aggregate_files_{anno}_{mese}.json"
                file_path = Path(ANALYTICS_OUTPUT_FOLDER) / anno / nome_file

                logger.info(f"📋 Richiesta dati cliente per mese specifico: {anno}_{mese}")
                json_manager = JSONFileManager()
                datatables_json = json_manager.transform_from_multiple_files([file_path])
                return jsonify(datatables_json)

            else:
                return jsonify({"data": [], "error": "Formato periodo non valido"}), 400

        except Exception as e:
            logger.error(f"❌ Errore endpoint AJAX: {e}")
            return jsonify({'data': [], 'error': str(e)}), 500
        

    # Aggiunge il traffico voip extra soglia sugli abbonamenti di ODOO
    @api_voip_cdr.route('genera_extra_soglia', methods=['POST'])
    @unified_api_admin_required
    def genera_extra_soglia():
        """
        API per ottenere la configurazione contratti salvata
        
        Returns:
            JSON con configurazione contratti corrente
        """
        try:
             # Inserisce il traffico voip extra soglia nel contratto corrente del cliente su ODOO
            from app.voip_cdr.fatturazione import processa_contratti_attivi
            periodo = request.get_json()
            result = processa_contratti_attivi(periodo)
            
            if isinstance(result, (dict, list)):
                # print(json.dumps(result, indent=4, ensure_ascii=False))
                return json.dumps(result, indent=4, ensure_ascii=False)
            else:
                # print(result)
                return result
            # return jsonify({
            #     'success': True,
            #     'config_file': str(contracts_file),
            #     'contracts_count': len(contracts_data.get('contracts', {})),
            #     'last_updated': contracts_data.get('metadata', {}).get('last_updated'),
            #     'data': contracts_data
            # })
            
        except Exception as e:
            logger.error(f"Errore lettura configurazione: {e}")
            return jsonify({
                'success': False,
                'message': f'Errore lettura configurazione: {str(e)}'
            }), 500
        
    # Aggiunge il traffico voip extra soglia sugli abbonamenti di ODOO
    @api_voip_cdr.route('aggiorna_dati_ftp', methods=['POST'])
    @unified_api_admin_required
    def aggiorna_dati_ftp():
        """
        API per scaricare dall'ftp tutti i CDR aggiornati
        
        Returns:
            JSON con configurazione contratti corrente
        """
        try:
            from app.voip_cdr.ftp_downloader import FTPDownloader
            downloader = FTPDownloader()

            data = request.get_json()
            
            pattern = data.get('pattern')
            test_ftp = data.get('test_ftp', False)

            if(not pattern):
                pattern_to_use = SPECIFIC_FILENAME
            else:
                pattern_to_use = pattern   

            if(not test_ftp):
                test_ftp_to_use = FTP_TEST
            else:
                test_ftp_to_use = test_ftp   

            # ✅ Chiama il metodo sull'istanza
            ftp_response = downloader.process_files(pattern_to_use, test_ftp_to_use) #'RIV_20943_%Y-%m*.CDR', False

            logger.info(f"Risultato: {ftp_response} ")

            if(ftp_response['success'] == True):      
                # Elenco di file scaricati dall'ftp
                files = ftp_response['files']
                # files = ['RIV_15232_MESE_1_2025-02-03-13.19.21.CDR']

                # Carico le classi necessarie
                from app.voip_cdr.cdr_processor import CDRProcessor, CDRAggregator, CDRContractsGenerator, JSONFileManager, JSONAggregator

                # Converte ogni CDR scaricato in un json inserendo già i prezzi con markup secondo la tabella nel json categorie 
                processor = CDRProcessor(files[0])
                json_to_cdr = json.loads(processor.process_files(files, riprocessa=True))
                json_file = json_to_cdr['nome_file']
            
                # Genera il json dei contatti attivi estrapolandoli dal CDR
                generator = CDRContractsGenerator(json_file)
                generator.save_contracts_json()
                print(json_file)

                # Unisce tutti i json appena elaborati in un unico json, aggrega le chiamate per ogni singolo Cliente(contratto), 
                # genera un record di costo totale per ogni categoria oltre ad un record costo globale che somma tutte le categorie. 
                aggregator = CDRAggregator()
                aggregate_json = aggregator.aggregate_cdr_data(json_file)
                print (aggregate_json)

                # Genera un file json per ogni Cliente (contratto) con tutti idati presenti nel json globale.
                aggregate_json_file = aggregate_json['file_name']
                detailed_json = aggregator.split_aggregate_to_contracts(aggregate_json_file)
                return detailed_json
            else:
                logger.error(f"Errore lettura configurazione: {ftp_response}")
                return jsonify({
                'success': False,
                'message': f'Errore lettura configurazione: {str(ftp_response)}'
            }), 500
            
        except Exception as e:
            logger.error(f"Errore lettura configurazione: {e}")
            return jsonify({
                'success': False,
                'message': f'Errore lettura configurazione: {str(e)}'
            }), 500