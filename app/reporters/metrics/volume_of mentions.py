from app.core.es import es_client
from app.reporters.metrics.base_analysis import BaseAnalysisService


class VolMentionsService(BaseAnalysisService):
    
    def analyze_mentions(self, index_name: str, query: str, start_date: str, end_date: str):
        
        try:
            es_query = self.build_query(query, start_date, end_date)

            # Elasticsearch aggregations for metrics
            es_aggregations = {
                "total_mentions": {
                    "value_count": {
                        "field": "_id"
                    }
                },
                "mentions_per_day": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "day"
                    }
                },
                "mentions_by_medium": {
                    "terms": {
                        "field": "source.name",
                        "size": 10  # Top 10 mediums
                    }
                },
                "mentions_by_medium_daily": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "day"
                    },
                    "aggs": {
                        "mediums": {
                            "terms": {
                                "field": "source.name",
                                "size": 10  # Top 10 mediums per day
                            }
                        }
                    }
                },
                "highest_mentions_day": {
                    "max_bucket": {
                        "buckets_path": "mentions_per_day._count"
                    }
                },
                "average_mentions_per_day": {
                    "avg_bucket": {
                        "buckets_path": "mentions_per_day._count"
                    }
                }
            }

            # Perform the search with aggregations
            response = es_client.search(
                index=index_name,
                body={
                    "query": es_query,
                    "aggs": es_aggregations,
                    "size": 0  # We don't need individual hits for analysis
                }
            )

            # Parse and return metrics
            metrics = {
                "total_mentions": response["aggregations"]["total_mentions"]["value"],
                "mentions_per_day": [
                    {
                        "date": bucket["key_as_string"],
                        "count": bucket["doc_count"]
                    }
                    for bucket in response["aggregations"]["mentions_per_day"]["buckets"]
                ],
                "mentions_by_medium": [
                    {
                        "medium": bucket["key"],
                        "count": bucket["doc_count"]
                    }
                    for bucket in response["aggregations"]["mentions_by_medium"]["buckets"]
                ],
                "mentions_by_medium_daily": [
                    {
                        "date": bucket["key_as_string"],
                        "mediums": [
                            {
                                "medium": medium_bucket["key"],
                                "count": medium_bucket["doc_count"]
                            }
                            for medium_bucket in bucket["mediums"]["buckets"]
                        ]
                    }
                    for bucket in response["aggregations"]["mentions_by_medium_daily"]["buckets"]
                ],
                "highest_mentions_day": response["aggregations"]["highest_mentions_day"]["value"],
                "average_mentions_per_day": response["aggregations"]["average_mentions_per_day"]["value"],
            }

            return metrics
        except Exception as e:
            return {"error": str(e)}