import datetime
from enum import Enum
from . import db

class Status (Enum):
    pending = "pending"
    scanned = "scanned"
    failed = "failed"

class EmailData(db.Model):
    __tablename__ = 'email_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True, index=True)
    customer_id = db.Column(db.String(255), nullable=False)
    #first 4 characters of the customer id make the priority
    priority = db.Column(db.String(4), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    body = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    from_email = db.Column(db.String(255), nullable=False)
    to_email = db.Column(db.String(255), nullable=False)
    state = db.Column(db.Enum(Status), default=Status.pending, nullable=False)
    malicious = db.Column(db.Boolean, default=False, nullable=False)
    domains = db.Column(db.String(255), nullable=False)
    spamhammer_metadata = db.Column(db.JSON, nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "contents": {
                "from": self.from_email,
                "to": self.to_email,
                "subject": self.subject,
                # "body": self.body
            },
            "status": self.state.value,
            "malicious": self.malicious,
            "domains": self.domains.split(",") if self.domains else [],
            "metadata": {
                "spamhammer": self.spamhammer_metadata
            }
        }