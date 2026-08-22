from src.tools.doc_search import doc_search
from src.schemas.doc_search_schema import DocumentSearchInput


def test_current_policy_search():

    results = doc_search(
        DocumentSearchInput(
            query="current P2 support response target",
            top_k=5,
        )
    )

    assert results

    for result in results:
        assert result.status != "DEPRECATED"

def test_northstar_search_returns_agreement():

    results = doc_search(
        DocumentSearchInput(
            query="Northstar cancellation before pickup",
            account_id="ACCT-001",
            top_k=5,
        )
    )

    assert results

    assert any(
        result.account_id == "ACCT-001"
        for result in results
    )

def test_account_scope_excludes_other_agreements():

    results = doc_search(
        DocumentSearchInput(
            query="service agreement cancellation terms",
            account_id="ACCT-001",
            top_k=10,
        )
    )

    assert all(
        result.account_id in {None, "ACCT-001"}
        for result in results
    )

def test_deprecated_excluded_by_default():

    results = doc_search(
        DocumentSearchInput(
            query="Enterprise P1 response time",
            top_k=10,
        )
    )

    assert all(
        result.status != "DEPRECATED"
        for result in results
    )