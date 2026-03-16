from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle
import os

# Dummy data
texts = ["This is a real review", "Excellent product", "I love this", "Fake review buy now", "Win money click here", "SPAM SPAM SPAM"]
labels = [0, 0, 0, 1, 1, 1]  # 0: real, 1: fake

# Train dummy components
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

model = LogisticRegression()
model.fit(X, labels)

# Save models
os.makedirs("models", exist_ok=True)
pickle.dump(model, open("models/fake_review_model.pkl", "wb"))
pickle.dump(vectorizer, open("models/tfidf_vectorizer.pkl", "wb"))

print("Dummy models created successfully.")
