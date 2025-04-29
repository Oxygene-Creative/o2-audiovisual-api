from app.reporters.metrics.base_analysis import BaseAnalysisService
from app.core.es import es_client

class ShareOfVoiceAnalysisService(BaseAnalysisService):
    def analyze_share_of_voice(
        self, index_name: str, brand_query: str, competitor_queries: list, start_date: str, end_date: str
    ):
        
        try:
            # Build query for the main brand
            brand_es_query = self.build_query(brand_query, start_date, end_date)

            # Build queries for competitors
            competitor_queries_list = [
                self.build_query(competitor_query, start_date, end_date)
                for competitor_query in competitor_queries
            ]

            # Elasticsearch aggregations for Share of Voice
            es_aggregations = {
                "brand_mentions": {
                    "value_count": {
                        "field": "_id"
                    }
                },
                "brand_mentions_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "month"
                    }
                },
                "competitor_mentions": {  
                    "filters": {
                        "filters": {
                            competitor_query: {"query": competitor_es_query}
                            for competitor_query, competitor_es_query in zip(competitor_queries, competitor_queries_list)
                        }
                    }
                },
                "competitor_mentions_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "month"
                    },
                    "aggs": {
                        "competitors": {
                            "filters": {
                                "filters": {
                                    competitor_query: {"query": competitor_es_query}
                                    for competitor_query, competitor_es_query in zip(competitor_queries, competitor_queries_list)
                                }
                            }
                        }
                    }
                },
                "mentions_by_medium": {
                    "terms": {
                        "field": "source.name",
                        "size": 10  # Top 10 mediums
                    },
                    "aggs": {
                        "brand_and_competitors": {
                            "filters": {
                                "filters": {
                                    "brand": {"query": brand_es_query},
                                    **{
                                        competitor_query: {"query": competitor_es_query}
                                        for competitor_query, competitor_es_query in zip(competitor_queries, competitor_queries_list)
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
                    "query": {"match_all": {}},  # Perform a match_all since aggregations handle the filtering
                    "aggs": es_aggregations,
                    "size": 0  # Minimize unnecessary hits, only return aggregations
                }
            )

            # Parse response for Share of Voice metrics
            total_brand_mentions = response["aggregations"]["brand_mentions"]["value"]
            competitor_mentions = [
                {
                    "competitor": competitor_query,
                    "mentions": response["aggregations"]["competitor_mentions"]["buckets"][competitor_query]["doc_count"]
                }
                for competitor_query in competitor_queries
            ]

            total_competitor_mentions = sum(
                competitor["mentions"] for competitor in competitor_mentions
            )
            total_mentions = total_brand_mentions + total_competitor_mentions

            # Calculate percentages for Share of Voice
            brand_percentage = (total_brand_mentions / total_mentions) * 100 if total_mentions > 0 else 0
            competitor_percentages = [
                {
                    "competitor": competitor["competitor"],
                    "percentage": (competitor["mentions"] / total_mentions) * 100 if total_mentions > 0 else 0
                }
                for competitor in competitor_mentions
            ]

            metrics = {
                "overall_share_of_voice": {
                    "brand": brand_percentage,
                    "competitors": competitor_percentages,
                    "total_mentions": total_mentions
                },
                "brand_mentions_over_time": [
                    {
                        "date": bucket["key_as_string"],
                        "count": bucket["doc_count"]
                    }
                    for bucket in response["aggregations"]["brand_mentions_over_time"]["buckets"]
                ],
                "competitor_mentions_over_time": [
                    {
                        "date": bucket["key_as_string"],
                        "competitors": [
                            {
                                "competitor": competitor_query,
                                "count": bucket["competitors"]["buckets"][competitor_query]["doc_count"]
                            }
                            for competitor_query in competitor_queries
                        ]
                    }
                    for bucket in response["aggregations"]["competitor_mentions_over_time"]["buckets"]
                ],
                "mentions_by_medium": [
                    {
                        "medium": bucket["key"],
                        "brand_mentions": bucket["brand_and_competitors"]["buckets"]["brand"]["doc_count"],
                        "competitor_mentions": [
                            {
                                "competitor": competitor_query,
                                "count": bucket["brand_and_competitors"]["buckets"][competitor_query]["doc_count"]
                            }
                            for competitor_query in competitor_queries
                        ]
                    }
                    for bucket in response["aggregations"]["mentions_by_medium"]["buckets"]
                ]
            }

            return metrics

        except Exception as e:
            return {"error": str(e)}