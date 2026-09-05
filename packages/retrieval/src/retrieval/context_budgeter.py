from retrieval.document_models import Chunk


class ContextBudgeter:
    def __init__(self, max_tokens: int = 4096, chars_per_token: float = 4.0):
        self.max_tokens = max_tokens
        self.chars_per_token = chars_per_token

    def filter_and_budget(
        self, candidate_chunks: list[Chunk], tenant_scope: str, auth_scope: str
    ) -> tuple[list[Chunk], dict]:
        selected = []
        metadata = {
            "total_candidates": len(candidate_chunks),
            "excluded_unauthorized": 0,
            "excluded_budget": 0,
            "excluded_duplicate": 0,
            "estimated_tokens_used": 0,
        }

        seen_content = set()
        current_tokens = 0

        for chunk in candidate_chunks:
            # 1. Tenant/Auth Filtering
            if chunk.metadata.tenant != tenant_scope or chunk.metadata.auth_scope != auth_scope:
                metadata["excluded_unauthorized"] += 1
                continue

            # 2. Deduplication (naive exact match for now)
            if chunk.content in seen_content:
                metadata["excluded_duplicate"] += 1
                continue

            # 3. Budgeting
            est_tokens = int(len(chunk.content) / self.chars_per_token)
            if current_tokens + est_tokens > self.max_tokens:
                metadata["excluded_budget"] += 1
                continue

            # Accept
            seen_content.add(chunk.content)
            current_tokens += est_tokens
            selected.append(chunk)

        metadata["estimated_tokens_used"] = current_tokens
        return selected, metadata
