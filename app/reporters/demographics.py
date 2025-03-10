from typing import List, Optional, Literal
from datetime import datetime, timedelta
from app.core.es import search
from dateutil.relativedelta import relativedelta

DateRangeType = Literal['daily', 'monthly']

def demographics_analysis(
    date: datetime,
    date_range: DateRangeType = 'daily',
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
        
    
    query = {
        "size": 0,  # We only want aggregations
        "query": {
            "range": {
                "timestamp": {
                    "gte": start_date.isoformat(),
                    "lte": end_date.isoformat()
                }
            }
        },
        "aggs": {
            "per_stream": {
                "terms": {
                    "field": "stream_id.keyword",
                    "size": 1000  # Adjust based on number of streams
                },
                "aggs": {
                    "stream_name": {
                        "terms": {
                            "field": "stream_name.keyword"
                        }
                    },
                    "total_male": {
                        "sum": {
                            "field": "male"
                        }
                    },
                    "total_female": {
                        "sum": {
                            "field": "female"
                        }
                    },
                    "total_music": {
                        "sum": {
                            "field": "music"
                        }
                    },
                    "avg_male": {
                        "avg": {
                            "field": "male"
                        }
                    },
                    "avg_female": {
                        "avg": {
                            "field": "female"
                        }
                    },
                    "avg_music": {
                        "avg": {
                            "field": "music"
                        }
                    }
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
                },
                "aggs": {
                    "male_dist": {
                        "avg": {
                            "field": "male"
                        }
                    },
                    "female_dist": {
                        "avg": {
                            "field": "female"
                        }
                    },
                    "music_dist": {
                        "avg": {
                            "field": "music"
                        }
                    }
                }
            }
        }
    }

    try:
        response = search(index="recordings", query=query)

        # Process results into a more usable format
        results = {
            "metadata": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "interval": interval
            },
            "streams": [
                {
                    "stream_id": bucket["key"],
                    "stream_name": bucket["stream_name"]["buckets"][0]["key"] if bucket["stream_name"]["buckets"] else "",
                    "totals": {
                        "male": bucket["total_male"]["value"],
                        "female": bucket["total_female"]["value"],
                        "music": bucket["total_music"]["value"]
                    },
                    # "averages": {
                    #     "male": bucket["avg_male"]["value"],
                    #     "female": bucket["avg_female"]["value"],
                    #     "music": bucket["avg_music"]["value"]
                    # }
                }
                for bucket in response["aggregations"]["per_stream"]["buckets"]
            ],
            "time_distribution": [
                {
                    "timestamp": bucket["key_as_string"],
                    "male": bucket["male_dist"]["value"],
                    "female": bucket["female_dist"]["value"],
                    "music": bucket["music_dist"]["value"]
                }
                for bucket in response["aggregations"]["time_distribution"]["buckets"]
            ]
        }

        return results

    except Exception as e:
        raise Exception(f"Error executing Elasticsearch query: {str(e)}")

# Example usage:
"""
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

results = get_stream_demographics(
    es_client,
    start_date=start_date,
    end_date=end_date,
    interval="day"
)

# Access stream totals
for stream in results["streams"]:
    # print(f"""
    # Stream: {stream['stream_name']} ({stream['stream_id']})
    # Totals:
    #     Male: {stream['totals']['male']:.2f}
    #     Female: {stream['totals']['female']:.2f}
    #     Music: {stream['totals']['music']:.2f}
    # Averages:
    #     Male: {stream['averages']['male']:.2f}
    #     Female: {stream['averages']['female']:.2f}
    #     Music: {stream['averages']['music']:.2f}
    # """)

# Access time distribution
# for point in results["time_distribution"]:
#     print(f"""
#     Time: {point['timestamp']}
#     Male: {point['male']:.2f}
#     Female: {point['female']:.2f}
#     Music: {point['music']:.2f}
#     """)
# """