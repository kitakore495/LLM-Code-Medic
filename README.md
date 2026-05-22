LLM-Code-Medic V3

基于 LangGraph 状态机构建的自动化多文件代码审计与协同修复系统。本项目已从 V2（仓库级全局感知版）正式升级至 V3（Shadow Workspace 沙箱版），支持通过 AST 抽象语法树动态扫描复杂项目目录，利用 DeepSeek-R1 的强推理能力进行跨文件 Bug 诊断，并配合 DeepSeek-V3 自动生成多文件补丁，在独立 output/ 影子工作区中完成原子验证与闭环修复。

📂 核心文件结构与组件解析

项目整体架构继续遵循模块化设计，并在 V3 中引入了 Shadow Workspace 验证机制：

LLM-Code-Medic/
├── .env                              # 🔐 API 密钥配置
├── .env.example                      # ⚙️ 环境变量模板
│
├── output/
│   └── __init__.py                   # 🧪 Shadow Workspace 沙箱输出目录
│
├── src/
│   ├── main.py                       # 🚀 智能体主入口
│   │
│   ├── agent/
│   │   ├── graph.py                  # 🧠 LangGraph 核心状态机
│   │   └── prompts.py                # 📝 Diagnose / Repair 提示词协议
│   │
│   └── tools/
│       ├── scanner.py                # 📡 AST 工程全景扫描器
│       └── executor.py               # 🧪 Shadow Workspace 沙箱执行器
│
├── tests/
│   └── v3/
│       ├── main.py                   # 🎯 测试主文件
│       └── utils.py                  # 🎯 测试依赖模块
│
├── requirements.txt
└── README.md
🧱 核心组件深入探讨
src/tools/scanner.py（AST 工程扫描器）：系统的“工程雷达”。通过 ast.parse() 动态扫描 Python 仓库结构，自动提取函数、类、导入关系与模块元数据，并在程序启动时构建完整工程地图作为全局上下文输入给大模型。
src/tools/executor.py（Shadow Workspace 执行器）：V3 最核心升级组件。系统不会再直接覆盖原始测试文件，而是自动创建 output/ 影子工作区，将修复后的文件写入隔离沙箱后独立运行，实现真正意义上的原子级验证。同时加入 pycache 清理、UTF-8 Runtime 注入、PYTHONPATH 隔离等机制，彻底解决 Windows 下的模块污染与 GBK 编码问题。
src/agent/graph.py（LangGraph 状态机）：系统的数据总线与控制中心。通过 TypedDict 管理 project_map、repo_files、target_files、error_message 等状态数据，并严格控制 Diagnose -> Repair -> Verify -> Router 的多轮自动修复流程，默认最大重试次数为 3 次。
🔄 V3 状态机工作流

V3 当前采用标准 LangGraph 有向图工作流：

Diagnose
   ↓
Repair
   ↓
Verify
   ↓
Router
Diagnose（诊断阶段）：由 DeepSeek-R1 负责。系统会自动扫描整个测试仓库、读取 Runtime Error、分析跨文件调用关系，并自动提取 TARGET_FILES 作为修复目标。
Repair（修复阶段）：由 DeepSeek-V3 负责。系统会基于 Diagnose 的分析结果生成符合协议的多文件 Patch：
<<<FILE_PATH: xxx.py>>>
...
<<<FILE_END>>>

随后自动解析补丁并更新仓库快照。

Verify（验证阶段）：系统自动创建 output/ Shadow Workspace，将修复后的文件写入隔离沙箱中运行，并捕获 stdout、stderr、Runtime Error 与 returncode，实现真正的原子级验证。
Router（状态流转阶段）：Verify 成功则进入 END，失败则重新回到 Diagnose 节点继续修复，形成完整闭环。
🌐 推荐大模型 API 签发渠道

V3 当前默认采用 DeepSeek 双模型协同架构：

模型角色	推荐模型	推荐 API 签发渠道
错误诊断节点	deepseek-ai/DeepSeek-R1	🚀 硅基流动（SiliconFlow）
代码修复节点	deepseek-ai/DeepSeek-V3	🚀 硅基流动（SiliconFlow）

推荐平台：

SiliconFlow 官方网站

V3 当前默认适配 SiliconFlow 的 OpenAI-Compatible API，无需代理即可运行。

⚡ 快速开始与部署指引
1. 安装项目依赖

首先安装项目所需的基础依赖：

pip install -r requirements.txt
2. 配置环境变量

将项目根目录下的：

.env.example

去掉后缀并重命名为：

.env

随后填入你的 API 密钥：

# DeepSeek API
DEEPSEEK_API_KEY=你的SiliconFlow密钥
DEEPSEEK_API_BASE=https://api.siliconflow.cn/v1

# 当前启用模型
ACTIVE_MODEL=deepseek

# Debug模式
DEBUG=True
3. 一键启动系统

在项目根目录执行：

python -m src.main

系统将自动：

扫描 tests/v3
构建 AST 工程地图
捕获 Runtime Error
调度 DeepSeek-R1 进行跨文件诊断
调度 DeepSeek-V3 生成多文件补丁
创建 output/ Shadow Workspace
在隔离沙箱中完成自动验证
自动回灌错误并进入下一轮修复

最终修复后的代码将自动输出至：

output/

目录下。

🆕 V3 更新内容简析

相比 V2，V3 完成了多个关键升级：

V2	V3
物理覆盖测试	Shadow Workspace 沙箱
单轮仓库修复	多轮 Autonomous Retry
普通路径处理	路径归一化系统
临时运行验证	原子级沙箱验证
普通 Runtime	UTF-8 Runtime 强制注入
基础文件覆盖	多文件 Patch 协议
基础执行器	pycache 污染隔离机制

V3 当前已经具备：

多文件联动修复
Runtime Error 自动回灌
Shadow Workspace 隔离验证
DeepSeek 双模型协同
LangGraph 多轮状态流转

等核心能力。