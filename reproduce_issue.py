import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_duplicate_reviews():
    print("Testing duplicate reviews from same user...")
    product_id = "69b6c35583dd81a52bc987fa"
    user_data = {
        "id": "u_repro_" + str(int(time.time())), # Use unique ID for new test run
        "name": "Repro User"
    }
    
    review_text = "Perfect product with perfect results. I cannot imagine using anything else now."
    
    for i in range(5):
        print(f"Submitting review {i+1}...")
        payload = {
            "productId": product_id,
            "user": user_data,
            "review": review_text,
            "rating": 5
        }
        response = requests.post(f"{BASE_URL}/reviews", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"Result: Label={result['fakeReviewLabel']}, UserStatus={result['userStatus']}, Prob={result['fakeProbability']}")
        else:
            print(f"Error: {response.text}")
        time.sleep(0.5)

def test_generic_fake_review():
    print("\nTesting generic ChatGPT-style fake review...")
    product_id = "69b6c35583dd81a52bc987fa"
    user_data = {
        "id": "u_generic_test",
        "name": "Generic Tester"
    }
    
    # This should be flagged by heuristics now
    review_text = "This is the best product I have ever used in my entire life. Absolutely perfect in every way and everyone should buy it immediately."
    
    payload = {
        "productId": product_id,
        "user": user_data,
        "review": review_text,
        "rating": 5
    }
    response = requests.post(f"{BASE_URL}/reviews", json=payload)
    if response.status_code == 200:
        result = response.json()
        print(f"Result: Label={result['fakeReviewLabel']}, Prob={result['fakeProbability']}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    try:
        test_duplicate_reviews()
        test_generic_fake_review()
    except Exception as e:
        print(f"Failed to connect to server: {e}")
