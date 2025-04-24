from app.core.es import es_client

class VolMentionsService:
    def __init__(self, query_parser):
        self.es = es_client
        self.query_parser = query_parser  # Inject the query parser instance

    def analyze_mentions(self, index_name: str, query: str, start_date: str, end_date: str):
        
        try:
            # Parse the search query using QueryParser
            parsed_query = self.query_parser.parse_query(query)[0]  # Obtain the parsed query tree
            es_query_raw_text = self.query_parser.build_es_query(parsed_query)  # Build raw_text query

            # Combine the parsed query with the date range filter
            es_query = {
                "bool": {
                    "must": [
                        es_query_raw_text,
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_date,  
                                    "lte": end_date
                                }
                            }
                        }
                    ]
                }
            }

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
            response = self.es.search(
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
                "highest_mentions_day": response["aggregations"]["highest_mentions_day"]["value"],
                "average_mentions_per_day": response["aggregations"]["average_mentions_per_day"]["value"],
            }

            return metrics
        except Exception as e:
            return {"error": str(e)}