from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
import google.generativeai as genai

# Load embedding model once
model = SentenceTransformer("BAAI/bge-small-en-v1.5")

# Load Chroma
client = PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("pdf_collection")

# Configure Gemini
genai.configure(api_key="your api-key")
gemini = genai.GenerativeModel("gemini-2.5-flash")

async def handle_query(question: str):
    # 1. Embed question
    q_emb = model.encode(question).tolist()

    # 2. Search in Chroma
    results = collection.query(query_embeddings=[q_emb], n_results=5)

    retrieved = "\n\n".join(r for r in results["documents"][0])

    # 3. Prepare prompt
    prompt = f"""
    You are a study assistant.

    QUESTION:
    {question}

    RELEVANT NOTES:
    {retrieved}

    Answer clearly using the above notes. 
    """

    # 4. Ask Gemini
    response = gemini.generate_content(prompt)

    return response.text
