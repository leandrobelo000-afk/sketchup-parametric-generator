import os

from dotenv import load_dotenv

from .main import create_app

# Para desenvolvimento sem o app desktop: `uvicorn backend_python.servidor_dev:app --reload` na raiz do repositório
load_dotenv()
app = create_app(token=os.getenv("SKETCHUP_AI_TOKEN"))
