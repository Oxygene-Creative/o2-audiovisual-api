from typing import List, Optional, Literal
from datetime import datetime, timedelta
from app.core.es import search
from dateutil.relativedelta import relativedelta

from app.models.reports import Competitor
from app.reporters.mentions import search_mentions

DateRangeType = Literal['daily', 'monthly']

def competitor_analysis(
    competitors: List[Competitor],
    date: datetime,
    date_range: DateRangeType = 'daily',
    size: int = 100
):  
    results = {}
    
    for competitor in competitors:
        results[competitor.name] = search_mentions(
            keywords=competitor.keywords,
            date=date,
            date_range=date_range,
            size=size
        )
    
    return results

# Example usage:
"""
keyword_sets = {
    "coca_cola": ["coca cola", "coke"],
    "pepsi": ["pepsi", "pepsi max"],
    "sprite": ["sprite", "7up"]
}

comparison = compare_keywords(
    es_client,
    keyword_sets=keyword_sets,
    date=datetime.now(),
    date_range='daily'
)

# Access results for each keyword set
for label, result in comparison.items():
    print(f"\nResults for {label}:")
    print(f"Total segments: {result['metadata']['total_segments']}")
    print(f"Total ads: {result['metadata']['total_ads']}")
    
    print("\nSentiment distribution:")
    for sentiment in result['sentiment_distribution']:
        print(f"{sentiment['key']}: {sentiment['doc_count']}")
    
    print("\nTop topics:")
    for topic in result['topics_distribution']:
        print(f"{topic['key']}: {topic['doc_count']}")

# Compare specific metrics
for label, result in comparison.items():
    total_segments = result['metadata']['total_segments']
    total_ads = result['metadata']['total_ads']
    print(f"\n{label}:")
    print(f"Segment to ad ratio: {total_segments/total_ads if total_ads else 0:.2f}")
"""