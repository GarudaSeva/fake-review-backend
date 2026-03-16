from datetime import datetime, timedelta

class UserBehaviorService:
    def analyze(self, user_data, reviews_col=None):
        """
        Analyzes user behavior to detect bots or suspicious activity.
        If reviews_col is provided, it checks for duplicates and frequency in DB.
        Returns a tuple: (status, reason)
        """
        user_id = user_data.get("id", "anonymous")
        review_text = user_data.get("review_text", "")
        
        # 1. Basic Rule-based checks (if stats provided from FE/elsewhere)
        reviews_per_day = user_data.get("reviews_per_day", 0)
        account_age_days = user_data.get("account_age_days", 0)

        if reviews_per_day > 10 and account_age_days < 10:
            return "bot", "High frequency and new account"

        if reviews_per_day > 10:
            return "suspicious", "High review frequency"

        # 2. Database-level checks (if DB access provided)
        if reviews_col is not None and user_id != "anonymous":
            # Check for duplicate review text by same user
            if review_text:
                duplicate_count = reviews_col.count_documents({
                    "userId": user_id,
                    "reviewText": review_text
                })
                if duplicate_count >= 3:
                    return "suspicious", "Duplicate review text"

            # Check for high frequency (e.g., more than 3 reviews in last 10 minutes)
            ten_minutes_ago = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
            recent_reviews = reviews_col.count_documents({
                "userId": user_id,
                "createdAt": {"$gte": ten_minutes_ago}
            })
            if recent_reviews >= 3:
                return "suspicious", "High review frequency"

        return "genuine", None
