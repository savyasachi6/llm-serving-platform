import pytest
from app.infrastructure.cache.exact_cache import CachePolicy, ExactCacheKeyBuilder
from contracts.openai_models import ChatCompletionRequest

def test_cache_bypassed_without_tenant():
    req = ChatCompletionRequest(model="test", messages=[])
    assert not CachePolicy.is_cacheable(req)
    
    req_tenant = ChatCompletionRequest(model="test", messages=[], tenant_scope="tenant1")
    assert CachePolicy.is_cacheable(req_tenant)

def test_exact_cache_key_determinism():
    req1 = ChatCompletionRequest(model="test", messages=[{"role": "user", "content": "hi"}], tenant_scope="tenant1")
    req2 = ChatCompletionRequest(model="test", messages=[{"role": "user", "content": "hi"}], tenant_scope="tenant1")
    req3 = ChatCompletionRequest(model="test", messages=[{"role": "user", "content": "hi"}], tenant_scope="tenant2")
    
    key1 = ExactCacheKeyBuilder.build_key(req1)
    key2 = ExactCacheKeyBuilder.build_key(req2)
    key3 = ExactCacheKeyBuilder.build_key(req3)
    
    assert key1 == key2
    assert key1 != key3 # tenant isolation
