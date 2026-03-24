import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        ef = SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL)
        _collection = _client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            embedding_function=ef,
        )
    return _collection


def store_article(article: dict):
    """Embed and store a news article."""
    col = _get_collection()
    col.upsert(
        ids=[article["url"]],
        documents=[article["headline"] + " " + article.get("content", "")],
        metadatas=[{
            "ticker": article.get("ticker", ""),
            "headline": article["headline"],
            "url": article["url"],
        }],
    )


def retrieve_relevant_news(ticker: str, query: str, n: int = 5) -> list[dict]:
    """Retrieve top-n relevant articles for a ticker + query."""
    col = _get_collection()
    try:
        results = col.query(
            query_texts=[query],
            n_results=n,
            where={"ticker": ticker.upper()},
        )
        articles = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            articles.append(
                {"headline": meta["headline"], "url": meta["url"], "content": doc})
        return articles
    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
        return []
