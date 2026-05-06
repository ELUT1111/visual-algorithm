<p align="center">
  <h1 align="center">🧪 Visual Algorithm Lab</h1>
  <p align="center">
    <strong>Interactive Algorithm Visualization Platform</strong>
  </p>
  <p align="center">
    <a href="#-english">English</a> | <a href="#-中文">中文</a>
  </p>
</p>

---

# 🇬🇧 English

## 📖 Introduction

Visual Algorithm Lab is a **highly interactive, visual algorithm learning platform** built with Python (FastAPI) and modern web technologies. It focuses on **graph algorithms** with a highly extensible architecture for adding new algorithm categories.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎨 **Interactive Graph Editor** | Create nodes and edges by clicking and dragging. Double-click to add nodes, drag between nodes to create edges. |
| 🛤️ **6 Built-in Algorithms** | Dijkstra, BFS, Bellman-Ford, A*, Prim, Kruskal — all with step-by-step visualization. |
| ⏯️ **Real-time Controls** | Play, Pause, Step-forward, Reset with adjustable speed slider. |
| 💻 **Custom Algorithms** | Write your own Python algorithm in the built-in editor and run it instantly. |
| 📁 **JSON Import/Export** | Save and load graphs as JSON files. 3 preset graphs included. |
| 🔌 **Plugin Architecture** | Drop a `.py` file into `backend/algorithms/graph/` to add a new algorithm — auto-discovered on startup. |
| 🌙 **Dark Theme** | Eye-friendly dark UI designed for algorithm visualization. |
| ⌨️ **Keyboard Shortcuts** | `Space` = play/pause, `→` = step, `R` = reset. |

### 🖼️ Architecture

```
┌──────────────┬──────────────────────────────────────────┐
│ 📋 Algorithms│  ┌──────────────────────────────────┐    │
│  🛤️ Dijkstra │  │                                  │    │
│  🔍 BFS      │  │    Graph Visualization            │    │
│  ⭐ A*       │  │    (vis-network canvas)           │    │
│  🌳 Prim     │  │                                  │    │
│  🔗 Kruskal  │  └──────────────────────────────────┘    │
│              │  ▶️ ⏸️ ⏭️ 🔄  Speed: ────●────            │
│ 📁 Presets   │  ┌──────────────────────────────────┐    │
│  + Import    │  │ Step Log                          │    │
│  + Export    │  └──────────────────────────────────┘    │
│              │  ┌──────────────────────────────────┐    │
│ 💻 Custom    │  │ Code Editor                       │    │
│              │  └──────────────────────────────────┘    │
└──────────────┴──────────────────────────────────────────┘
```

**Backend**: FastAPI + WebSocket for real-time step streaming
**Frontend**: Vanilla JS + vis-network (graph visualization) + no build step

## 🚀 Quick Start

### Prerequisites

- Python 3.10+

### Installation

```bash
# Clone or download the project
cd visual-algorithm

# Create virtual environment (recommended)
python -m venv .venv
source .venv/Scripts/activate    # Windows (Git Bash)
# .venv\Scripts\activate         # Windows (CMD)

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python run.py
```

Open your browser and navigate to **http://localhost:8000**

### Usage

1. **Load a preset graph** — click a preset card in the sidebar (e.g., "City Road Network")
2. **Or build your own** — click "➕ Node" to add nodes, "🔗 Edge" to connect them
3. **Select an algorithm** — click an algorithm card (e.g., "🛤️ dijkstra")
4. **Set parameters** — choose source/target nodes from the dropdown
5. **Run!** — click ▶️ Play, use ⏸️ Pause and ⏭️ Step to control execution
6. **Watch** — nodes and edges change color as the algorithm progresses
7. **Check the log** — step-by-step messages appear in the bottom panel

## 📁 Project Structure

```
visual-algorithm/
├── run.py                          # Entry point
├── requirements.txt                # Python dependencies
├── backend/
│   ├── app.py                      # FastAPI application
│   ├── models/
│   │   └── graph.py                # Graph, Node, Edge models
│   ├── engine/
│   │   ├── protocol.py             # Algorithm protocol (ABC)
│   │   ├── registry.py             # Auto-discovery plugin registry
│   │   └── runner.py               # Execution lifecycle manager
│   ├── algorithms/graph/           # Built-in algorithms
│   │   ├── dijkstra.py
│   │   ├── bfs.py
│   │   ├── bellman_ford.py
│   │   ├── astar.py
│   │   ├── prim.py
│   │   └── kruskal.py
│   ├── routers/                    # API endpoints
│   └── presets/graphs/             # Preset graph JSON files
└── frontend/
    ├── index.html                  # Single-page app
    ├── css/style.css               # Styles (dark theme)
    └── js/                         # Modular JavaScript
```

## 🔌 Adding Custom Algorithms

### Method 1: Code Editor (in-browser)

1. Scroll to "💻 Custom Algorithm" in the sidebar
2. Write your algorithm following the template
3. Click "🚀 Submit Algorithm"
4. It appears in the algorithm list immediately

### Method 2: File (auto-discovered)

Create a `.py` file in `backend/algorithms/graph/`:

```python
from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry

@registry.register
class MyAlgorithm(AlgorithmProtocol):
    def get_meta(self):
        return AlgorithmMeta(
            name="my_algorithm",
            category="graph",
            description="What it does",
            emoji="🔮",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Start node"}
            ]
        )

    def run(self, graph, params):
        source = params["source"]
        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Processing {source}",
            phase="explore"
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
| `WS`  | `/ws/run` | Algorithm execution (real-time) |

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic
- **Frontend**: Vanilla JavaScript, vis-network, CSS Custom Properties
- **Communication**: WebSocket for real-time algorithm streaming
- **Data**: JSON files (no database required)

---

# 🇨🇳 中文

## 📖 项目介绍

Visual Algorithm Lab 是一个**高度交互式、可视化的算法学习平台**，使用 Python (FastAPI) 和现代 Web 技术构建。当前专注于**图算法**，并提供高度可扩展的架构，方便后续添加新的算法类别（如排序、树等）。

### ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🎨 **交互式图编辑器** | 点击画布添加节点，拖拽连线创建边，双击快速添加节点。 |
| 🛤️ **6 个内置算法** | Dijkstra、BFS、Bellman-Ford、A*、Prim、Kruskal，全部支持逐步可视化。 |
| ⏯️ **实时控制** | 播放、暂停、单步、重置，配合速度滑块自由调节。 |
| 💻 **自定义算法** | 在内置代码编辑器中编写 Python 算法，提交后即可运行。 |
| 📁 **JSON 导入/导出** | 一键保存和加载图数据，内置 3 个预制图。 |
| 🔌 **插件化架构** | 在 `backend/algorithms/graph/` 中放入 `.py` 文件即可自动注册新算法。 |
| 🌙 **暗色主题** | 专为算法可视化设计的护眼深色界面。 |
| ⌨️ **键盘快捷键** | `空格` = 播放/暂停，`→` = 单步，`R` = 重置。 |

### 🖼️ 系统架构

```
┌──────────────┬──────────────────────────────────────────┐
│ 📋 算法列表   │  ┌──────────────────────────────────┐    │
│  🛤️ Dijkstra │  │                                  │    │
│  🔍 BFS      │  │    图可视化区域                    │    │
│  ⭐ A*       │  │    (vis-network 画布)             │    │
│  🌳 Prim     │  │                                  │    │
│  🔗 Kruskal  │  └──────────────────────────────────┘    │
│              │  ▶️ ⏸️ ⏭️ 🔄  速度: ────●────             │
│ 📁 预制图     │  ┌──────────────────────────────────┐    │
│  + 导入       │  │ 步骤日志                           │    │
│  + 导出       │  └──────────────────────────────────┘    │
│              │  ┌──────────────────────────────────┐    │
│ 💻 自定义算法  │  │ 代码编辑器                         │    │
│              │  └──────────────────────────────────┘    │
└──────────────┴──────────────────────────────────────────┘
```

**后端**: FastAPI + WebSocket 实时步骤流传输
**前端**: 原生 JS + vis-network（图可视化），无需构建工具

## 🚀 快速上手

### 环境要求

- Python 3.10+

### 安装

```bash
# 克隆或下载项目
cd visual-algorithm

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/Scripts/activate    # Windows (Git Bash)
# .venv\Scripts\activate         # Windows (CMD)

# 安装依赖
pip install -r requirements.txt
```

### 启动

```bash
python run.py
```

打开浏览器访问 **http://localhost:8000**

### 使用步骤

1. **加载预制图** — 点击侧边栏中的预制图卡片（如"城市道路网络"）
2. **或手动建图** — 点击"➕ Node"添加节点，"🔗 Edge"连接节点
3. **选择算法** — 点击算法卡片（如"🛤️ dijkstra"）
4. **设置参数** — 从下拉框选择起始/目标节点
5. **运行！** — 点击 ▶️ 播放，使用 ⏸️ 暂停和 ⏭️ 单步控制执行
6. **观察变化** — 节点和边会随算法进度变色
7. **查看日志** — 底部面板显示每一步的详细说明

## 📁 项目结构

```
visual-algorithm/
├── run.py                          # 启动入口
├── requirements.txt                # Python 依赖
├── backend/
│   ├── app.py                      # FastAPI 应用
│   ├── models/
│   │   └── graph.py                # Graph, Node, Edge 数据模型
│   ├── engine/
│   │   ├── protocol.py             # 算法协议（抽象基类）
│   │   ├── registry.py             # 自动发现插件注册表
│   │   └── runner.py               # 执行生命周期管理器
│   ├── algorithms/graph/           # 内置算法
│   │   ├── dijkstra.py
│   │   ├── bfs.py
│   │   ├── bellman_ford.py
│   │   ├── astar.py
│   │   ├── prim.py
│   │   └── kruskal.py
│   ├── routers/                    # API 路由
│   └── presets/graphs/             # 预制图 JSON 文件
└── frontend/
    ├── index.html                  # 单页应用
    ├── css/style.css               # 样式（暗色主题）
    └── js/                         # 模块化 JavaScript
```

## 🔌 添加自定义算法

### 方式一：网页代码编辑器

1. 滚动到侧边栏的"💻 自定义算法"
2. 按模板编写你的算法
3. 点击"🚀 提交算法"
4. 算法立即出现在算法列表中

### 方式二：文件方式（自动发现）

在 `backend/algorithms/graph/` 中创建 `.py` 文件：

```python
from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry

@registry.register
class MyAlgorithm(AlgorithmProtocol):
    def get_meta(self):
        return AlgorithmMeta(
            name="my_algorithm",
            category="graph",
            description="算法描述",
            emoji="🔮",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "起始节点"}
            ]
        )

    def run(self, graph, params):
        source = params["source"]
        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"正在处理节点 {source}",
            phase="explore"
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
| `WS`  | `/ws/run` | 算法执行（实时通信） |

## 🛠️ 技术栈

- **后端**: Python 3.10+, FastAPI, Uvicorn, Pydantic
- **前端**: 原生 JavaScript, vis-network, CSS 自定义属性
- **通信**: WebSocket 实时算法步骤流
- **数据**: JSON 文件（无需数据库）

---

<p align="center">
  Made with ❤️ for algorithm learners
</p>
