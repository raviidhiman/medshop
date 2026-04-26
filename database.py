from pymongo import MongoClient
from datetime import datetime, date, timedelta
from urllib.parse import quote_plus
import os

# ─────────────────────────────────────────────────────────
#  PASTE YOUR MONGODB DETAILS HERE
# ─────────────────────────────────────────────────────────
MONGO_USERNAME = "raviidhiman"
MONGO_PASSWORD = "Ravi@Medshop123"
MONGO_CLUSTER  = "medshop.wi6y5tf.mongodb.net"
DB_NAME        = "medshop"

username  = quote_plus(MONGO_USERNAME)
password  = quote_plus(MONGO_PASSWORD)
MONGO_URI = os.environ.get(
    "MONGO_URI",
    f"mongodb+srv://{username}:{password}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=medshop"
)


def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]


def init_db():
    db  = get_db()
    col = db.medicines
    if col.count_documents({}) == 0:
        today   = date.today()
        samples = [
            {'name': 'Paracetamol 500mg',  'manufacturer': 'Sun Pharma', 'category': 'Analgesic',     'price': 5.50,  'quantity': 150, 'expiry_date': (today + timedelta(days=365)).isoformat(), 'description': 'For fever and mild pain',       'created_at': datetime.now().isoformat()},
            {'name': 'Amoxicillin 250mg',  'manufacturer': 'Cipla',      'category': 'Antibiotic',    'price': 45.00, 'quantity': 8,   'expiry_date': (today + timedelta(days=180)).isoformat(), 'description': 'Broad-spectrum antibiotic',     'created_at': datetime.now().isoformat()},
            {'name': 'Metformin 500mg',    'manufacturer': 'Dr. Reddys', 'category': 'Antidiabetic',  'price': 12.00, 'quantity': 200, 'expiry_date': (today + timedelta(days=400)).isoformat(), 'description': 'Type 2 diabetes management',   'created_at': datetime.now().isoformat()},
            {'name': 'Cetirizine 10mg',    'manufacturer': 'Mankind',    'category': 'Antihistamine', 'price': 8.75,  'quantity': 5,   'expiry_date': (today + timedelta(days=90)).isoformat(),  'description': 'Allergy relief',               'created_at': datetime.now().isoformat()},
            {'name': 'Omeprazole 20mg',    'manufacturer': 'Torrent',    'category': 'Antacid',       'price': 22.00, 'quantity': 120, 'expiry_date': (today + timedelta(days=300)).isoformat(), 'description': 'Acid reflux treatment',        'created_at': datetime.now().isoformat()},
            {'name': 'Expired Aspirin',    'manufacturer': 'Generic',    'category': 'Analgesic',     'price': 3.00,  'quantity': 50,  'expiry_date': (today - timedelta(days=10)).isoformat(),  'description': 'Expired stock - for testing',  'created_at': datetime.now().isoformat()},
            {'name': 'Vitamin D3 1000IU',  'manufacturer': 'HealthVit',  'category': 'Supplement',    'price': 18.00, 'quantity': 3,   'expiry_date': (today + timedelta(days=500)).isoformat(), 'description': 'Vitamin D supplement',         'created_at': datetime.now().isoformat()},
            {'name': 'Atorvastatin 10mg',  'manufacturer': 'Pfizer',     'category': 'Cardiac',       'price': 55.00, 'quantity': 75,  'expiry_date': (today + timedelta(days=250)).isoformat(), 'description': 'Cholesterol management',       'created_at': datetime.now().isoformat()},
            {'name': 'Azithromycin 500mg', 'manufacturer': 'Cipla',      'category': 'Antibiotic',    'price': 89.00, 'quantity': 40,  'expiry_date': (today + timedelta(days=200)).isoformat(), 'description': 'Bacterial infections',         'created_at': datetime.now().isoformat()},
            {'name': 'Ibuprofen 400mg',    'manufacturer': 'Abbott',     'category': 'Analgesic',     'price': 14.00, 'quantity': 9,   'expiry_date': (today + timedelta(days=365)).isoformat(), 'description': 'Anti-inflammatory',            'created_at': datetime.now().isoformat()},
        ]
        col.insert_many(samples)
        print("✅ Sample data seeded into MongoDB!")
    else:
        print("✅ MongoDB connected. Database ready.")
