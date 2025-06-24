# config.py
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

# Carica le variabili dal file .env
load_dotenv()

# Leggi le variabili d'ambiente
AZURE_ENDPOINT = os.getenv('AZURE_ENDPOINT')
AZURE_DEPLOYMENT = os.getenv('AZURE_DEPLOYMENT')
AZURE_API_KEY = os.getenv('AZURE_API_KEY')
AZURE_API_VERSION = os.getenv('AZURE_API_VERSION')

# Crea il client Azure OpenAI
azure_client = AzureOpenAI(
    api_version=AZURE_API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
)