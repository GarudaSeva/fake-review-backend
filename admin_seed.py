import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def seed_admin():
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/fake-review")
    client = MongoClient(MONGO_URI)
    db = client['fake-review']
    users_col = db['users']

    admin_email = "admin@shop.com"
    admin_password = "admin123"
    
    # Check if admin exists
    if users_col.find_one({"email": admin_email}):
        print(f"Admin {admin_email} already exists.")
        return

    admin_user = {
        "name": "Admin",
        "email": admin_email,
        "password": generate_password_hash(admin_password),
        "role": "admin",
        "status": "genuine",
        "createdAt": "2026-03-16T12:00:00Z"
    }
    
    users_col.insert_one(admin_user)
    print(f"Admin user {admin_email} seeded successfully.")

if __name__ == "__main__":
    seed_admin()
