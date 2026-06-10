
---

# LLM-Code-Medic V5：工业级多文件智能协同修复系统

**基于 LangGraph 状态机与双大模型（Dual-LLM）驱动的自适应代码审计、契约强化与分布式服务化自动修复系统。**

---

## 🚀 V5 版本核心进化范式

**LLM-Code-Medic V5** 实现了从“本地独立脚本（CLI）”向“服务化（Service-Oriented）两栖架构”的重大技术飞跃。通过重构底层逻辑，V5 既保留了全量 Benchmark 跑分的硬核终端模式，又完美融入了全生态的开发者日常工作流。

### V5 核心升级特性

* **全栈 C/S 服务化重构**：全面转为由 FastAPI/Uvicorn 驱动的现代化后端服务，将智能体修复内核封装为标准 Web 接口，为多端联动（VS Code 插件/Web 端）提供坚座。
* **VS Code 插件无缝嵌入**：告别繁琐的终端命令，直接在 IDE 中通过右键菜单、编辑器图标一键唤醒修复。
* **物理绝对路径“精准打击”**：彻底重构路径解析流，直接解耦父文件夹追溯。点选单文件即刻切入“靶向外科手术”模式，点选目录则自动触发全项目拓扑审计。

---

## 📂 架构全景与目录解析（精简版）

```text
LLM-Code-Medic/
│
├── 📁 server/                         # 🌐 V5 新增：FastAPI 本地后端网关服务
│   ├── 📁 routes/                     # 接口路由层（包含 /repair, /diagnose, /health）
│   ├── 📁 schemas/                    # Pydantic 强类型请求/响应数据契约
│   └── 📄 app.py                      # Uvicorn 调度驱动的后端服务主入口
│
├── 📁 extension/                      # 🔌 V5 新增：VS Code 插件源码与发布包
│   ├── 📁 src/                        # 插件 TypeScript 原始源码（含 UI 交互与 HTTP 客户端）
│   ├── 📄 package.json                # 插件清单（定义右键菜单、快捷键等激活事件）
│   └── 📄 readme.md                   # 插件市场专用的用户安装配置指南
│
├── 📁 src/                            # 🐍 系统底层核心算法与智能体引擎
│   ├── 📁 service/                    # ⚙️ V5 新增：业务逻辑适配层
│   │   └── 📄 medic_service.py        # [MedicService] 核心桥梁，调度引擎并清洗提炼状态
│   ├── 📁 engine/                     # 🚂 LangGraph 有向图状态机流控内核
│   └── 📁 agent/, quality/, tools/... # [内核略] 涵盖双 LLM 提示词、AST 四重门禁网关与隔离沙箱
│
├── 🧪 output/                         # 🧪 Shadow Workspace 影子隔离沙箱物理执行区（修复产物输出点）
└── 🎯 tests/                          # 🎯 多文件复杂漏洞工程评估基准库 (Benchmarks)

```

---

## 🧠 服务化核心流控中枢

V5 引入了专门的 **`src/service/medic_service.py`** 作为业务适配层。它完美解耦了“外部网络请求”与“内部图状态机”，扮演了整个后端的大堂经理：

1. **接口原子化**：将复杂的智能体演进拆分为 `.diagnose()`（纯静态符号审计与根因分析）与 `.repair()`（执行自愈闭环、沙箱跑通并生成补丁）两大标准服务。
2. **数据清洗与标准交付**：自动从 LangGraph 错综复杂的全局内存字典（`final_state`）中精准剥离出 `is_fixed`、`modified_files`、`final_patch` 等关键物理指标，并将其翻译成前端高可读的 JSON 结构体进行交付。

---

## ⚡ 工业级部署与运行指南

### 1. 部署项目环境

```bash
pip install -r requirements.txt

```

### 2. 配置硬核安全策略环境 (`.env`)

在项目根目录下创建 `.env` 文件，配置你的大模型凭证：

```env
# 🌐 API 凭证
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=
GEMINI_API_KEY=

# ⚙️ 双 LLM 路由配置
DIAGNOSE_PROVIDER=
DIAGNOSE_MODEL=
REPAIR_PROVIDER=
REPAIR_MODEL=

# [仅CLI模式需要] 目标测试仓库根目录路径
TEST_REPO_ROOT=./tests/v3

```

---

### 3. 选择你的运行模式

V5 支持以下**双模自适应分流**运行：

#### 🔥 模式 A：VS Code 插件联动模式（推荐）

如果你想在 VS Code 享受指哪打哪的一键修复，请保持本后端服务在后台常驻：

```bash
uvicorn server.app:app --reload

```

> 💡 后端服务启动后，在 VS Code 资源管理器或代码编辑区**右键**点击目标文件/目录，选择 `LLM Code Medic: One Click Fix` 即可完美唤醒。

#### 🛠️ 模式 B：独立 CLI 管道模式

如果你需要大批量跑测试集进行算法跑分或漏洞重现：

```bash
python -m src.main

```

---

## 🛡️ 修复安全边界（保持）

为了绝对保障源码资产安全，不论通过何种模式触发，V5 依然遵循“影子隔离沙箱”**机制：系统**绝不会直接修改你的原文件。所有的原子级修复、后置风格对齐以及自动反向生成的单元测试（`test_*.py`），均会安全地沉淀在本地的 `output/` 目录中，供你人工审核后一键合并。