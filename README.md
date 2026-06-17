# LLM-Code-Medic：工业级多文件智能协同修复系统

**基于 LangGraph 状态机与双大模型（Dual-LLM）驱动的自适应代码审计、契约强化、多重门禁拦截与分布式服务化自动修复系统。**

---

## 🚀 项目演进范式：从独狼脚本到工业级中枢

**LLM-Code-Medic** 历经数个版本的迭代，完成了从“被动黑盒修复”到“主动契约防御与生产级工程落地”的颠覆性跨越：

* **V2（仓库级全局感知）**：引入 AST 动态扫描，摆脱暴力文本读取，利用 **DeepSeek/Gemini** 强推理长链条进行跨文件 Bug 根因诊断。
* **V3（Shadow Workspace 沙箱化）**：破除物理覆盖文件的危险行为，首创影子隔离工作区，通过多文件 Patch 协议实现原地原子化安全验证与运行期错误自愈回灌。
* **V4（契约防御与门禁矩阵）**：解耦战略诊断与战术修复，构建四大 **AST 级语义拦截网关**，彻底封死 AI 常见的“异常静默吞噬”、“公式数值篡改”与“幻觉硬编码”等恶性行为，并加入后置插件总线与反向单测补全。
* **V5（服务化 C/S 两栖架构）**：由 FastAPI 与 VS Code 插件双向赋能。既支持全量大规模测试集跑分的硬核 CLI 管道模式，又完美融入了开发者日常右键“精准打击”的工作流。

---

## 📂 最终版全量架构与目录解析

以下为系统 V5 版本的完整全景源码树，完美整合了历代升级的核心底座：

```text
LLM-Code-Medic/
│
├── 📁 server/                                  # 🌐 V5：FastAPI 本地网络接入网关服务
│   ├── 📁 routes/                              # 标准化 HTTP 路由层
│   │   ├── 📄 health.py                        # /health  服务存活健康检查
│   │   ├── 📄 diagnose.py                      # /diagnose 纯符号诊断接口（只析不修）
│   │   └── 📄 repair.py                        # /repair   核心修复入口
│   ├── 📁 schemas/                             # Pydantic 强类型请求/响应数据契约层
│   │   ├── 📄 request.py                       # 声明 DiagnoseRequest / RepairRequest
│   │   └── 📄 response.py                      # 声明 DiagnoseResponse / RepairResponse
│   └── 📄 app.py                               # Uvicorn 调度驱动的全局异步服务主入口
│
├── 📁 extension/                               # 🔌 V5：VS Code 插件源码与构建产物
│   ├── 📁 src/                                 # TS 原始源码层
│   │   ├── 📁 commands/
│   │   │   └── 📄 fix.ts                       # UI 交互、上下文物理绝对路径捕获核心
│   │   ├── 📄 extension.ts                     # 插件激活（activate）与菜单注册
│   │   └── 📄 medicClient.ts                   # 强类型前端 HTTP 客户端（封装 fetch）
│   ├── 📁 out/                                 # TSC 编译后的生产级 JS 分发产物
│   ├── 📄 package.json                         # 插件清单（定义 explorer/editor 右键挂载菜单）
│   ├── 📄 tsconfig.json                        # TypeScript 编译器配置文件
│   └── 📄 readme.md                            # 插件市场专用用户指南
│
├── 📁 src/                                     # 🐍 系统底层智能体内核与算法底座
│   ├── 📄 main.py                              # 传统 CLI 批量跑分测试终端启动入口
│   │
│   ├── 📁 config/                              # 全局配置与安全模式解析
│   │   └── 📄 runtime_config.py                # 环境变量类型强转与运行状态校验
│   │
│   ├── 📁 service/                             # ⚙️ V5：后端业务逻辑适配与桥接层
│   │   └── 📄 medic_service.py                 # [MedicService] 解耦网络流，提炼清洗图状态总线
│   │
│   ├── 📁 engine/                              # 🚂 核心业务流控编排引擎
│   │   ├── 📄 medic_engine.py                  # 核心守护进程（初始化并冷启动系统状态）
│   │   ├── 📄 repair_pipeline.py               # 修复流水线管理器（组织拓扑扫描与后置治理）
│   │   └── 📄 runtime_session.py               # 运行时会话管理（单例维护底层 LLM 客户端）
│   │
│   ├── 📁 agent/                               # 🧠 认知智能体感知层
│   │   ├── 📄 state.py                         # 全局 TypedDict 状态总线（承载项目依赖地图与漏洞清单）
│   │   ├── 📄 graph.py                         # 基于 LangGraph 的有向循环图拓扑控制中心
│   │   └── 📄 prompts.py                       # 认知协议规约（硬核内置 5 阶段审计与自查自省问卷）
│   │
│   ├── 📁 llm/                                 # 🌐 弹性多供应商容灾适配层
│   │   ├── 📄 model_factory.py                 # 模型解耦工厂（对齐 OpenAI/Google 等规范）
│   │   ├── 📄 provider_router.py               # 双 LLM 认知角色静态路由与运行时物理降级
│   │   └── 📄 llm_invoker.py                   # 弹性调用原子（指数退避重试抵抗 RateLimit）
│   │
│   ├── 📁 quality/                             # 🛡️ AST 静态代码语义与策略防御门禁矩阵
│   │   ├── 📄 patch_quality_gate.py            # 补丁物理完备性门禁（拦截断裂块）
│   │   ├── 📄 semantic_patch_gate.py           # AST 语义红线门禁（拦截异常吞噬与算法微调）
│   │   ├── 📄 policy_gate.py                   # 安全策略常量保护网关（防越权字面量覆盖）
│   │   └── 📄 repairability_gate.py            # 可修复性收敛评估（人工 Guided 降级放权管道）
│   │
│   ├── 📁 tools/                               # 📡 静态分析工具集与虚拟运行时
│   │   ├── 📄 scanner.py                       # 项目雷达（通过 ast.parse 测绘全局依赖拓扑关系）
│   │   ├── 📄 ast_resolver.py                  # 符号依赖解析器（上下游闭包扩展）
│   │   └── 📄 executor.py                      # 影子执行器（构建虚拟扁平工作区，免疫文件锁死锁）
│   │
│   ├── 📁 plugins/                             # 🧩 后置代码治理插件总线
│   │   ├── 📄 base_plugin.py                   # 行为契约抽象基类
│   │   ├── 📄 plugin_manager.py                # 集中式链式串行分发器
│   │   ├── 📄 style_plugin.py                  # 源码文本流格式化规范对齐
│   │   ├── 📄 security_plugin.py               # 高危特征二次安全复审
│   │   └── 📄 llm_test_generator.py            # 反向单测补齐核心组件
│   │
│   └── 📁 report/                              # 📈 交付物度量与审计报告域
│       └── 📄 report_generator.py              # 汇聚漏洞治理度量指标，持久化 Markdown 报告
│
├── 🧪 output/                                  # 🧪 Shadow Workspace 影子隔离沙箱物理执行区与产物落地点
└── 🎯 tests/                                   # 🎯 历代复杂漏洞工程评估基准库 (Benchmarks)
    ├── 📁 benchmark_project_v1/                
    ├── 📁 benchmark_project_v2/                  
    ├── 📁 benchmark_project_v3/  
    ├── 📁 benchmark_project_v4/  
    └── 📁 benchmark_project_v5/                 
                                 

```

---

## 🧠 核心技术深度解析

### 1. 双 LLM 协同认知环路

放弃单模型包揽全局的做法，解耦为**战略指挥官**与**战术特种兵**的协同运作：

* **战略诊断（Diagnose Node） $\rightarrow$ `DeepSeek-R1` / `Gemini 1.5 Pro**`：拥有极长思维链（CoT），专注于吞噬 `ProjectScanner` 测绘出的全局 AST 地图、堆栈崩溃日志，进行链条追溯推理。输出深度根因分析报告，并把发现的所有衍生漏洞汇总归入 `BUG_INVENTORY`，防止顾此失彼。
* **战术修复（Repair Node） $\rightarrow$ `DeepSeek-V4**`：具备高遵从度与生成速度，严格消费诊断结论，按照标准**多文件 Patch 协议**（格式见下文）执行差异化补丁并行组装。

### 2. prompts.py 严苛的契约控制流

系统强制要求 AI 必须挺过五大阶段检查，不允许任何跨越或模糊妥协：

* **PHASE 0：静态符号校验**（逐项执行模块存在性、顶层符号导出、形参实参签名对齐以及常量溯源审计）。
* **PHASE 1：追溯链推理**（严厉判定为 `[CONTRACT_UNDEFINED]` 或 `[CALLER_VIOLATED]`，无偏袒承诺）。
* **PHASE 2：验证死循环阻断**：当重试次数 $\ge 1$ 且报错未发生任何转移，若 Callee 侧已写防御性断言，系统将强行在有向图中把根因修正为 Caller 侧违规，扩大修复域，阻断大模型在被调用方盲目堆砌面条式垫片的死循环。
* **修复自查**：修复工程师在吐出代码前，必须在内心闭环解答完 Q1 至 Q10 的硬性自省问卷（如：是否隐藏了魔术返回值？是否静默吞噬了 Catch 块的 Exception？）。

### 3. 多重防御门禁矩阵（Multi-Gate Matrix）

补丁在落地前，必须通过 `src/quality/` 目录下由 AST（抽象语法树）驱动的无情审判：

| 门禁网关组件 | 核心拦截机制 | 红灯触发惩罚行为 |
| --- | --- | --- |
| **PatchQualityGate** | 静态物理块破损校验 | 检查 `<<<FILE_PATH>>>` 与 `<<<FILE_END>>>` 标签是否断裂。直接丢弃并回灌惩罚日志。 |
| **SemanticPatchGate** | 前后 AST 节点变动深度对比 | 拦截 `try-except` 中无 `raise` 的异常吞噬行为；监控核心业务算法公式的恶性变动（例如严禁将 $x - 10$ 微调篡改为 $x - 9$）。 |
| **PolicyGate** | 静态赋值语句追踪监控 | 严格保护全局配置文件中的常资产（如安全授权地址或核心阈值），拒绝未授权的本地字面量字面覆盖。 |
| **RepairabilityGate** | 收敛性动态评测检测 | 遭遇深层软件架构死锁导致修复不收敛时，立刻熔断退出，向终端发起 `prompt_user_authorization` 降级放权，请求人类专家提供引导性修正或完全覆写。 |

### 4. 影子隔离沙箱（Shadow Workspace）

为了实现无污染的原子化验证，`CodeExecutor` 会在程序运行时自动在 `output/` 建立与原测试仓库完全平行的镜像工作区：

* **绝对安全**：所有的多文件补丁写入、隔离测试运行全部在沙箱中平摊扁平化执行，不污染开发者的原始物理源码。
* **环境净化**：自动切分运行时工作目录（CWD），强力执行 `pycache` 污染拦截清理，强制进行 `UTF-8 Runtime` 注入，彻底免疫 Windows 物理系统环境下的文件锁 PermissionError 锁死以及中文字符集 GBK 编码黑洞。

### 5. 后置治理总线与反向单测补全

当沙箱验证吐出 0-Error（完全通关）后，触发后置流水线。系统会调度 `LLMTestGenerator` 智能提取受损文件的最新符号变动域，反向编写物理 `test_*.py` 单元测试脚本并灌入沙箱二次跑通，实现全自动的保障交付。

---

## ⚡ 工业级部署与运行指南

### 1. 物理环境准备

克隆项目后，部署所需的底层核心依赖包：

```bash
pip install -r requirements.txt

```

### 2. 配置硬核安全策略环境（`.env`）

在项目根目录下，将 `.env.example` 物理重命名为 `.env`，或直接新建并配置多模型路由和测试根路径：

```env
# 🌐 弹性 API 凭证密钥
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_API_BASE=
GEMINI_API_KEY=your_google_ai_studio_key

# ⚙️ 核心架构双大模型（Dual-LLM）解耦路由
# [战略诊断中枢角色] 推荐长链条高推理模型，如deepseek-R1
DIAGNOSE_PROVIDER=
DIAGNOSE_MODEL=

# [战术并行修复角色] 推荐高遵从度、极速模型,如deepseek-v4-flash
REPAIR_PROVIDER=
REPAIR_MODEL=

# [仅在模式 B：CLI 管道模式下生效] 自动化大规模跑分的目标仓库根目录
TEST_REPO_ROOT=./tests/v3

# 🧪 调试与安全网关模式
DEBUG=True

```

### 3. 选择自适应双模运行

V5 系统支持以下**双轨分流运行模式**，无缝对齐不同工程场景：

#### 💡 模式 A：VS Code 插件联动模式（IDE 生产开发推荐）

如果你希望直接在编辑器中享受“指哪打哪”的一键外科手术级修复，请在项目根目录启动常驻本地分布式后端：

```bash
uvicorn server.app:app --host 127.0.0.1 --port 8000 

```

**IDE 唤醒流程**：

1. 后端成功挂载运行（默认监听 `http://127.0.0.1:8000`）。
2. 打开宿主 VS Code 载入 `extension` 插件。
3. 在左侧资源管理器（Explorer）或代码任意编辑区中，**右键**点击受损的多文件目录或单个文件。
4. 唤醒右键上下文菜单中的 `LLM Code Medic: One Click Fix` 项。
5. 插件将自动捕获当点绝对物理路径（`fsPath`），通过网关投递给后端的 `MedicService` 进行靶向收敛。修复完成后将弹出通知提示，并允许你一键跳转并打开物理 `output/` 导出目录。

#### 🛠️ 模式 B：独立 CLI 管道模式（大规模跑分/跑 Benchmark 专用）

如果你处于实验室打分、离线大批量漏洞重现或集成在 CI/CD 自动化检测流中，直接切入黑盒跑分管道：

```bash
python -m src.main

```

系统将全自动提取 `.env` 中声明的 `TEST_REPO_ROOT` 路径，绘制项目雷达，调度状态机有向图进行最大次数为 3 次的循环闭环试炼，并将修复产物与反向生成的单元测试全量 атом 级沉淀到 `output/` 影子隔离区中。

---

## 🛡️ 修复资产安全承诺

无论通过右键插件触发，还是 CLI 脚本批量跑分，**LLM-Code-Medic 始终严格恪守沙箱底层底线：决不在未经确认的情况下覆盖或修改您的线上原生产代码**。所有经由多重门禁矩阵层层严审通过的代码以及配套生成的单测文件，均安全、透明地暂存在本地的 `output/` 影子空间内，静待人类专家最后的终审一键合并（Merge）。