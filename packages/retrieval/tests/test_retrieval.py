from retrieval.context_budgeter import ContextBudgeter
from retrieval.document_models import Chunk, ChunkMetadata


def test_context_budgeter_auth():
    budgeter = ContextBudgeter()
    chunks = [
        Chunk(id="1", document_id="doc1", content="test", metadata=ChunkMetadata(tenant="t1", auth_scope="user", corpus_version="1", source="sys")),
        Chunk(id="2", document_id="doc1", content="secret", metadata=ChunkMetadata(tenant="t2", auth_scope="user", corpus_version="1", source="sys"))
    ]
    
    selected, meta = budgeter.filter_and_budget(chunks, tenant_scope="t1", auth_scope="user")
    assert len(selected) == 1
    assert selected[0].id == "1"
    assert meta["excluded_unauthorized"] == 1

def test_context_budgeter_dedup():
    budgeter = ContextBudgeter()
    chunks = [
        Chunk(id="1", document_id="doc1", content="duplicate", metadata=ChunkMetadata(tenant="t1", auth_scope="user", corpus_version="1", source="sys")),
        Chunk(id="2", document_id="doc1", content="duplicate", metadata=ChunkMetadata(tenant="t1", auth_scope="user", corpus_version="1", source="sys"))
    ]
    
    selected, meta = budgeter.filter_and_budget(chunks, tenant_scope="t1", auth_scope="user")
    assert len(selected) == 1
    assert meta["excluded_duplicate"] == 1
