from typing import List, Optional, Literal
from datetime import datetime, timedelta
from app.core.es import search
from dateutil.relativedelta import relativedelta

DateRangeType = Literal['daily', 'monthly']

def search_mentions(
    indexes: List[str],
    keywords: List[str],
    date: datetime,
    date_range: DateRangeType = 'daily',
    size: int = 0
) -> dict:
    
    # Calculate date range based on date_range parameter
    if date_range == 'daily':
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1) - timedelta(microseconds=1)
        interval = "hour"
    else:  # monthly
        start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = (start_date + relativedelta(months=1)) - timedelta(microseconds=1)
        interval = "day"
        
    # Create keyword match conditions for ads
    ad_match_conditions = []
    for keyword in keywords:
        ad_match_conditions.extend([
            {"match_phrase": {"ads.brand": keyword}},
            {"match_phrase": {"ads.product": keyword}}
        ])

    # Base query
    # Base query
    query = {
        "size": size,
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "timestamp": {
                                "gte": start_date.isoformat(),
                                "lte": end_date.isoformat()
                            }
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {"terms": {"keywords": keywords}},
                                {
                                    "nested": {
                                        "path": "ads",
                                        "query": {
                                            "bool": {
                                                "should": ad_match_conditions
                                            }
                                        }
                                    }
                                }
                            ],
                            "minimum_should_match": 1
                        }
                    }
                ]
            }
        },
        "_source": {
            "includes": [
                "recording_id",
                "timestamp",
                "raw_text",
                "keywords",
                "topics",
                "sentiment",
                "program_name",
                "host",
                "duration",
                "ads"
            ]
        },
        "aggs": {
            "matching_ads": {
                "nested": {
                    "path": "ads"
                },
                "aggs": {
                    "ad_matches": {
                        "filter": {
                            "bool": {
                                "should": ad_match_conditions
                            }
                        }
                    },
                    "ads_over_time": {
                        "date_histogram": {
                            "field": "timestamp",
                            "calendar_interval": interval,
                            "min_doc_count": 0,
                            "extended_bounds": {
                                "min": start_date.isoformat(),
                                "max": end_date.isoformat()
                            }
                        }
                    }
                }
            },
            "sentiment_distribution": {
                "terms": {
                    "field": "sentiment"
                }
            },
            "topics_distribution": {
                "terms": {
                    "field": "topics"
                }
            },
            "time_distribution": {
                "date_histogram": {
                    "field": "timestamp",
                    "calendar_interval": interval,
                    "min_doc_count": 0,
                    "extended_bounds": {
                        "min": start_date.isoformat(),
                        "max": end_date.isoformat()
                    }
                }
            }
        },
        "sort": [
            {
                "timestamp": "desc"
            }
        ]
    }
    
    try:
        # Execute search
        response = search(index=indexes, body=query)

        # Process results
        results = {
            "metadata": {
                "date_range": date_range,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_segments": response["hits"]["total"]["value"],
                "total_ads": response["aggregations"]["ad_matches"]["matching"]["doc_count"]
            },
            "mentions": [hit["_source"] for hit in response["hits"]["hits"]],
            "sentiment_distribution": response["aggregations"]["sentiment_distribution"]["buckets"],
            "topics_distribution": response["aggregations"]["topics_distribution"]["buckets"],
            "time_distribution": response["aggregations"]["time_distribution"]["buckets"]
        }

    except Exception as e:
        raise Exception(f"Error executing Elasticsearch query: {str(e)}")

# Example usage:
"""
es_client = Elasticsearch(["your_elasticsearch_host"])

# Search for daily data
daily_results = search_keywords_segments(
    es=es_client,
    keywords=["news", "sports"],
    date=datetime.now(),
    date_range='daily'
)

# Search for monthly data
monthly_results = search_keywords_segments(
    es=es_client,
    keywords=["news", "sports"],
    date=datetime.now(),
    date_range='monthly'
)

# Access results
print(f"Date range: {daily_results['metadata']['date_range']}")
print(f"From: {daily_results['metadata']['start_date']}")
print(f"To: {daily_results['metadata']['end_date']}")
print(f"Total hits: {daily_results['metadata']['total_hits']}")

# Access time-based distribution
for bucket in daily_results['aggregations']['time_distribution']['buckets']:
    print(f"Time: {bucket['key_as_string']}, Count: {bucket['doc_count']}")
"""