import os
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
import chromadb

DATA_DIR = "data_pdfs"
EMBED_DIR = "embeddings"

os.makedirs(EMBED_DIR, exist_ok=True)

# ---- CONFIG ----
MAX_PDFS = 10
CHUNK_SIZE = 500      # characters per chunk
CHUNK_OVERLAP = 50    # character overlap


def extract_pdf_text(pdf_path):
    """Extract text from PDF with fallback OCR."""
    summary = {
        "pages": 0,
        "chars": 0,
        "used_ocr": False,
        "chunks": 0
    }

    text = ""

    try:
        reader = PdfReader(pdf_path)
        summary["pages"] = len(reader.pages)

        for page in reader.pages:
            text += page.extract_text() or ""

        summary["chars"] = len(text)

        if len(text.strip()) > 0:
            return text, summary
        else:
            print("🔍 Using OCR (scanned PDF detected)...")
            summary["used_ocr"] = True
            return ocr_pdf(pdf_path, summary)

    except Exception:
        print("🔍 Using OCR (PDF cannot be parsed)...")
        summary["used_ocr"] = True
        return ocr_pdf(pdf_path, summary)


def ocr_pdf(pdf_path, summary):
    """Perform OCR when PDF is scanned."""
    try:
        pages = convert_from_path(pdf_path)
        summary["pages"] = len(pages)

        ocr_text = ""
        for img in pages:
            ocr_text += pytesseract.image_to_string(img)

        summary["chars"] = len(ocr_text)
        return ocr_text, summary

    except Exception as e:
        print(f"❌ OCR failed: {e}")
        return "", summary


def chunk_text(text):
    """Split long text into overlapping chunks."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - CHUNK_OVERLAP

    return chunks


def embed_pdfs():
    print("Loading model: BAAI/bge-small-en-v1.5...")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_or_create_collection("pdf_embeddings")

    pdf_files = [
        f for f in os.listdir(DATA_DIR)
        if f.lower().endswith(".pdf")
    ][:MAX_PDFS]

    print(f"\n📁 Found {len(pdf_files)} PDFs\n")

    for pdf in pdf_files:
        print(f"\n📘 Processing: {pdf}")
        pdf_path = os.path.join(DATA_DIR, pdf)

        text, summary = extract_pdf_text(pdf_path)

        if len(text.strip()) == 0:
            print(f"⚠ No text found in {pdf}")
            continue

        # Chunking
        chunks = chunk_text(text)
        summary["chunks"] = len(chunks)

        print(f"📑 Extracted:")
        print(f"   • Pages: {summary['pages']}")
        print(f"   • Characters: {summary['chars']}")
        print(f"   • Chunks: {summary['chunks']}")
        print(f"   • OCR used: {summary['used_ocr']}")

        # Embeddings
        embeddings = model.encode(chunks, convert_to_numpy=True)

        for i, emb in enumerate(embeddings):
            collection.add(
                ids=[f"{pdf}_chunk_{i}"],
                embeddings=[emb],
                metadatas=[{"pdf": pdf, "chunk_index": i}],
                documents=[chunks[i]]
            )

        print(f"✔ Done embedding {summary['chunks']} chunks from {pdf}")

    print("\n🎉 ALL PDFs EMBEDDED SUCCESSFULLY!")


if __name__ == "__main__":
    embed_pdfs()
