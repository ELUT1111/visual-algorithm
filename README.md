# Visual Algorithm Lab

<p align="center">
  <h1>🧪 Visual Algorithm Lab</h1>
  <p><strong>Interactive Algorithm Visualization Platform</strong></p>
  <p>
    <a href="#english">English</a> | <a href="#chinese">中文</a>
  </p>

---

# English

## 📖 Introduction

Visual Algorithm Lab is a **highly interactive, visual algorithm learning platform** built with Python (FastAPI) and modern web technologies. It covers **graph, tree, array/DP, and string algorithms** with a highly extensible plugin architecture.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎨 **Interactive Graph Editor** | Create nodes and edges by clicking and dragging. Double-click to add nodes, drag between nodes to create edges. |
| 🛤️ **53 Built-in Algorithms** | 20 graph algorithms + 13 tree algorithms + 6 array algorithms + 9 DP algorithms + 5 string algorithms, all with step-by-step visualization. |
| 🧭 **Learning Paths** | Filter algorithms by curated tracks such as Graph Core, Graph Advanced, DP Foundations, String Matching, Data Structures, and Arrays. |
| 📈 **Algorithm Library Overview** | See total algorithm count, category counts, and available visualization modes directly in the sidebar. |
| ⭐ **Favorites & Recent Algorithms** | Pin frequently used algorithms and jump back to recently selected algorithms from the sidebar. |
| 🔎 **Algorithm Search** | Quickly filter the algorithm list by name, category, description, or use case. |
| ⏯️ **Real-time Controls** | Play, Pause, Step-forward, Reset with adjustable speed slider. |
| 🕒 **Timeline Replay** | Scrub completed runs, jump between steps, and replay recorded visual states locally. |
| 📊 **Structured State Panel** | Inspect queues, stacks, distance tables, parent maps, and DP decisions while algorithms run. |
| 💾 **Run Import/Export** | Export a completed run as JSON and import it later to restore the graph, timeline, steps, and final state. |
| 🧩 **Example Inputs** | Load curated sample parameters and preset graphs for common algorithms. |
| 💻 **Custom Algorithms** | Write your own Python algorithm in the built-in editor and run it instantly. |
| 📁 **JSON Import/Export** | Save and load graphs as JSON files. Preset graphs and trees included. |
| 🎲 **Graph Generator** | Generate random graphs, DAGs, grids, bipartite graphs, connected graphs, and negative-weight DAGs in-browser. |
| 🔢 **Array & Matrix Views** | Dedicated visual surfaces for sorting arrays and dynamic-programming matrices. |
| 🔌 **Plugin Architecture** | Drop a `.py` file into `backend/algorithms/<category>/` to add a new algorithm — auto-discovered on startup. |
| 🌙 **Dark Theme** | Eye-friendly dark UI designed for algorithm visualization. |
| ⌨️ **Keyboard Shortcuts** | `Space` = play/pause, `→` = step, `R` = reset. |
| 📐 **Resizable Panel** | Drag the handle between the graph area and the bottom panel to resize the step log.

### 🗂️ Built-in Algorithms

**Graph Algorithms (20)**
- BFS, DFS, Dijkstra, Bellman-Ford, SPFA, Johnson, Edmonds-Karp, Dinic, A\*, Prim, Kruskal, Topological Sort, Cycle Detection, Connected Components, Tarjan SCC, Kosaraju SCC, Union-Find, Bipartite Check, Floyd-Warshall, Bridges & Articulation Points

**Tree Algorithms (13)**
- BST, AVL, Red-Black Tree, B-Tree, B+ Tree, Heap, Fenwick Tree, Huffman, Trie, Aho-Corasick, Tree BFS, Tree DFS, Level Order

**Array / DP Algorithms (15)**
- Bubble Sort, Quick Sort, Merge Sort, Heap Sort, Binary Search, Kadane, Longest Common Subsequence (LCS), Edit Distance, 0/1 Knapsack, Coin Change, Longest Increasing Subsequence (LIS), Matrix Chain Multiplication, Fibonacci DP, Subset Sum, Word Break

**String Algorithms (5)**
- Knuth-Morris-Pratt (KMP), Rabin-Karp, Boyer-Moore, Z Algorithm, Manacher

### 🖼️ Architecture

```
┌──────────────┬──────────────────────────────────────────┐
│ Algorithms   │  ┌──────────────────────────────────┐   │
│ 🛤️ Graph    │  │                                  │   │
│  Dijkstra    │  │                                  │   │
│  BFS, DFS    │  │    Graph / Tree Visualization     │   │
│  Bellman-Ford│  │    (vis-network canvas)           │   │
│  A*, Prim    │  │                                  │   │
│  Kruskal     │  └──────────────────────────────────┘   │
│──────────────│  ═══════ drag handle (resizable) ══════  │
│ 🌲 Tree      │  ┌──────────────────────────────────┐   │
│  BST, AVL    │  │ ⏯️ Playback Controls              │   │
│  Red-Black   │  │  ▶️ ⏸️ ⏭️ 🔄  Speed: ───●────    │   │
│  B/B+ Tree   │  └──────────────────────────────────┘   │
│  Heap        │  ┌──────────────────────────────────┐   │
│  Huffman     │  │ 📋 Step Log (resizable)           │   │
│  Trie        │  │  [INIT] Created root             │   │
│  Aho-Corasick│  │  [EXPLORE] Visiting node A       │   │
│  Tree BFS/DFS│  └──────────────────────────────────┘   │
│  Level Order │  ┌──────────────────────────────────┐   │
│──────────────│  │ 💻 Code Editor                    │   │
│ 📁 Presets   │  └──────────────────────────────────┘   │
│  Import/Export└──────────────────────────────────────────┘
└──────────────┘
```

**Backend**: FastAPI + WebSocket for real-time step streaming
**Frontend**: Vanilla JS + vis-network (graph/tree visualization) + no build step

## 🚀 Quick Start

### Prerequisites

- Python 3.10+

### Installation

```bash
cd visual-algorithm
python -m venv .venv
source .venv/Scripts/activate    # Windows (Git Bash)
# .venv\Scripts\activate         # Windows (CMD)
pip install -r requirements.txt
```

### Run

```bash
python run.py
```

Open your browser and navigate to **http://localhost:8000**

### Frontend Smoke Tests

```bash
npm install
npm run test:e2e
```

### Full Regression

```bash
npm run verify
```

### Usage

1. 📁 **Load a preset** — click a preset card in the sidebar (graph or tree)
2. 🎨 **Or build your own** — click "Node" to add nodes, "Edge" to connect them
3. 🛤️ **Select an algorithm** — click an algorithm card in the sidebar
4. ⚙️ **Set parameters** — fill in parameters (e.g., values, patterns, source node)
5. ▶️ **Run** — click Play, use ⏸ Pause and ⏭ Step to control execution
6. 👀 **Watch** — nodes and edges change color as the algorithm progresses
7. 📐 **Resize the log** — drag the handle above the bottom panel to adjust height

## 📁 Project Structure

```
visual-algorithm/
├── run.py                           # Entry point
├── requirements.txt                 # Python dependencies
├── backend/
│   ├── app.py                       # FastAPI application
│   ├── models/
│   │   └── graph.py                 # Graph, Node, Edge models
│   ├── engine/
│   │   ├── protocol.py              # Algorithm protocol (ABC)
│   │   ├── registry.py              # Auto-discovery plugin registry
│   │   └── runner.py                # Execution lifecycle manager
│   ├── algorithms/
│   │   ├── graph/                   # Graph algorithms
│   │   │   ├── dijkstra.py
│   │   │   ├── bfs.py
│   │   │   ├── dfs.py
│   │   │   ├── bellman_ford.py
│   │   │   ├── spfa.py
│   │   │   ├── johnson.py
│   │   │   ├── edmonds_karp.py
│   │   │   ├── dinic.py
│   │   │   ├── astar.py
│   │   │   ├── prim.py
│   │   │   ├── kruskal.py
│   │   │   ├── topological_sort.py
│   │   │   ├── cycle_detection.py
│   │   │   ├── connected_components.py
│   │   │   ├── tarjan_scc.py
│   │   │   ├── kosaraju_scc.py
│   │   │   ├── union_find.py
│   │   │   ├── bipartite.py
│   │   │   ├── floyd_warshall.py
│   │   │   └── bridges_articulation.py
│   │   ├── array/                   # Array algorithms
│   │   │   ├── bubble_sort.py
│   │   │   ├── quick_sort.py
│   │   │   ├── merge_sort.py
│   │   │   ├── heap_sort.py
│   │   │   ├── binary_search.py
│   │   │   └── kadane.py
│   │   ├── dp/                      # Dynamic programming algorithms
│   │   │   ├── lcs.py
│   │   │   ├── edit_distance.py
│   │   │   ├── knapsack.py
│   │   │   ├── lis.py
│   │   │   ├── coin_change.py
│   │   │   ├── matrix_chain.py
│   │   │   ├── fibonacci_dp.py
│   │   │   ├── subset_sum.py
│   │   │   └── word_break.py
│   │   ├── string/                  # String algorithms
│   │   │   ├── kmp.py
│   │   │   ├── rabin_karp.py
│   │   │   ├── boyer_moore.py
│   │   │   ├── z_algorithm.py
│   │   │   └── manacher.py
│   │   └── tree/                    # Tree algorithms
│   │       ├── bst.py
│   │       ├── avl.py
│   │       ├── red_black.py
│   │       ├── btree.py
│   │       ├── bplus.py
│   │       ├── heap.py
│   │       ├── fenwick_tree.py
│   │       ├── huffman.py
│   │       ├── trie.py
│   │       ├── aho_corasick.py
│   │       ├── tree_bfs.py
│   │       ├── tree_dfs.py
│   │       └── level_order.py
│   ├── routers/                     # API endpoints
│   └── presets/
│       ├── graphs/                  # Preset graph JSON files
│       └── trees/                   # Preset tree JSON files
└── frontend/
    ├── index.html                   # Single-page app
    ├── css/style.css                # Styles (dark theme)
    └── js/                          # Modular JavaScript
        ├── app.js                   # Main application
        ├── graph-editor.js          # vis-network wrapper
        ├── visualizer.js            # Step action renderer
        ├── algorithm-panel.js       # Algorithm selector & controls
        ├── ws-client.js            # WebSocket client
        ├── code-editor.js           # Custom algorithm editor
        └── preset-manager.js        # Preset graph/tree loader
```

## 🔌 Adding Custom Algorithms

### Method 1: In-browser Code Editor

1. Scroll to "Custom Algorithm" in the sidebar
2. Write your algorithm following the template
3. Click "Submit Algorithm"
4. It appears in the algorithm list immediately

### Method 2: File (auto-discovered)

Create a `.py` file in `backend/algorithms/<category>/`:

```python
from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry

@registry.register
class MyAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="my_algorithm",
            category="tree",
            description="What it does",
            emoji="🔮",
            parameters=[
                {"name": "values", "type": "str", "required": True,
                 "description": "Comma-separated values"}
            ],
            time_complexity="O(n log n)",
            space_complexity="O(n)",
            layout="hierarchical",
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        yield Step(
            action=StepAction.ADD_NODE,
            target_type="node",
            target_id="root",
            value={"id": "root", "label": "root"},
            message="Start",
            phase="init",
        )
```

Restart the server — the new algorithm is auto-registered.

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health, registered algorithm count, category counts, and visualization counts |
| `GET` | `/api/algorithms` | List all algorithms with metadata |
| `GET` | `/api/graphs` | List preset graphs |
| `GET` | `/api/graphs/{id}` | Get a specific graph |
| `GET` | `/api/presets/bundle` | All presets as JSON |
| `POST` | `/api/algorithms/custom` | Submit custom algorithm code |
| `POST` | `/api/random-params` | Generate random parameters |
| `WS` | `/ws/run` | Algorithm execution (real-time step streaming) |

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic
- **Frontend**: Vanilla JavaScript, vis-network, CSS Custom Properties
- **Communication**: WebSocket for real-time algorithm step streaming
- **Data**: JSON files (no database required)

---

# Chinese

## 📖 项目介绍

Visual Algorithm Lab 是一个**高度交互式、可视化的算法学习平台**，使用 Python (FastAPI) 和现代 Web 技术构建。覆盖**图算法、树算法、数组/动态规划算法和字符串算法**，提供高度可扩展的插件化架构。

### ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🎨 **交互式图编辑器** | 点击画布添加节点，拖拽连线创建边，双击快速添加节点。 |
| 🛤️ **53 个内置算法** | 20 个图算法 + 13 个树算法 + 6 个数组算法 + 9 个动态规划算法 + 5 个字符串算法，全部支持逐步可视化。 |
| 🧭 **学习路线** | 可按 Graph Core、Graph Advanced、DP Foundations、String Matching、Data Structures、Arrays 等路线筛选算法。 |
| 📈 **算法库概览** | 在侧边栏直接查看算法总数、分类数量和可视化模式数量。 |
| ⭐ **收藏与最近使用** | 可收藏常用算法，并从侧边栏快速回到最近选择过的算法。 |
| 🔎 **算法搜索** | 可按名称、分类、描述或使用场景快速筛选算法列表。 |
| ⏯️ **实时控制** | 播放、暂停、单步、重置，配合速度滑块自由调节。 |
| 🕒 **时间轴回放** | 完成运行后可拖动时间轴、跳转步骤，并在本地重放已记录的可视化状态。 |
| 📊 **结构化状态面板** | 运行时查看队列、栈、距离表、父节点映射和动态规划决策。 |
| 💾 **运行记录导入/导出** | 可将一次完成的运行导出为 JSON，也可再次导入以恢复图、时间轴、步骤和最终状态。 |
| 🧩 **示例输入** | 为常见算法提供可一键加载的样例参数和预制图。 |
| 💻 **自定义算法** | 在内置代码编辑器中编写 Python 算法，提交后即可运行。 |
| 📁 **JSON 导入/导出** | 一键保存和加载图数据，预制图和预制树内置。 |
| 🎲 **图生成器** | 在浏览器内生成随机图、DAG、网格图、二分图、连通图和带负权 DAG。 |
| 🔢 **数组与矩阵视图** | 为排序数组和动态规划矩阵提供专用可视化区域。 |
| 🔌 **插件化架构** | 在 `backend/algorithms/<category>/` 中放入 `.py` 文件即可自动注册新算法。 |
| 🌙 **暗色主题** | 专为算法可视化设计的护眼深色界面。 |
| ⌨️ **键盘快捷键** | `空格` = 播放/暂停，`→` = 单步，`R` = 重置。 |
| 📐 **可拉伸面板** | 拖拽图形区域与底部面板之间的手柄，可自由调整日志区域高度。 |

### 🗂️ 内置算法

**图算法 (20)**
- BFS, DFS, Dijkstra, Bellman-Ford, SPFA, Johnson, Edmonds-Karp, Dinic, A\*, Prim, Kruskal, Topological Sort, Cycle Detection, Connected Components, Tarjan SCC, Kosaraju SCC, Union-Find, Bipartite Check, Floyd-Warshall, Bridges & Articulation Points

**树算法 (13)**
- BST, AVL, 红黑树, B-Tree, B+ Tree, Heap, Fenwick Tree, Huffman, Trie, Aho-Corasick, Tree BFS, Tree DFS, Level Order

**数组 / 动态规划算法 (15)**
- Bubble Sort, Quick Sort, Merge Sort, Heap Sort, Binary Search, Kadane, Longest Common Subsequence (LCS), Edit Distance, 0/1 Knapsack, Coin Change, Longest Increasing Subsequence (LIS), Matrix Chain Multiplication, Fibonacci DP, Subset Sum, Word Break

**字符串算法 (5)**
- Knuth-Morris-Pratt (KMP), Rabin-Karp, Boyer-Moore, Z Algorithm, Manacher

### 🖼️ 系统架构

```
┌──────────────┬──────────────────────────────────────────┐
│ 算法列表      │  ┌──────────────────────────────────┐   │
│ 🛤️ 图算法   │  │                                  │   │
│  Dijkstra    │  │                                  │   │
│  BFS, DFS    │  │    图 / 树可视化区域               │   │
│  Bellman-Ford│  │    (vis-network 画布)             │   │
│  A*, Prim    │  │                                  │   │
│  Kruskal     │  └──────────────────────────────────┘   │
│──────────────│  ═══════ 可拖拽手柄（可调整高度） ══════  │
│ 🌲 树算法    │  ┌──────────────────────────────────┐   │
│  BST, AVL    │  │ ⏯️ 播放控制栏                      │   │
│  Red-Black   │  │  ▶️ ⏸️ ⏭️ 🔄  速度: ───●────    │   │
│  B/B+ Tree   │  └──────────────────────────────────┘   │
│  Heap        │  ┌──────────────────────────────────┐   │
│  Huffman     │  │ 📋 步骤日志（可调整高度）           │   │
│  Trie        │  │  [INIT] 创建根节点               │   │
│  Aho-Corasick│  │  [EXPLORE] 访问节点 A            │   │
│  Tree BFS/DFS│  └──────────────────────────────────┘   │
│  Level Order │  ┌──────────────────────────────────┐   │
│──────────────│  │ 💻 代码编辑器                      │   │
│ 📁 预制数据   │  └──────────────────────────────────┘   │
│  导入 / 导出  └──────────────────────────────────────────┘
└──────────────┘
```

**后端**: FastAPI + WebSocket 实时步骤流传输
**前端**: 原生 JS + vis-network（图/树可视化），无需构建工具

## 🚀 快速上手

### 环境要求

- Python 3.10+

### 安装

```bash
cd visual-algorithm
python -m venv .venv
source .venv/Scripts/activate    # Windows (Git Bash)
# .venv\Scripts\activate         # Windows (CMD)
pip install -r requirements.txt
```

### 启动

```bash
python run.py
```

打开浏览器访问 **http://localhost:8000**

### 前端冒烟测试

```bash
npm install
npm run test:e2e
```

### 完整回归

```bash
npm run verify
```

### 使用步骤

1. 📁 **加载预制数据** — 点击侧边栏中的预制卡片（图或树）
2. 🎨 **或手动建图** — 点击"Node"添加节点，"Edge"连接节点
3. 🛤️ **选择算法** — 点击侧边栏中的算法卡片
4. ⚙️ **设置参数** — 填写参数（如 values、patterns、起始节点）
5. ▶️ **运行** — 点击播放，使用 ⏸ 暂停和 ⏭ 单步控制执行
6. 👀 **观察变化** — 节点和边会随算法进度变色
7. 📐 **调整日志区域** — 拖拽底部面板上方的手柄可自由调整高度

## 📁 项目结构

```
visual-algorithm/
├── run.py                           # 启动入口
├── requirements.txt                  # Python 依赖
├── backend/
│   ├── app.py                       # FastAPI 应用
│   ├── models/
│   │   └── graph.py                 # Graph, Node, Edge 数据模型
│   ├── engine/
│   │   ├── protocol.py              # 算法协议（抽象基类）
│   │   ├── registry.py             # 自动发现插件注册表
│   │   └── runner.py               # 执行生命周期管理器
│   ├── algorithms/
│   │   ├── graph/                   # 图算法
│   │   │   ├── dijkstra.py
│   │   │   ├── bfs.py
│   │   │   ├── dfs.py
│   │   │   ├── bellman_ford.py
│   │   │   ├── spfa.py
│   │   │   ├── johnson.py
│   │   │   ├── edmonds_karp.py
│   │   │   ├── dinic.py
│   │   │   ├── astar.py
│   │   │   ├── prim.py
│   │   │   ├── kruskal.py
│   │   │   ├── topological_sort.py
│   │   │   ├── cycle_detection.py
│   │   │   ├── connected_components.py
│   │   │   ├── tarjan_scc.py
│   │   │   ├── kosaraju_scc.py
│   │   │   ├── union_find.py
│   │   │   ├── bipartite.py
│   │   │   ├── floyd_warshall.py
│   │   │   └── bridges_articulation.py
│   │   ├── array/                  # 数组算法
│   │   │   ├── bubble_sort.py
│   │   │   ├── quick_sort.py
│   │   │   ├── merge_sort.py
│   │   │   ├── heap_sort.py
│   │   │   ├── binary_search.py
│   │   │   └── kadane.py
│   │   ├── dp/                     # 动态规划算法
│   │   │   ├── lcs.py
│   │   │   ├── edit_distance.py
│   │   │   ├── knapsack.py
│   │   │   ├── lis.py
│   │   │   ├── coin_change.py
│   │   │   ├── matrix_chain.py
│   │   │   ├── fibonacci_dp.py
│   │   │   ├── subset_sum.py
│   │   │   └── word_break.py
│   │   ├── string/                 # 字符串算法
│   │   │   ├── kmp.py
│   │   │   ├── rabin_karp.py
│   │   │   ├── boyer_moore.py
│   │   │   ├── z_algorithm.py
│   │   │   └── manacher.py
│   │   └── tree/                   # 树算法
│   │       ├── bst.py
│   │       ├── avl.py
│   │       ├── red_black.py
│   │       ├── btree.py
│   │       ├── bplus.py
│   │       ├── heap.py
│   │       ├── fenwick_tree.py
│   │       ├── huffman.py
│   │       ├── trie.py
│   │       ├── aho_corasick.py
│   │       ├── tree_bfs.py
│   │       ├── tree_dfs.py
│   │       └── level_order.py
│   ├── routers/                    # API 路由
│   └── presets/
│       ├── graphs/                  # 预制图 JSON 文件
│       └── trees/                  # 预制树 JSON 文件
└── frontend/
    ├── index.html                  # 单页应用
    ├── css/style.css              # 样式（暗色主题）
    └── js/
        ├── app.js                  # 主应用
        ├── graph-editor.js        # vis-network 封装
        ├── visualizer.js          # 步骤动作渲染器
        ├── algorithm-panel.js      # 算法选择器与控制
        ├── ws-client.js           # WebSocket 客户端
        ├── code-editor.js         # 自定义算法编辑器
        └── preset-manager.js      # 预制数据加载器
```

## 🔌 添加自定义算法

### 方式一：网页代码编辑器

1. 滚动到侧边栏的"自定义算法"
2. 按模板编写你的算法
3. 点击"提交算法"
4. 算法立即出现在算法列表中

### 方式二：文件方式（自动发现）

在 `backend/algorithms/<category>/` 中创建 `.py` 文件：

```python
from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry

@registry.register
class MyAlgorithm(AlgorithmProtocol):
    def get_meta(self) -> AlgorithmMeta:
        return AlgorithmMeta(
            name="my_algorithm",
            category="tree",
            description="算法描述",
            emoji="🔮",
            parameters=[
                {"name": "values", "type": "str", "required": True,
                 "description": "逗号分隔的值"}
            ],
            time_complexity="O(n log n)",
            space_complexity="O(n)",
            layout="hierarchical",
        )

    def run(self, graph, params) -> Generator[Step, None, None]:
        yield Step(
            action=StepAction.ADD_NODE,
            target_type="node",
            target_id="root",
            value={"id": "root", "label": "root"},
            message="开始",
            phase="init",
        )
```

重启服务器，新算法自动注册。

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 服务健康状态、已注册算法数量、分类统计和可视化类型统计 |
| `GET` | `/api/algorithms` | 获取所有算法及元数据 |
| `GET` | `/api/graphs` | 获取预制图列表 |
| `GET` | `/api/graphs/{id}` | 获取指定图 |
| `GET` | `/api/presets/bundle` | 获取所有预制数据 |
| `POST` | `/api/algorithms/custom` | 提交自定义算法代码 |
| `POST` | `/api/random-params` | 生成随机参数 |
| `WS` | `/ws/run` | 算法执行（实时步骤流） |

## 🛠️ 技术栈

- **后端**: Python 3.10+, FastAPI, Uvicorn, Pydantic
- **前端**: 原生 JavaScript, vis-network, CSS 自定义属性
- **通信**: WebSocket 实时算法步骤流
- **数据**: JSON 文件（无需数据库）

---

<p align="center">
  Made with ❤️ for algorithm learners
</p>
