from app.reporters.metrics.base_analysis import BaseAnalysisService
from app.core.es import es_client

class EmotionAnalysisService(BaseAnalysisService):
    
    def analyze_emotions(self, index_name: str, query: str, start_date: str, end_date: str):
        try:
            # Use the shared build_query logic from the BaseAnalysisService
            es_query = self.build_query(query, start_date, end_date)

            # Define Elasticsearch emotion-specific aggregations
            es_aggregations = {
                "emotion_totals": {
                    "terms": {
                        "field": "emotions",  # Assuming the field contains emotions like anger, fear, etc.
                        "size": 10  # Top 10 emotions
                    }
                },
                "emotion_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "month"  # Aggregation by month for time-based analysis
                    },
                    "aggs": {
                        "emotions": {
                            "terms": {
                                "field": "emotions",
                                "size": 10  # Top 10 emotions
                            }
                        }
                    }
                },
                "emotion_per_medium": {
                    "terms": {
                        "field": "source.name",  # Medium/source field for categorization
                        "size": 10  # Top 10 mediums
                    },
                    "aggs": {
                        "emotions": {
                            "terms": {
                                "field": "emotions",
                                "size": 10  # Top 10 emotions for each medium
                            }
                        }
                    }
                },
                "emotion_over_time_per_medium": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "month"
                    },
                    "aggs": {
                        "mediums": {
                            "terms": {
                                "field": "source.name",
                                "size": 10
                            },
                            "aggs": {
                                "emotions": {
                                    "terms": {
                                        "field": "emotions",
                                        "size": 10
                                    }
                                }
                            }
                        }
                    }
                }
            }

            # Execute the Elasticsearch query
            response = es_client.search(
                index=index_name,
                body={
                    "query": es_query,
                    "aggs": es_aggregations,
                    "size": 0  # Minimize unnecessary hits, only return aggregations
                }
            )

            # Parse response for emotion metrics
            metrics = {
                "emotion_totals": [
                    {
                        "emotion": bucket["key"],
                        "count": bucket["doc_count"]
                    }
                    for bucket in response["aggregations"]["emotion_totals"]["buckets"]
                ],
                "emotion_over_time": [
                    {
                        "date": bucket["key_as_string"],
                        "emotions": [
                            {
                                "emotion": emotion_bucket["key"],
                                "count": emotion_bucket["doc_count"]
                            }
                            for emotion_bucket in bucket["emotions"]["buckets"]
                        ]
                    }
                    for bucket in response["aggregations"]["emotion_over_time"]["buckets"]
                ],
                "emotion_per_medium": [
                    {
                        "medium": bucket["key"],
                        "emotions": [
                            {
                                "emotion": emotion_bucket["key"],
                                "count": emotion_bucket["doc_count"]
                            }
                            for emotion_bucket in bucket["emotions"]["buckets"]
                        ]
                    }
                    for bucket in response["aggregations"]["emotion_per_medium"]["buckets"]
                ],
                "emotion_over_time_per_medium": [
                    {
                        "date": bucket["key_as_string"],
                        "mediums": [
                            {
                                "medium": medium_bucket["key"],
                                "emotions": [
                                    {
                                        "emotion": emotion_bucket["key"],
                                        "count": emotion_bucket["doc_count"]
                                    }
                                    for emotion_bucket in medium_bucket["emotions"]["buckets"]
                                ]
                            }
                            for medium_bucket in bucket["mediums"]["buckets"]
                        ]
                    }
                    for bucket in response["aggregations"]["emotion_over_time_per_medium"]["buckets"]
                ]
            }

            return metrics

        except Exception as e:
            return {"error": str(e)}