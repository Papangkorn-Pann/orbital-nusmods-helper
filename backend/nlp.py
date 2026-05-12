from bs4 import BeautifulSoup #for formatting (turning html into plain text)

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer #sorting comments positive/neutral/negative
analyzer = SentimentIntensityAnalyzer()

#sentiment value breakpoints obtained from
#https://ak1adyous.medium.com/sentiment-analysis-using-vader-c56bcffe6f24
def analyze_sentiment(comment):
    comment_message_plaintext = BeautifulSoup(comment["message"], "html.parser").get_text(separator="\n")

    score = analyzer.polarity_scores(comment_message_plaintext)["compound"]
    if score >= 0.05:
        return "positive"
    elif score <= -0.05:
        return "negative"
    else:
        return "neutral"

from transformers import pipeline

classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)

difficulty_labels = [
    "very easy",
    "easy",
    "moderate",
    "hard",
    "very hard"
]

recommend_labels = [
    "recommend",
    "not recommend"
]

difficulty_map = {
    "very easy": 1,
    "easy": 2,
    "moderate": 3,
    "hard": 4,
    "very hard": 5
}

recommend_map = {
    "recommend": 5,
    "not recommend": 0
}

def analyze_diff_recc(comment):

    #multi_label=False ensures total weights of each category sums to 1
    difficulty_result = classifier(comment, difficulty_labels, multi_label=False)
    recommendation_result = classifier(comment, recommend_labels, multi_label=False)

    difficulty_score = 0

    for label, confidence in zip(
        difficulty_result["labels"],
        difficulty_result["scores"]
    ):
        difficulty_score += difficulty_map[label] * confidence

    recommendation_score = 0

    for label, confidence in zip(
        recommendation_result["labels"],
        recommendation_result["scores"]
    ):
        recommendation_score += recommend_map[label] * confidence

    return {
        "difficulty_score": difficulty_score,
        "recommendation_score": recommendation_score
    }
