"""
Demo RAG: sobe um documento (.txt ou .pdf), indexa no Azure AI Search
com embeddings, e permite conversar com ele via Azure OpenAI.

Uso:
    python rag_chat.py ingest caminho/do/documento.pdf
    python rag_chat.py chat
"""

import os
import sys
import uuid

from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

load_dotenv()

SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
SEARCH_KEY = os.environ["AZURE_SEARCH_KEY"]
SEARCH_INDEX = os.environ["AZURE_SEARCH_INDEX"]

OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
OPENAI_KEY = os.environ["AZURE_OPENAI_KEY"]
CHAT_DEPLOYMENT = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]
EMBEDDING_DEPLOYMENT = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]

EMBEDDING_DIMENSIONS = 1536  # text-embedding-3-small
CHUNK_SIZE_CHARS = 1500
CHUNK_OVERLAP_CHARS = 200

openai_client = AzureOpenAI(
    azure_endpoint=OPENAI_ENDPOINT,
    api_key=OPENAI_KEY,
    api_version="2024-10-21",
)


# --------------------------------------------------------------------------
# Leitura e chunking do documento
# --------------------------------------------------------------------------
def read_document(path: str) -> str:
    if path.lower().endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str, size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return [c.strip() for c in chunks if c.strip()]


def embed(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input=text,
    )
    return response.data[0].embedding


# --------------------------------------------------------------------------
# Índice no Azure AI Search
# --------------------------------------------------------------------------
def ensure_index():
    index_client = SearchIndexClient(SEARCH_ENDPOINT, AzureKeyCredential(SEARCH_KEY))

    if SEARCH_INDEX in [i.name for i in index_client.list_indexes()]:
        return

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name="default-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="default-hnsw")],
        profiles=[
            VectorSearchProfile(
                name="default-profile",
                algorithm_configuration_name="default-hnsw",
            )
        ],
    )

    index = SearchIndex(name=SEARCH_INDEX, fields=fields, vector_search=vector_search)
    index_client.create_index(index)
    print(f"Índice '{SEARCH_INDEX}' criado.")


def ingest(path: str):
    ensure_index()
    search_client = SearchClient(SEARCH_ENDPOINT, SEARCH_INDEX, AzureKeyCredential(SEARCH_KEY))

    print(f"Lendo {path}...")
    text = read_document(path)
    chunks = chunk_text(text)
    print(f"{len(chunks)} pedaços (chunks) gerados. Gerando embeddings e enviando...")

    docs = []
    for chunk in chunks:
        docs.append(
            {
                "id": str(uuid.uuid4()),
                "content": chunk,
                "source": os.path.basename(path),
                "content_vector": embed(chunk),
            }
        )

    search_client.upload_documents(docs)
    print(f"Pronto! {len(docs)} chunks indexados em '{SEARCH_INDEX}'.")


# --------------------------------------------------------------------------
# Chat com RAG
# --------------------------------------------------------------------------
def retrieve(question: str, top_k: int = 4) -> list[str]:
    search_client = SearchClient(SEARCH_ENDPOINT, SEARCH_INDEX, AzureKeyCredential(SEARCH_KEY))
    vector_query = VectorizedQuery(
        vector=embed(question), k_nearest_neighbors=top_k, fields="content_vector"
    )
    results = search_client.search(search_text=None, vector_queries=[vector_query], top=top_k)
    return [r["content"] for r in results]


def ask(question: str) -> str:
    context_chunks = retrieve(question)
    context = "\n\n---\n\n".join(context_chunks)

    system_prompt = (
        "Você responde perguntas usando APENAS o contexto fornecido abaixo. "
        "Se a resposta não estiver no contexto, diga que não encontrou essa informação "
        "no documento.\n\nContexto:\n" + context
    )

    response = openai_client.chat.completions.create(
        model=CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


def chat_loop():
    print("Chat RAG iniciado. Digite 'sair' para encerrar.\n")
    while True:
        question = input("Você: ").strip()
        if question.lower() in ("sair", "exit", "quit"):
            break
        answer = ask(question)
        print(f"\nAssistente: {answer}\n")


# --------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "ingest":
        if len(sys.argv) < 3:
            print("Uso: python rag_chat.py ingest caminho/do/documento.pdf")
            sys.exit(1)
        ingest(sys.argv[2])

    elif command == "chat":
        chat_loop()

    else:
        print(__doc__)
        sys.exit(1)
