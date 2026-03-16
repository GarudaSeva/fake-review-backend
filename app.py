from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
from datetime import datetime
from services.sentiment_service import SentimentService
from services.fake_review_service import FakeReviewService
from services.user_behavior_service import UserBehaviorService
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app) # Enable CORS for all routes

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/fake-review")
client = MongoClient(MONGO_URI)
db = client['fake-review']
products_col = db['products']
reviews_col = db['reviews']
users_col = db['users']

# Initialize services
sentiment_service = SentimentService()
fake_service = FakeReviewService()
user_service = UserBehaviorService()

def serialize_doc(doc):
    if not doc:
        return None
    doc['_id'] = str(doc['_id'])
    return doc

@app.route("/")
def index():
    return send_from_directory(app.static_folder, 'index.html')

# --- Product APIs ---

@app.route("/api/products", methods=["GET"])
def get_products():
    try:
        # Check if caller is admin (e.g., from admin dashboard)
        is_admin = request.args.get("admin", "false").lower() == "true"
        
        query = {}
        if not is_admin:
            query["status"] = "public"
            
        products = list(products_col.find(query))
        return jsonify([serialize_doc(p) for p in products])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/products", methods=["POST"])
def add_product():
    try:
        data = request.json
        if not data or 'name' not in data or 'price' not in data:
            return jsonify({"error": "Name and Price are required"}), 400
        
        new_product = {
            "name": data['name'],
            "description": data.get('description', ''),
            "price": float(data['price']),
            "image": data.get('image', 'https://via.placeholder.com/300'),
            "rating": 0,
            "reviewCount": 0,
            "trustScore": 100,
            "status": "public",
            "createdAt": datetime.utcnow().isoformat()
        }
        result = products_col.insert_one(new_product)
        new_product['_id'] = str(result.inserted_id)
        return jsonify(new_product), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/products/<product_id>", methods=["GET"])
def get_product(product_id):
    try:
        product = products_col.find_one({"_id": ObjectId(product_id)})
        if not product:
            return jsonify({"error": "Product not found"}), 404
        return jsonify(serialize_doc(product))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    try:
        data = request.json
        update_data = {}
        if 'name' in data: update_data['name'] = data['name']
        if 'description' in data: update_data['description'] = data['description']
        if 'price' in data: update_data['price'] = float(data['price'])
        if 'image' in data: update_data['image'] = data['image']
        if 'status' in data: update_data['status'] = data['status']
        
        result = products_col.update_one({"_id": ObjectId(product_id)}, {"$set": update_data})
        if result.matched_count == 0:
            return jsonify({"error": "Product not found"}), 404
        return jsonify({"message": "Product updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    try:
        # Delete product and its reviews
        products_col.delete_one({"_id": ObjectId(product_id)})
        reviews_col.delete_many({"productId": product_id})
        return jsonify({"message": "Product and associated reviews deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Auth APIs ---

@app.route("/api/auth/signup", methods=["POST"])
def signup():
    try:
        data = request.json
        if not data or 'email' not in data or 'password' not in data or 'name' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        if users_col.find_one({"email": data['email']}):
            return jsonify({"error": "User already exists"}), 400
        
        new_user = {
            "name": data['name'],
            "email": data['email'],
            "password": generate_password_hash(data['password']),
            "role": "user",
            "status": "genuine",
            "createdAt": datetime.utcnow().isoformat()
        }
        result = users_col.insert_one(new_user)
        new_user['_id'] = str(result.inserted_id)
        del new_user['password']
        return jsonify(new_user), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        data = request.json
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Missing email or password"}), 400
        
        user = users_col.find_one({"email": data['email']})
        if not user or not check_password_hash(user['password'], data['password']):
            return jsonify({"error": "Invalid credentials"}), 401
        
        user['_id'] = str(user['_id'])
        del user['password']
        return jsonify(user), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/status/<user_id>", methods=["GET"])
def get_user_status(user_id):
    try:
        user = users_col.find_one({"_id": ObjectId(user_id) if len(user_id) == 24 else user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"status": user.get("status", "genuine")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/reviews", methods=["GET"])
def get_all_reviews():
    try:
        reviews = list(reviews_col.find().sort("createdAt", -1))
        return jsonify([serialize_doc(r) for r in reviews])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/reviews/<review_id>", methods=["DELETE"])
def delete_review(review_id):
    try:
        review = reviews_col.find_one({"_id": ObjectId(review_id)})
        if not review:
            return jsonify({"error": "Review not found"}), 404
        
        product_id = review['productId']
        reviews_col.delete_one({"_id": ObjectId(review_id)})

        # Re-calculate product stats
        all_reviews = list(reviews_col.find({"productId": product_id}))
        if all_reviews:
            count = len(all_reviews)
            avg_rating = sum([r['rating'] for r in all_reviews]) / count
            fake_reviews = [r for r in all_reviews if r['fakeReviewLabel'] == 'fake']
            trust_score = 100 - (len(fake_reviews) / count * 100)
            
            products_col.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {
                    "rating": round(avg_rating, 1),
                    "reviewCount": count,
                    "trustScore": round(trust_score, 1)
                }}
            )
        else:
            products_col.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {"rating": 0, "reviewCount": 0, "trustScore": 100}}
            )

        return jsonify({"message": "Review deleted and stats updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/reviews/<review_id>", methods=["PATCH"])
def patch_review(review_id):
    try:
        data = request.json
        if not data: return jsonify({"error": "No data provided"}), 400
        
        result = reviews_col.update_one({"_id": ObjectId(review_id)}, {"$set": data})
        if result.matched_count == 0:
            return jsonify({"error": "Review not found"}), 404
            
        return jsonify({"message": "Review updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/users", methods=["GET"])
def get_admin_users():
    try:
        # Get all users from users collection who are NOT genuine
        # User requested: "dont every use come to suspecious list bro"
        # and "show reason there why he is suspecious list"
        query = {"status": {"$in": ["suspicious", "bot"]}, "role": "user"}
        suspicious_users = list(users_col.find(query))
        
        # Aggregate stats by user from reviews
        pipeline = [
            {"$group": {
                "_id": "$userId",
                "reviewCount": {"$sum": 1},
                "fakeCount": {"$sum": {"$cond": [{"$eq": ["$fakeReviewLabel", "fake"]}, 1, 0]}}
            }}
        ]
        review_stats = {str(s['_id']): s for s in reviews_col.aggregate(pipeline)}
        
        results = []
        for user in suspicious_users:
            u_id = str(user['_id'])
            stats = review_stats.get(u_id, {"reviewCount": 0, "fakeCount": 0})
            results.append({
                "userId": u_id,
                "userName": user['name'],
                "email": user['email'],
                "reviewCount": stats['reviewCount'],
                "fakeCount": stats['fakeCount'],
                "status": user.get('status', 'genuine'),
                "reason": user.get('suspiciousReason', 'N/A')
            })
            
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/users/<user_id>/status", methods=["PUT"])
def update_user_status(user_id):
    try:
        data = request.json
        if not data or 'status' not in data:
            return jsonify({"error": "Status is required"}), 400
        
        new_status = data['status']
        if new_status not in ["genuine", "suspicious", "bot"]:
            return jsonify({"error": "Invalid status"}), 400
            
        result = users_col.update_one(
            {"_id": ObjectId(user_id) if len(user_id) == 24 else user_id},
            {"$set": {"status": new_status}}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({"message": f"User status updated to {new_status}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reviews", methods=["POST"])
def add_review():
    try:
        data = request.json
        if not data or "review" not in data or "productId" not in data or "user" not in data:
            return jsonify({"error": "Invalid request format."}), 400

        review_text = data["review"]
        user_data = data["user"]
        product_id = data["productId"]
        
        # Check if user is blocked or suspicious
        user_id = user_data.get("id")
        if user_id:
            db_user = users_col.find_one({"_id": ObjectId(user_id) if len(user_id) == 24 else user_id})
            if db_user and db_user.get("status") in ["suspicious", "bot"]:
                return jsonify({"error": "Action blocked: Suspicious activity detected on your account."}), 403

        # 1. Sentiment Analysis (BERT)
        sentiment_result = sentiment_service.predict(review_text)

        # 2. Fake Review Detection (ML)
        fake_result = fake_service.predict(review_text)

        # 3. User Behavior Analysis (Rules + DB)
        user_data["review_text"] = review_text
        user_status, user_reason = user_service.analyze(user_data, reviews_col=reviews_col)

        # Update user status and reason in DB if suspicious or bot
        if user_id and user_status != "genuine":
             users_col.update_one(
                {"_id": ObjectId(user_id) if len(user_id) == 24 else user_id},
                {"$set": {"status": user_status, "suspiciousReason": user_reason}}
            )

        # Prepare review document
        new_review = {
            "productId": product_id,
            "userId": user_data.get("id", "anonymous"),
            "userName": user_data.get("name", "Guest"),
            "reviewText": review_text,
            "rating": data.get("rating", 5),
            "sentiment": sentiment_result['sentiment'],
            "sentimentConfidence": sentiment_result['confidence'],
            "fakeReviewLabel": fake_result['review_label'],
            "fakeProbability": fake_result['fake_probability'],
            "userStatus": user_status,
            "createdAt": datetime.utcnow().isoformat()
        }

        result = reviews_col.insert_one(new_review)
        new_review['_id'] = str(result.inserted_id)

        # Update Product Stats (Simplified)
        all_reviews = list(reviews_col.find({"productId": product_id}))
        count = len(all_reviews)
        avg_rating = sum([r['rating'] for r in all_reviews]) / count
        fake_reviews = [r for r in all_reviews if r['fakeReviewLabel'] == 'fake']
        trust_score = 100 - (len(fake_reviews) / count * 100)

        products_col.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {
                "rating": round(avg_rating, 1),
                "reviewCount": count,
                "trustScore": round(trust_score, 1)
            }}
        )

        return jsonify(new_review)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/products/<product_id>/reviews", methods=["GET"])
def get_product_reviews(product_id):
    try:
        reviews = list(reviews_col.find({"productId": product_id}).sort("createdAt", -1))
        return jsonify([serialize_doc(r) for r in reviews])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Admin APIs ---

@app.route("/api/admin/stats", methods=["GET"])
def get_admin_stats():
    try:
        total_products = products_col.count_documents({})
        total_reviews = reviews_col.count_documents({})
        
        # Sentiment counts
        positive = reviews_col.count_documents({"sentiment": "positive"})
        negative = reviews_col.count_documents({"sentiment": "negative"})
        neutral = reviews_col.count_documents({"sentiment": "neutral"})
        
        # Fake vs Real
        fake = reviews_col.count_documents({"fakeReviewLabel": "fake"})
        real = reviews_col.count_documents({"fakeReviewLabel": "real"})
        
        # Suspicious users
        bot_count = reviews_col.distinct("userId", {"userStatus": "bot"})
        suspicious_count = reviews_col.distinct("userId", {"userStatus": "suspicious"})

        return jsonify({
            "totalProducts": total_products,
            "totalReviews": total_reviews,
            "sentiment": {
                "positive": positive,
                "negative": negative,
                "neutral": neutral
            },
            "authenticity": {
                "fake": fake,
                "real": real
            },
            "users": {
                "bots": len(bot_count),
                "suspicious": len(suspicious_count)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
