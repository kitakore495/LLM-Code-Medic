# LLM-Code-Medic V4：工业级多文件智能协同修复系统

**基于 LangGraph 状态机与双大模型（Dual-LLM）驱动的自适应代码审计、契约强化与沙箱原子级自动修复系统。**

---

## 🚀 V4 版本核心进化范式

**LLM-Code-Medic V4** 完成了从“被动运行测试”到“主动契约防御与认知闭环”**的颠覆性跨越。引入了工业级**双 LLM（Dual-LLM）协同认知架构与基于 **AST 的多重防御门禁矩阵（Multi-Gate Matrix）**，彻底封死了大模型在自动代码修复中常见的“幻觉硬编码”、“异常静默吞噬”、“公式数值篡改”以及“Callee 防御堆砌死循环”等高危恶性行为。

### 核心设计哲学

1. **契约恢复重于测试通过**：通过对测试通过率的盲目追求往往会导致 AI 编写出面条式的防御垫片。V4 强制通过静态符号审计与调用链逆向追踪，恢复并强化软件原生的架构契约。
2. **确定性规约拦截随机性幻觉**：利用 AST 静态解析与语义网关作为强监督屏障（Guardrails），让大模型的生成能力永远运行在工程规范的铁轨之上。

---

## 📂 架构全景与目录解析

```text
LLM-Code-Medic/
│
├── 📁 src/                             # 系统核心源代码根目录
│   ├── 📄 main.py                      # 系统全局启动入口（负责初始化并调度 MedicEngine）
│   ├── 📁 config/                      # 全局配置与环境解析模块
│   │   └── ⚙️ runtime_config.py        # 运行时配置解析器（环境变量类型转换与安全模式校验）
│   │
│   ├── 📁 engine/                      # 🚂 核心业务逻辑编排与会话流控引擎
│   │   ├── ⚙️ medic_engine.py          # 核心守护进程（封装系统初始化、冷启动与执行挂起逻辑）
│   │   ├── ⛓️ repair_pipeline.py       # 修复流水线管理器（组织依赖拓扑扫描、状态机流转与后置质量治理）
│   │   └── 🌐 runtime_session.py       # 运行时会话上下文管理（单例模式管理 LLM 客户端）
│   │
│   ├── 📁 agent/                       # 🧠 认知智能体感知层与契约规约定义
│   │   ├── 📊 state.py                 # 全局状态总线（承载全景依赖、异常堆栈与补丁快照）
│   │   ├── 🕸️ graph.py                 # 基于 LangGraph 的有向图状态机（编排节点流转与自愈闭环）
│   │   └── 📜 prompts.py               # 系统级认知协议规约（内置 PHASE 与 Q&A 自查问卷）
│   │
│   ├── 📁 llm/                         # 🌐 模型访问抽象层与弹性容灾适配层
│   │   ├── 🏭 model_factory.py         # 模型解耦实例化工厂（适配多供应商 API 规范）
│   │   ├── 🧭 provider_router.py       # 双 LLM 认知角色静态路由与运行时降级拓扑管理器
│   │   └── 🔌 llm_invoker.py           # 弹性接口调用原子（集成指数退避重试机制）
│   │
│   ├── 📁 quality/                     # 🛡️ 静态代码语义与策略门禁矩阵
│   │   ├── 📦 patch_quality_gate.py    # 补丁物理完备性验证器（检查补丁块的物理闭合性）
│   │   ├── 🧠 semantic_patch_gate.py   # AST 语义变动审查器（拦截异常吞噬、算法篡改与签名漂移）
│   │   ├── 🔒 policy_gate.py           # 安全策略常量保护网关（分析赋值语句流，拦截越权硬编码）
│   │   └── 🔁 repairability_gate.py    # 可修复性评估组件（收敛性检测与人工授权管道）
│   │
│   ├── 📁 tools/                       # 📡 静态分析工具集与沙箱运行时环境
│   │   ├── 🔍 scanner.py               # 项目静态扫描器（测绘 ExportTable、CallGraph 与 ImportGraph）
│   │   ├── 📐 ast_resolver.py          # 符号依赖解析器（执行上下游传递闭包扩展）
│   │   └── 🧪 executor.py              # 影子隔离沙箱执行器（组装虚拟工作区，执行原子化验证）
│   │
│   ├── 🧩 plugins/                     # 🧩 后置代码治理插件总线（涵盖风格、安全、单测补全）
│   │
│   └── 📊 report/                      # 📈 自动化交付物度量与报告域
│       └── 📄 report_generator.py      # 度量报告生成器（汇聚诊断度量与拦截记录，持久化 Markdown）
│
├── 🧪 output/                          # 🧪 Shadow Workspace 影子隔离沙箱物理执行区
│
└── 🎯 tests/                           # 🎯 多文件复杂漏洞工程评估基准库 (Benchmarks)

```

---

## 🧠 核心技术深度拆解

### 1. 双 LLM 协同认知架构（Dual-LLM Cognitive Engine）

V4 放弃了单模型包揽全局的低效做法，构建了战略诊断（R1）**与**战术修复（V3）解耦的双模型协同环路：

* **错误诊断节点（Diagnose Node） $\rightarrow$ `deepseek-ai/DeepSeek-R1**`：利用强大的长链条高难度逻辑推理能力。专注消化静态 AST 图谱、历史修复上下文与沙箱 `stderr` 崩溃日志，输出深度根因分析报告，并精准裁定目标文件范围（`TARGET_FILES`）。
* **代码修复节点（Repair Node） $\rightarrow$ `deepseek-ai/DeepSeek-V3**`：利用其极高的代码生成速度与极强的工程协议遵从度。严格消费 Diagnose 节点的判定结论，按照 V4 严格的代码 Patch 协议执行多文件补丁的并行组装。

---

### 2. 认知与工程契约中枢：`prompts.py`

`prompts.py` 是整个系统运行的最核心规则库，通过强约束的阶段控制流（Phases）与硬性惩罚条件，规范了 AI 的行为。

#### 🩺 诊断专家契约 (`DIAGNOSE_SYSTEM_PROMPT`)

诊断专家必须无条件、全量串行执行以下五个阶段，严禁任何形式的跨越：

* **PHASE 0: 静态符号校验（Static Symbol Validation）**：**必须执行，不可跳过。** 物理读取每个模块源文本，进行严苛的跨文件审计：
* *STEP A (模块存在检查)*：若 `import X` 的 `X.py` 在扁平布局中不存在 $\rightarrow$ 标记 `BUG [MODULE_NOT_FOUND: X]`。
* *STEP B (符号存在检查)*：逐行扫描 `from X import Y`，若 `Y` 未在 `X.py` 顶层定义 $\rightarrow$ 标记 `BUG [SYMBOL_NOT_FOUND: Y in X]`，并强行提取正确符号名。
* *STEP C (签名对齐检查)*：对每一个函数调用点进行形参实参的个数及具名键的精准对齐 $\rightarrow$ 标记 `BUG [SIGNATURE_MISMATCH: f]`。
* *STEP D (常量溯源检查)*：扫描字面量参数，若仓库内存在对应全局常量（如 `config.REPORT_PATH`）$\rightarrow$ 标记 `BUG [HARDCODED_LITERAL]`。
* *STEP E (全漏洞打包)*：严禁解决当前报错而遗留其他可见 Bug（**违规定义：WATERFALL_REPAIR**）。必须将全量 Bug 并入 `BUG_INVENTORY` 一轮清空。


* **PHASE 1: 追溯链推理（Traceback Reasoning）**：沿着 `error_site → immediate_caller → parameter_source → contract_owner` 进行逐跳追踪。大模型必须在以下两类分类中做出非此即彼的唯一承诺，不允许模糊两可（No hedging）：
* `[CONTRACT_UNDEFINED]`：Callee 未写断言守护。修复手段：Callee 加前置拦截 `raise`。
* `[CALLER_VIOLATED]`：Callee 契约完备，Caller 传入非法值。修复手段：修正 Caller 侧传入。


* **PHASE 2: 验证死循环阻断（Verify-Loop Detection）**：**防止诊断死循环的核心绝招。** 当重试次数 $\ge 1$ 且报错未变，且前一轮仅修改了 Callee，且 Callee 内部已存在 `raise` 守卫时，**触发熔断机制**：强行将根因层转移判定为 `[CALLER_VIOLATED]`，扩大修复域（`REPAIR_SCOPE`）至 Caller，严禁在 Callee 侧盲目堆砌防御代码。
* **PHASE 3 & 4: 反垫片审计与调用方修正约束**：严厉拒绝未记录历史默认值的硬编码硬垫片（`Shim with default`）、无重抛的异常吞噬（`Silent failure`）以及边界数据造假（`Magic return`）。Caller 侧修改的值必须在仓库中具备具名的、可追溯的 `VALUE_SOURCE`（常量、文档或既有惯例），否则直接输出 `ESCALATE_REQUIRED` 挂起，拒绝凭空捏造（Invented Value）。

#### 🛠️ 修复工程师契约 (`REPAIR_SYSTEM_PROMPT`)

接收诊断专家传递的契约报告，严格遵循 **6 级修复阶梯矩阵（Repair Hierarchy）**，并且在输出补丁代码前，必须在其输出中逐条完成 **Q1 至 Q10 的自查自省问卷（Self-Verification）**。任何一项触碰强行熔断条件（如引入无具名变量注释的魔术数字、Catch块未 `raise` 重抛、公式或阈值被微调、未一次性清空漏洞清单等），系统将被迫丢弃整个修复结果并强行重构思考（`RESTART`）。

---

### 3. 多重防御门禁矩阵（Multi-Gate Matrix）

补丁生成后，必须依次横穿 `quality/` 目录下的四大 AST 级拦截网关。任一网关亮起红灯，补丁立刻作废并回灌惩罚日志：

1. **补丁物理门禁 (`PatchQualityGate`)**：检查大模型输出的结构体是否完整闭合，物理文件解析（`<<<FILE_PATH>>>` 到 `<<<FILE_END>>>`）是否发生块断裂。
2. **语义红线门禁 (`SemanticPatchGate`)**：通过对比补丁前后的 AST（抽象语法树）节点，强行执行高级静态规约：
* 异常吞噬监控（`_check_swallowed_exceptions`）
* 魔术返回值监控（`_check_division_magic_returns`）
* 业务算法公式微调监控（`_check_formula_mutations`）：严禁 AI 将算法中的 `x - 10` 改为 `x - 9` 或微调核心浮点数系数。


3. **策略常量门禁 (`PolicyGate`)**：在高级安全或严格（`STRICT`）模式下，跟踪代码赋值语句（`_collect_assignments`），保护全局命名常量资产，拒绝任何未授权的字面量覆盖。
4. **可行性熔断门禁 (`RepairabilityGate`)**：动态监控修复状态与死循环频次。在遭遇无法通过静态或沙箱逻辑自动收敛的深层架构死锁时，主动退出自动状态机，通过标准控制台启动 `prompt_user_authorization` 向人类专家发起 **Guided（引导型放权修正）** 或 **Override（完全覆写模式）** 的人工介入授权请求，保留安全的降级出口。

---

## 🔁 LangGraph 状态机拓扑工作流

V4 采用全自适应的图拓扑循环，各个节点通过条件边进行高频状态响应：

```text
       [ Start ]
           │
           ▼
     ┌───────────┐
     │  Scanner  │ ◄──────────────────────────────────────┐ (动态内存刷新拓扑)
     └─────┬─────┘                                        │
           │                                              │
           ▼                                              │
     ┌───────────┐                                        │
     │ Diagnose  │ (DeepSeek-R1 战略诊断根因层)            │
     └─────┬─────┘                                        │
           │                                              │
           ▼                                              │
     ┌───────────┐                                        │
     │  Repair   │ (DeepSeek-V3 战术并行生成补丁)          │
     └─────┬─────┘                                        │
           │                                              │
           ▼                                              │
  =================== Gate Matrix ===================     │
  [ 🛡️ Quality Gate ] ──✖ (物理块破损) ──> [ Fail / Retry ] ┤
  [ 🧠 SemanticGate ] ──✖ (吞异常/改公式) ──> [ Fail / Retry ] ┤
  [ 🔒 Policy Gate  ] ──✖ (常量违规覆盖) ──> [ Fail / Retry ] ┤
  ===================================================     │
           │ (全面绿灯通过)                                 │
           ▼                                              │
     ┌───────────┐                                        │
     │  Verify   │ (Shadow Workspace 沙箱扁平执行)         │
     └─────┬─────┘                                        │
           │                                              │
           ├─ ✖ (沙箱崩溃 / Stderr 报错) ───────────────────┘
           │
           ▼ (沙箱完全通过 0-Error)
     ┌───────────┐
     │  Plugins  │ (后置流：代码风格审计 -> 安全特征扫描 -> AI自动补全生成缺失单测)
     └─────┬─────┘
           │
           ▼
        [ END ] (完美修复并闭环交付交付交付交付交付交付交付交付交付交付交付)

```

1. **全景雷达测绘**：`ProjectScanner` 提取符号大地图。
2. **认知链诊断**：R1 锁定根因层（`[CONTRACT_UNDEFINED]` / `[CALLER_VIOLATED]`），识别多文件漏洞并沉淀到 `BUG_INVENTORY`。
3. **并行契约修复**：V3 严格根据问卷自查，在目标文件中输出纯净的语义补丁。
4. **防御网关审判**：补丁必须无条件挺过四大门禁的静态 AST 扫描。
5. **影子沙箱试炼**：`CodeExecutor` 创建专属的扁平 `output/` 隔离影子工作区，彻底隔离 `pycache` 污染与 Windows 路径下的 GBK 编码黑洞。
6. **后置插件治理**：沙箱测试完全通关后，状态机安全退出。交由后置组件完成风格格式化与安全复审，并激活 **`LLMTestGenerator`** 针对代码变更域反向补齐、自动生成全新的单元测试文件（如 `test_main.py`），实现 100% 放心交付。

---

## ⚡ 工业级部署与运行指南

### 1. 部署项目环境

```bash
pip install -r requirements.txt

```

### 2. 配置硬核安全策略环境 (`.env`)

```env
# [必填] 目标测试仓库根目录路径
TEST_REPO_ROOT=./tests/v3

# 🌐 API 凭证 (按需填入)
DEEPSEEK_API_KEY=your_siliconflow_api_key
DEEPSEEK_API_BASE=https://api.siliconflow.cn/v1
GEMINI_API_KEY=

# ⚙️ 双 LLM 路由配置
# [诊断] 可选: deepseek / gemini
DIAGNOSE_PROVIDER=deepseek
DIAGNOSE_MODEL=deepseek-ai/DeepSeek-R1

# [修复] 可选: deepseek / gemini
REPAIR_PROVIDER=deepseek
REPAIR_MODEL=deepseek-ai/DeepSeek-V3

```

### 3. 一键启动修复引擎

```bash
python -m src.main

```

系统将自动锁定目标测试目标，绘制 AST 全景地图，调度双 LLM 认知模型在独立沙箱中进行高速多轮自适应演进。最终完美修复的代码及反向补齐的单元测试，将统一原子级沉淀输出至 `output/` 影子工作区。