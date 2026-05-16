from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

print("Initializing Firestore client...")
db = firestore.Client(project="demodev-cfb09", database="(default)")
print(f"Firestore client initialized. Project: {db.project}")

def get_all_active_users():
    print("Listing all collections...")
    collections = list(db.collections())
    print(f"Found {len(collections)} collections:")
    for col in collections:
        print(f"  Collection: {col.id}")
    return []