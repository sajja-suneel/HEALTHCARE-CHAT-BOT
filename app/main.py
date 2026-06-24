from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.api import health, chat, upload
from fastapi.middleware.cors import CORSMiddleware

# Load env variables
load_dotenv()

app = FastAPI(
    title="Health",
    version="1.0.0"
)

# -------------------------
# Register Routers
# -------------------------
app.include_router(health.router)
app.include_router(upload.router)
app.include_router(chat.router)



# -------------------------
# Custom OpenAPI Schema Overrider (Fixes Multiple File Upload in Swagger UI)
# -------------------------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Health",
        version="1.0.0",
        routes=app.routes,
    )
    
    # 1. Fix file upload definitions in global component schemas
    for schema in openapi_schema.get("components", {}).get("schemas", {}).values():
        properties = schema.get("properties", {})
        for prop in properties.values():
            # Fix single file inputs
            if prop.get("contentMediaType") == "application/octet-stream":
                prop.pop("contentMediaType", None)
                prop["format"] = "binary"
            # Fix multiple file input arrays (List[UploadFile])
            elif prop.get("type") == "array":
                items = prop.get("items", {})
                if items.get("contentMediaType") == "application/octet-stream":
                    items.pop("contentMediaType", None)
                    items["format"] = "binary"

    # 2. Fix file upload definitions inside inline route request bodies
    for path_data in openapi_schema.get("paths", {}).values():
        for operation in path_data.values():
            request_body = operation.get("requestBody", {})
            content = request_body.get("content", {})
            for media_type in content.values():
                schema = media_type.get("schema", {})
                properties = schema.get("properties", {})
                for prop in properties.values():
                    # Fix single file inputs
                    if prop.get("contentMediaType") == "application/octet-stream":
                        prop.pop("contentMediaType", None)
                        prop["format"] = "binary"
                    # Fix multiple file input arrays (List[UploadFile])
                    elif prop.get("type") == "array":
                        items = prop.get("items", {})
                        if items.get("contentMediaType") == "application/octet-stream":
                            items.pop("contentMediaType", None)
                            items["format"] = "binary"
                            
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Assign the custom openapi schema generator
app.openapi = custom_openapi


# ==========================================================
# CORS
# ==========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# -------------------------
# Run Server
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )