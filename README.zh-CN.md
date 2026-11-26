# Temporal Jacobians｜时间雅可比

[English](README.md) · [在线交互页面](https://m0m0ko.github.io/temporal-jacobians-companion/) · [归档结果](source-data/analysis_summary.json) · [任务 fMRI 使用说明](docs/task-fmri.md)

论文 *From prediction to mechanism in psychoradiology: validation of recurrent neural networks using temporal Jacobians* 的配套代码与交互页面。

## 研究问题

循环模型能够预测行为，也能预测对自身状态施加扰动后的输出变化，这是否说明它恢复了产生数据的真实动力学？

我们分别检验行为预测、模型内干预预测和生成机制恢复。仓库提供时间雅可比计算、公开结果的交互复核，以及事件对齐任务 fMRI 编码分析工具。

## 主要发现

| 检验 | 结果 |
| --- | --- |
| 已知生成系统的测量恢复 | 精确测量条件下，**60/60** 个模拟队列通过恢复检验。 |
| 拟合模型的响应预测与机制恢复 | 有限扰动 R² 和方向检验均通过，训练模型的完整生成机制恢复为 **3/60**。 |
| 人体行为预测的等效性 | 在 **109 名参与者、73,219 个共同事件**上，**0/24** 组架构集成比较达到原等效标准。 |

这些结果区分了预测模型响应与恢复生成机制。人体证据来自行为分析；任务 fMRI 工具提供模拟示例与真实数据接口。结果来源见[汇总](source-data/analysis_summary.json)和[等效比较表](source-data/figure4b_architecture_equivalence.csv)。

## 快速上手

### 在浏览器中查看结果

[打开交互页面](https://m0m0ko.github.io/temporal-jacobians-companion/)，或下载源码 ZIP 后在本地浏览器打开 `index.html`。

| 按钮 | 内容 |
| --- | --- |
| Recompute recovery summary | 对冻结公开表重新应用五项恢复标准，汇总精确测量、扰动检验和完整机制恢复 |
| Check behavioral equivalence | 使用归档的参与者 bootstrap 区间，重新应用原等效规则 |
| Run example | 模拟二状态系统，比较预测和重新计算的有限变化，并检查仿射状态坐标变换下的不变性 |

前两个按钮复核公开表与判定规则。完整模型拟合和参与者级重采样使用原分析流程及冻结输入。

### 运行 Python 示例

需要 Python 3.10 或更高版本。以下安装命令固定到发布版本 `v0.1.0`：

```bash
python -m pip install "temporal-jacobians[fmri] @ git+https://github.com/M0M0KO/temporal-jacobians-companion.git@v0.1.0"
temporal-jacobians demo --output demo-output
```

示例生成模拟脑区时间序列，估计逐试次 beta，从已知二状态系统计算几何特征，并在 3 名留出模拟参与者上比较两个编码器。模拟信号被构造为与几何特征相关，用于演示分析流程。

| 输出 | 内容 |
| --- | --- |
| `predictors.csv` | 事件、参与者与预测变量 |
| `betas.npz` | 事件级 beta、事件 ID 和脑区 ID |
| `holdout.txt` | 留出模拟参与者 |
| `encoding.json` | 编码比较与参与者级结果 |

## 使用自己的任务 fMRI 数据

准备已预处理的 4D BOLD NIfTI、同网格的 3D 整数标签图谱、BIDS `events.tsv` 和以秒计的 TR。先估计事件级脑区 beta，再比较基线编码器与增加雅可比特征的编码器：

```bash
temporal-jacobians bold --bold sub-01_preproc_bold.nii.gz --atlas atlas_in_bold_grid.nii.gz --events sub-01_events.tsv --tr 1.5 --run-id sub-01_task-flanker_run-1 --output run1.npz
temporal-jacobians compare --betas run1.npz run2.npz run3.npz run4.npz --predictors predictors.tsv --holdout holdout.txt --baseline task_indicator reaction_time --features g00 g01 g11 --alpha 100 --output comparison.json
```

第二条命令使用已准备的多个运行和预测变量表。完整字段、事件匹配、混杂回归量、体积剔除及 Python 接口见[任务 fMRI 使用说明（英文）](docs/task-fmri.md)。

模型按事件 ID 精确对齐，在开发参与者上拟合，在独立留出参与者上评分；区间以参与者为统计单位。正则化参数、特征定义和状态协方差在读取留出结果前固定。预处理、空间配准、图谱覆盖和 QC 由数据分析流程负责。

## 复现范围

| 内容 | 仓库提供 | 其他所需输入 |
| --- | --- | --- |
| 已发表汇总结果复核 | 冻结源表、判定规则和交互页面 | 完整模型拟合与参与者重采样使用原分析输入 |
| 二状态与任务 fMRI 演示 | 生成数据和可运行示例 | 无需人体影像 |
| 自有任务 fMRI 编码分析 | 事件估计、雅可比特征和参与者留出比较接口 | 经 QC 的影像、图谱、事件、预测变量及预先固定的划分 |

## 仓库结构

| 位置 | 内容 |
| --- | --- |
| [`index.html`](index.html) | 可离线使用的单文件交互页面 |
| [`template.html`](template.html) · [`build_browser.py`](build_browser.py) | 页面模板与构建脚本 |
| [`source-data/`](source-data/) | 恢复、行为等效及汇总结果 |
| [`src/temporal_jacobians/`](src/temporal_jacobians/) | 雅可比、几何特征、事件估计和编码比较 |
| [`docs/task-fmri.md`](docs/task-fmri.md) | 任务 fMRI 输入契约和 Python 接口 |

## 数据

公开表与汇总字段来自[原始代码与数据仓库的固定提交 6233df2](https://github.com/pwa209/Temporal-Jacobians-predict-fitted-model-interventions-without-recovering-known-latent-dynamics/tree/6233df2584e2176fe65794a3b741c8bda2c98605)。在源码根目录运行 `python build_browser.py` 可从这些表重新生成交互页面。

## 引用

引用研究时，请使用本页开头的论文题目。引用代码或交互页面时，请注明[仓库地址](https://github.com/M0M0KO/temporal-jacobians-companion)及所用提交或发布版本。

## 许可

代码与软件文档采用 [MIT 许可证](LICENSE)。`source-data/` 中的归档结果及嵌入 `index.html` 的副本遵循原始来源条款。
