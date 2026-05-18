# 知识库索引

最后更新：2026-05-15

这是整个知识库的内容导向目录。每次摄入后 LLM 都会更新它。回答查询时以此为入口。

---

## 综合论述

- [[微服务部署与路由优化概览]] — 部署-路由-资源分配三元耦合全景、延迟模型、求解算法谱系、创新方向

---

## 来源（16）

- [[mint-managed-infrastructure-training-serving-millions-llms|MinT: 百万级 LoRA 策略训练与服务基础设施]] — LoRA adapter revision 为核心管理单元，Scale Up/Down/Out 三轴扩展，训练-服务交接加速 18.3 倍，百万策略目录，冷加载 8.5-8.7 倍 | 2026-05-13 | #基础设施 #LoRA #GRPO #MoE #服务部署
- [[openclaw-rl-turning-daily-usage-into-training-signals|OpenClaw-RL: 把日常使用变成训练信号]] — next-state 信号实时转化在线训练，混合 RL（evaluative + directive）+ overlap-guided hint selection，零中断推理，统一个人/通用 Agent RL 训练 | 2026-03 | #AgentRL #在线学习 #混合RL
- [[agent0-bootstrapping-from-zero-data|Agent0: 从零数据自举起来]] — 双 Agent 协同进化 + 工具集成推理，零人工数据自举，ADPO 模糊感知优化，Qwen3-8B 数学+18% 通用+24% | 2025-11 | #Agent #自演化 #零数据 #协同进化
- [[metaclaw-continuous-evolution-in-production|MetaClaw: 在生产环境里持续进化不停机]] — 技能驱动快速适配（梯度无关）+ 机会主义策略优化（RL+Cloud LoRA），无停机持续元学习，Kimi-K2.5 准确率 21.4%→40.6% | 2026-03 | #元学习 #持续学习 #生产部署 #技能库
- [[evolver-from-trajectories-to-principles|EvolveR: 从轨迹到原则的闭环]] — 经验驱动的 Agent 策略自演化框架，轨迹提取原则 → 自蒸馏训练 → 新轨迹循环 | 2025-10 | #Agent #自演化 #自蒸馏 #经验学习
- [[mem0-building-production-ready-ai-agents|Mem0: Building Production-ready AI Agents with Scalable Long-term Memory]] — 文本记忆+图记忆双架构，LOCOMO 全面领先，p95 延迟比全上下文低 91%，token 成本节省 90%+ | 2025-04 | #LLM记忆 #Agent记忆 #图记忆 #生产部署
- [[titans-learning-to-memorize-at-test-time|Titans: Learning to Memorize at Test Time]] — 神经长期记忆 + 测试时学习 + Titans 架构家族（MAC/MAG/MAL），全面超越 Transformer 和线性循环模型 | 2024 | #LLM记忆 #测试时学习 #序列模型
- [[context-rot-how-increasing-input-tokens-impacts-llm|Context Rot: How Increasing Input Tokens Impacts LLM Performance]] — Chroma 技术报告，18 个主流 LLM 的系统评估，揭示仅增加输入长度就会导致性能非均匀退化的"上下文腐烂"现象 | 2025-07-14 | #长上下文 #LLM评估 #上下文退化
- [[llms-get-lost-in-multi-turn-conversation|LLMs Get Lost in Multi-turn Conversation]] — 20万+对话大规模实验揭示所有主流 LLM 在多轮欠规范对话中平均性能下降 39%，能力-可靠性分解，"对话迷失"现象 | 2025-05-09 | #LLM评估 #多轮对话 #可靠性
- [[lora-low-rank-adaptation|LoRA: Low-Rank Adaptation of Large Language Models]] — 冻结预训练权重 + 注入低秩分解矩阵 BA，10,000× 减少可训练参数，零推理延迟的参数高效微调 | 2021-10 | #参数高效微调 #低秩分解 #Transformer
- [[delta-mem-efficient-online-memory|δ-mem: Efficient Online Memory for LLMs]] — 冻结骨干 + 8×8 在线关联记忆状态 + delta-rule 低秩修正，轻量高效 LLM 记忆机制 | 2026-05-13 | #LLM记忆 #在线学习 #delta-rule
- [[swarm-ide|Swarm-IDE: 自组织的 Agent 蜂群]] — 去中心化多 Agent 协作平台，create+send 极简原语，动态嵌套 + 实时 Graph 可视化 + MCP 技能系统 | 2026-01-02 | #Agent #多Agent #开源 #MCP
- [[agent-world|Agent-World: Scaling Real-World Environment Synthesis for Evolving General Agent Intelligence]] — 1978 环境 + 19822 工具的自我进化 Agent 训练平台，8B/14B 超越闭源模型 | 2026-04 | #Agent #RL #MCP
- [[gstc-zero-cost-proxy-nas|Zero-Cost Proxy NAS-Driven Collaborative Deployment Optimization]] — GSTC 零成本代理 + JCQDA 部署 + LAMRA 动态替换，AI 服务全生命周期优化 | 2026-04-21 | #NAS #微服务 #精读
- [[joint-deployment-request-routing-microservice-tpds|Joint Deployment and Request Routing for Microservice Call Graphs]] — GMDA-RMPR 两阶段启发式，联合优化微服务部署与路由 | 2023-11 | #微服务 #排队网络
- [[joint-task-offloading-resource-allocation-model-placement-6g|Joint Task Offloading, Resource Allocation and Model Placement for AIaaS in 6G]] — DA-MAB 策略，边-网-云 AIaaS 两时间尺度优化 | 2024-11 | #6G #AIaaS

---

## 实体（53）

- [[Peng Xia]] — UNC-Chapel Hill，Agent0/MetaClaw 共同一作，自演化 Agent 研究方向
- [[Huaxiu Yao]] — UNC-Chapel Hill 教授，Agent0/MetaClaw 通讯作者，AIMing Lab
- [[Cihang Xie]] — UC Santa Cruz 教授，MetaClaw 共同作者
- [[Zeyu Zheng]] — UC Berkeley，MetaClaw 共同作者
- [[Yinjie Wang]] — Gen-Verse，OpenClaw-RL 共同一作
- [[Xuyang Chen]] — Gen-Verse，OpenClaw-RL 共同一作
- [[Xiaolong Jin]] — Gen-Verse，OpenClaw-RL 共同一作
- [[Ling Yang]] — Gen-Verse，OpenClaw-RL 通讯作者
- [[Mengdi Wang]] — OpenClaw-RL 通讯作者，RL 理论与优化
- [[UNC-Chapel-Hill]] — 美国顶尖研究型大学，Agent0/MetaClaw 第一作者机构
- [[UC-Santa-Cruz]] — 加州大学圣克鲁兹分校，MetaClaw 合作机构
- [[Carnegie-Mellon-University]] — 卡内基梅隆大学，MetaClaw 合作机构
- [[UC-Berkeley]] — 加州大学伯克利分校，MetaClaw 合作机构
- [[Gen-Verse]] — AI 研究团队，OpenClaw-RL 第一署名机构
- [[Salesforce-Research]] — Salesforce AI 研究部门，Agent0 合作机构
- [[Stanford-University]] — 斯坦福大学，Agent0 合作机构
- [[OpenClaw]] — 开源 Agent 平台，OpenClaw-RL/MetaClaw 基础设施
- [[AutoResearchClaw]] — MetaClaw 论文中的自动化研究 Agent
- [[Rong Wu]] — 浙江大学 & 上海人工智能实验室，EvolveR 共同一作
- [[Xiaoman Wang]] — 华东师范大学，EvolveR 共同一作
- [[Botian Shi]] — 上海人工智能实验室，EvolveR 通讯作者
- [[上海人工智能实验室]] — 中国 AI 研究，EvolveR 主要研究机构
- [[浙江大学]] — EvolveR 第一作者机构
- [[Mem0]] — AI Agent 记忆基础设施公司（后更名为 Letta），Mem0/Mem0g 记忆架构提出者
- [[Deshraj Yadav]] — Mem0/Letta 联合创始人、CEO，Mem0 论文通讯作者
- [[Prateek Chhikara]] — Mem0/Letta 研究员，Mem0 论文共同一作
- [[Ali Behrouz]] — Google Research 研究科学家，Titans 一作，神经记忆模块和序列建模
- [[Peilin Zhong]] — Google Research 研究科学家，Titans 共同作者，高效注意力机制
- [[Vahab Mirrokni]] — Google Research Distinguished Scientist，Titans 共同作者，算法与 ML 系统
- [[Google Research]] — Google 研究部门，Transformer、BERT、Titans 等成果产出机构
- [[Chroma]] — 向量数据库公司，Context Rot 技术报告的发布机构
- [[Kelly Hong]] — Chroma 研究员，Context Rot 第一作者
- [[Anton Troynikov]] — Chroma 研究员，Context Rot 共同作者
- [[Jeff Huber]] — Chroma 研究员，Context Rot 共同作者
- [[Mind Lab]] — 跨机构研究合作团队，专注 LLM 记忆和 Agent 系统
- [[Jingdi Lei]] — 南洋理工大学，δ-mem 共同一作/通讯作者，LLM 注意力与记忆
- [[Di Zhang]] — 复旦大学，δ-mem 共同一作/通讯作者，LLM 记忆与 Agent
- [[Soujanya Poria]] — 南洋理工大学教授，δ-mem 通讯作者，DECLARE Lab
- [[南洋理工大学]] — 新加坡顶尖研究型大学，δ-mem 第一署名机构
- [[复旦大学]] — 中国顶尖研究型大学，δ-mem 第二署名机构
- [[Swarm-IDE]] — 开源去中心化多 Agent 协作平台，create+send 极简原语，支持动态嵌套与实时 Graph 可视化
- [[Guanting Dong]] — 中国人民大学博士生，Agent RL / 工具使用训练方向
- [[Zhicheng Dou]] — 中国人民大学教授，Agent 系统方向
- [[中国人民大学]] — 高瓴人工智能学院
- [[字节跳动 Seed]] — 字节 AI 研究团队，Doubao-Seed 模型
- [[Menglan Hu]] — 华中科技大学副教授，三篇论文核心通讯作者
- [[Kai Peng]] — 华中科技大学教授，论文1和2共同作者
- [[Yi Hu]] — 华中科技大学博士生，论文1和2共同作者
- [[Bharadwaj Veeravalli]] — 新加坡国立大学教授，TPDS 论文共同作者
- [[华中科技大学]] — 论文1和2的主要研究机构
- [[Yue Yang]] — 华中科技大学研究生，GSTC 论文共同作者
- [[Jing Lu]] — 华中科技大学研究生，GSTC 论文共同作者
- [[北京邮电大学]] — 论文3的主要研究机构

---

## 概念（45）

- [[Adapter-Revision-Path|Adapter-Revision Path]] — 基座常驻，仅 LoRA adapter 在训练-服务全生命周期流转的设计模式
- [[Packed-MoE-LoRA-Tensors|Packed MoE LoRA Tensors]] — 将碎片化 MoE LoRA 小对象打包为紧凑连续表示，冷加载加速 8.5-8.7 倍
- [[Policy-Catalog|Policy Catalog]] — 百万级策略可寻址目录，三层缓存（目录/CPU/GPU）分离可寻址性与同时驻留
- [[混合RL-Hybrid-RL|混合 RL]] — 统一评估性信号（过程奖励模型）+ 指导性信号（hints）的 RL 训练目标，OpenClaw-RL 核心
- [[Overlap-Guided-Hint-Selection]] — 基于覆盖率贪心选择互补 hints，避免冗余训练信号
- [[Log-Probability-Difference-Clip]] — 对数概率差值裁剪，稳定 teacher-student RL 训练
- [[Next-State-Signal]] — 用户回复、工具输出、终端/GUI 状态变化等 Agent 交互后的自然反馈信号
- [[ADPO-Ambiguity-Dynamic-Policy-Optimization|ADPO]] — 模糊性动态策略优化，处理多解问题的 RL 目标，Agent0 核心
- [[协同进化课程学习]] — 课程 Agent 与执行 Agent 从同一基座协同进化，互相提供训练压力
- [[零数据自举]] — 无需任何人工标注数据，完全从 LLM 自身生成训练信号启动学习
- [[工具集成推理-TIR]] — Agent 推理过程中调用外部工具增强推理能力
- [[持续元学习]] — 将 MAML 内外循环映射到技能适配/策略优化的在线元学习范式
- [[技能代际版本化]] — 支撑-查询分离的数据治理机制，按代际管理技能库
- [[经验驱动自演化]] — Agent 从交互轨迹中提取可复用原则并自我改进的范式
- [[自蒸馏（Agent策略自蒸馏）]] — Agent 用自身生成的策略原则作为训练数据的蒸馏方法
- [[对话迷失现象（lost-in-conversation）]] — LLM 在多轮欠规范对话中系统性偏离用户真实需求，性能平均下降 39%
- [[指令分片（instruction-sharding）]] — 将复杂指令拆分为多轮对话的评估方法论，五个属性定义
- [[能力-可靠性分解（aptitude-reliability）]] — 将 LLM 性能分解为能力（最佳表现）和可靠性（一致性）两个维度的分析框架
- [[文本记忆]] — 将显著信息提取为自然语言句子存储，Mem0 的核心记忆形式
- [[图记忆]] — 以实体-关系三元组构成的有向标记图存储信息，Mem0g 的核心记忆形式
- [[LOCOMO]] — 长对话记忆评估基准，10 段扩展多会话对话 + ~2000 问题
- [[Titans]] — Google Research 提出的序列模型架构家族，神经长期记忆 + 短期注意力，含 MAC/MAG/MAL 三种变体
- [[Context-Rot]] — 上下文腐烂现象：仅增加输入 token 长度就会导致 LLM 性能非均匀退化
- [[LoRA]] — 低秩适配：冻结预训练权重，用低秩矩阵分解参数化权重更新，参数高效微调的经典方法
- [[δ-mem（在线关联记忆）]] — 冻结骨干 + 8×8 在线状态 + delta-rule 低秩修正的 LLM 记忆机制
- [[delta-rule-learning]] — 基于预测误差的在线学习规则，只写入差分信息
- [[Language Server Protocol (LSP)]] — 编辑器与语言服务器之间的开放标准通信协议，基于 JSON-RPC
- [[Model Context Protocol (MCP)]] — AI 模型连接外部工具的统一开放标准协议
- [[Agent RL]] — Agent 在可执行环境中通过闭环交互学习的强化学习方法
- [[GRPO]] — 无需 critic 的组相对策略优化算法
- [[POMDP]] — 部分可观测马尔可夫决策过程，Agent 交互的理论框架
- [[工具依赖图]] — 工具间参数依赖关系的有向加权图，用于任务合成
- [[神经架构搜索 (NAS)]] — 自动化神经网络架构设计
- [[零成本代理]] — 无需训练即可评估架构性能
- [[微服务调用图]] — 微服务间调用关系形成的图结构
- [[M/M/C 排队模型]] — 经典多服务台排队论模型
- [[JCQDA]] — 联合通信与队列感知部署算法，基于 M/M/C 和服务-服务器亲和的静态部署启发式
- [[LAMRA]] — 负载感知模型替换算法，Pareto 前沿 + 加权评分的动态模型版本选择
- [[Jackson 排队网络]] — 可解析求解的开放排队网络
- [[AI as a Service (AIaaS)]] — 6G 网络中的 AI 服务基础设施模式
- [[Lyapunov 优化]] — 将长期随机优化分解为短期确定性子问题
- [[混合整数非线性规划 (MINLP)]] — 联合优化问题的通用数学建模形式
- [[任务卸载]] — 将计算任务从边缘转移到资源充足的节点执行
- [[边缘计算]] — 将计算能力下沉到靠近用户的位置
- [[两时间尺度优化]] — 长期慢变量与短期快变量的协同优化

---

## 对比（0）

*（尚无对比页面。）*

---

## 草稿 & 待处理

需要扩展的页面：

*（暂无。）*

---

## 最近活动

查看 [[log/2026/05-15|今日日志]] 了解完整时间线。
