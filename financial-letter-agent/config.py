# config.py
from openai import AzureOpenAI

AZURE_ENDPOINT = "https://matte-mb4x24lj-eastus2.cognitiveservices.azure.com/"
AZURE_DEPLOYMENT = "gpt-4o-2"
AZURE_API_KEY = "DF3ExC1zxMYZiu1NFefdjQPfJzum2bH3Kk7OE5aOj6yi7leDOSP1JQQJ99BEACHYHv6XJ3w3AAAAACOGvXwd"
AZURE_API_VERSION = "2024-12-01-preview"

azure_client = AzureOpenAI(
    api_version=AZURE_API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
)
