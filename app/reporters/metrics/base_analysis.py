from app.core.es import es_client

class BaseAnalysisService:
    def __init__(self, query_parser):
        self.es = es_client
        self.query_parser = query_parser  # Inject the query parser instance

    def build_query(self, query: str, start_date: str, end_date: str):
        parsed_query = self.query_parser.parse_query(query)[0]
        es_query_raw_text = self.query_parser.build_es_query(parsed_query)

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
        return es_query