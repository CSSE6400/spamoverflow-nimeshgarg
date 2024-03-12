from . import db
import datetime
from enum import Enum

class DomainType (Enum):
    sender = "sender"
    recipient = "recipient"
    domain = "domain"

class DomainData(db.Model):
    __tablename__ = 'domain_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True, index=True)
    customer_id = db.Column(db.String(255), nullable=False)
    actor = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Enum(DomainType), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    count = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {
            "generated_at": datetime.datetime.utcnow(),
            "id": self.actor,
            "count" : self.count
        }