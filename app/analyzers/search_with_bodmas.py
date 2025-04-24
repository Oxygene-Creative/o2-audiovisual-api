from pyparsing import Word, alphanums, Forward, infixNotation, opAssoc, ParseResults
from app.core.es import es_client
from elasticsearch.exceptions import NotFoundError, ConnectionError

class QueryParser:
    """A parser to process logical queries based on BODMAS precedence."""

    def __init__(self):
        # Define grammar
        self.expr = Forward()
        term = Word(alphanums)
        self.expr <<= infixNotation(
            term,
            [
                ('not', 1, opAssoc.RIGHT),
                ('and', 2, opAssoc.LEFT),
                ('or', 2, opAssoc.LEFT),
            ],
        )

    def parse_query(self, query: str):
        """Parse the query and return the structured parse tree."""
        return self.expr.parseString(query, parseAll=True)

    def build_es_query(self, parsed_query):
        # If the parsed query is a complex expression (e.g., ['term1', 'and', 'term2'])
        if isinstance(parsed_query, ParseResults) and len(parsed_query) > 1:
            operator = parsed_query[1]  # Get the operator ('and', 'or', 'not')
            if operator == "and":
                # For AND operators, use 'must'
                return {
                    "bool": {
                        "must": [
                            self.build_es_query(parsed_query[0]),  # Left operand
                            self.build_es_query(parsed_query[2])   # Right operand
                        ]
                    }
                }
            elif operator == "or":
                # For OR operators, use 'should'
                return {
                    "bool": {
                        "should": [
                            self.build_es_query(parsed_query[0]),  # Left operand
                            self.build_es_query(parsed_query[2])   # Right operand
                        ]
                    }
                }
            elif operator == "not":
                # For NOT operators, use 'must_not'
                return {
                    "bool": {
                        "must_not": self.build_es_query(parsed_query[2])  # Operand to negate
                    }
                }
        else:
            # If the parsed query is a single term (e.g., 'safaricom'), handle it as a match query
            if isinstance(parsed_query, ParseResults):
                term = parsed_query[0]  # Extract the single term as a string
            else:
                term = parsed_query  # This is already a string
            return {"match": {"raw_text": term}}
        
class SearchService:
    """ElasticSearch service for searching with parsed queries."""

    def __init__(self):
        self.es = es_client
        self.query_parser = QueryParser()

    def search_index(self, index_name: str, query: str, start_date: str = None, end_date: str = None, size: int = 10):

        try:
            # Parse the query and build Elasticsearch DSL query
            parsed_query = self.query_parser.parse_query(query)[0]
            es_query = self.query_parser.build_es_query(parsed_query)
            
            # Add date range filter if provided
            if start_date or end_date:
                date_range_query = {
                    "range": {
                        "timestamp": {  # Assuming the date field in the mappings is "timestamp"
                            "gte": start_date,  # Greater than or equal to start_date
                            "lte": end_date     # Less than or equal to end_date
                        }
                    }
                }
                # Combine date range filter with the main parsed query
                es_query = {
                    "bool": {
                        "must": [es_query, date_range_query]
                    }
                }
            # Perform the search query
            response = self.es.search(
                index=index_name,
                body={
                    "query": es_query,
                    "_source": {
                        "excludes": ["embeddings"]  # Exclude the 'embeddings' field
                    },
                    "size": size
                }
            )
            return response['hits']['hits']
        except NotFoundError:
            return {"error": f"Index {index_name} not found."}
        except ConnectionError:
            return {"error": "Could not connect to Elasticsearch server."}
        except Exception as e:
            return {"error": str(e)}
