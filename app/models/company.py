from app import db
from datetime import datetime
import uuid
from sqlalchemy import func
from app.utils.env_manager import *
from sqlalchemy.orm import aliased

related_companies = db.Table('related_companies',
    db.Column('main_company_uid', db.String(255), db.ForeignKey('companies.uid'), primary_key=True),
    db.Column('related_company_uid', db.String(255), db.ForeignKey('companies.uid'), primary_key=True)
)

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    odoo_id = db.Column(db.String(255), nullable=True, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    nome_societa = db.Column(db.String(255), nullable=True)
    indirizzo = db.Column(db.String(150), nullable=True)
    cap = db.Column(db.String(6), nullable=True)
    citta = db.Column(db.String(45), nullable=True)
    telefono = db.Column(db.String(15), nullable=True)
    fax = db.Column(db.String(15), nullable=True)
    e_mail = db.Column(db.String(45), nullable=True)
    pec = db.Column(db.String(100), nullable=True)
    sito_web = db.Column(db.String(150), nullable=True)
    partita_iva = db.Column(db.String(20), nullable=True)
    codice_fiscale = db.Column(db.String(25), nullable=True)
    codice_univoco = db.Column(db.String(100), nullable=True)
    societa_di_riferimento = db.Column(db.String(255), nullable=True)
    main_company = db.Column(db.String(3), nullable=True)
    tipologia = db.Column(db.Integer, nullable=True)
    categoria = db.Column(db.Integer, nullable=True)
    note = db.Column(db.Text, nullable=True)
    logo = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    json = db.Column(db.Text, nullable=True)
    token = db.Column(db.String(100), nullable=True)
    societa_principale = db.Column(db.Boolean, default=False)
    companycol = db.Column(db.String(45), nullable=True)
    
    related_companies = db.relationship(
        'Company',
        secondary=related_companies,
        primaryjoin=uid==related_companies.c.main_company_uid,
        secondaryjoin=uid==related_companies.c.related_company_uid,
        backref='related_to'
    )

    # Relazione con users
    users = db.relationship('User', back_populates='company')

    # Relazione master-slave: una company può essere master di altre
    master_company_uid = db.Column(db.String(255), db.ForeignKey('companies.uid'), nullable=True)
    
    # Relazioni
    # Una company master può avere più companies slave
    slave_companies = db.relationship('Company', 
                                    backref=db.backref('master_company', remote_side=[uid]),
                                    foreign_keys=[master_company_uid])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.uid:
            self.uid = str(uuid.uuid4())
            
    @property
    def avatar_url(self):
        """Restituisce URL dell'avatar (immagine o placeholder)"""
        if self.logo:
            # Controlla se il file esiste
            # static_path = f"app/static/{self.profile_image}"
            static_path = AVATAR_FOLDER
            if os.path.exists(static_path):
                return f"{AVATAR_URL}/{self.logo}"
        
        # Genera avatar con iniziali usando servizio esterno
        return f"https://ui-avatars.com/api/?name={self.nome_societa}&background=30a257&color=fff&size=128"
    
    @property
    def related_children_summary(self):
        return [
            {'uid': c.uid, 'nome_societa': c.nome_societa}
            for c in self.related_companies
        ]
    
    @classmethod
    def get_master_companies(cls):
        """Restituisce tutte le company master"""
        return cls.query.filter_by(societa_principale=True, is_active=True).all()
    
    @classmethod
    def get_slave_companies(cls, master_uid=None):
        """Restituisce le company slave, optionally filtrate per master"""
        query = cls.query.filter(cls.master_company_uid.isnot(None), cls.is_active.is_(None))
        if master_uid:
            query = query.filter_by(master_company_uid=master_uid)
        return query.all()
    
    @classmethod
    def find_by_name(cls, nome_societa):
        """Trova utente per nome società (case-insensitive)"""
        return cls.query.filter(func.lower(cls.nome_societa) == func.lower(nome_societa)).first()
    
    @classmethod
    def find_by_e_mail(cls, e_mail):
        """Trova utente per e_mail (case-insensitive)"""
        return cls.query.filter(func.lower(cls.e_mail) == func.lower(e_mail)).first()
    
    @classmethod
    def find_related_companies_summary(cls, uid):
        company = cls.query.filter_by(uid=uid).first()
        if not company:
            return []
        return [
            {'uid': c.uid, 'nome_societa': c.nome_societa}
            for c in company.related_companies
        ]
    
    @classmethod
    def find_related_companies_summary_for_select(cls, uid):
        company = cls.query.filter_by(uid=uid).first()
        if not company:
            return []
        return [c.uid for c in company.related_companies]
    
    @classmethod
    def get_all_for_select(cls):
        results = db.session.query(cls.uid, cls.nome_societa).order_by(cls.nome_societa).all()
        return [{'id': uid, 'text': nome} for uid, nome in results]

    @classmethod
    def get_companies_with_related_summary(cls):
        slave = aliased(Company)

        # Ottieni tutte le company principali con i related uniti (via outerjoin)
        query = (
            db.session.query(cls, slave)
            .outerjoin(cls.related_companies.of_type(slave))
            .all()
        )

        summary = {}

        for company, related in query:
            uid = company.uid
            if uid not in summary:
                # Usa to_dict o costruisci tutti i campi manualmente
                company_data = company.to_dict() if hasattr(company, "to_dict") else {
                    "uid": company.uid,
                    "id": company.id,
                    "nome_societa": company.nome_societa,
                    "partita_iva": company.partita_iva,
                    "e_mail": company.e_mail,
                    "telefono": company.telefono,
                    "created_at": company.created_at.isoformat() if company.created_at else None,
                    "pec": company.pec,
                    "indirizzo": company.indirizzo,
                    "citta": company.citta,
                    "cap": company.cap,
                    "codice_fiscale": company.codice_fiscale,
                    "codice_univoco": company.codice_univoco,
                    "sito_web": company.sito_web,
                    "is_active": company.is_active,
                    "societa_principale": company.societa_principale,
                    "slaves_count": len(company.related_companies),
                    "logo": company.logo_url if hasattr(company, "logo_url") else None
                }

                company_data["related_children"] = []
                summary[uid] = company_data

            # Aggiungi il related se presente
            if related:
                summary[uid]["related_children"].append({
                    "uid": related.uid,
                    "nome_societa": related.nome_societa
                })

        return list(summary.values())





    def set_as_master(self):
        """Imposta questa company come master"""
        self.societa_principale = True
        self.master_company_uid = None  # Una master non può avere un master
        db.session.commit()
    
    def set_as_slave(self, master_company_uid):
        """Imposta questa company come slave di un'altra"""
        master_company = Company.query.get(master_company_uid)
        if not master_company:
            raise ValueError("Company master non trovata")
        if master_company.societa_principale != True:
            raise ValueError("La company specificata non è una master")
        
        self.societa_principale = False
        self.master_company_uid = master_company_uid
        db.session.commit()
    
    def remove_from_master(self):
        """Rimuove questa company da qualsiasi master"""
        self.master_company_uid = None
        db.session.commit()
    
    def get_all_slaves(self):
        """Restituisce tutte le company slave di questa master (ricorsivo)"""
        if self.societa_principale != True:
            return []
        
        slaves = []
        direct_slaves = self.slave_companies
        
        for slave in direct_slaves:
            slaves.append(slave)
            # Aggiunge anche le slave delle slave (se esistono)
            slaves.extend(slave.get_all_slaves())
        
        return slaves
    
    def is_master(self):
        """Controlla se questa company è master"""
        return self.societa_principale == True
    
    def is_slave(self):
        """Controlla se questa company è slave"""
        return self.master_company_uid is not None
    
    def is_currently_active(self):
        """Controlla se la company è attiva"""
        return self.is_active == False and self.is_active != True
    
    def soft_delete(self):
        """Eliminazione soft della company"""
        self.is_active = False
        db.session.commit()
    
    def restore(self):
        """Ripristina una company eliminata"""
        self.is_active = True
        db.session.commit()
    
    def to_dict(self):
        """Converte il modello in dizionario"""
        return {
            'id': self.id,
            'uid': self.uid,
            'odoo_id': self.odoo_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'nome_societa': self.nome_societa,
            'indirizzo': self.indirizzo,
            'cap': self.cap,
            'citta': self.citta,
            'telefono': self.telefono,
            'fax': self.fax,
            'e_mail': self.e_mail,
            'pec': self.pec,
            'sito_web': self.sito_web,
            'partita_iva': self.partita_iva,
            'codice_fiscale': self.codice_fiscale,
            'codice_univoco': self.codice_univoco,
            'societa_di_riferimento': self.societa_di_riferimento,
            'main_company': self.main_company,
            'tipologia': self.tipologia,
            'categoria': self.categoria,
            'logo': self.avatar_url,
            'is_active': self.is_active,
            'json': self.json,
            'token': self.token,
            'societa_principale': self.societa_principale,
            'companycol': self.companycol,
            'master_company_id': self.master_company_uid,
            'master_company_name': self.master_company.nome_societa if self.master_company else None,
            'slaves_count': len(self.slave_companies) if self.is_master() else 0,
            
            # 'related_children': [c.uid for c in self.related_companies],
            # 'related_parents': [c.uid for c in self.related_to],

            # 'related_children_complete': [
            #     {'uid': c.uid, 'nome_societa': c.nome_societa}
            #     for c in self.related_companies
            # ],
            # 'related_children_complete': [
            #     {'uid': c.uid, 'nome_societa': c.nome_societa}
            #     for c in self.related_to
            # ]
        }
    
    def __repr__(self):
        return f'<Company {self.nome_societa}>'