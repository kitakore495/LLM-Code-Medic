# LLM-Code-Medic



基于 **LangGraph** 状态机构建的自动化代码审计与修复系统。本项目已从 V1（单文件盲区版）正式升级至 **V2（仓库级全局感知版）**，支持通过 AST 抽象语法树动态扫描复杂项目目录，利用 **DeepSeek-R1** 的强推理能力进行跨文件 Bug 诊断，并配合 **DeepSeek-V4-Flash** 快速生成并验证代码补丁。

---

## 📂 核心文件结构与组件解析

项目的核心架构遵循模块化设计，各组件职责分明：

```text
LLM-Code-Medic/
├── src/
│   ├── main.py            # 🚀 智能体主入口，支持配置单文件/多文件仓库级灰度测试
│   ├── agent/
│   │   ├── graph.py       # 🧠 LangGraph 核心工作流，控制「诊断->修复->验证->控制流转」状态机
│   │   └── prompts.py     # 📝 提示词底座，包含 R1 跨文件诊断逻辑及 Flash 模型的绝对防御约束
│   └── tools/
│       ├── scanner.py     # 📂 项目全景扫描器，基于 AST 提取项目内各 Python 文件的类与函数元数据
│       └── executor.py    # 🧪 高级沙箱执行器，支持 CWD 动态切分运行与 Windows 文件锁物理免疫
├── tests/
│   ├── v1_single_file/    # 📄 V1 单文件算法/逻辑 Bug 测试集
│   └── v2_repo_case/      # 📦 V2 跨文件模块调用/接口不一致测试仓库（含 main.py 和 utils.py）
├── .env.example           # ⚙️ 环境变量配置模板
└── requirements.txt       # 📌 项目依赖声明
```

### 🧱 核心组件深入探讨：

- **`src/tools/scanner.py` (项目扫描器)**：系统的“工程雷达”。它不依赖暴力文本读取，而是通过 `ast.parse` 动态抓取 Python 文件的骨架，自动在程序启动时画出一张包含 `(defs: ...)` 和 `(classes: ...)` 的全景地图，作为全局上下文喂给大模型。
- **`src/tools/executor.py` (沙箱执行器)**：系统的“实验沙箱”。升级后的执行器支持将当前工作目录 (`cwd`) 切换到测试仓库的物理路径下，完美解决同级模块 `ModuleNotFoundError` 迷路问题；同时优化了 `tempfile` 的读写生命周期，彻底攻克了 Windows 系统下偶发触发的 `PermissionError` 文件锁死锁。
- **`src/agent/graph.py` (智能体状态机)**：通过 `TypedDict` 扩展了包含 `project_map` 和 `repo_root` 的 V2 增强版状态。通过有向图严格控制 `diagnose -> repair -> verify` 的流水线重试，最大重试次数上限为 3 次。

------

## 🌐 推荐大模型 API 签发渠道

本项目推荐使用**双模型协同双星阵列**：用高推理模型（如 R1）做诊断，用快稳模型（如 Flash/V3）做代码生成。

| **模型角色**     | **推荐使用模型**                                            | **推荐 API 签发渠道 **                                       |
| ---------------- | ----------------------------------------------------------- | ------------------------------------------------------------ |
| **错误诊断节点** | `Pro/deepseek-ai/DeepSeek-R1`                               | 🚀 **硅基流动 (SiliconFlow)** 🔗 https://cloud.siliconflow.cn/ |
| **代码修复节点** | `deepseek-ai/DeepSeek-V4-Flash` 或 `Gemini 1.5 Pro / Flash` | 🌐 **Google AI Studio** 🔗 https://aistudio.google.com/        |

------

## ⚡ 快速开始与部署指引

### 1. 克隆与环境配置

首先安装项目所需的底层物理依赖：

```
pip install -r requirements.txt
```

### 2. 签署密钥凭证

将项目根目录下的 `.env.example` 物理重命名为 `.env`，并填入API 密钥：

```
DEEPSEEK_API_KEY=换成你申请的SiliconFlow或AI_Studio密钥
DEEPSEEK_API_BASE=[https://api.siliconflow.cn/v1](https://api.siliconflow.cn/v1)
```

### 3. 一键启动审计

在项目根目录下，敲下以下命令启动：

```
python -m src.main
```

系统将会自动扫描 `tests/v2_repo_case`、绘制项目地图、捕获初始报错、调度 DeepSeek-R1 并在沙箱中完成自动物理闭环，修复后的代码将自动导出至 `output/` 目录下。
