from elasticsearch import Elasticsearch

# Connect to Elasticsearch
es = Elasticsearch(["http://localhost:9200"])  # Adjust URL if needed

# Define the mapping
mapping = {
    "mappings": {
        "properties": {
            "name": {
                "type": "text",  # Searchable text
                "fields": {
                    "keyword": {  # Also keep exact match version
                        "type": "keyword"
                    }
                }
            },
            "skills": {
                "type": "nested",
                "properties": {
                    "name": {
                        "type": "keyword"  # For exact skill matches
                    },
                    "name_text": {
                        "type": "text"     # For partial text matches
                    }
                }
            },
            "experience": {
                "type": "float"
            },
            "cgpa": {
                "type": "float"
            }
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1
    }
}

# Create the index
index_name = "students"
if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)
es.indices.create(index=index_name, body=mapping)