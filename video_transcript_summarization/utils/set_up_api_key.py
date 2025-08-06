# def get_api_key(api_endpoint):
#     if api_endpoint == "Groq":
#       return get_groq_api_key()
#     try:
#         from google.colab import userdata
#         api_key = userdata.get('api_key')
#     except ImportError:
#         load_dotenv()
#         api_key = os.getenv('api_key')
#
#     if not api_key:
#         raise ValueError("API key not found in environment variables or Colab secrets")
#
#     return api_key

# def get_groq_api_key():
#     try:
#         from google.colab import userdata
#         groq_api_key = userdata.get('api_key_groq')
#     except ImportError:
#         load_dotenv()
#         groq_api_key = os.getenv('api_key_groq')
#
#     if not groq_api_key:
#         raise ValueError("Groq API key not found in environment variables or Colab secrets")
#
#     return groq_api_key