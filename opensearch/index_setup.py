from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

region = "us-east-1"
host = "YOUR-OPENSEARCH-ENDPOINT"  # e.g. search-xxx.us-east-1.es.amazonaws.com

credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, "es")

client = OpenSearch(
    hosts=[{"host": host, "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
)

index_body = {
    "settings": {"index": {"knn": True}},
    "mappings": {
        "properties": {
            "text": {"type": "text"},
            "vector": {"type": "knn_vector", "dimension": 1536},
        }
    },
}

client.indices.create(index="kb-index", body=index_body)
print("Index created")
