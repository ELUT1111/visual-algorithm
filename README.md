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

Visual Algorithm Lab is a **highly interactive, visual algorithm learning platform** built with Python (FastAPI) and modern web technologies. It covers **graph algorithms** and **tree algorithms** with a highly extensible plugin architecture.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎨 **Interactive Graph Editor** | Create nodes and edges by clicking and dragging. Double-click to add nodes, drag between nodes to create edges. |
| 🛤️ **23 Built-in Algorithms** | 11 graph algorithms + 12 tree algorithms, all with step-by-step visualization. |
| ⏯️ **Real-time Controls** | Play, Pause, Step-forward, Reset with adjustable speed slider. |
| 💻 **Custom Algorithms** | Write your own Python algorithm in the built-in editor and run it instantly. |
| 📁 **JSON Import/Export** | Save and load graphs as JSON files. Preset graphs and trees included. |
| 🔌 **Plugin Architecture** | Drop a `.py` file into `backend/algorithms/graph/` or `backend/algorithms/tree/` to add a new algorithm — auto-discovered on startup. |
| 🌙 **Dark Theme** | Eye-friendly dark UI designed for algorithm visualization. |
| ⌨️ **Keyboard Shortcuts** | `Space` = play/pause, `→` = step, `R` = reset. |
| 📐 **Resizable Panel** | Drag the handle between the graph area and the bottom panel to resize the step log.

### 🗂️ Built-in Algorithms

**Graph Algorithms (11)**
- BFS, DFS, Dijkstra, Bellman-Ford, A\*, Prim, Kruskal, Topological Sort, Cycle Detection, Connected Components, Tarjan SCC

**Tree Algorithms (12)**
- BST, AVL, Red-Black Tree, B-Tree, B+ Tree, Heap, Huffman, Trie, Aho-Corasick, Tree BFS, Tree DFS, Level Order

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
│   │   │   ├── astar.py
│   │   │   ├── prim.py
│   │   │   ├── kruskal.py
│   │   │   ├── topological_sort.py
│   │   │   ├── cycle_detection.py
│   │   │   ├── connected_components.py
│   │   │   └── tarjan_scc.py
│   │   └── tree/                    # Tree algorithms
│   │       ├── bst.py
│   │       ├── avl.py
│   │       ├── red_black.py
│   │       ├── btree.py
│   │       ├── bplus.py
│   │       ├── heap.py
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

Create a `.py` file in `backend/algorithms/graph/` or `backend/algorithms/tree/`:

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

Visual Algorithm Lab 是一个**高度交互式、可视化的算法学习平台**，使用 Python (FastAPI) 和现代 Web 技术构建。覆盖**图算法**和**树算法**，提供高度可扩展的插件化架构。

### ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🎨 **交互式图编辑器** | 点击画布添加节点，拖拽连线创建边，双击快速添加节点。 |
| 🛤️ **23 个内置算法** | 11 个图算法 + 12 个树算法，全部支持逐步可视化。 |
| ⏯️ **实时控制** | 播放、暂停、单步、重置，配合速度滑块自由调节。 |
| 💻 **自定义算法** | 在内置代码编辑器中编写 Python 算法，提交后即可运行。 |
| 📁 **JSON 导入/导出** | 一键保存和加载图数据，预制图和预制树内置。 |
| 🔌 **插件化架构** | 在 `backend/algorithms/graph/` 或 `backend/algorithms/tree/` 中放入 `.py` 文件即可自动注册新算法。 |
| 🌙 **暗色主题** | 专为算法可视化设计的护眼深色界面。 |
| ⌨️ **键盘快捷键** | `空格` = 播放/暂停，`→` = 单步，`R` = 重置。 |
| 📐 **可拉伸面板** | 拖拽图形区域与底部面板之间的手柄，可自由调整日志区域高度。 |

### 🗂️ 内置算法

**图算法 (11)**
- BFS, DFS, Dijkstra, Bellman-Ford, A\*, Prim, Kruskal, Topological Sort, Cycle Detection, Connected Components, Tarjan SCC

**树算法 (12)**
- BST, AVL, 红黑树, B-Tree, B+ Tree, Heap, Huffman, Trie, Aho-Corasick, Tree BFS, Tree DFS, Level Order

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
│   │   │   ├── astar.py
│   │   │   ├── prim.py
│   │   │   ├── kruskal.py
│   │   │   ├── topological_sort.py
│   │   │   ├── cycle_detection.py
│   │   │   ├── connected_components.py
│   │   │   └── tarjan_scc.py
│   │   └── tree/                   # 树算法
│   │       ├── bst.py
│   │       ├── avl.py
│   │       ├── red_black.py
│   │       ├── btree.py
│   │       ├── bplus.py
│   │       ├── heap.py
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

在 `backend/algorithms/graph/` 或 `backend/algorithms/tree/` 中创建 `.py` 文件：

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
