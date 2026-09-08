"""
Dynamic Few-Shot In-Context Exemplar Store.
Indexes and retrieves golden training demonstrations from versioned dataset files
to provide few-shot epistemic grounding for LLM agents across all pipeline tasks.
"""

import os
import json
import glob
from typing import List, Dict, Any, Optional
from src.core.logging import logger
from src.gateway.base import ModelMessage


class ExemplarRegistry:
    """
    Registry that dynamically loads training demonstrations from datasets/
    and injects them as few-shot exemplars into live inference prompts.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ExemplarRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, datasets_dir: Optional[str] = None):
        if getattr(self, "_initialized", False):
            return
        self.datasets_dir = datasets_dir or self._resolve_datasets_dir()
        self.exemplars: Dict[str, List[Dict[str, Any]]] = {}
        self.load_all()
        self._initialized = True

    def _resolve_datasets_dir(self) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        primary = os.path.join(base_dir, "datasets")
        if os.path.exists(primary) and any(os.scandir(primary)):
            return primary
        secondary = os.path.join(base_dir, "output", "datasets")
        if os.path.exists(secondary):
            return secondary
        return primary

    def load_all(self):
        """Scans the dataset directory and indexes all training demonstration pairs."""
        if not os.path.exists(self.datasets_dir):
            logger.warning(f"ExemplarRegistry: Directory '{self.datasets_dir}' does not exist.")
            return

        jsonl_files = glob.glob(os.path.join(self.datasets_dir, "*.jsonl"))
        total_loaded = 0

        for fpath in jsonl_files:
            fname = os.path.basename(fpath).replace(".jsonl", "")
            task_key = fname.lower()
            self.exemplars[task_key] = []

            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fl:
                    for line in fl:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            self.exemplars[task_key].append(record)
                            total_loaded += 1
                        except Exception as e:
                            logger.debug(f"Skipping malformed line in {fname}: {e}")
            except Exception as e:
                logger.error(f"Error reading dataset {fpath}: {e}")

        logger.info(f"ExemplarRegistry: Indexed {total_loaded} training exemplars across {len(self.exemplars)} task domains.")

    def get_exemplars(self, task_name: str, count: int = 1) -> List[Dict[str, Any]]:
        """Retrieve golden exemplars for a specific task domain."""
        norm_key = task_name.lower().replace("-", "_").replace(" ", "_")
        matches = self.exemplars.get(norm_key, [])
        if not matches:
            for k in self.exemplars.keys():
                if norm_key in k or k in norm_key:
                    matches = self.exemplars[k]
                    break
        return matches[:count]

    def get_chat_messages(self, task_name: str, count: int = 1) -> List[ModelMessage]:
        """Format exemplars as a sequence of ModelMessage objects for chat completion injection."""
        exemplars = self.get_exemplars(task_name, count)
        result: List[ModelMessage] = []

        for ex in exemplars:
            if "messages" in ex and isinstance(ex["messages"], list):
                for m in ex["messages"]:
                    role = m.get("role", "user")
                    content = m.get("content", "")
                    if role in ("user", "assistant"):
                        result.append(ModelMessage(role=role, content=content))
            elif "user_prompt" in ex and "target_response" in ex:
                result.append(ModelMessage(role="user", content=ex["user_prompt"]))
                result.append(ModelMessage(role="assistant", content=ex["target_response"]))

        return result

    def format_few_shot_prompt(self, task_name: str, count: int = 1) -> str:
        """Format exemplars as a markdown few-shot text block for prompt preamble injection."""
        exemplars = self.get_exemplars(task_name, count)
        if not exemplars:
            return ""

        parts = ["\n### Golden Reference Demonstrations (Trained Grounding Examples):"]
        for i, ex in enumerate(exemplars, 1):
            if "messages" in ex and isinstance(ex["messages"], list):
                u = next((m.get("content", "") for m in ex["messages"] if m.get("role") == "user"), "")
                a = next((m.get("content", "") for m in ex["messages"] if m.get("role") == "assistant"), "")
                parts.append(f"\n[Example {i}]\nInput: {u}\nExpected Verified Output: {a}")
            elif "user_prompt" in ex and "target_response" in ex:
                parts.append(f"\n[Example {i}]\nInput: {ex['user_prompt']}\nExpected Verified Output: {ex['target_response']}")

        return "\n".join(parts) + "\n\n"


# Global singleton instance
default_exemplar_registry = ExemplarRegistry()
