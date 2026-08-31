import hashlib
import json
from typing import List, Dict, Any

class StablePrefix:
    def __init__(self, system_instruction: str, policies: str, org_context: str, tools: List[Dict[str, Any]]):
        self.system_instruction = system_instruction
        self.policies = policies
        self.org_context = org_context
        # Deterministically sort tools
        self.tools = sorted(tools, key=lambda x: json.dumps(x, sort_keys=True))
        
    def hash_prefix(self) -> str:
        # Create deterministic hash for exact prefix
        data = {
            "system_instruction": self.system_instruction,
            "policies": self.policies,
            "org_context": self.org_context,
            "tools": self.tools
        }
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

class PromptBuilder:
    def __init__(self, prefix: StablePrefix):
        self.prefix = prefix
        
    def build(self, user_request: str, memory: List[Dict[str, str]] = None, dynamic_context: List[str] = None) -> List[Dict[str, str]]:
        messages = []
        
        # 1. System instruction
        # 2. Stable policy and safety instructions
        # 3. Stable organization or project context
        # 4. Stable tool definitions in deterministic order
        system_content = f"{self.prefix.system_instruction}\n\nPolicies:\n{self.prefix.policies}\n\nContext:\n{self.prefix.org_context}"
        if self.prefix.tools:
            system_content += f"\n\nTools:\n{json.dumps(self.prefix.tools, sort_keys=True)}"
            
        messages.append({"role": "system", "content": system_content})
        
        # 5. Stable retrieval corpus (skipped for now, assuming org_context covers it)
        # 6. Conversation memory
        if memory:
            messages.extend(memory)
            
        # 7. Dynamic retrieval results
        # 8. Agent/task state
        if dynamic_context:
            for ctx in dynamic_context:
                messages.append({"role": "system", "content": f"Dynamic Context:\n{ctx}"})
                
        # 9. User request
        messages.append({"role": "user", "content": user_request})
        
        return messages
