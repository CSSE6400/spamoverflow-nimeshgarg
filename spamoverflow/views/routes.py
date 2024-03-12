from flask import Blueprint, jsonify, request, make_response
from spamoverflow.models.email_data import EmailData, Status
from datetime import datetime
import re
from urllib.parse import urlparse
from spamoverflow.models import db

api = Blueprint('api', __name__, url_prefix='/api/v1')

# 0 - unhealthy
# 1 - healthly 
# 2 - backlog
health = 1

validation_error = ""


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
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)
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
        return make_response(jsonify({"error": str(e)}), 400)

    except Exception as e:
        return make_response(jsonify({"error": "An unknown error occurred."}), 500)
    
@api.route('/customers/<string:customer_id>/emails', methods=['POST'])
def post_email(customer_id):
    try:
        # Extract data from the request
        data = request.get_json()

        # # Validate customer_id
        # if not validate_uuid4(customer_id):
        #     return make_response(jsonify({"error": "Invalid customer_id"}), 400)

        # Validate request body
        if not validate_request_body(data):
            return make_response(jsonify({"error": "Invalid request body","error":validation_error}), 400)

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
            domains=extract_domains(data['contents']['body']),
            spamhammer_metadata=data['metadata']['spamhammer']
        )

        # Save the email to the database
        db.session.add(email)
        db.session.commit()

        return jsonify(email.to_dict()), 201

    except Exception as e:
        print(e)
        return make_response(jsonify({"error": "An unknown error occurred.","error":e}), 500)