from app.core.es import es_client
from app.reporters.metrics.base_analysis import BaseAnalysisService


class SentimentAnalysis((BaseAnalysisService)):
    
    def analyze_mentions(self, index_name: str, query: str, start_date: str, end_date: str):
        try:
            # Use the shared build_query logic from the BaseAnalysisService
            es_query = self.build_query(query, start_date, end_date)

            # Define Elasticsearch sentiment-specific aggregations
            es_aggregations = {
                "sentiment_totals": {
                    "terms": {
                        "field": "sentiment",
                        "size": 3  # Assuming categories: 'positive', 'negative', 'neutral'
                    }
                },
                "sentiment_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "day"
                    },
                    "aggs": {
                        "sentiments": {
                            "terms": {
                                "field": "sentiment",
                                "size": 3
                            }
                        }
                    }
                },
                "sentiment_per_medium": {
                    "terms": {
                        "field": "source.name",
                        "size": 10  # Top 10 mediums
                    },
                    "aggs": {
                        "sentiments": {
                            "terms": {
                                "field": "sentiment",
                                "size": 3
                            }
                        }
                    }
                },
                "sentiment_over_time_per_medium": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "day"
                    },
                    "aggs": {
                        "mediums": {
                            "terms": {
                                "field": "source.name",
                                "size": 10
                            },
                            "aggs": {
                                "sentiments": {
                                    "terms": {
                                        "field": "sentiment",
                                        "size": 3
                                    }
                                }
                            }
                        }
                    }
                }
            }

            # Perform the Elasticsearch search with aggregations
            response = es_client.search(
                index=index_name,
                body={
                    "query": es_query,  # Include the shared query
                    "aggs": es_aggregations,
                    "size": 0 
                }
            )

            # Parse response for sentiment metrics
            metrics = {
                "sentiment_totals": [
                    {
                        "sentiment": bucket["key"],
                        "count": bucket["doc_count"]
                    }
                    for bucket in response["aggregations"]["sentiment_totals"]["buckets"]
                ],
                "sentiment_over_time": [
                    {
                        "date": bucket["key_as_string"],
                        "sentiments": [
                            {
                                "sentiment": sentiment_bucket["key"],
                                "count": sentiment_bucket["doc_count"]
                            }
                            for sentiment_bucket in bucket["sentiments"]["buckets"]
                        ]
                    }
                    for bucket in response["aggregations"]["sentiment_over_time"]["buckets"]
                ],
                "sentiment_per_medium": [
                    {
                        "medium": bucket["key"],
                        "sentiments": [
                            {
                                "sentiment": sentiment_bucket["key"],
                                "count": sentiment_bucket["doc_count"]
                            }
                            for sentiment_bucket in bucket["sentiments"]["buckets"]
                        ]
                    }
                    for bucket in response["aggregations"]["sentiment_per_medium"]["buckets"]
                ],
                "sentiment_over_time_per_medium": [
                    {
                        "date": bucket["key_as_string"],
                        "mediums": [
                            {
                                "medium": medium_bucket["key"],
                                "sentiments": [
                                    {
                                        "sentiment": sentiment_bucket["key"],
                                        "count": sentiment_bucket["doc_count"]
                                    }
                                    for sentiment_bucket in medium_bucket["sentiments"]["buckets"]
                                ]
                            }
                            for medium_bucket in bucket["mediums"]["buckets"]
                        ]
                    }
                    for bucket in response["aggregations"]["sentiment_over_time_per_medium"]["buckets"]
                ]
            }

            return metrics

        except Exception as e:
            return {"error": str(e)}

