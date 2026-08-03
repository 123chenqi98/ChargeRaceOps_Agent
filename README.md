![alt text](ChargeRaceOps_Agent/img/image-2.png)
![alt text](ChargeRaceOps_Agent/img/image-3.png)
## 冲锋赛风神数据看板（私密数据）
![alt text](ChargeRaceOps_Agent/img/image-4.png)
冲锋赛过程管理 - 数据驱动业务闭环

http://localhost:8765/index.html

## 项目概述
基于数据驱动理念，为生活服务东部大区冲锋赛构建的过程管理系统。核心实现「数据采集 → 智能识别 → 精准触达 → 状态追踪 → 复盘优化」完整数据闭环。

## 核心功能

| 模块 | 文件 | 功能说明 |
|------|------|---------|
| 数据采集 | `src/core/fetch.py` | 对接风神看板API，小时级拉取BDM/CM指标数据 |
| 规则引擎 | `src/core/detector.py` | 4条预警规则（R1低完成率/R2增速停滞/R3冲刺不足/R4层级失衡） |
| 飞书推送 | `src/core/notifier.py` | 四层分层触达（大区/城市/BDM/CM），结构化卡片推送 |
| 状态追踪 | `src/core/tracker.py` | open→acknowledged→expired 三态状态机，多维表格持久化 |
| 任务调度 | `src/core/scheduler.py` | 支持 peak/warmup/daily/recap 四种调度模式 |
| 复盘报告 | `src/core/recap.py` | 自动生成结构化数据复盘，含预警覆盖率/跟进率/规则效果分析 |

## 快速开始

### 1. 安装依赖

```bash
cd ChargeRaceOps_Agent
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入实际的API凭证
```

### 3. 运行巡检（Mock模式 - 推荐先用这个测试）

```bash
python main.py run --mode manual
```

### 4. 启动定时调度

```bash
python main.py start
```

### 5. 生成复盘报告

```bash
python main.py recap --name "618冲锋赛"
```

### 6. 使用真实API

```bash
python main.py run --mode manual --real
```

## 命令行参数

| 命令 | 参数 | 说明 |
|------|------|------|
| `run` | `--mode` | 执行一次巡检，可选 manual/peak/warmup/daily |
| `start` | - | 启动定时巡检模式 |
| `recap` | `--name`, `--output` | 生成复盘报告 |
| `status` | - | 查看系统状态 |
| `--real` | - | 使用真实API（默认Mock模式） |

## 项目结构

```
ChargeRaceOps_Agent/
├── main.py                 # 主入口
├── requirements.txt        # 依赖清单
├── .env.example            # 环境变量模板
├── config/
│   ├── settings.yaml       # 配置文件（规则/指标/调度）
│   └── __init__.py         # 配置加载器
├── src/
│   ├── core/
│   │   ├── fetch.py        # 数据采集模块
│   │   ├── detector.py     # 规则引擎模块
│   │   ├── notifier.py     # 飞书推送模块
│   │   ├── tracker.py      # 状态追踪模块
│   │   ├── scheduler.py    # 任务调度模块
│   │   └── recap.py        # 复盘报告模块
│   └── __init__.py
└── logs/                   # 日志目录
```

## 预警规则说明

| 规则 | 视角 | 触发条件 | 业务价值 |
|------|------|---------|---------|
| **R1** | 总量（过去） | 完成度 < 60% | 识别长期落后的BDM/CM |
| **R2** | 动能（现在） | 连续2小时增量=0 | 识别正在掉队的BDM |
| **R3** | 预测（未来） | 预计无法完成目标 | 提前3小时主动干预 |
| **R4** | 结构（内部） | CM间极差 > 40% | 识别BDM内部分化隐患 |

## 数据流向

```
风神看板API → 数据采集 → 规则引擎 → 飞书分层推送 → 状态追踪 → 复盘报告
```

## 配置说明

编辑 `config/settings.yaml` 可调整：
- 监控指标（monitoring.metrics）
- 预警规则（rules.R1-R4）
- 推送层级（notification.layers）
- 调度模式（scheduler.peak/warmup/daily/recap）

## 实习项目亮点

1. **数据驱动的业务决策闭环** - 从"人找数据"到"数据找人"
2. **四维度预警规则体系** - 总量/动能/预测/结构四视角组合
3. **四层分层触达机制** - 大区/城市/BDM/CM差异化推送
4. **可量化的业务价值** - 异常发现时效提升4-8倍，工时节省70-80%


![alt text](ChargeRaceOps_Agent/img/image.png)

![alt text](ChargeRaceOps_Agent/img/image-1.png)