import pytest
from app.analyzers.nlp import (
    sentiment_analysis,
    match_keywords,
    categorize_text,
    topic_modelling,
)
from unittest.mock import patch


def test_sentiment_analysis():
    with patch("app.analyzers.nlp.classifier") as mock_classifier:
        # Mock response for the classifier
        mock_classifier.return_value = [{"label": "POSITIVE", "score": 0.99}]

        # Positive case
        result = sentiment_analysis("I love this product!")
        assert result == "Positive"

        # Negative case
        mock_classifier.return_value = [{"label": "NEGATIVE", "score": 0.95}]
        result = sentiment_analysis("I hate this experience.")
        assert result == "Negative"

        # Neutral case (Mock case without real neutral label behavior)
        mock_classifier.return_value = [{"label": "NEUTRAL", "score": 0.75}]
        result = sentiment_analysis("It's okay.")
        assert result == "Neutral"


def test_match_keywords():
    keywords = ["finance", "technology", "health"]
    text = "I am interested in the latest finance trends."
    
    matched = match_keywords(text, keywords)
    assert "finance" in matched, "Expected 'finance' to be matched"
    assert len(matched) == 1

    # Edge case: No match
    text = "I am into sports."
    matched = match_keywords(text, keywords)
    assert matched == [], "Expected no matches for unrelated words"


def test_categorize_text():
    categories = ["finance", "technology", "health"]
    
    # Use dependency injection to mock `embed_text`
    with patch("app.analyzers.embeddings.embed_text") as mock_embed_text:
        mock_embed_text.side_effect = lambda texts: [[1.0, 0.0, 0.0] for text in texts]

        # Similar text
        text = "finance topic about money"
        result = categorize_text(text, categories, threshold=0.1)
        assert "finance" in result, "Expected 'finance' to be categorized"
        assert len(result) == 1

        # Dissimilar text
        text = "sports topic"
        result = categorize_text(text, categories, threshold=0.5)
        assert result == [], "Expected no categories for dissimilar text"


def test_topic_modelling():
    input_texts = ["This is about AI and machine learning.", "This relates to technology and AI."]

    # Mock BERTopic and LLM components
    with patch("app.analyzers.text_processing.topic_model") as mock_topic_model, \
         patch("app.analyzers.text_processing.llm") as mock_llm:

        # Mock BERTopic fit_transform
        mock_topic_model.fit_transform.return_value = ([0, 1], [0.9, 0.8])  # Two topic IDs

        # Mock topic keywords
        mock_topic_model.get_topic.side_effect = [
            [("AI", 0.9), ("ML", 0.85)],  # Topic 0
            [("Technology", 0.8), ("Innovation", 0.75)],  # Topic 1
        ]

        # Mock LLM response
        mock_llm.return_value.invoke.return_value = "Artificial Intelligence"

        # Call the function
        final_topics = topic_modelling(input_texts)

        # Validate structure and results
        assert isinstance(final_topics, list), "Expected final_topics to be a list"
        assert len(final_topics) == 2, "Expected two distinct topics"
        assert final_topics[0]["label"] == "Artificial Intelligence", "Expected label for Topic 0"
        assert final_topics[0]["words"] == [("AI", 0.9), ("ML", 0.85)], "Expected keywords for Topic 0"
        assert final_topics[1]["words"] == [("Technology", 0.8), ("Innovation", 0.75)], "Expected keywords for Topic 1"