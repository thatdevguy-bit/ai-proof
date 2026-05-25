import sqlite3
import json
from datetime import datetime

DB_PATH = 'ai_proof.db'

def init_db():
    """Create tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            source TEXT,
            license TEXT,
            email TEXT NOT NULL,
            file_blob_id TEXT NOT NULL,
            metadata_blob_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def save_dataset(dataset_id, name, description, source, license, email, file_blob_id, metadata_blob_id):
    """Save dataset record to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO datasets (dataset_id, name, description, source, license, email, file_blob_id, metadata_blob_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (dataset_id, name, description, source, license, email, file_blob_id, metadata_blob_id))
    
    conn.commit()
    conn.close()

def get_dataset_by_id(dataset_id):
    """Retrieve dataset by its ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM datasets WHERE dataset_id = ?', (dataset_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'dataset_id': row[1],
            'name': row[2],
            'description': row[3],
            'source': row[4],
            'license': row[5],
            'email': row[6],
            'file_blob_id': row[7],
            'metadata_blob_id': row[8],
            'created_at': row[9]
        }
    return None

def get_recent_datasets(limit=6):
    """Get most recent datasets for gallery"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT dataset_id, name, description, source, license, file_blob_id, created_at
        FROM datasets 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        'dataset_id': row[0],
        'name': row[1],
        'description': row[2],
        'source': row[3],
        'license': row[4],
        'file_blob_id': row[5],
        'created_at': row[6]
    } for row in rows]

