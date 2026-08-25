from __future__ import annotations

import logging
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from src.schemas.doc_search_schema import (
    DocumentSearchInput,
    DocumentSearchResult,
)


logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parents[2]

CHROMA_DIR = BASE_DIR / "data" / "chroma"

COLLECTION_NAME = "parcelpilot_documents"

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


class DocumentSearch:
    """Semantic search over the ParcelPilot document index."""

    def __init__(self,chroma_dir: Path = CHROMA_DIR,embedding_model: str = EMBEDDING_MODEL,) -> None:

        self.chroma_dir = chroma_dir

        logger.info(
            "Loading embedding model: %s",
            embedding_model,
        )

        self.embedding_model = SentenceTransformer(
            embedding_model
        )

        self.client = chromadb.PersistentClient(
            path=str(chroma_dir)
        )

        try:
            self.collection = (
                self.client.get_collection(
                    name=COLLECTION_NAME
                )
            )
        except Exception as exc:
            raise RuntimeError(
                f"Chroma collection '{COLLECTION_NAME}' "
                "does not exist. Build the document index first."
            ) from exc

    def _build_where_filter(
        self,
        account_id: str | None,
        include_deprecated: bool,
    ) -> dict | None:
        """
        Build Chroma metadata filters.

        Default behaviour:
        - exclude deprecated documents
        - include general documents
        - optionally include account-specific agreements
        """

        conditions: list[dict] = []

        # Never return deprecated documents unless explicitly requested.
        if not include_deprecated:
            conditions.append(
                {
                    "status": {
                        "$ne": "DEPRECATED"
                    }
                }
            )

        # Customer/account-specific retrieval.
        #
        # General documents use account_id = "".
        # An account-scoped query may retrieve:
        #   account_id == ""
        #   account_id == requested account
        if account_id:
            conditions.append(
                {
                    "$or": [
                        {
                            "account_id": ""
                        },
                        {
                            "account_id": account_id
                        },
                    ]
                }
            )

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        return {
            "$and": conditions
        }

    def search(
        self,
        request: DocumentSearchInput,
    ) -> list[DocumentSearchResult]:
        """Search the Chroma document collection."""

        logger.info(
            "Document search started | query=%r | account_id=%s | "
            "top_k=%d | include_deprecated=%s",
            request.query,
            request.account_id,
            request.top_k,
            request.include_deprecated,
        )

        query_embedding = self.embedding_model.encode(
            request.query,
            normalize_embeddings=True,
        ).tolist()

        where_filter = self._build_where_filter(
            account_id=request.account_id,
            include_deprecated=request.include_deprecated,
        )

        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": request.top_k,
        }

        if where_filter is not None:
            query_kwargs["where"] = where_filter

        results = self.collection.query(
            **query_kwargs
        )

        documents = results.get(
            "documents",
            [[]],
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]],
        )[0]

        distances = results.get(
            "distances",
            [[]],
        )[0]

        search_results: list[
            DocumentSearchResult
        ] = []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        ):
            # Chroma returns distance rather than similarity.
            # With normalized embeddings, cosine distance is
            # commonly used. Convert it to an intuitive score.
            score = 1.0 - float(distance)

            search_results.append(
                DocumentSearchResult(
                    content=document,
                    document_name=metadata[
                        "document_name"
                    ],
                    document_type=metadata[
                        "document_type"
                    ],
                    status=metadata[
                        "status"
                    ],
                    version=(
                        metadata.get("version")
                        or None
                    ),
                    effective_date=metadata[
                        "effective_date"
                    ],
                    account_id=(
                        metadata.get("account_id")
                        or None
                    ),
                    customer_name=(
                        metadata.get("customer_name")
                        or None
                    ),
                    score=score,
                )
            )

        logger.info(
            "Document search completed | results=%d",
            len(search_results),
        )

        return search_results



def create_search_engine() -> DocumentSearch:
    """
    Create the document search engine.

    This loads the embedding model and initializes
    the Chroma collection. It should normally be called
    once during FastAPI application startup.
    """
    return DocumentSearch()

_search_engine: DocumentSearch | None = None


def get_search_engine() -> DocumentSearch:
    global _search_engine

    if _search_engine is None:
        logger.info(
            "Initializing document search engine."
        )
        _search_engine = create_search_engine()
        logger.info(
            "Document search engine initialized."
        )

    return _search_engine

def doc_search(
    query: str | DocumentSearchInput,
    account_id: str | None = None,
    top_k: int = 5,
    include_deprecated: bool = False,
    search_engine: DocumentSearch | None = None,
) -> list[DocumentSearchResult]:

    if isinstance(
        query,
        DocumentSearchInput,
    ):
        request = query
    else:
        request = DocumentSearchInput(
            query=query,
            account_id=account_id,
            top_k=top_k,
            include_deprecated=include_deprecated,
        )

    if search_engine is None:
        search_engine = get_search_engine()

    return search_engine.search(request)