import json
from app.main import app

def generate_openapi_spec():
    openapi_schema = app.openapi()
    
    # Save as JSON
    with open("openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print("OpenAPI specification generated as openapi.json")

if __name__ == "__main__":
    generate_openapi_spec()
