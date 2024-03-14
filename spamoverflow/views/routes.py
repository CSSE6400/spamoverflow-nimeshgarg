import json
import os
import subprocess
from flask import Blueprint, jsonify, request
from spamoverflow.models.email_data import EmailData, Status
from datetime import datetime
import re
from urllib.parse import urlparse
from spamoverflow.models import db
from sqlalchemy import func

api = Blueprint('api', __name__, url_prefix='/api/v1')

# 0 - unhealthy
# 1 - healthly 
# 2 - backlog
health = 1

validation_error = ""

#first 4 characters should be integer
def validate_uuid4(uuid_string):
    try:
        int(uuid_string[:4])
        return True
    except ValueError:
        return False


def validate_request_body(data):
    # Check if required fields are present
    required_fields = ['metadata', 'contents']
    if not all(field in data for field in required_fields):
        validation_error = "metadata/contents not found"
        return False

    # Check if required fields are present in 'contents'
    required_contents_fields = ['from', 'to', 'subject', 'body']
    if not all(field in data['contents'] for field in required_contents_fields):
        validation_error = "contents"
        return False

    # Check if required fields are present in 'metadata'
    required_metadata_fields = ['spamhammer']
    if not all(field in data['metadata'] for field in required_metadata_fields):
        validation_error = "metadata"
        return False

    return True

def extract_domains(body):
    # Find all URLs in the body
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, body)

    # Extract domains from the URLs
    domains = [urlparse(url).netloc for url in urls]

    # remove dulicates
    domains = list(set(domains))

    # Join the domains into a string with commas
    domains_string = ",".join(domains)

    return domains_string

@api.route('/health', methods=['GET'])
def health():
    if health == 0:
        return jsonify({"status":"Unhealthy"}),500
    elif health == 2:
        return jsonify({"status":"Backlog"}),503
    else:
        return jsonify({"status":"Healthy"}),200

@api.route('/customers/<string:uuidV4>/emails', methods=['GET'])
def get_emails(uuidV4):
    try:
        limit = request.args.get('limit', type=int, default=100)
        offset = request.args.get('offset', type=int, default=0)
        start = request.args.get('start', type=str)
        end = request.args.get('end', type=str)
        from_email = request.args.get('from', type=str)
        to_email = request.args.get('to', type=str)
        state = request.args.get('state', default=None, type=str)
        only_malicious = request.args.get('only_malicious', default=False, type=bool)

        query = EmailData.query.filter_by(customer_id=uuidV4)

        if start:
            start = datetime.fromisoformat(start)
            query = query.filter(EmailData.submitted_date >= start)

        if end:
            end = datetime.fromisoformat(end)
            query = query.filter(EmailData.submitted_date <= end)

        if from_email:
            query = query.filter(EmailData.from_email == from_email)

        if to_email:
            query = query.filter(EmailData.to_email == to_email)

        if state:
            query = query.filter(EmailData.state == state)

        if only_malicious:
            query = query.filter(EmailData.malicious == True)

        emails = query.limit(limit).offset(offset).all()

        return jsonify([email.to_dict() for email in emails]), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": "An unknown error occurred.","specific":str(e)}), 500
    
@api.route('/customers/<string:customer_id>/emails', methods=['POST'])
def post_email(customer_id):
    try:
        # Extract data from the request
        data = request.get_json()

        # Validate customer_id
        if not validate_uuid4(customer_id):
            return jsonify({"error": "Invalid customer_id","error":"Invalid Customer ID format"}), 400

        # Validate request body
        if not validate_request_body(data):
            return jsonify({"error": "Invalid request body","error":validation_error}), 400

        # Create a new EmailData object
        email = EmailData(
            customer_id=customer_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            from_email=data['contents']['from'],
            to_email=data['contents']['to'],
            subject=data['contents']['subject'],
            body=data['contents']['body'],
            state=Status.pending,
            # malicious=False,
            priority=customer_id[:4],
            domains=extract_domains(data['contents']['body']),
            spamhammer_metadata=data['metadata']['spamhammer']
        )

        # Save the email to the database
        db.session.add(email)
        db.session.commit()

        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        if not os.path.exists("inputs"):
            os.makedirs("inputs")
            
        dictionary  = {
            'id': f"{email.id}",
            'content':email.body,
            'metadata':email.spamhammer_metadata
        }
        print(str(dictionary))
        
        json_object = json.dumps(dictionary, indent=4) 

        with open(f"inputs/{email.id}.json", "w") as outfile:
            outfile.write(json_object)
        
        # subprocess.run(["pwd"])
        # subprocess.run([f"./spamhammer scan --input inputs/{email.id}.json --output outputs/{email.id}"])
            
        os.system(f"./spamhammer scan --input inputs/{email.id}.json --output outputs/{email.id}")

        if os.path.exists(f"outputs/{email.id}.json"):
            with open(f"outputs/{email.id}.json") as f:
                data = json.load(f)
                email.malicious = data['malicious']
                email.state = Status.scanned
                email.updated_at = datetime.now()
                db.session.commit()

        return jsonify(email.to_dict()), 201

    except Exception as e:
        return jsonify({"error": "An unknown error occurred.","specific":str(e)}), 500
    

@api.route('/customers/<string:customer_id>/emails/<int:id>', methods=['GET'])
def get_email(customer_id, id):
    try:
        # Extract data from the request
        data = request.get_json()
        # Validate customer_id
        if not validate_uuid4(customer_id):
            return jsonify({"error": "Invalid customer_id"}), 400
        
        email = EmailData.query.filter_by(customer_id=customer_id, id=id)
        print(str(email))
        if email:
            return jsonify(email.to_dict()), 200
        else:
            email = EmailData.query.filter_by(customer_id=customer_id)
            if email:
                return jsonify({"error": "ID not found"}), 404
            else:
                return jsonify({"error": "Customer not found"}), 404

    except Exception as e:
         return jsonify({"error": "An unknown error occurred.","specific":str(e)}), 500

@api.route('/customers/<string:customer_id>/reports/actors', methods=['GET'])
def get_malicious_senders(customer_id):
    try:
        # Validate customer_id
        if not validate_uuid4(customer_id):
            return jsonify({"error": "Invalid customer_id"}), 400

        # Query the database for malicious senders
        malicious_senders = db.session.query(
            EmailData.from_email.label('id'),
            func.count(EmailData.id).label('count')
        ).filter(
            EmailData.customer_id == customer_id,
            EmailData.malicious == True
        ).group_by(
            EmailData.from_email
        ).all()

        # Prepare the response
        response = {
            "generated_at": datetime.now().isoformat(),
            "total": len(malicious_senders),
            "data": [sender._asdict() for sender in malicious_senders]
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": "An unknown error occurred.", "specific": str(e)}), 500

@api.route('/customers/<string:customer_id>/reports/domains', methods=['GET'])
def get_malicious_domains(customer_id):
    try:
        # Validate customer_id
        if not validate_uuid4(customer_id):
            return jsonify({"error": "Invalid customer_id"}), 400

        # Query the database for malicious domains
        malicious_domains = db.session.query(
            EmailData.domains.label('id'),
            func.count(EmailData.id).label('count')
        ).filter(
            EmailData.customer_id == customer_id,
            EmailData.malicious == True
        ).group_by(
            EmailData.domains
        ).all()

        # Prepare the response
        response = {
            "generated_at": datetime.now().isoformat(),
            "total": len(malicious_domains),
            "data": [domain._asdict() for domain in malicious_domains]
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": "An unknown error occurred.", "specific": str(e)}), 500

@api.route('/customers/<string:customer_id>/reports/recipients', methods=['GET'])
def get_recipients_of_malicious_emails(customer_id):
    try:
        # Validate customer_id
        if not validate_uuid4(customer_id):
            return jsonify({"error": "Invalid customer_id"}), 400

        # Query the database for recipients of malicious emails
        malicious_recipients = db.session.query(
            EmailData.to_email.label('id'),
            func.count(EmailData.id).label('count')
        ).filter(
            EmailData.customer_id == customer_id,
            EmailData.malicious == True
        ).group_by(
            EmailData.to_email
        ).all()

        # Prepare the response
        response = {
            "generated_at": datetime.now().isoformat(),
            "total": len(malicious_recipients),
            "data": [recipient._asdict() for recipient in malicious_recipients]
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": "An unknown error occurred.", "specific": str(e)}), 500