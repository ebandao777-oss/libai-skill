#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rule loading and merging for AI text detection and rewriting."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# 默认规则文件路径
DEFAULT_RULES_FILE = Path(__file__).parent.parent / "resources" / "zh_rules.json"


class RuleSet:
    """Container for all detection and rewriting rules."""
    
    def __init__(self, rules_data: Dict[str, Any]):
        self.data = rules_data
    
    @property
    def replacements(self) -> Dict[str, str]:
        """替换规则：短语 -> 替换文本"""
        return self.data.get("replacements", {})
    
    @property
    def sentence_patterns(self) -> List[Dict[str, str]]:
        """句子级改写模式列表"""
        return self.data.get("sentence_patterns", [])
    
    @property
    def ai_jargon(self) -> List[str]:
        """AI 高频词汇列表"""
        return self.data.get("ai_jargon", [])
    
    @property
    def puffery_phrases(self) -> List[str]:
        """夸大性短语"""
        return self.data.get("puffery_phrases", [])
    
    @property
    def marketing_speak(self) -> List[str]:
        """宣传性语言"""
        return self.data.get("marketing_speak", [])
    
    @property
    def vague_attributions(self) -> List[str]:
        """模糊归因"""
        return self.data.get("vague_attributions", [])
    
    @property
    def hedging_phrases(self) -> List[str]:
        """模棱两可表达"""
        return self.data.get("hedging_phrases", [])
    
    @property
    def chatbot_artifacts(self) -> List[str]:
        """聊天机器人痕迹"""
        return self.data.get("chatbot_artifacts", [])
    
    @property
    def citation_bugs(self) -> List[str]:
        """引用痕迹"""
        return self.data.get("citation_bugs", [])
    
    @property
    def knowledge_cutoff(self) -> List[str]:
        """知识截止表述"""
        return self.data.get("knowledge_cutoff", [])
    
    @property
    def markdown_artifacts(self) -> List[str]:
        """Markdown 痕迹"""
        return self.data.get("markdown_artifacts", [])
    
    @property
    def negative_parallelisms(self) -> List[str]:
        """否定平行结构"""
        return self.data.get("negative_parallelisms", [])
    
    @property
    def superficial_verbs(self) -> List[str]:
        """肤浅动词"""
        return self.data.get("superficial_verbs", [])
    
    @property
    def filler_phrases(self) -> List[str]:
        """填充短语"""
        return self.data.get("filler_phrases", [])
    
    @property
    def rule_of_three_patterns(self) -> List[str]:
        """三点式结构"""
        return self.data.get("rule_of_three_patterns", [])
    
    @property
    def list_markers(self) -> List[str]:
        """列表标记"""
        return self.data.get("list_markers", [])
    
    @property
    def punctuation(self) -> Dict[str, int]:
        """标点阈值配置"""
        return self.data.get("punctuation", {})
    
    @property
    def rhetorical_patterns(self) -> List[str]:
        """反问句模式"""
        return self.data.get("rhetorical_patterns", [])
    
    @property
    def sentence_starters(self) -> List[str]:
        """句首连接词"""
        return self.data.get("sentence_starters", [])


@lru_cache(maxsize=4)
def load_rules(file_path: Union[str, Path] = None) -> RuleSet:
    """加载规则文件，返回 RuleSet 实例。
    
    使用 LRU 缓存（maxsize=4），避免每次实例化都重新解析 1900+ 行 JSON。
    """
    path = Path(file_path) if file_path else DEFAULT_RULES_FILE
    if not path.exists():
        raise FileNotFoundError(f"Rules file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 省略号统一：将 replacements 键中的 ……(U+2026) 替换为 ASCII ...，
        # 使其与 utils.clean_text() 的省略号正常化保持一致
        if "replacements" in data and isinstance(data["replacements"], dict):
            norm = {}
            for k, v in data["replacements"].items():
                nk = k.replace('\u2026', '...')
                norm[nk] = v
            data["replacements"] = norm
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in rules file {path}: {e.msg}",
            e.doc, e.pos
        ) from e
    return RuleSet(data)


# Whitelist of allowed keys for user-supplied rules (must match RuleSet properties)
ALLOWED_RULE_KEYS = {
    "replacements", "sentence_patterns", "ai_jargon", "puffery_phrases",
    "marketing_speak", "vague_attributions", "hedging_phrases", "chatbot_artifacts",
    "citation_bugs", "knowledge_cutoff", "markdown_artifacts", "negative_parallelisms",
    "superficial_verbs", "filler_phrases", "rule_of_three_patterns", "list_markers",
    "punctuation", "rhetorical_patterns", "sentence_starters", "post_cleanup",
}


def _filter_user_rules(user_rules: Dict[str, Any]) -> Dict[str, Any]:
    """Strip unknown/unauthorized keys from user-supplied rules to prevent injection."""
    rejected = [k for k in user_rules if k not in ALLOWED_RULE_KEYS]
    if rejected:
        import warnings
        warnings.warn(f"Ignored unauthorized rule keys: {rejected}")
    return {k: v for k, v in user_rules.items() if k in ALLOWED_RULE_KEYS}


def merge_rules(base: RuleSet, user_rules: Dict[str, Any]) -> RuleSet:
    """合并用户自定义规则到基础规则集。"""
    merged = base.data.copy()
    for key, value in user_rules.items():
        if key in merged:
            if isinstance(merged[key], list) and isinstance(value, list):
                if value == []:
                    merged[key] = []
                else:
                    merged[key].extend(value)
            elif isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key].update(value)
            else:
                merged[key] = value
        else:
            merged[key] = value
    return RuleSet(merged)


def _validate_rules_path(file_path: Union[str, Path]) -> Path:
    """Validate that a user-supplied rules path is within the resources directory."""
    resolved = Path(file_path).resolve()
    resources_dir = (Path(__file__).parent.parent / "resources").resolve()
    try:
        resolved.relative_to(resources_dir)
    except ValueError:
        raise ValueError(
            f"Security: rules file must be within {resources_dir}. "
            f"Rejected path: {file_path}"
        )
    if not resolved.exists():
        raise FileNotFoundError(f"Rules file not found: {resolved}")
    return resolved


def load_rules_with_user(user_rules_path: Optional[Union[str, Path]] = None) -> RuleSet:
    """加载默认规则，并可选地合并用户提供的规则文件。"""
    base = load_rules()
    if user_rules_path:
        safe_path = _validate_rules_path(user_rules_path)
        with open(safe_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)
        # Only allow whitelisted keys in user rules
        user_data = _filter_user_rules(user_data)
        return merge_rules(base, user_data)
    return base
