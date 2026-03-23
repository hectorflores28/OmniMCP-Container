from fastmcp import FastMCP
from fastapi import Request # For direct SSE message handling
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 1. Inicializar FastMCP
mcp = FastMCP("OmniMCP-Container")

# Forzamos la creación de la app de FastAPI interna definiendo una herramienta dummy
@mcp.tool()
def _init_mcp(): pass

# 2. Configurar CORS y soporte de conexión directa
if hasattr(mcp, "_app") and mcp._app:
    mcp._app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 🛠️ SOPORTE DIRECTO PARA ANTIGRAVITY:
    # Capturamos POST a /sse para reenviarlos al gestor de mensajes de MCP
    @mcp._app.post("/sse")
    async def sse_post_handler(request: Request):
        return await mcp._app.handlers.get("post_messages")(request)


# 2. Tool: Web Search (Placeholder for Tavily or DuckDuckGo)
@mcp.tool()
async def web_search(query: str) -> str:
    """Searches the web for real-time information.
    Required environment variable: SEARCH_API_KEY (if using a specific service)
    """
    search_api_key = os.getenv("SEARCH_API_KEY")
    # For now, this is a mockup. In a real scenario, you'd call an API like Tavily:
    # async with httpx.AsyncClient() as client:
    #     response = await client.get(f"https://api.tavily.com/search?api_key={search_api_key}&query={query}")
    #     return response.text
    return f"Mock search results for: {query}. (Configure SEARCH_API_KEY for real results)"

# 3. Tool: Filesystem Access (Safe traversal within /data)
@mcp.tool()
def read_local_file(file_path: str) -> str:
    """Reads a file from the local mounted volume. 
    Files should be located in the /data directory inside the container.
    """
    # Security note: Ensure file_path doesn't attempt to escape /data
    safe_path = os.path.join("/data", os.path.normpath(file_path).lstrip(os.sep))
    
    if not os.path.exists(safe_path):
        return f"Error: File {file_path} not found in /data"
    
    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

# 4. Tool: Fetch Private Data (Generic GET with credentials)
@mcp.tool()
async def fetch_private_data(endpoint: str) -> str:
    """Fetches data from a private API using a secure token.
    Required environment variable: PRIVATE_TOKEN
    """
    token = os.getenv("PRIVATE_TOKEN")
    if not token:
        return "Error: PRIVATE_TOKEN not configured."
    
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        try:
            # Note: You should specify the base URL in your .env or code
            base_url = os.getenv("PRIVATE_API_BASE_URL", "https://api.example.com")
            response = await client.get(f"{base_url}/{endpoint}", headers=headers)
            response.raise_for_status()
            return json.dumps(response.json(), indent=2)
        except Exception as e:
            return f"Error fetching private data: {str(e)}"
    return "Error: Unexpected end of function."

# --- REEMPLAZA EL FINAL DE app.py CON ESTO ---
if __name__ == "__main__":
    import sys

    # 1. Si enviamos --sse (como hace el Dockerfile), abrimos el PUERTO 8000
    if "--sse" in sys.argv:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        # El print ayuda a depurar, pero para SSE debe ir ANTES de arrancar el servidor
        print(f"🚀 Iniciando servidor SSE en {host}:{port}")
        mcp.run(transport="sse", host=host, port=port)
    
    # 2. Si NO hay argumentos (como hace Antigravity), usamos el modo CONSOLA
    else:
        # IMPORTANTE: En modo stdio NO debemos imprimir nada extra a la consola 
        # o romperemos el JSON de comunicación con Antigravity.
        mcp.run(transport="stdio")