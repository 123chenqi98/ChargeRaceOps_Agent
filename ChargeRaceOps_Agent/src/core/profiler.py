"""
BDM 多维能力画像系统

6大维度打分：
1. 目标达成能力（单计/双计/扫码完成度）
2. 增长动能（近N小时增速）
3. 执行响应速度（预警跟进率、响应时长）
4. 团队均衡度（CM间极差倒数）
5. 过程稳定性（连续预警次数倒数）
6. 历史成长性（环比提升 pct）

输出：
- 每个BDM的画像分数 + 等级标签
- 排名榜
- 改进建议
"""

import json
import math
from datetime import datetime
from typing import List, Dict


DIMENSIONS = [
    {'key': 'achievement',  'name': '目标达成',   'weight': 0.25, 'desc': '三大KPI完成度综合'},
    {'key': 'momentum',     'name': '增长动能',   'weight': 0.18, 'desc': '近3小时核销增速'},
    {'key': 'response',     'name': '执行响应',   'weight': 0.17, 'desc': '预警跟进率 + 平均响应时长'},
    {'key': 'balance',      'name': '团队均衡',   'weight': 0.15, 'desc': 'CM间完成度的均衡程度'},
    {'key': 'stability',    'name': '过程稳定',   'weight': 0.12, 'desc': '预警频次 / 波动水平'},
    {'key': 'growth',       'name': '成长潜力',   'weight': 0.13, 'desc': '环比上一场冲锋的进步幅度'},
]


LEVEL_BADGES = [
    {'min': 90, 'label': 'S·卓越先锋', 'color': '#facc15', 'emoji': '🏆'},
    {'min': 80, 'label': 'A·优秀骨干', 'color': '#38ef7d', 'emoji': '⭐'},
    {'min': 70, 'label': 'B·稳步发展', 'color': '#4facfe', 'emoji': '👍'},
    {'min': 60, 'label': 'C·待加速',   'color': '#ffa751', 'emoji': '⚡'},
    {'min': 0,  'label': 'D·需帮扶',   'color': '#f5576c', 'emoji': '🆘'},
]


ADVICE_LIB = {
    'achievement_low': '目标达成偏弱，建议：①提前3天做CM层面一对一目标对齐；②每日早/中/晚3次standup拉齐进度',
    'momentum_low':    '增长动能不足，建议：①重点关注TOP3门店的午晚高峰核销；②设立每2小时的最小核销里程碑',
    'response_low':    '执行响应偏慢，建议：①给预警设置"30分钟内必须处理"的SLA；②指定值班人员盯预警看板',
    'balance_low':     '团队均衡度差，建议：①优秀CM和落后CM结对子"陪跑"；②重新分配大客户资源给落后CM',
    'stability_low':   '过程波动大，建议：①每日复盘异常触发原因；②把"低预警频次"作为BDM考核项',
    'growth_low':      '成长停滞，建议：①参考S/A级BDM打法手册；②每周一次横向经验分享会',
}


class BDMProfiler:
    """BDM 多维能力画像"""

    def __init__(self, alert_tracker=None, metrics_history=None):
        self.tracker = alert_tracker
        self.history = metrics_history or {}
        self._bdm_static = {
            '王鸿鹏': {'city': '杭州一区', 'seniority': 0.3, 'cm_count': 4},
            '朱超颖': {'city': '杭州一区', 'seniority': 2.1, 'cm_count': 5},
            '李明':   {'city': '杭州二区', 'seniority': 1.0, 'cm_count': 4},
            '张伟':   {'city': '绍兴一区', 'seniority': 3.2, 'cm_count': 6},
            '陈静':   {'city': '金华一区', 'seniority': 1.5, 'cm_count': 3},
            '刘强':   {'city': '台州一区', 'seniority': 0.5, 'cm_count': 4},
            '黄磊':   {'city': '温州一区', 'seniority': 2.8, 'cm_count': 5},
            '周婷':   {'city': '宁波一区', 'seniority': 2.0, 'cm_count': 4},
        }

    # ========== 公开入口 ==========

    def build_profile(self, bdm_name: str, snapshot: dict = None) -> dict:
        """生成单个 BDM 的完整画像"""
        snapshot = snapshot or self._default_snapshot(bdm_name)

        dim_scores = self._compute_dimension_scores(bdm_name, snapshot)

        dim_by_key = {d['key']: d for d in DIMENSIONS}
        total_score = round(
            sum(dim_scores[k]['score'] * dim_by_key[k]['weight'] for k in dim_scores),
            1
        )

        badge = self._pick_badge(total_score)
        advices = self._generate_advices(dim_scores)

        return {
            'name': bdm_name,
            'city': self._bdm_static.get(bdm_name, {}).get('city', '-'),
            'seniority': self._bdm_static.get(bdm_name, {}).get('seniority', 1),
            'cm_count': self._bdm_static.get(bdm_name, {}).get('cm_count', 4),
            'snapshot': snapshot,
            'dimensions': [
                {
                    'key': d['key'],
                    'name': d['name'],
                    'desc': d['desc'],
                    'weight': d['weight'],
                    'score': round(dim_scores[d['key']]['score'], 1),
                    'grade': dim_scores[d['key']]['grade'],
                }
                for d in DIMENSIONS
            ],
            'total_score': total_score,
            'badge_label': badge['label'],
            'badge_color': badge['color'],
            'badge_emoji': badge['emoji'],
            'advices': advices,
            'generated_at': datetime.now().isoformat(),
        }

    def build_all_profiles(self, snapshots: dict = None) -> List[dict]:
        """生成全部 BDM 画像并排名"""
        profiles = [
            self.build_profile(name, (snapshots or {}).get(name) if snapshots else None)
            for name in self._bdm_static.keys()
        ]
        profiles.sort(key=lambda p: -p['total_score'])
        for rank, p in enumerate(profiles, 1):
            snap = (snapshots or {}).get(p['name']) if snapshots else None
            p['rank'] = rank
            p['prev_rank'] = (snap or {}).get('prev_rank', rank + self._random_offset())
        return profiles

    def export_report(self, profiles: List[dict]) -> str:
        """导出 Markdown 格式的团队画像报告"""
        lines = ['# 🏅 BDM 团队多维能力画像报告', '']
        lines.append(f'> 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}')
        lines.append(f'> 覆盖BDM：{len(profiles)} 人')
        lines.append('')

        avg_score = round(sum(p['total_score'] for p in profiles) / len(profiles), 1)
        s_count = sum(1 for p in profiles if p['total_score'] >= 90)
        a_count = sum(1 for p in profiles if 80 <= p['total_score'] < 90)
        d_count = sum(1 for p in profiles if p['total_score'] < 60)

        lines.append('## 📊 团队总览')
        lines.append(f'- 平均分：**{avg_score}**')
        lines.append(f'- S/A级占比：**{round((s_count+a_count)/len(profiles)*100, 1)}%**（{s_count+a_count}/{len(profiles)}）')
        lines.append(f'- D级需帮扶：**{d_count}人**（建议专项提升计划）')
        lines.append('')

        lines.append('## 🏆 综合排行榜')
        lines.append('| 排名 | 姓名 | 城市 | 分数 | 等级 | CM数 | 标签 |')
        lines.append('|------|------|------|------|------|------|------|')
        for p in profiles:
            diff = p.get('prev_rank', p['rank']) - p['rank']
            trend = '↑' if diff > 0 else ('↓' if diff < 0 else '→')
            lines.append(
                f"| {p['rank']} {trend} | **{p['name']}** | {p['city']} | "
                f"**{p['total_score']}** | {p['badge_emoji']} {p['badge_label']} | {p['cm_count']} | "
                f"{'/'.join([d['grade'] for d in p['dimensions']])} |"
            )
        lines.append('')

        lines.append('## 👥 TOP3 深度画像')
        for p in profiles[:3]:
            lines.append(f"### {p['badge_emoji']} No.{p['rank']} {p['name']}（{p['city']}）")
            lines.append(f"综合得分：**{p['total_score']}** —— {p['badge_label']}")
            lines.append('')
            lines.append('| 维度 | 得分 | 权重 |')
            lines.append('|------|------|------|')
            for d in p['dimensions']:
                lines.append(f"| {d['name']} | {d['grade']} **{d['score']}** | ×{d['weight']}")
            lines.append('')
            if p['advices']:
                lines.append('**💡 提升建议**：')
                for a in p['advices'][:2]:
                    lines.append(f'- {a}')
            lines.append('')

        lines.append('## 🆘 需帮扶对象专项提升建议')
        for p in profiles[-min(2, len(profiles)):]:
            lines.append(f"### {p['badge_emoji']} {p['name']}（分数 {p['total_score']}）")
            for a in p['advices']:
                lines.append(f'- {a}')
            lines.append('')

        return '\n'.join(lines)

    # ========== 内部逻辑 ==========

    def _default_snapshot(self, name: str) -> dict:
        """无外部快照时，生成演示用分数（每次略有波动）"""
        seed = sum(ord(c) for c in name)
        import random
        rng = random.Random(seed)

        base = {
            '王鸿鹏': 40, '刘强': 55, '李明': 68,
            '陈静': 74, '黄磊': 79, '周婷': 82,
            '朱超颖': 86, '张伟': 91,
        }.get(name, 70)

        return {
            'single_rate':  min(99, max(5,  base + rng.randint(-8, 8))),
            'double_rate':  min(99, max(5,  base + 3 + rng.randint(-6, 6))),
            'scan_rate':    min(99, max(3,  base - 5 + rng.randint(-10, 5))),
            'speed_3h':     max(0, 0.5 + rng.random() * 3),
            'ack_rate':     min(99, max(30, base + 10 + rng.randint(-8, 8))),
            'response_min': max(5, 120 - base + rng.randint(-10, 30)),
            'cm_gap':       max(5, 100 - base + rng.randint(-10, 20)),
            'alert_count_7d': max(0, int((100 - base) / 3 + rng.randint(-2, 4))),
            'mom_growth_pct': rng.randint(-8, 12),
        }

    def _compute_dimension_scores(self, name: str, snap: dict) -> dict:
        """6 维度打分（0~100）"""
        return {
            'achievement': self._d_achievement(snap),
            'momentum':    self._d_momentum(snap),
            'response':    self._d_response(snap),
            'balance':     self._d_balance(snap),
            'stability':   self._d_stability(snap),
            'growth':      self._d_growth(snap),
        }

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 90: return 'S'
        if score >= 80: return 'A'
        if score >= 70: return 'B'
        if score >= 60: return 'C'
        return 'D'

    @staticmethod
    def _d_achievement(snap: dict) -> dict:
        sr = snap.get('single_rate', 70)
        dr = snap.get('double_rate', 70)
        sc = snap.get('scan_rate', 65)
        s = round(min(100, (sr * 0.35 + dr * 0.35 + sc * 0.30)), 1)
        return {'score': s, 'grade': BDMProfiler._grade(s)}

    @staticmethod
    def _d_momentum(snap: dict) -> dict:
        speed = snap.get('speed_3h', 1.0)
        # 3.0 => 100分，0 => 0
        s = round(min(100, max(0, speed / 3.0 * 100)), 1)
        return {'score': s, 'grade': BDMProfiler._grade(s)}

    @staticmethod
    def _d_response(snap: dict) -> dict:
        ack = snap.get('ack_rate', 70)
        minutes = snap.get('response_min', 60)
        # ack权重0.6，响应时长0.4
        min_score = max(0, 100 - minutes / 4)
        s = round(ack * 0.6 + min_score * 0.4, 1)
        return {'score': s, 'grade': BDMProfiler._grade(s)}

    @staticmethod
    def _d_balance(snap: dict) -> dict:
        gap = snap.get('cm_gap', 30)
        # gap=10 => 100, gap=60 => 0
        s = round(max(0, min(100, 100 - (gap - 10) * 2)), 1)
        return {'score': s, 'grade': BDMProfiler._grade(s)}

    @staticmethod
    def _d_stability(snap: dict) -> dict:
        c = snap.get('alert_count_7d', 5)
        # 0=>100, 20=>0
        s = round(max(0, min(100, 100 - c * 5)), 1)
        return {'score': s, 'grade': BDMProfiler._grade(s)}

    @staticmethod
    def _d_growth(snap: dict) -> dict:
        g = snap.get('mom_growth_pct', 0)
        # -10 => 0, +15 => 100
        s = round(max(0, min(100, 50 + g * 4)), 1)
        return {'score': s, 'grade': BDMProfiler._grade(s)}

    @staticmethod
    def _pick_badge(score: float):
        for b in LEVEL_BADGES:
            if score >= b['min']:
                return b
        return LEVEL_BADGES[-1]

    @staticmethod
    def _generate_advices(dim_scores: dict) -> List[str]:
        advices = []
        mapping = [
            ('achievement', 'achievement_low', 70),
            ('momentum',    'momentum_low',    65),
            ('response',    'response_low',    65),
            ('balance',     'balance_low',     65),
            ('stability',   'stability_low',   60),
            ('growth',      'growth_low',      55),
        ]
        for key, lib_key, threshold in mapping:
            if dim_scores[key]['score'] < threshold:
                advices.append(f'【{dim_scores[key]["grade"]} {key}】' + ADVICE_LIB[lib_key])

        if len(advices) < 2:
            advices.append('整体表现良好，建议把打法沉淀为经验手册，帮助团队其他成员复制')
        return advices[:3]


    @staticmethod
    def _random_offset():
        import random
        return random.randint(-1, 1)


def random_offset():
    import random
    return random.randint(-1, 1)
