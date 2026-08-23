import pytest

from src.tools.doc_search import (
    create_search_engine,
    doc_search,
)
from src.schemas.doc_search_schema import (
    DocumentSearchInput,
)


@pytest.fixture(scope="module")
def search_engine():
    return create_search_engine()


def test_current_policy_search(search_engine):

    results = doc_search(
        DocumentSearchInput(
            query="current P2 support response target",
            top_k=5,
        ),
        search_engine=search_engine,
    )

    assert results

    for result in results:
        assert result.status != "DEPRECATED"


def test_northstar_search_returns_agreement(
    search_engine,
):

    results = doc_search(
        DocumentSearchInput(
            query="Northstar cancellation before pickup",
            account_id="ACCT-001",
            top_k=5,
        ),
        search_engine=search_engine,
    )

    assert results

    assert any(
        result.account_id == "ACCT-001"
        for result in results
    )


def test_account_scope_excludes_other_agreements(
    search_engine,
):

    results = doc_search(
        DocumentSearchInput(
            query="service agreement cancellation terms",
            account_id="ACCT-001",
            top_k=10,
        ),
        search_engine=search_engine,
    )

    assert all(
        result.account_id in {
            None,
            "ACCT-001",
        }
        for result in results
    )


def test_deprecated_excluded_by_default(
    search_engine,
):

    results = doc_search(
        DocumentSearchInput(
            query="Enterprise P1 response time",
            top_k=10,
        ),
        search_engine=search_engine,
    )

    assert all(
        result.status != "DEPRECATED"
        for result in results
    )