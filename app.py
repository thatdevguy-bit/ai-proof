import os
import requests
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
import hashlib

from database import init_db, save_dataset, get_dataset_by_id, get_recent_datasets


# Load environment variables from .env file
load_dotenv()

# Create Flask application
app = Flask(__name__)

# Initialize database on startup
init_db()

# Get API key from environment
TATUM_API_KEY = os.getenv('TATUM_API_KEY')

# Walrus upload endpoint
WALRUS_UPLOAD_URL = "https://api.tatum.io/v4/data/storage/upload"

# Headers for Tatum API calls
HEADERS = {"x-api-key": TATUM_API_KEY}

@app.route('/')
def index():
    """Homepage - shows upload form"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_dataset():
    """Handles file upload and stores to Walrus"""
    # 1. get the form data
    name = request.form.get('name')
    description = request.form.get('description')
    source = request.form.get('source')
    license_type = request.form.get('license')
    email = request.form.get('email')
    file = request.files.get('file')
    
    if not file:
        return "No File provided", 400
    
    if not email:
        return "Email required", 400
    
    # 2. Read file content
    file_content = file.read()

    # 3. Upload file to Walrus
    files = {'file': (file.filename, file_content, file.content_type)}
    walrus_response = requests.post(WALRUS_UPLOAD_URL, files=files, headers=HEADERS)
    
    if walrus_response.status_code != 201:
        return f"Upload failed: {walrus_response.text}", 500

    walrus_data = walrus_response.json()
    blob_id = walrus_data.get('blobId')
    job_id = walrus_data.get('jobId')

    # 4. Create metadata JSON and upload to Walrus
    metadata = {
        'name': name,
        'description': description,
        'source': source,
        'license': license_type,
        'uploaded_at': datetime.utcnow().isoformat(),
        'original_filename': file.filename,
        'file_blob_id': blob_id,
        'email': email
    }

    metadata_response = requests.post(
        WALRUS_UPLOAD_URL,
        files={'file': ('metadata.json', json.dumps(metadata), 'application/json')},
        headers=HEADERS
    )

    if metadata_response.status_code != 201:
        return f"Metadata upload failed", 500
    
    metadata_blob_id = metadata_response.json().get('blobId')
    
    # 5. Generate a unique ID for this dataset
    
    dataset_id = hashlib.sha256(f"{blob_id}{metadata_blob_id}".encode()).hexdigest()[:16]
    
    # Save to database with email
    save_dataset(
        dataset_id=dataset_id,
        name=name,
        description=description,
        source=source,
        license=license_type,
        email=email,
        file_blob_id=blob_id,
        metadata_blob_id=metadata_blob_id
        )
    
    # show verification page
    return render_template('verify.html',
        dataset_id=dataset_id,
        blob_id=blob_id,
        metadata_blob_id=metadata_blob_id,
        metadata=metadata,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        verification_hash=hashlib.sha256(f"{blob_id}{metadata_blob_id}".encode()).hexdigest()[:32]
    )


@app.route('/verify/<dataset_id>')
def verify_dataset(dataset_id):
    """Shows verification page for a specific dataset"""
    dataset = get_dataset_by_id(dataset_id)
    
    if not dataset:
        return "Dataset not found", 404
    
    return render_template('verify.html',
        dataset_id=dataset['dataset_id'],
        blob_id=dataset['file_blob_id'],
        metadata_blob_id=dataset['metadata_blob_id'],
        metadata={
            'name': dataset['name'],
            'description': dataset['description'],
            'source': dataset['source'],
            'license': dataset['license']
        },
        timestamp=dataset['created_at'],
        verification_hash=hashlib.sha256(f"{dataset['file_blob_id']}{dataset['metadata_blob_id']}".encode()).hexdigest()[:32]
    )
    
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)

    