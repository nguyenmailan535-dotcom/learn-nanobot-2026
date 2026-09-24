# 第14章 2026年 AI Agent / 后端就业与求职准备

> 🎯 本章定位：帮助求职者全面了解 2026 年 AI Agent 相关岗位的市场现状、薪资水平、技能要求和求职策略，制定针对性的求职规划。

---

## 目录

- [一、2026年 AI Agent 市场概览](#一2026年-ai-agent-市场概览)
- [二、常见岗位类型详解](#二常见岗位类型详解)
- [三、JD 关键词深度分析](#三jd-关键词深度分析)
- [四、薪资范围参考](#四薪资范围参考)
- [五、主要招聘平台与渠道](#五主要招聘平台与渠道)
- [六、大厂 AI Agent 团队介绍](#六大厂-ai-agent-团队介绍)
- [七、必备技能清单](#七必备技能清单)
- [八、简历关键词优化](#八简历关键词优化)
- [九、面试流程介绍](#九面试流程介绍)
- [十、求职时间线规划](#十求职时间线规划)
- [十一、2026-09 补充：Agent 开发 + Java 后端双轨准备](#十一2026-09-补充agent-开发--java-后端双轨准备)

---

## 一、2026年 AI Agent 市场概览

> **2026-09-24 更新说明**：原版中的市场规模、薪资区间、公司团队描述属于阶段性参考，不应当成实时招聘事实。真正投递前请以当周 JD、公司官网和招聘平台为准。本章保留原版对岗位类型、技能关键词、面试流程和求职节奏仍然有价值的内容，并在后文补充 current Agent Engineering / Java Backend 双轨准备。


### 1.1 行业背景

原版这一节的核心判断仍有价值：Agent 已经从“只做 Demo”转向“进入真实产品与内部工作流”。但具体厂商发布时间、招聘增幅等数据变化很快，本仓库不再写未经逐条核验的精确时间线和百分比。

对求职更重要的 2026 工程趋势是：

1. **Agent 与普通后端正在融合**：很多岗位实际是“后端服务 + LLM/Tool/RAG/Workflow”，并不会把 Agent 单独做成一个孤立系统。
2. **Tool Calling / MCP 的工程边界更重要**：不仅要“能调用”，还要考虑 Schema、权限、Timeout、Retry、Credential、Audit。
3. **RAG 从能跑转向可评测**：Hybrid Retrieval、Rerank、Citation/Grounding、Eval、Bad Case 分析比单纯 Vector DB Demo 更有区分度。
4. **长任务与 Runtime 能力更受关注**：Streaming、Session、Checkpoint、Background Job、Subagent、Automation、Observability 都属于真实落地问题。
5. **Java/Go/Python 都有机会**：Python 在 Agent/RAG 原型和生态里常见；Java/Go 在平台、服务治理、数据与基础设施侧依然重要。

> 求职判断应以你投递当周的 JD 为准，而不是把一张“2026 Agent 市场统计表”当作长期事实。


### 1.2 市场规模

原版用市场规模、岗位数和 MCP Server 数量展示增长趋势，但这些精确数字没有在本仓库中持续维护，因此不再作为 current 事实保留。

更实用的做法是每次准备投递时自己做一次 **JD Snapshot**：

~~~text
目标城市 / 公司层级 / 岗位关键词
        ↓
收集 30-50 条当周 JD
        ↓
统计：
- 语言：Java / Python / Go
- Agent：Tool Calling / Workflow / MCP
- RAG：Embedding / Vector DB / BM25 / Rerank
- Backend：MySQL / Redis / MQ / Docker
- Engineering：Eval / Trace / Monitoring / Security
        ↓
按真实频率决定本月学习优先级
~~~

这样得到的是与你当下目标岗位直接相关的数据，而不是泛行业报告的宏观数字。

### 1.3 需求侧分析

招聘需求主要来自以下方向：

1. **大厂 AI 平台团队**：字节、阿里、腾讯、百度等构建 Agent 开发平台
2. **垂直领域 Agent**：金融、医疗、法律、教育、电商等行业定制 Agent
3. **AI 原生创业公司**：从 0 到 1 打造 Agent 产品
4. **传统企业 AI 转型**：用 Agent 改造内部流程（如智能客服、知识管理）
5. **开发者工具**：IDE 插件、AI 代码助手、自动化测试工具
6. **AI 基础设施**：模型推理服务、向量数据库、MCP 生态

---

## 二、常见岗位类型详解

### 2.1 AI 应用开发工程师

**岗位定位**：将 AI 能力集成到产品中，是需求量最大的岗位类型。

**核心职责**：
- 使用 LLM API（OpenAI/Claude/通义千问）开发 AI 功能
- 实现 RAG 检索增强、对话系统、内容生成等应用场景
- 设计和优化 Prompt 工程
- 构建 AI 应用的后端服务和 API

**技术要求**：
- Python/TypeScript 开发能力
- 熟悉至少一种 LLM API（OpenAI/Anthropic/阿里云 DashScope）
- 了解 RAG 基本流程和向量数据库
- Web 开发基础（FastAPI/Flask/Next.js）

**适合人群**：有 1-3 年后端开发经验，希望转型 AI 方向的工程师

**薪资区间**：18K-45K/月（一线城市）

---

### 2.2 LLM 应用工程师

**岗位定位**：专注于大模型应用层的深度开发，比 AI 应用开发工程师更偏底层。

**核心职责**：
- 设计和实现 LLM 应用架构（Agent 循环、记忆系统、工具调用）
- 模型选型和评测（对比不同模型在特定场景下的表现）
- Prompt 工程和上下文管理优化
- 搭建 LLM 应用的监控和评测体系
- 解决幻觉、延迟、成本等工程问题

**技术要求**：
- 深入理解 Transformer 架构和推理过程
- 熟悉 Agent 框架（LangChain/LangGraph/Nanobot）
- 掌握 MCP 协议和 Function Calling 机制
- 了解模型训练流程（SFT/RLHF/DPO）
- 性能优化经验（缓存、异步、批处理）

**适合人群**：有 2-5 年开发经验，对 LLM 原理有深入学习的工程师

**薪资区间**：25K-55K/月（一线城市）

---

### 2.3 AI Agent 开发工程师

**岗位定位**：专注于 Agent 系统的设计、开发和优化，是最对口的岗位。

**核心职责**：
- 设计和实现 Agent 系统架构（ReAct 循环、多 Agent 编排）
- 开发自定义工具和 MCP Server
- 实现 Agent 的记忆管理和状态管理
- 构建 Agent 评测和调试体系
- 优化 Agent 的可靠性、效率和成本

**技术要求**：
- 深入理解 Agent 架构（至少读过一个框架的源码，如 Nanobot）
- 掌握 MCP 协议（能开发 MCP Server）
- 熟悉 ReAct、Reflection、Planning 等 Agent 设计模式
- 异步编程和并发控制（Python asyncio）
- 系统设计能力（高可用、可观测性）

**适合人群**：对 Agent 技术有热情，有源码阅读和框架开发经验的工程师

**薪资区间**：30K-65K/月（一线城市）

---

### 2.4 大模型算法工程师

**岗位定位**：从事大模型的训练、微调和优化，偏算法和研究方向。

**核心职责**：
- 大模型的 Pretrain/SFT/RLHF/DPO 训练
- LoRA/QLoRA 等参数高效微调
- 模型评测和分析
- 推理优化（量化、蒸馏、加速）
- 数据清洗和质量控制

**技术要求**：
- 扎实的深度学习基础（PyTorch）
- 深入理解 Transformer 架构（Attention、位置编码、归一化等）
- 熟悉训练流程和优化技巧（学习率调度、混合精度、分布式训练）
- 了解 RLHF/DPO 等对齐技术
- 论文阅读和复现能力

**适合人群**：计算机/AI 相关硕博，有模型训练经验

**薪资区间**：35K-80K/月（一线城市）

---

### 2.5 AI 产品经理

**岗位定位**：负责 AI Agent 产品的规划、设计和落地。

**核心职责**：
- AI Agent 产品的需求分析和功能设计
- 用户体验设计（对话交互、多模态交互）
- 与算法团队沟通模型能力和限制
- 竞品分析和市场洞察
- 产品数据分析和迭代优化

**技术要求**：
- 理解 LLM 和 Agent 的基本原理和能力边界
- 了解 Prompt 工程和 RAG 的基本概念
- 数据分析能力
- 具备一定的技术背景（能与工程师有效沟通）
- 了解 AI 安全和合规要求

**适合人群**：有产品经验的 PM 转型 AI 方向，或有技术背景的毕业生

**薪资区间**：20K-50K/月（一线城市）

---


### 2.6 Java 后端 / AI 平台后端

**岗位定位**：核心仍是服务端工程，但业务中包含模型调用、RAG、Agent、数据/任务平台或 AI 基础设施。

**常见职责**：
- Spring Boot / Java 服务开发与 API 设计；
- MySQL / Redis / MQ / Cache；
- 异步任务、幂等、限流、重试与可观测性；
- 接入 LLM/RAG/Agent Service；
- 管理用户、文档、任务、权限、审计等 Control Plane；
- 与 Python AI Service / MCP Server 协作。

**为什么值得关注**：这类岗位能同时复用后端基本盘和 Agent 项目经验，尤其适合希望保留 Java 后端求职面、又想进入 AI 应用/平台方向的候选人。

---


## 三、JD 关键词深度分析

> 原版的“500+ JD / 出现频率 xx%”属于一次性样本，不再当作 2026-09 的实时统计。下面保留原版关键词框架，但改成**面试与项目准备优先级**。

### 3.1 语言与工程基础

| 关键词 | 建议优先级 | 你需要证明什么 |
|---|---:|---|
| Java / Spring Boot | ★★★★★（后端路线） | API、IOC/AOP、事务、异常处理、工程项目 |
| Python | ★★★★★（Agent 路线） | asyncio、类型、FastAPI、AI 生态 |
| SQL / MySQL / PostgreSQL | ★★★★★ | Index、Transaction、Query、数据建模 |
| Redis | ★★★★★ | Cache、TTL、击穿/穿透、一致性、限流 |
| HTTP / REST / SSE / WebSocket | ★★★★★ | 普通请求、Streaming、连接生命周期 |
| Git / Linux | ★★★★★ | 真实开发与排障 |
| Docker | ★★★★ | 可复现部署 |
| MQ / Async Job | ★★★★ | 长任务、削峰、Retry、Idempotency |
| Go | ★★★ | 平台/基础设施岗位按 JD 补 |

### 3.2 Agent 与编排

| 关键词 | 建议优先级 | 面试要点 |
|---|---:|---|
| Tool / Function Calling | ★★★★★ | Schema、Execution、Error、Observation |
| Agent vs Workflow | ★★★★★ | 控制权、可靠性、适用边界 |
| ReAct / Tool Loop | ★★★★★ | Provider → Tool → Result → Provider |
| Session / State | ★★★★★ | FIFO、Persistence、Recovery |
| MCP | ★★★★ | Host/Client/Server、Lifecycle、Security |
| Subagent / Orchestrator-Workers | ★★★ | 并发收益与协调成本 |
| LangGraph / 其他框架 | ★★★ | 会用即可，重点是可迁移 Runtime 思维 |

### 3.3 检索与知识

| 关键词 | 建议优先级 | 面试要点 |
|---|---:|---|
| RAG | ★★★★★ | Parsing → Chunk → Retrieval → Generation |
| Embedding / Vector Search | ★★★★★ | 相似度、索引、召回 |
| BM25 / Hybrid Search | ★★★★ | exact term 与 semantic 互补 |
| Rerank | ★★★★ | 精排位置、成本、收益 |
| Citation / Grounding | ★★★★ | Claim-Evidence 对齐 |
| Retrieval Eval | ★★★★★ | Recall@k、MRR、nDCG、Bad Case |

### 3.4 Agent 工程化

2026 求职项目里很容易被忽略、但很有后端价值的关键词：

~~~text
Streaming
Timeout / Retry
Idempotency
Rate Limit
Cache
Queue / Background Job
Observability / Trace
Eval
Prompt Injection
Workspace / Sandbox
Credential / Secret
Cost / Token Usage
~~~

### 3.5 大模型基础

Agent/应用岗位通常至少要能解释：
- Transformer / Attention 基本原理；
- Token / Context Window；
- Temperature / Top-p；
- KV Cache；
- Structured Output；
- Streaming；
- Embedding；
- 模型选型与 Eval。

除非 JD 明确偏算法训练，不要让 SFT/RLHF/DPO/LoRA 挤占后端与 Agent Runtime 的核心准备时间。

### 3.6 框架关键词怎么用

框架名应作为“会落地”的证据，而不是技能墙：

~~~text
低质量：
LangChain / LangGraph / Nanobot / Dify / Coze 全都熟悉

高质量：
追过 Nanobot MessageBus → AgentLoop → AgentRunner → ToolRegistry → Session，
并将 Retrieval MCP 接入真实 Tool Loop，用 Eval 验证结果。
~~~


## 四、薪资范围参考

> 薪资高度依赖城市、学历、实习/校招/社招、公司层级、业务和谈判。原版固定区间不再作为 current 数据保留。

### 4.1 如何做自己的薪资/实习日薪调研

投递前一周：
1. 在目标平台搜索 **同城市 + 同年限/届别 + 同岗位**；
2. 至少看 20 条有效 JD；
3. 分开记录 Java 后端、AI 应用、Agent、算法岗位；
4. 区分实习日薪、月薪、总包、股票、年终；
5. 对未公开薪资的岗位不要自行补数字。

### 4.2 比薪资数字更重要的实习变量

对第一段实习，建议同时比较：
- 是否进真实代码库；
- 是否有 Code Review；
- Mentor 是否明确；
- 是否能碰线上/测试环境；
- 能否做后端/Agent 核心模块而非纯标注；
- 实习周期是否与学业/秋招冲突；
- 项目成果是否可在简历中准确描述。

### 4.3 Offer/实习比较模板

| 维度 | 问题 |
|---|---|
| 工作内容 | 写核心代码还是边缘支持？ |
| 技术栈 | 能否积累 Java/Python/Agent/RAG 的可迁移能力？ |
| Mentor | 是否有人 Review 和带项目？ |
| 工程流程 | Git、测试、CI/CD、监控是否正规？ |
| 品牌/业务 | 下一段求职是否能被快速理解？ |
| 地点/WLB | 是否符合个人长期约束？ |
| 薪酬 | 在同地区同类型岗位中是否合理？ |


## 五、主要招聘平台与渠道

### 5.1 综合招聘平台

原版列出的 Boss 直聘、牛客、猎聘、脉脉、LinkedIn 等仍可按各自场景使用。平台热度会变化，不再给“岗位数量五星”这类伪精确排名。

建议用途：
- **Boss 直聘**：日常实习/社招式即时沟通；
- **牛客/校招官网**：校招、笔面经、正式批次；
- **公司招聘官网/公众号**：最可靠的正式岗位状态；
- **脉脉/LinkedIn/技术社群**：找团队信息和内推；
- **GitHub/开源社区**：发现与 Agent/MCP/RAG 强相关团队。

### 5.2 高效求职策略

不要机械执行“每天打招呼 20+”或相信“内推通过率是海投 3-5 倍”这种无法普遍验证的数字。更稳妥的流程：

~~~text
建立岗位表
→ 每天新增/更新
→ 按 JD 定制简历关键词
→ 投递
→ 24-72h 后记录状态
→ 面试题回流学习清单
→ 每周统计：
   有效回复率 / 面试率 / 被卡环节
~~~

### 5.3 第一段实习的渠道策略

同时跑三条线：
1. **中大厂日常实习**：争取品牌和工程流程；
2. **本地/中型技术公司**：提高面试密度与拿第一段经历概率；
3. **研究/AI 创业团队**：如果能做真实 Agent/RAG/Backend Core，同样有价值。

公司“大小”不是唯一变量；工作内容、Mentor、真实工程流程更重要。

## 六、大厂 AI Agent 团队介绍

> **使用说明**：以下保留原版用于帮助理解“大厂可能有哪些 AI/Agent 业务入口”，但团队名称、组织归属、技术栈和招聘状态都可能调整。准备具体面试时必须重新查看公司官网、产品页和当周 JD，不把本节当组织架构事实表。

### 6.1 字节跳动

**相关团队**：
- **Coze（扣子）团队**：字节的 Agent 开发平台，支持低代码构建 Agent，集成了工作流编排、知识库、插件市场等能力
- **豆包团队**：基于豆包大模型的 Agent 应用开发
- **飞书 AI 团队**：将 Agent 能力集成到飞书办公套件中
- **TikTok AI 团队**：海外市场的 AI Agent 应用

**技术栈**：Go/Python、自研 Agent 框架、MCP 兼容、分布式系统

**招聘特点**：要求扎实的工程能力，偏好有大规模系统经验的候选人。面试侧重系统设计和编码能力。

---

### 6.2 阿里巴巴

**相关团队**：
- **通义实验室**：通义千问大模型团队，包括 Agent 能力开发
- **百炼平台**：阿里云的 Agent 开发平台，提供模型调用、RAG、Agent 编排等全栈能力
- **钉钉 AI**：将 Agent 集成到钉钉工作流中
- **达摩院**：前沿 AI 研究，包括多 Agent 协作、Agent 安全等

**技术栈**：Python/Java、ModelScope、DashScope API、阿里云基础设施

**招聘特点**：重视项目经验和业务理解，要求候选人能将技术与业务场景结合。面试中常有业务案例分析。

---

### 6.3 腾讯

**相关团队**：
- **腾讯混元团队**：混元大模型的 Agent 能力开发
- **微信 AI 团队**：微信生态内的 AI Agent 应用
- **企业微信 AI**：企业级 Agent 解决方案
- **腾讯云 AI**：云端 Agent 开发平台和工具链

**技术栈**：C++/Go/Python、自研推理引擎、腾讯云基础设施

**招聘特点**：技术面试难度较高，注重算法基础和系统设计能力。偏好有社交/内容场景经验的候选人。

---

### 6.4 百度

**相关团队**：
- **文心一言团队**：基于文心大模型的 Agent 应用
- **百度智能云千帆**：企业级 Agent 开发平台
- **百度搜索 AI**：搜索增强的 Agent 能力
- **Apollo（自动驾驶）**：车载 Agent 和具身智能

**技术栈**：Python/C++、PaddlePaddle（飞桨）、百度云基础设施

**招聘特点**：搜索和 NLP 背景较深，偏好有信息检索和知识图谱经验的候选人。

---

### 6.5 其他重要玩家

| 公司 | Agent 相关方向 | 特点 |
|------|---------------|------|
| **美团** | 本地生活 Agent、智能客服 | 强调业务理解 |
| **京东** | 电商 Agent、物流 Agent | 强调工程落地 |
| **华为** | 盘古大模型 Agent、CloudAgent | 偏重 ToB 场景 |
| **商汤** | 多模态 Agent、具身智能 | 偏重研究 |
| **智谱 AI** | GLM Agent、MaaS 平台 | 开源生态 |
| **月之暗面** | Kimi Agent 能力 | 长文本 Agent |
| **MiniMax** | 海螺 AI Agent | 海外市场 |
| **零一万物** | 大模型 + Agent 应用 | 李开复团队 |
| **Anthropic（海外）** | Claude Agent、MCP 生态 | Agent 方向引领者 |
| **OpenAI（海外）** | GPT Agent、Assistants API | 行业标杆 |

---

## 七、必备技能清单

### 按优先级排序的 8 大必备技能

#### 技能 1：Python 编程与异步编程 ⭐⭐⭐⭐⭐

**为什么必备**：95% 的 Agent 岗位要求 Python，Agent 系统大量使用 async/await。

**具体要求**：
- 熟练使用 Python 3.11+ 特性（类型注解、match-case、dataclass）
- 掌握 asyncio 编程模型（协程、Task、Event Loop、Semaphore）
- 熟悉 FastAPI/Flask 等 Web 框架
- 了解 Python 的并发模型（GIL、多线程、多进程、协程的选择）

**学习建议**：通过阅读 Nanobot 源码学习 asyncio 在 Agent 系统中的实际应用

---

#### 技能 2：LLM API 使用与 Prompt 工程 ⭐⭐⭐⭐⭐

**为什么必备**：这是所有 AI Agent 工作的基础操作技能。

**具体要求**：
- 熟悉 OpenAI/Anthropic/通义千问的 API 调用方式
- 掌握 System Prompt 设计、Few-shot 示例构造
- 理解 Token 计数、上下文窗口管理、流式响应处理
- 了解模型参数调节（temperature、top_p、max_tokens）
- 能设计结构化输出的 Prompt（JSON 输出、格式约束）

**学习建议**：动手实践 100+ 个不同类型的 Prompt，总结模式和经验

---

#### 技能 3：Agent 架构理解 ⭐⭐⭐⭐⭐

**为什么必备**：区分「会调 API」和「会做 Agent」的核心能力。

**具体要求**：
- 理解 ReAct 循环的原理和实现
- 了解 Agent 的记忆系统（短期/长期/外部）
- 理解工具调用机制（Tool Calling / Function Calling）
- 至少深入追过一个 Agent 框架的核心运行链（例如 Nanobot current-source 的 MessageBus → AgentLoop → AgentRunner → ToolRegistry → Session）
- 了解多 Agent 协作模式（Orchestrator-Workers、Pipeline）

**学习建议**：跟随 learn-nanobot 项目的章节逐步深入

---

#### 技能 4：MCP 协议 ⭐⭐⭐⭐

**为什么必备**：MCP 正在成为 AI 工具连接的事实标准，2026 年起的 JD 中出现率快速上升。

**具体要求**：
- 理解 MCP 的 Host/Client/Server 三层架构
- 了解三大原语（Tools/Resources/Prompts）
- 能使用官方 SDK 开发简单的 MCP Server
- 理解 MCP 与 Function Calling 的区别和关系
- 了解 MCP 的传输层选择（stdio/HTTP+SSE/Streamable HTTP）

**学习建议**：动手开发一个 MCP Server（如 MySQL 查询工具），并在 Nanobot 中集成测试

---

#### 技能 5：RAG 系统 ⭐⭐⭐⭐

**为什么必备**：RAG 是目前 LLM 应用中最成熟和最广泛使用的模式。

**具体要求**：
- 掌握 RAG 的完整流程（文档解析 → Chunk → Embedding → 检索 → 生成）
- 熟悉至少一种向量数据库（Milvus/ChromaDB/Pinecone）
- 了解 Chunk 分割策略和 Embedding 模型选择
- 理解混合检索和 Rerank 的优化手段
- 能搭建一个端到端的 RAG 系统

**学习建议**：用 LangChain + ChromaDB 搭建一个个人知识库问答系统

---

#### 技能 6：大模型原理 ⭐⭐⭐⭐

**为什么必备**：理解原理才能在出问题时定位根因，面试中必考。

**具体要求**：
- 理解 Transformer 架构（Self-Attention、Multi-Head、FFN）
- 了解位置编码（RoPE）、归一化（RMSNorm）、激活函数（SwiGLU）
- 理解 KV Cache 和推理加速原理
- 了解 SFT/RLHF/DPO 训练流程
- 了解 LoRA 等参数高效微调方法

**学习建议**：通过阅读 Nanobot 源码中 Provider 层的实现，理解 LLM 推理流程；结合开源小模型项目从零实现一个小型 Transformer，建立直觉理解

---

#### 技能 7：系统设计 ⭐⭐⭐

**为什么必备**：中高级岗位的面试中必考系统设计题。

**具体要求**：
- 能设计一个企业级 Agent 系统（考虑高可用、多租户、安全）
- 理解微服务架构和 API 设计
- 了解消息队列、缓存、数据库的选型
- 能做成本估算和容量规划
- 了解监控和可观测性方案

**学习建议**：练习 3-5 个 Agent 系统设计题，参考第 13 章的系统设计部分

---

#### 技能 8：工程素养 ⭐⭐⭐

**为什么必备**：工程素养决定了你能否把 demo 变成产品。

**具体要求**：
- Git 工作流（分支管理、Code Review、CI/CD）
- Docker 容器化和 K8s 基础
- 单元测试和集成测试编写习惯
- 代码文档化（README、API 文档、注释）
- 安全意识（密钥管理、输入校验、日志脱敏）

**学习建议**：在自己的 Agent 项目中严格执行工程规范，而非只做 demo

---

## 八、简历关键词优化

### 8.1 高优先级关键词（务必出现）

```
AI Agent, LLM, 大模型, RAG, Python, Prompt Engineering,
Tool Calling, Function Calling, MCP, 向量数据库,
Agent 框架, ReAct, 异步编程, API 集成
```

### 8.2 中优先级关键词（按岗位方向选择）

```
# Agent 开发方向
Nanobot, LangChain, LangGraph, 多Agent, 工具调用,
记忆管理, SubAgent, MCP Server, Skills

# 算法方向
Transformer, SFT, RLHF, DPO, LoRA, QLoRA,
PyTorch, 分布式训练, 模型评测, 数据质量

# 应用开发方向
FastAPI, Docker, Redis, PostgreSQL, Milvus,
微服务, CI/CD, 高可用, 监控
```

### 8.3 加分关键词（区分度高）

```
源码研究, MCP Server 开发, Agent 评测, Prompt Cache,
Multi-Agent 编排, 端侧部署, 知识蒸馏,
开源贡献, 技术博客
```

### 8.4 关键词使用策略

1. **标题**：岗位名称 + 核心关键词（如「AI Agent 开发工程师 | Python & MCP」）
2. **技能列表**：按 JD 中的关键词顺序排列，匹配度高的放前面
3. **项目描述**：自然地融入关键词，避免堆砌
4. **自我评价**：用 1-2 句话概括核心能力，包含 3-5 个高优关键词

---

## 九、面试流程介绍

### 9.1 典型面试流程（大厂）

```
简历筛选 → 笔试（可选） → 一面（技术面） → 二面（技术深度面）
→ 三面（技术/业务 Leader 面） → HR 面 → Offer 沟通
```

**时间跨度**：通常 2-4 周

### 9.2 各轮面试重点

#### 一面：基础技术面（45-60 分钟）

**面试官**：通常是团队的高级工程师

**考察内容**：
- 编程基础：Python 语法、数据结构、算法题（LeetCode Medium 难度）
- LLM 基础：Transformer 架构、Attention 机制、Token 化
- Agent 基础：ReAct 循环、工具调用、记忆系统
- 项目经历：简要介绍 1-2 个项目
- 手撕代码：1-2 道编程题（可能涉及异步编程、JSON 解析等）

**准备建议**：刷 50 道 LeetCode（重点：字符串、树、图、动态规划）；熟练回答本章 Q1-Q15 基础题

---

#### 二面：技术深度面（60-90 分钟）

**面试官**：技术 Leader 或架构师

**考察内容**：
- 项目深挖：详细讲解一个项目（技术选型、架构设计、难点解决）
- 技术深度：Agent 架构设计、MCP 协议细节、RAG 优化
- 系统设计：设计一个企业级 Agent 系统
- 开放问题：如何评测 Agent 效果、如何控制成本等
- 源码理解：如果简历写了源码研究，会深入问

**准备建议**：用 STAR 法则准备项目介绍；练习 3-5 个系统设计题；深入理解一个 Agent 框架的源码

---

#### 三面：Leader 面/交叉面（45-60 分钟）

**面试官**：部门 Leader 或其他团队技术负责人

**考察内容**：
- 技术视野：对 AI Agent 行业的理解和判断
- 团队协作：过往的团队合作经验
- 问题解决：遇到的最大技术挑战及解决过程
- 学习能力：如何学习新技术、如何保持技术敏感度
- 职业规划：短期和长期的职业目标

**准备建议**：关注 AI Agent 行业动态；准备 2-3 个团队协作/挑战克服的故事

---

#### HR 面（30-45 分钟）

**考察内容**：
- 离职原因/求职动机
- 薪资期望（务必提前做好调研）
- 工作稳定性
- 文化匹配度
- 加班/出差接受度

**准备建议**：诚实但策略性地回答；薪资谈判可以参考本章的薪资数据

---

### 9.3 面试中的常见坑

1. **过度夸大项目经验**：被深挖时露馅比不写更致命
2. **只会调 API 没有原理理解**：能力天花板太低，面试官一追问就答不上来
3. **忽视工程素养**：只关注模型和算法，不关心测试、部署、监控
4. **对公司业务不了解**：面试前至少花 30 分钟研究目标公司的 AI 产品
5. **薪资期望不合理**：过高可能错失机会，过低可能被低估

---

## 十、求职时间线规划

### 10.1 应届生时间线（以 2026 年秋招为例）

| 时间段 | 重点任务 | 产出 |
|--------|---------|------|
| 2026.01-03 | 技术学习期 | 学完 Nanobot 源码 + 实战项目练习 |
| 2026.03-04 | 项目积累期 | 完成 2 个可写入简历的项目 |
| 2026.04-05 | 简历准备期 | 简历定稿、开始投递暑期实习 |
| 2026.05-06 | 暑期实习 | 积累实际工作经验 |
| 2026.07-08 | 秋招准备期 | 刷八股文、模拟面试 |
| 2026.08-10 | 秋招高峰 | 大量投递和面试 |
| 2026.10-11 | Offer 决策 | 拿到多个 offer 后选择 |

### 10.2 社招跳槽时间线

| 时间段 | 重点任务 | 产出 |
|--------|---------|------|
| 第 1-2 周 | 学习充电 | 学完核心技术点（本项目 1-12 章） |
| 第 3-4 周 | 项目包装 | 简历优化、项目话术准备 |
| 第 5-6 周 | 面试冲刺 | 刷面试题（第 13 章）、模拟面试 |
| 第 7-10 周 | 集中面试 | 每周 3-5 场面试 |
| 第 11-12 周 | Offer 谈判 | 横向比较、薪资谈判 |

### 10.3 每日学习建议

| 时段 | 内容 | 时长 |
|------|------|------|
| 早上 | 刷 1-2 道面试八股文（第 13 章） | 30 分钟 |
| 上午 | 源码阅读或项目实践 | 2-3 小时 |
| 下午 | LeetCode 算法练习 | 1-2 小时 |
| 晚上 | 学习理论知识（Transformer/RAG/MCP） | 1-2 小时 |
| 睡前 | 浏览 AI 新闻和行业动态 | 30 分钟 |

---

## 十一、2026-09 补充：Agent 开发 + Java 后端双轨准备

### 11.1 先理解 2026 Agent 岗真正需要什么

只会调用一个 LLM SDK 已经很难形成区分度。更常见的工程能力组合是：

~~~text
Python / Java Backend
+
LLM API / Streaming
+
Tool Calling / MCP
+
RAG / Retrieval / Rerank
+
Agent State / Memory
+
Eval / Trace / Observability
+
Redis / MySQL / Queue / Cache
+
Docker / Linux
~~~

真正有价值的项目应该能回答：

- 为什么需要 Agent，而不是普通 Workflow？
- Tool 失败怎么恢复？
- RAG 怎么评测？
- Citation 怎么验证？
- Session 如何持久化？
- 长任务如何异步？
- 如何做限流、幂等、缓存？
- 怎么定位 P95 延迟？
- Prompt Injection 如何做硬边界防护？

### 11.2 Agent 开发岗与 Java 后端岗的交集

很多人把两条路线理解成完全互斥，其实工程交集非常大。

| 后端能力 | Agent 系统中的对应问题 |
|---|---|
| REST API | Agent / Retrieval Service 接口 |
| Redis | Cache / Rate Limit / Job State |
| MySQL | Metadata / User / Job / Audit |
| MQ / Async | Long-running Agent Task |
| Thread / Concurrency | Tool/Subagent 并发控制 |
| Transaction | Side-effect Tool 一致性 |
| Idempotency | Tool Retry / Ingestion / Job |
| AOP / Middleware | Trace / Auth / Metrics |
| Docker / Linux | Agent Runtime 部署 |
| Logging | Tool/Model/Request Trace |

所以如果目标同时覆盖 Java 后端和 Agent 实习，最好的项目不是做两个互不相关 Demo，而是做一个有扎实 Backend Boundary 的 Agent Project。

### 11.3 对第一段实习更现实的优先级

如果目标是在较短时间内拿到第一段实习，建议把准备顺序放在：

~~~text
第一优先级：能面试
├── Java / Python 基础
├── 数据结构与常见算法
├── MySQL / Redis / HTTP
├── Git / Linux
└── 一个能讲深的项目

第二优先级：Agent 区分度
├── Tool Calling
├── MCP
├── RAG
├── Eval
├── Streaming
└── Agent Runtime 源码理解

第三优先级：进阶
├── Multi-Agent
├── Fine-tuning
├── Kubernetes
└── 复杂分布式架构
~~~

不要因为“Agent 很新”而跳过普通后端基础。

### 11.4 Agent 岗 JD 的高价值关键词

看到 JD 时，可以优先标记：

~~~text
Python / FastAPI
Java / Spring Boot
Agent / Workflow
MCP
Tool Calling
RAG
Embedding
Vector Database
BM25 / Hybrid Search
Reranker
Evaluation
Tracing / Observability
SSE / WebSocket
Redis
MySQL / PostgreSQL
Docker
Linux
Cloud
~~~

如果一个 Agent 岗只写“熟悉大模型、会 Prompt”，技术深度通常很难从 JD 判断，需要面试时进一步确认实际工作内容。

### 11.5 Java 后端岗仍然要准备的核心

Agent 项目不能替代 Java 基础。

至少保证：

~~~text
Java
├── 集合
├── 泛型
├── 异常
├── JVM 基础
├── 并发基础
└── 常见 IO

Spring
├── IOC / DI
├── AOP
├── Spring MVC
├── Spring Boot
├── Transaction
└── Validation / Exception Handler

Database
├── Index
├── Transaction
├── Isolation
├── MVCC
├── SQL Optimization
└── Redis

Engineering
├── HTTP
├── Git
├── Linux
├── Docker
├── Log / Metrics
└── Basic System Design
~~~

### 11.6 Agent 岗需要额外补的核心

~~~text
LLM
├── Token / Context Window
├── Temperature
├── Streaming
├── Structured Output
└── Function Calling

Agent
├── ReAct
├── Tool Loop
├── Session / State
├── Memory
├── MCP
├── Subagent
└── Failure Recovery

RAG
├── Chunking
├── Embedding
├── Vector Search
├── BM25
├── Hybrid
├── Rerank
└── Citation

Evaluation
├── Retrieval Recall@k
├── Grounding
├── Citation Accuracy
├── Task Success
├── Latency
└── Cost
~~~

### 11.7 项目组合建议

最有性价比的组合：

~~~text
项目 A：Java 后端项目
→ 展示 Spring / MySQL / Redis / 事务 / 缓存 / API

项目 B：ResearchPilot Agent
→ 展示 Nanobot / MCP / RAG / Eval / Backend Engineering
~~~

如果时间有限，ResearchPilot 可以增加 Java Control Plane，使两个方向形成关联。

### 11.8 简历不要堆关键词

低质量：

> 熟悉 RAG、MCP、Agent、LangChain、Redis、MySQL、Docker、K8s……

高质量：

> 将论文检索服务封装为 MCP Tool 接入 Nanobot AgentRunner；使用 Vector+BM25 Hybrid Retrieval，并基于人工标注 Query 以 Recall@5/MRR 做回归评测；对 Retrieval Result 加 Redis Cache，并通过 corpus_version 防止索引升级后的脏缓存。

关键词必须落到：

~~~text
做了什么
为什么
怎么实现
怎么验证
结果怎样
~~~

### 11.9 面试准备：不要把 Agent 面试和后端面试割裂

Agent Interview 也经常追 Backend：

- HTTP Streaming
- Async
- Queue
- Redis
- Database
- Cache Consistency
- Rate Limit
- Idempotency
- Docker
- Observability

Backend Interview 也越来越可能问：

- 你怎么调用 LLM？
- Agent 与 Workflow 区别？
- RAG 怎么做？
- MCP 是什么？
- AI 功能怎么落到现有系统？

最好的状态是：

> 后端基本盘稳定，Agent 作为差异化工程能力。

### 11.10 投递时如何判断岗位是否值得

不要只看公司大小。

可以从五个维度判断：

| 维度 | 观察点 |
|---|---|
| 工作内容 | 真做服务/Agent/RAG，还是纯标注/Prompt |
| Mentor | 是否有明确工程指导 |
| 技术栈 | 是否能积累可迁移能力 |
| 实习周期 | 与学业、秋招冲突多大 |
| 品牌/业务 | 对下一段经历是否有帮助 |

第一段实习的核心价值通常是：

~~~text
真实代码库
Code Review
真实协作
线上问题
工程规范
可验证产出
~~~

### 11.11 8 周求职准备模板

#### Week 1-2

~~~text
Java 基础复习
MySQL / Redis
算法每日 1-2 题
Nanobot 1-8 章
ResearchPilot Vector MVP
~~~

#### Week 3-4

~~~text
Spring 高频八股
MCP + Skill
ResearchPilot MCP Integration
开始投递
每周至少 2 次模拟面试
~~~

#### Week 5-6

~~~text
Hybrid Retrieval
Eval
Docker
Backend System Design
持续面试
根据真实面试问题补短板
~~~

#### Week 7-8

~~~text
项目性能/稳定性
简历量化
面试复盘
扩大投递
不要等项目“完美”才找实习
~~~

### 11.12 最终求职 Checklist

~~~text
[ ] 1 分钟自我介绍
[ ] 3 分钟项目介绍
[ ] 10 分钟项目深挖
[ ] Java / Python 基础
[ ] MySQL / Redis
[ ] HTTP / Linux / Git
[ ] 常见算法题
[ ] AgentLoop / AgentRunner 能白板画
[ ] MCP 能解释 Host/Client/Server
[ ] RAG 有 Eval，不只是 Demo
[ ] 会讲一个真实 Failure Case
[ ] 会讲一个性能优化
[ ] 会讲一个安全边界
[ ] 每次面试都有复盘记录
~~~


## 总结

2026 年的 AI Agent 就业市场特点：

1. **需求旺盛**：Agent 从概念到产品的过渡期，人才供不应求
2. **技能溢价**：有 Agent 框架实战经验（特别是源码级理解）的候选人明显溢价
3. **MCP 是新高地**：MCP 协议经验正在成为差异化竞争力
4. **复合型吃香**：「懂算法 + 会工程 + 理解业务」的全栈型人才最受欢迎
5. **学习路径清晰**：从 Nanobot 源码入手理解 Agent → 通过实战项目深化理解 → MCP 理解工具生态

> 💡 **核心建议**：不要只做「API Wrapper Engineer」（套壳工程师），要做理解原理、能设计系统、能解决问题的 Agent 工程师。本学习项目（learn-nanobot）就是帮你从「会用」到「会造」的桥梁。

---

*上一章：[第13章 面试八股文](../13-interview-bagua/README.md)*
*下一章：[第15章 简历模板](../15-resume-template/README.md)*
