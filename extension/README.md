# LLM Code Medic

一键式 AI 代码修复助手（Python 项目）。

LLM Code Medic 能够自动分析项目结构、定位错误根因、生成修复补丁，并完成自动验证。

---

## 功能特性

* 🚀 一键修复代码
* 🔍 自动诊断 Bug 根因
* 🧠 AI 生成修复方案
* 📁 多文件协同修复
* 🌳 AST 语法树分析
* 🛡️ 补丁质量检查
* ✅ 自动验证修复结果
* 🔄 LangGraph 智能修复流程

---

## 重要说明

**本插件不是独立运行的产品。**

安装 VS Code 插件后，还需要下载 LLM Code Medic 项目源码并启动本地后端服务，否则会出现：

```text
fetch failed
```

错误。

---

## 安装步骤

### 1. 下载项目源码

项目地址：

```text
https://github.com/kitakore495/LLM-Code-Medic
```

克隆仓库：

```bash
git clone https://github.com/kitakore495/LLM-Code-Medic.git
cd LLM-Code-Medic
```

---

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

---

### 3. 配置模型接口

创建：

```text
```env

# 🌐 API 凭证 (按需填入)
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=
GEMINI_API_KEY=

# ⚙️ 双 LLM 路由配置
# [诊断] 可选: deepseek / gemini
DIAGNOSE_PROVIDER=
DIAGNOSE_MODEL=

# [修复] 可选: deepseek / gemini
REPAIR_PROVIDER=
REPAIR_MODEL=

```

### 4. 启动后端服务

在项目根目录执行：

```bash
uvicorn server.app:app --reload
```

启动成功后访问：

```text
http://127.0.0.1:8000/docs
```

如果能看到 Swagger 页面，说明后端运行正常。

---

## 使用方法

### 方法一：资源管理器右键

右键项目目录：

```text
LLM Code Medic: One Click Fix
```

---

### 方法二：编辑器菜单

打开代码文件后点击：

```text
LLM Code Medic: One Click Fix
```

---

### 方法三：命令面板

按：

```text
Ctrl + Shift + P
```

输入：

```text
LLM Code Medic: One Click Fix
```

执行修复。

---

## 修复结果

当前版本不会直接修改原项目文件。

修复后的代码会输出到：

```text
output/
```

目录中。

用户可以自行对比和合并修改内容。

这样可以避免 AI 修改错误导致项目损坏。

---

## 环境要求

### 普通用户

* Python 3.10+
* VS Code

### 开发者（仅源码开发需要）

* Node.js 22+
* TypeScript 5+

如果只是安装 VS Code 插件并使用，不需要安装 Node.js。

---

## 当前限制

* 需要本地启动后端服务
* 需要配置大模型 API
* 当前主要针对 Python 项目
* AI 生成的补丁建议人工审核后再投入生产环境

---

## 开发路线图

* 云端修复服务
* 自动应用补丁
* Git 集成
* 多语言支持
* 修复历史记录
* VS Code 侧边栏面板
* 团队协作支持

---

## 开源地址

https://github.com/kitakore495/LLM-Code-Medic

---

## License

MIT License
