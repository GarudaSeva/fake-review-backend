from transformers import pipeline
import re

class FakeReviewService:
    def __init__(self):
        # pretrained fake review detection model (using fake news detection as a proxy)
        self.classifier = pipeline(
            "text-classification",
            model="mrm8488/bert-tiny-finetuned-fake-news-detection"
        )
        
        # Heuristic keywords often found in ChatGPT generic reviews
        self.generic_phrases = [
            "perfect product", "perfect results", "cannot imagine using anything else",
            "everyone should buy it", "best product I have ever used", "absolutely perfect",
            "recommend this to all my friends", "must buy", "hurry up", "less stock available"
        ]

    def predict(self, review_text):
        # 1. ML Prediction
        result = self.classifier(review_text)[0]
        label = result["label"]
        score = result["score"]

        # Base probability from ML
        if label.upper() == "FAKE":
            fake_probability = score
        else:
            fake_probability = 1 - score

        # 2. Heuristic Analysis
        text_lower = review_text.lower()
        heuristic_score = 0
        
        # Check for generic phrases
        matched_phrases = [p for p in self.generic_phrases if p in text_lower]
        heuristic_score += len(matched_phrases) * 0.2
        
        # Check for repetitive exclamation marks or caps
        if re.search(r'!{2,}', review_text):
            heuristic_score += 0.15
        if review_text.isupper() and len(review_text) > 20:
            heuristic_score += 0.25
            
        # Check for very high polarity but generic nature
        # Increased word count threshold to 30 to catch more generic descriptions
        if len(review_text.split()) < 30 and len(matched_phrases) >= 2:
            heuristic_score += 0.4

        # Combine scores (ML + Heuristics, capped at 1.0)
        final_fake_probability = min(1.0, fake_probability + heuristic_score)
        
        # Determine label based on combined probability (threshold 0.5)
        review_label = "fake" if final_fake_probability > 0.5 else "real"

        return {
            "review_label": review_label,
            "fake_probability": round(float(final_fake_probability), 4),
            "ml_confidence": round(float(score), 4),
            "heuristic_boost": round(float(heuristic_score), 4),
            "matched_phrases": matched_phrases
        }
