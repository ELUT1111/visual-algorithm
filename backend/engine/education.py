"""Education content generation for algorithm metadata."""
from __future__ import annotations

import re
from typing import Any


_SECTION_LABELS = {
    "en": {
        "time": "Time",
        "space": "Space",
        "summary": "Summary",
        "idea": "Core idea",
        "implementation": "Implementation",
        "example_code": "Example code",
        "use_cases": "Typical scenarios",
        "next": "Next",
    },
    "zh": {
        "time": "时间",
        "space": "空间",
        "summary": "概述",
        "idea": "核心思路",
        "implementation": "实现方式",
        "example_code": "示例代码",
        "use_cases": "典型场景",
        "next": "下一步",
    },
}


_FAMILY_HINTS = {
    "graph": {
        "en": ("Graph problems", "Organize state around traversal, shortest paths, connectivity, flow, and cuts."),
        "zh": ("图论场景", "围绕图的遍历、最短路、连通性、流和割来组织状态。"),
    },
    "tree": {
        "en": ("Tree problems", "Organize state around hierarchy, ancestors, ranges, rotations, and path queries."),
        "zh": ("树结构场景", "围绕层次、祖先、区间、旋转和路径查询来组织状态。"),
    },
    "array": {
        "en": ("Array problems", "Organize state around scanning, divide-and-conquer, prefix sums, and static queries."),
        "zh": ("数组与区间场景", "围绕扫描、分治、前缀和和静态查询来组织状态。"),
    },
    "dp": {
        "en": ("Dynamic programming", "Organize state around transitions, table filling, and backtracking."),
        "zh": ("动态规划场景", "围绕状态转移、表格填充和回溯恢复来组织状态。"),
    },
    "string": {
        "en": ("String matching", "Organize state around prefixes, suffixes, windows, hashes, and automata."),
        "zh": ("字符串与模式匹配场景", "围绕前缀、后缀、窗口、哈希和自动机构建状态。"),
    },
}


_ALGO_PROFILES: dict[str, dict[str, tuple[str, str]]] = {
    "bfs": {
        "en": (
            "BFS expands the frontier level by level, so the first time a node appears is through the shortest unweighted route.",
            "Keep a queue, a visited set, and a parent map; every discovery is appended once and processed in FIFO order.",
        ),
        "zh": (
            "BFS 按层扩展前沿，因此一个节点第一次被发现时，就是它在无权图中的最短路径。",
            "维护队列、访问集合和前驱表；每次发现新节点都只入队一次，并按先进先出处理。",
        ),
    },
    "dfs": {
        "en": (
            "DFS goes deep first, then backtracks, which makes it ideal for discovery times, recursion trees, and component structure.",
            "Use a stack or recursion, and store the current path so the backtracking story stays visible.",
        ),
        "zh": (
            "DFS 先深入再回溯，很适合记录发现时间、递归树和组件结构。",
            "可以用栈或递归，并把当前路径保存下来，回溯过程就会更直观。",
        ),
    },
    "dijkstra": {
        "en": (
            "Dijkstra always expands the currently cheapest frontier node and relaxes its outgoing edges.",
            "A min-heap keeps the frontier ordered, while the distance table shows exactly when each node settles.",
        ),
        "zh": (
            "Dijkstra 总是扩展当前代价最小的前沿节点，并松弛它的出边。",
            "最小堆维护前沿顺序，距离表则清楚显示每个节点何时被最终确定。",
        ),
    },
    "kmp": {
        "en": (
            "KMP builds a prefix table so a mismatch can jump to the next viable alignment without rechecking old characters.",
            "The LPS table and fallback positions are the heart of the method.",
        ),
        "zh": (
            "KMP 会先构建前缀表，这样失配时就能直接跳到下一个可行对齐位置，而不必重复比较旧字符。",
            "LPS 表和回退位置就是它的核心。",
        ),
    },
    "lcs": {
        "en": (
            "LCS fills a dynamic-programming matrix to keep the longest common subsequence length and then backtracks to recover one solution.",
            "The diagonal matches and the backtrack path show exactly which characters survive the comparison.",
        ),
        "zh": (
            "LCS 会用动态规划矩阵保存最长公共子序列长度，再通过回溯恢复一个具体解。",
            "对角线匹配和回溯路径能直接看出哪些字符被保留了下来。",
        ),
    },
}


_PHRASE_TRANSLATIONS = [
    ("all-pairs shortest paths", "全源最短路径"),
    ("all pairs min cuts", "全对最小割"),
    ("bellman-ford potentials", "Bellman-Ford 潜势"),
    ("row/column reduction", "行列缩减"),
    ("row column reduction", "行列缩减"),
    ("exact dp search", "精确动态规划搜索"),
    ("segment tree", "线段树"),
    ("route table", "路由表"),
    ("routing table", "路由表"),
    ("routes", "路线"),
    ("route", "路线"),
    ("shortest paths", "最短路径"),
    ("shortest path", "最短路径"),
    ("minimum spanning tree", "最小生成树"),
    ("minimum-cost assignment", "最小费用分配"),
    ("minimum cost matching", "最小费用匹配"),
    ("minimum-cost matching", "最小费用匹配"),
    ("minimum cost", "最小费用"),
    ("maximum flow", "最大流"),
    ("minimum cut", "最小割"),
    ("minimum mean cycle", "最小平均环"),
    ("cycle basis", "环基"),
    ("suffix automaton", "后缀自动机"),
    ("suffix array", "后缀数组"),
    ("rolling hash", "滚动哈希"),
    ("level graph", "分层图"),
    ("blocking flow", "阻塞流"),
    ("preflow-push", "预流推进"),
    ("push-relabel", "推送重标记"),
    ("dominator tree", "支配树"),
    ("dominance frontier", "支配边界"),
    ("binary lifting", "倍增"),
    ("topological sort", "拓扑排序"),
    ("topological order", "拓扑序"),
    ("euler path", "欧拉路径"),
    ("residual network", "残量网络"),
    ("path queries", "路径查询"),
    ("range sum query", "区间和查询"),
    ("range minimum query", "区间最小值查询"),
    ("point updates", "单点更新"),
    ("substring search", "子串搜索"),
    ("pattern matching", "模式匹配"),
    ("graph traversals", "图遍历"),
    ("weighted grids", "带权网格"),
    ("weighted graph", "带权图"),
    ("weighted graphs", "带权图"),
    ("sparse all-pairs shortest paths", "稀疏全源最短路径"),
    ("sparse", "稀疏"),
    ("no negative cycles", "无负权环"),
    ("no negative cycle", "无负权环"),
    ("negative cycles", "负权环"),
    ("negative edges", "负权边"),
    ("worker-task", "工人-任务"),
    ("spur iterations", "支路迭代"),
    ("cut-equivalent tree", "割等价树"),
    ("global min cut", "全局最小割"),
    ("cycle contraction", "环收缩"),
    ("odd-cycle blossom", "奇环花朵"),
    ("independent light cycles", "独立轻环"),
    ("backup routes", "备份路线"),
    ("shortest alternatives", "最短备选路径"),
    ("DAG longest path", "DAG 最长路径"),
    ("control-flow joins", "控制流汇合点"),
    ("residual shortest paths", "残量最短路"),
    ("routing-table precomputation", "路由表预处理"),
    ("reweighting technique", "重标定技巧"),
    ("game pathfinding on weighted grids", "带权网格上的游戏寻路"),
    ("gps navigation and mapping", "GPS 导航与制图"),
    ("network routing protocols", "网络路由协议"),
    ("social network shortest connection", "社交网络最短连接"),
    ("fast substring search", "快速子串搜索"),
    ("text editors and search tools", "文本编辑器与搜索工具"),
    ("log scanning", "日志扫描"),
    ("pattern matching education", "模式匹配教学"),
    ("range sum queries", "区间和查询"),
    ("interval data structures", "区间数据结构"),
    ("competitive programming", "竞赛编程"),
    ("query-heavy dashboards", "查询密集型看板"),
]


_WORD_TRANSLATIONS = {
    "source": "源点",
    "target": "终点",
    "node": "节点",
    "nodes": "节点",
    "edge": "边",
    "edges": "边",
    "path": "路径",
    "paths": "路径",
    "search": "搜索",
    "sort": "排序",
    "match": "匹配",
    "matching": "匹配",
    "prefix": "前缀",
    "suffix": "后缀",
    "queue": "队列",
    "stack": "栈",
    "heap": "堆",
    "tree": "树",
    "graph": "图",
    "array": "数组",
    "matrix": "矩阵",
    "flow": "流",
    "cut": "割",
    "query": "查询",
    "queries": "查询",
    "update": "更新",
    "window": "窗口",
    "range": "区间",
    "weight": "权值",
    "weights": "权值",
    "capacity": "容量",
    "negative": "负权",
    "minimum": "最小",
    "maximum": "最大",
    "shortest": "最短",
    "longest": "最长",
    "dynamic": "动态",
    "programming": "规划",
    "all": "全",
    "pairs": "对",
    "level": "层",
    "bfs": "广度优先搜索",
    "dfs": "深度优先搜索",
    "dijkstra": "Dijkstra",
    "kmp": "KMP",
    "lcs": "LCS",
    "gps": "GPS",
    "navigation": "导航",
    "mapping": "制图",
    "network": "网络",
    "routing": "路由",
    "protocols": "协议",
    "log": "日志",
    "social": "社交",
    "connection": "连接",
    "connections": "连接",
    "comparison": "比较",
    "reasoning": "推理",
    "teaching": "教学",
    "education": "教学",
    "interactive": "交互式",
    "optimization": "优化",
    "optimized": "优化",
    "competitive": "竞赛",
    "operations": "运筹",
    "research": "研究",
    "reduction": "缩减",
    "reduced": "缩减",
    "exact": "精确",
    "dp": "动态规划",
    "sparse": "稀疏",
    "bellman": "Bellman",
    "ford": "Ford",
    "ospf": "OSPF",
    "column": "列",
    "columns": "列",
    "row": "行",
    "rows": "行",
    "precomputation": "预处理",
    "compression": "压缩",
    "worker": "工人",
    "task": "任务",
    "tasks": "任务",
    "assignment": "分配",
    "scheduling": "调度",
    "searching": "搜索",
    "substring": "子串",
    "palindrome": "回文",
    "residual": "残量",
    "fuel": "燃料",
    "build": "构建",
    "answer": "回答",
    "find": "求",
    "use": "使用",
    "using": "使用",
    "with": "结合",
    "and": "与",
    "or": "或",
    "for": "用于",
    "from": "从",
    "to": "到",
    "on": "在",
    "by": "通过",
    "one": "一个",
    "pass": "遍",
    "fast": "快速",
    "text": "文本",
    "editor": "编辑器",
    "editors": "编辑器",
    "tool": "工具",
    "tools": "工具",
    "game": "游戏",
    "research": "研究",
    "preprocessing": "预处理",
    "scan": "扫描",
    "scanning": "扫描",
    "interview": "面试",
    "algorithm": "算法",
    "algorithms": "算法",
    "greedy": "贪心",
    "divide": "分治",
    "conquer": "分治",
    "static": "静态",
    "cost": "费用",
    "costs": "费用",
    "route": "路线",
    "routes": "路线",
    "backup": "备份",
    "spur": "支路",
    "iterations": "迭代",
    "cycle": "环",
    "cycles": "环",
    "blossom": "花朵",
    "odd": "奇",
    "independent": "独立",
    "light": "轻",
    "equivalent": "等价",
    "global": "全局",
    "trail": "通路",
    "alternative": "备选",
    "alternatives": "备选",
    "average": "平均",
    "relabel": "重标记",
    "push": "推进",
    "preflow": "预流",
    "hierarchy": "层次",
    "ancestor": "祖先",
    "ancestors": "祖先",
    "rotation": "旋转",
    "rotations": "旋转",
    "backtracking": "回溯",
    "transitions": "状态转移",
    "transition": "状态转移",
    "table": "表",
    "tables": "表",
    "filling": "填充",
    "fill": "填充",
    "window": "窗口",
    "hashes": "哈希",
    "automata": "自动机",
}


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _apply_phrase_translations(text: str) -> str:
    translated = text
    for english, chinese in sorted(_PHRASE_TRANSLATIONS, key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(re.escape(english), chinese, translated, flags=re.IGNORECASE)
    return translated


def _translate_text(text: str) -> str:
    result = str(text or "").strip()
    if not result:
        return ""

    result = _apply_phrase_translations(result)
    result = re.sub(r"([A-Za-z]+)-([A-Za-z]+)", r"\1 \2", result)
    result = re.sub(r"\b(a|an|the)\b", " ", result, flags=re.IGNORECASE)
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_']*|[0-9]+|[\u4e00-\u9fff]+|\s+|[^\w\s]", result)
    translated: list[str] = []
    for token in tokens:
        if not token or token.isspace():
            translated.append(token)
            continue
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_']*", token):
            translated.append(_WORD_TRANSLATIONS.get(token.lower(), token))
        else:
            translated.append(token)

    text_zh = "".join(translated)
    text_zh = re.sub(r"\s+([,.;:!?。！？；：])", r"\1", text_zh)
    text_zh = re.sub(r"\(\s+", "(", text_zh)
    text_zh = re.sub(r"\s+\)", ")", text_zh)
    text_zh = re.sub(r"\s{2,}", " ", text_zh).strip()
    return text_zh


def _default_profile(meta: Any) -> dict[str, tuple[str, str]]:
    category = str(getattr(meta, "category", "") or "").lower()
    category_en, category_zh = {
        "graph": ("graph", "图"),
        "tree": ("tree", "树"),
        "array": ("array", "数组"),
        "dp": ("dynamic programming", "动态规划"),
        "string": ("string", "字符串"),
    }.get(category, ("problem", "问题"))

    description = str(getattr(meta, "description", "") or "").strip()
    name = str(getattr(meta, "name", "") or "").replace("_", " ").strip()
    family = _FAMILY_HINTS.get(category)

    summary_en = description or f"Study {name} through a step-by-step {category_en} visualization."
    idea_en = f"Track the key {category_en} state, then update only the part that changes at each step."
    summary_zh = _translate_text(description) or f"通过逐步可视化学习 {name} 这个{category_zh}问题。"
    idea_zh = f"重点追踪核心{category_zh}状态，并在每一步只更新真正变化的部分。"

    if family:
        if not description:
            summary_en = f"Study {name} through a step-by-step {family['en'][0].lower()} visualization."
        idea_en = family["en"][1]
        if not _contains_cjk(summary_zh):
            summary_zh = f"通过逐步可视化学习 {name} 这个{category_zh}问题。"
        summary_zh = summary_zh if _contains_cjk(summary_zh) else family["zh"][0]
        idea_zh = family["zh"][1]

    return {"en": (summary_en, idea_en), "zh": (summary_zh, idea_zh)}


def _build_english_use_cases(meta: Any) -> list[str]:
    cases = [str(item).strip() for item in getattr(meta, "use_cases", []) or [] if str(item).strip()]
    if cases:
        return cases

    name = str(getattr(meta, "name", "") or "").replace("_", " ")
    category = str(getattr(meta, "category", "") or "").lower()
    prefix = _FAMILY_HINTS.get(category, {}).get("en", ("General education", ""))[0]
    return [
        f"{prefix}: {name}",
        "Interactive teaching and demonstrations",
        "Algorithm comparison and reasoning exercises",
    ]


def _build_zh_use_cases(meta: Any, en_cases: list[str]) -> list[str]:
    category = str(getattr(meta, "category", "") or "").lower()
    header = _FAMILY_HINTS.get(category, {}).get("zh", ("通用场景", ""))[0]

    zh_cases: list[str] = []
    for case in en_cases:
        translated = _translate_text(case)
        zh_cases.append(translated if translated else case)

    if not zh_cases:
        zh_cases = [
            f"{header}：{str(getattr(meta, 'name', '') or '').replace('_', ' ')}",
            "交互式教学与演示",
            "算法对比与推理练习",
        ]
    return zh_cases


def _build_implementation(summary_en: str, idea_en: str, summary_zh: str, idea_zh: str, pseudocode: str) -> dict[str, str]:
    if pseudocode:
        return {"en": idea_en, "zh": idea_zh}
    return {"en": summary_en, "zh": summary_zh}


def build_education_content(meta: Any) -> dict[str, dict[str, Any]]:
    """Return bilingual education content for an algorithm meta object."""
    name = str(getattr(meta, "name", "") or "").lower()
    profile = _ALGO_PROFILES.get(name) or _default_profile(meta)
    summary_en, idea_en = profile["en"]
    summary_zh, idea_zh = profile["zh"]
    description = str(getattr(meta, "description", "") or "").strip()
    pseudocode = str(getattr(meta, "pseudocode", "") or "").strip()
    use_cases_en = _build_english_use_cases(meta)
    use_cases_zh = _build_zh_use_cases(meta, use_cases_en)
    impl = _build_implementation(summary_en, idea_en, summary_zh, idea_zh, pseudocode)

    if description and name not in _ALGO_PROFILES:
        summary_en = description

    return {
        "en": {
            "summary": summary_en,
            "idea": idea_en,
            "implementation": impl["en"],
            "example_code": pseudocode,
            "use_cases": use_cases_en,
            "time": str(getattr(meta, "time_complexity", "") or "").strip() or "O(?)",
            "space": str(getattr(meta, "space_complexity", "") or "").strip() or "O(?)",
            "labels": _SECTION_LABELS["en"],
        },
        "zh": {
            "summary": summary_zh,
            "idea": idea_zh,
            "implementation": impl["zh"],
            "example_code": pseudocode,
            "use_cases": use_cases_zh,
            "time": str(getattr(meta, "time_complexity", "") or "").strip() or "O(?)",
            "space": str(getattr(meta, "space_complexity", "") or "").strip() or "O(?)",
            "labels": _SECTION_LABELS["zh"],
        },
    }
