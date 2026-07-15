from dotenv import load_dotenv
import os

load_dotenv()

PAT = os.getenv("AZURE_PAT")
ORG = os.getenv("AZURE_ORG")
PROJECT = os.getenv("AZURE_PROJECT")
API_KEY = os.getenv("GEMINI_API_KEY")
TEAM = os.getenv("TEAM")