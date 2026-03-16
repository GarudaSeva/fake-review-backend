from transformers import pipeline

class SentimentService:
    def __init__(self):
        # Using a very common BERT model for sentiment analysis
        self.model = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment"
        )

    def predict(self, text):
        result = self.model(text)[0]
        score = result["score"]
        label = result["label"]

        # convert stars to sentiment (1-5 star rating)
        if "1" in label or "2" in label:
            sentiment = "negative"
        elif "3" in label:
            sentiment = "neutral"
        else:
            sentiment = "positive"

        return {
            "sentiment": sentiment,
            "confidence": round(float(score), 4)
        }
