import pytest
from app.analyzers.nlp import (
    sentiment_analysis,
    match_keywords,
    categorize_text,
    topic_modelling,
)

def test_sentiment_analysis():
    # Positive case
    result = sentiment_analysis("I love this product!")
    assert result == "Positive", "Expected sentiment to be Positive"

    # Negative case
    result = sentiment_analysis("I hate this experience.")
    assert result == "Negative", "Expected sentiment to be Negative"

    # A neutral-like case (actual behavior depends on the pre-trained model)
    result = sentiment_analysis("It's just okay.")
    assert result in ["Neutral", "Positive", "Negative"], "Unexpected sentiment analysis result"

def test_match_keywords():
    keywords = ["finance", "technology", "health"]

    # Match case
    text = "I am interested in the latest finance trends."
    matched = match_keywords(text, keywords)
    assert "finance" in matched, "Expected 'finance' to be matched"
    assert len(matched) == 1, "Expected exactly one match"

    # Edge case: No match
    text2 = "I am into sports."
    matched2 = match_keywords(text2, keywords)
    assert matched2 == [], "Expected no matches for unrelated words"

def test_categorize_text():
    categories = ["finance", "technology", "health"]

    # Similar text
    text = "a hot topic about money"
    result = categorize_text(text, categories, threshold=0.7)
    assert "finance" in result, "Expected 'finance' to be categorized"
    assert len(result) == 1, "Expected exactly one category match"

    # Dissimilar text
    text2 = "i love football"
    result2 = categorize_text(text2, categories, threshold=0.7)
    assert result2 == [], "Expected no categories for dissimilar text"

def test_topic_modelling():
    input_texts = ["This is about AI and machine learning.", "This relates to technology and innovation."]

    # Call the function
    final_topics = topic_modelling(input_texts)

    # Validate structure and results
    assert isinstance(final_topics, list), "Expected final_topics to be a list"
    assert len(final_topics) > 0, "Expected at least one topic to be generated"

    for topic in final_topics:
        assert "label" in topic, "Expected each topic to have a label"
        assert "words" in topic, "Expected each topic to have associated words"
        assert isinstance(topic["words"], list), "Expected topic words to be a list"
        assert len(topic["words"]) > 0, "Expected words for each topic to have at least one entry"