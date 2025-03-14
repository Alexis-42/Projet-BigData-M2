
from elasticsearch import Elasticsearch

class ES_connector:
    def __init__(self) -> None:
        self.es_client = None
        self.connect()

    def connect(self):
        # we can put host and port in config or env
        host = "elasticsearch"
        port = "9200"
        es = Elasticsearch(f"http://{host}:{port}")
        self.es_client = es
        
    def index_data(self, index_name: str, data: dict) -> dict:
        try:
            document_id = data.pop("html_url")
            # Index the document in Elasticsearch
            response = self.es_client.index(
                index=index_name,
                id=document_id,
                document=data
            )
            return response
        except Exception as e:
            # Handle other errors
            raise Exception(f"Failed to index data: {str(e)}")

    def insert_document(self, index_name, document_type, document_id, document, refresh=False):
        try:
            return self.es_client.index(index=index_name, doc_type=document_type, id=document_id, body=document,
                                            refresh='wait_for', request_timeout=30)
        except Exception as e:
            print(e)

    def get_data(self, index_name, search_query, size=10): #size can come from config file
        try:
            result = self.es_client.search(index=index_name, body=search_query, allow_partial_search_results=True,
                                           size=size, request_timeout=120)
            return result
        except Exception as e:
            print(e)

    def get_all_data(self, index_name):
        try:
            result = self.es_client.search(index=index_name, body={"query": {"match_all": {}}}, size=100)
            return result
        except Exception as e:
            print(e)


