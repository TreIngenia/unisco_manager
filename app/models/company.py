from app import db
from datetime import datetime
import uuid

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.String(100), nullable=True, unique=True)
    odoo_id = db.Column(db.String(255), nullable=True, unique=True)
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(150), nullable=True)
    postal_code = db.Column(db.String(6), nullable=True)
    city = db.Column(db.String(45), nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    fax = db.Column(db.String(15), nullable=True)
    e_mail = db.Column(db.String(45), nullable=True)
    pec = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(150), nullable=True)
    vat_number = db.Column(db.String(20), nullable=True)
    fiscal_code = db.Column(db.String(25), nullable=True)
    mail_domain = db.Column(db.Text, nullable=True)
    unique_code_ita = db.Column(db.String(100), nullable=True)
    reference_company = db.Column(db.String(100), nullable=True)
    main_company = db.Column(db.String(3), nullable=True)
    typology = db.Column(db.Integer, nullable=True)
    category = db.Column(db.Integer, nullable=True)
    note = db.Column(db.Text, nullable=True)
    logo = db.Column(db.Text, nullable=True)
    active = db.Column(db.String(3), default='SI')
    deleted = db.Column(db.String(3), nullable=True)
    json = db.Column(db.Text, nullable=True)
    token = db.Column(db.String(100), nullable=True)
    master = db.Column(db.String(5), default='FALSE')
    companycol = db.Column(db.String(45), nullable=True)
    
    # Relazione master-slave: una company può essere master di altre
    master_company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    
    # Relazioni
    # Una company master può avere più companies slave
    slave_companies = db.relationship('Company', 
                                    backref=db.backref('master_company', remote_side=[id]),
                                    foreign_keys=[master_company_id])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.uid:
            self.uid = str(uuid.uuid4())
    
    @classmethod
    def get_master_companies(cls):
        """Restituisce tutte le company master"""
        return cls.query.filter_by(master='TRUE', deleted=None).all()
    
    @classmethod
    def get_slave_companies(cls, master_id=None):
        """Restituisce le company slave, optionally filtrate per master"""
        query = cls.query.filter(cls.master_company_id.isnot(None), cls.deleted.is_(None))
        if master_id:
            query = query.filter_by(master_company_id=master_id)
        return query.all()
    
    def set_as_master(self):
        """Imposta questa company come master"""
        self.master = 'TRUE'
        self.master_company_id = None  # Una master non può avere un master
        db.session.commit()
    
    def set_as_slave(self, master_company_id):
        """Imposta questa company come slave di un'altra"""
        master_company = Company.query.get(master_company_id)
        if not master_company:
            raise ValueError("Company master non trovata")
        if master_company.master != 'TRUE':
            raise ValueError("La company specificata non è una master")
        
        self.master = 'FALSE'
        self.master_company_id = master_company_id
        db.session.commit()
    
    def remove_from_master(self):
        """Rimuove questa company da qualsiasi master"""
        self.master_company_id = None
        db.session.commit()
    
    def get_all_slaves(self):
        """Restituisce tutte le company slave di questa master (ricorsivo)"""
        if self.master != 'TRUE':
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
        return self.master == 'TRUE'
    
    def is_slave(self):
        """Controlla se questa company è slave"""
        return self.master_company_id is not None
    
    def is_active(self):
        """Controlla se la company è attiva"""
        return self.active == 'SI' and self.deleted != 'SI'
    
    def soft_delete(self):
        """Eliminazione soft della company"""
        self.deleted = 'SI'
        self.active = 'NO'
        db.session.commit()
    
    def restore(self):
        """Ripristina una company eliminata"""
        self.deleted = None
        self.active = 'SI'
        db.session.commit()
    
    def to_dict(self):
        """Converte il modello in dizionario"""
        return {
            'id': self.id,
            'uid': self.uid,
            'odoo_id': self.odoo_id,
            'date_time': self.date_time.isoformat() if self.date_time else None,
            'name': self.name,
            'address': self.address,
            'postal_code': self.postal_code,
            'city': self.city,
            'phone': self.phone,
            'fax': self.fax,
            'e_mail': self.e_mail,
            'pec': self.pec,
            'website': self.website,
            'vat_number': self.vat_number,
            'fiscal_code': self.fiscal_code,
            'unique_code_ita': self.unique_code_ita,
            'reference_company': self.reference_company,
            'main_company': self.main_company,
            'typology': self.typology,
            'category': self.category,
            'logo': self.logo,
            'active': self.active,
            'json': self.json,
            'token': self.token,
            'master': self.master,
            'companycol': self.companycol,
            'master_company_id': self.master_company_id,
            'master_company_name': self.master_company.name if self.master_company else None,
            'slaves_count': len(self.slave_companies) if self.is_master() else 0
        }
    
    def __repr__(self):
        return f'<Company {self.name}>'