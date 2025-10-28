"""
评论引导系统 - 核心引擎
功能: 爬取分析 → AI评分 → 话术生成 → 发布调度
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import sqlite3


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    nickname: str
    comment_text: str
    video_id: str
    video_topic: str
    score: int = 0
    destination: str = ""
    travel_time: str = ""
    budget_range: str = ""
    persona: str = ""
    priority: str = ""  # A/B/C类


@dataclass
class CommentTask:
    """评论任务"""
    task_id: str
    target_user: UserProfile
    account_id: str
    role_name: str
    comment_text: str
    scheduled_time: datetime
    status: str = "pending"  # pending/published/failed
    result: Optional[Dict] = None


class CommentGuideEngine:
    """评论引导引擎"""

    def __init__(self, db_path: str = "comment_guide.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 用户表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            nickname TEXT,
            comment_text TEXT,
            video_id TEXT,
            video_topic TEXT,
            score INTEGER,
            destination TEXT,
            travel_time TEXT,
            budget_range TEXT,
            persona TEXT,
            priority TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 评论任务表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS comment_tasks (
            task_id TEXT PRIMARY KEY,
            user_id TEXT,
            account_id TEXT,
            role_name TEXT,
            comment_text TEXT,
            scheduled_time TIMESTAMP,
            status TEXT,
            published_at TIMESTAMP,
            likes INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            converted_to_dm BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)

        # 账号池表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_pool (
            account_id TEXT PRIMARY KEY,
            role_name TEXT,
            gender TEXT,
            age INTEGER,
            persona_description TEXT,
            daily_quota INTEGER DEFAULT 5,
            used_today INTEGER DEFAULT 0,
            last_used_date DATE,
            status TEXT DEFAULT 'active'
        )
        """)

        # 转化追踪表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversion_tracking (
            tracking_id TEXT PRIMARY KEY,
            user_id TEXT,
            task_id TEXT,
            dm_received_at TIMESTAMP,
            contact_exchanged BOOLEAN DEFAULT FALSE,
            handed_to_agency BOOLEAN DEFAULT FALSE,
            final_deal BOOLEAN DEFAULT FALSE,
            deal_amount DECIMAL(10,2),
            commission DECIMAL(10,2),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)

        conn.commit()
        conn.close()

    # ==================== 1. 数据分析模块 ====================

    async def analyze_user(self, comment_data: Dict) -> UserProfile:
        """
        分析用户意向评分
        对接AI (GPT-4 / Claude)
        """
        # 这里调用你的AI评分prompt
        ai_analysis = await self._call_ai_scoring(comment_data)

        profile = UserProfile(
            user_id=comment_data['user_id'],
            nickname=comment_data['nickname'],
            comment_text=comment_data['comment_text'],
            video_id=comment_data['video_id'],
            video_topic=comment_data['video_topic'],
            score=ai_analysis['总分'],
            destination=ai_analysis['目的地'],
            travel_time=ai_analysis['出行时间'],
            budget_range=ai_analysis['预算范围'],
            persona=ai_analysis['用户画像'],
            priority=self._classify_priority(ai_analysis['总分'])
        )

        # 存入数据库
        self._save_user_profile(profile)

        return profile

    def _classify_priority(self, score: int) -> str:
        """分类用户优先级"""
        if score >= 90:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 50:
            return "C"
        else:
            return "DROP"

    async def _call_ai_scoring(self, data: Dict) -> Dict:
        """调用AI评分接口"""
        # TODO: 对接你的n8n workflow或直接调用OpenAI API
        # 这里是示例返回
        return {
            "总分": 85,
            "目的地": "云南大理",
            "出行时间": "5月中旬",
            "预算范围": "3000-5000",
            "用户画像": "25-30岁女性,独自旅行",
            "建议策略": "A类高优"
        }

    # ==================== 2. 话术生成模块 ====================

    async def generate_comment(
        self,
        user_profile: UserProfile,
        role_name: str
    ) -> List[str]:
        """
        生成多变体话术
        返回3-5条备选话术
        """
        role_persona = self._get_role_persona(role_name)

        # 调用AI生成话术
        comments = await self._call_ai_comment_generation({
            "role_persona": role_persona,
            "user_profile": asdict(user_profile),
            "video_summary": self._get_video_summary(user_profile.video_id)
        })

        # 风险检测
        safe_comments = []
        for comment in comments:
            if await self._risk_check(comment):
                safe_comments.append(comment)

        return safe_comments

    def _get_role_persona(self, role_name: str) -> Dict:
        """获取角色人设"""
        personas = {
            "小鹿": {
                "gender": "女",
                "age": 25,
                "style": "姐妹/yyds/活泼",
                "expertise": "省钱攻略/美食探店"
            },
            "阿强": {
                "gender": "男",
                "age": 30,
                "style": "老表/地道/热情",
                "expertise": "本地文化/小众景点"
            },
            "Emma": {
                "gender": "女",
                "age": 28,
                "style": "真的超级/精致/文艺",
                "expertise": "拍照打卡/民宿推荐"
            },
            "老张": {
                "gender": "男",
                "age": 35,
                "style": "兄弟/稳/专业",
                "expertise": "户外徒步/装备经验"
            }
        }
        return personas.get(role_name, personas["小鹿"])

    def _get_video_summary(self, video_id: str) -> str:
        """获取视频摘要"""
        # 从MediaCrawler爬取的数据中读取
        # TODO: 实现视频内容摘要逻辑
        return "云南大理旅游攻略,洱海骑行+古城漫步"

    async def _call_ai_comment_generation(self, context: Dict) -> List[str]:
        """调用AI生成评论"""
        # TODO: 对接AI接口
        return [
            "姐妹我上个月刚去的大理!古城真的巨美😍 我有份避雷攻略,需要的话可以私我~",
            "巧了,我表哥在丽江开客栈,经常有内部折扣票,你们几个人去呀?",
            "5月大理客栈超难订!我之前住的那家老板娘人超好,要不要我帮你问问还有房?"
        ]

    async def _risk_check(self, comment: str) -> bool:
        """风险检测"""
        # 检测敏感词
        sensitive_words = ["微信", "VX", "wx", "QQ", "电话", "手机号", "公众号", "加我"]
        for word in sensitive_words:
            if word in comment:
                return False

        # TODO: 更多检测逻辑(AI营销痕迹检测等)
        return True

    # ==================== 3. 发布调度模块 ====================

    async def schedule_comments(self, user_profiles: List[UserProfile]):
        """
        智能调度评论发布
        考虑:时间分布/账号轮换/频率控制
        """
        tasks = []

        # 按优先级排序
        sorted_users = sorted(
            [u for u in user_profiles if u.priority != "DROP"],
            key=lambda x: x.score,
            reverse=True
        )

        current_time = datetime.now()

        for user in sorted_users:
            # 选择合适的账号
            account = self._select_best_account(user)
            if not account:
                continue

            # 生成话术
            comments = await self.generate_comment(user, account['role_name'])
            if not comments:
                continue

            # 计算发布时间
            scheduled_time = self._calculate_publish_time(
                current_time,
                user.priority
            )

            # 创建任务
            task = CommentTask(
                task_id=f"task_{user.user_id}_{int(datetime.now().timestamp())}",
                target_user=user,
                account_id=account['account_id'],
                role_name=account['role_name'],
                comment_text=random.choice(comments),
                scheduled_time=scheduled_time
            )

            tasks.append(task)
            self._save_comment_task(task)

        return tasks

    def _select_best_account(self, user: UserProfile) -> Optional[Dict]:
        """
        选择最佳账号
        匹配逻辑:目的地匹配 > 性别匹配 > 剩余配额
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 查询可用账号
        cursor.execute("""
        SELECT * FROM account_pool 
        WHERE status = 'active' 
        AND (last_used_date != date('now') OR used_today < daily_quota)
        ORDER BY used_today ASC
        """)

        accounts = cursor.fetchall()
        conn.close()

        if not accounts:
            return None

        # 简单选择第一个可用账号
        # TODO: 实现更复杂的匹配算法
        account = accounts[0]
        return {
            "account_id": account[0],
            "role_name": account[1],
            "daily_quota": account[5],
            "used_today": account[6]
        }

    def _calculate_publish_time(
        self,
        base_time: datetime,
        priority: str
    ) -> datetime:
        """
        计算发布时间
        A类: 2小时内
        B类: 24小时内
        C类: 48小时内
        """
        if priority == "A":
            delay = random.randint(30, 120)  # 30分钟-2小时
        elif priority == "B":
            delay = random.randint(120, 1440)  # 2-24小时
        else:
            delay = random.randint(1440, 2880)  # 24-48小时

        return base_time + timedelta(minutes=delay)

    # ==================== 4. 执行发布模块 ====================

    async def execute_tasks(self):
        """
        执行待发布任务
        真实环境需要对接抖音/小红书API或使用自动化工具
        """
        pending_tasks = self._get_pending_tasks()

        for task in pending_tasks:
            if datetime.now() >= task['scheduled_time']:
                success = await self._publish_comment(task)

                if success:
                    self._update_task_status(task['task_id'], 'published')
                    self._update_account_usage(task['account_id'])
                else:
                    self._update_task_status(task['task_id'], 'failed')

    async def _publish_comment(self, task: Dict) -> bool:
        """
        发布评论到平台
        """
        # TODO: 对接真实平台API
        # 这里需要使用:
        # 1. Playwright模拟操作
        # 2. 平台官方API(如果有)
        # 3. 第三方自动化工具

        print(f"[模拟发布] 账号:{task['account_id']} → 用户:{task['user_id']}")
        print(f"评论内容: {task['comment_text']}")

        await asyncio.sleep(1)  # 模拟发布延迟

        return True

    def _get_pending_tasks(self) -> List[Dict]:
        """获取待发布任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM comment_tasks 
        WHERE status = 'pending'
        AND scheduled_time <= datetime('now')
        ORDER BY scheduled_time ASC
        LIMIT 10
        """)

        tasks = cursor.fetchall()
        conn.close()

        # 转换为字典
        return [
            {
                "task_id": t[0],
                "user_id": t[1],
                "account_id": t[2],
                "role_name": t[3],
                "comment_text": t[4],
                "scheduled_time": datetime.fromisoformat(t[5])
            }
            for t in tasks
        ]

    # ==================== 5. 数据库操作 ====================

    def _save_user_profile(self, profile: UserProfile):
        """保存用户画像"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            profile.user_id,
            profile.nickname,
            profile.comment_text,
            profile.video_id,
            profile.video_topic,
            profile.score,
            profile.destination,
            profile.travel_time,
            profile.budget_range,
            profile.persona,
            profile.priority
        ))

        conn.commit()
        conn.close()

    def _save_comment_task(self, task: CommentTask):
        """保存评论任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO comment_tasks 
        (task_id, user_id, account_id, role_name, comment_text, scheduled_time, status)
        VALUES (?,?,?,?,?,?,?)
        """, (
            task.task_id,
            task.target_user.user_id,
            task.account_id,
            task.role_name,
            task.comment_text,
            task.scheduled_time.isoformat(),
            task.status
        ))

        conn.commit()
        conn.close()

    def _update_task_status(self, task_id: str, status: str):
        """更新任务状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE comment_tasks 
        SET status = ?, published_at = datetime('now')
        WHERE task_id = ?
        """, (status, task_id))

        conn.commit()
        conn.close()

    def _update_account_usage(self, account_id: str):
        """更新账号使用次数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE account_pool 
        SET used_today = used_today + 1,
            last_used_date = date('now')
        WHERE account_id = ?
        """, (account_id,))

        conn.commit()
        conn.close()

    # ==================== 6. 转化追踪模块 ====================

    def track_conversion(
        self,
        user_id: str,
        stage: str,
        deal_amount: float = 0
    ):
        """
        追踪转化漏斗
        stage: dm_received / contact_exchanged / handed_to_agency / final_deal
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 查找或创建追踪记录
        cursor.execute(
            "SELECT tracking_id FROM conversion_tracking WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()

        if not result:
            tracking_id = f"track_{user_id}_{int(datetime.now().timestamp())}"
            cursor.execute("""
            INSERT INTO conversion_tracking 
            (tracking_id, user_id, dm_received_at)
            VALUES (?, ?, datetime('now'))
            """, (tracking_id, user_id))
        else:
            tracking_id = result[0]

        # 更新对应阶段
        if stage == "contact_exchanged":
            cursor.execute(
                "UPDATE conversion_tracking SET contact_exchanged = TRUE WHERE tracking_id = ?",
                (tracking_id,)
            )
        elif stage == "handed_to_agency":
            cursor.execute(
                "UPDATE conversion_tracking SET handed_to_agency = TRUE WHERE tracking_id = ?",
                (tracking_id,)
            )
        elif stage == "final_deal":
            commission = deal_amount * 0.1  # 10%提成
            cursor.execute("""
            UPDATE conversion_tracking 
            SET final_deal = TRUE, deal_amount = ?, commission = ?
            WHERE tracking_id = ?
            """, (deal_amount, commission, tracking_id))

        conn.commit()
        conn.close()

    # ==================== 7. 数据分析报表 ====================

    def generate_report(self, days: int = 7) -> Dict:
        """生成运营报表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 统计数据
        cursor.execute("""
        SELECT 
            COUNT(*) as total_users,
            SUM(CASE WHEN priority = 'A' THEN 1 ELSE 0 END) as a_users,
            SUM(CASE WHEN priority = 'B' THEN 1 ELSE 0 END) as b_users,
            SUM(CASE WHEN priority = 'C' THEN 1 ELSE 0 END) as c_users
        FROM users
        WHERE created_at >= date('now', '-{} days')
        """.format(days))

        user_stats = cursor.fetchone()

        cursor.execute("""
        SELECT 
            COUNT(*) as total_comments,
            SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(likes) as total_likes,
            SUM(replies) as total_replies,
            SUM(CASE WHEN converted_to_dm = TRUE THEN 1 ELSE 0 END) as dm_conversions
        FROM comment_tasks
        WHERE scheduled_time >= date('now', '-{} days')
        """.format(days))

        comment_stats = cursor.fetchone()

        cursor.execute("""
        SELECT 
            COUNT(*) as total_conversions,
            SUM(CASE WHEN contact_exchanged = TRUE THEN 1 ELSE 0 END) as contacts,
            SUM(CASE WHEN final_deal = TRUE THEN 1 ELSE 0 END) as deals,
            SUM(deal_amount) as total_revenue,
            SUM(commission) as total_commission
        FROM conversion_tracking
        WHERE dm_received_at >= date('now', '-{} days')
        """.format(days))

        conversion_stats = cursor.fetchone()

        conn.close()

        # 计算转化率
        dm_rate = (comment_stats[5] / comment_stats[1]
                   * 100) if comment_stats[1] > 0 else 0
        deal_rate = (conversion_stats[2] / conversion_stats[0]
                     * 100) if conversion_stats[0] > 0 else 0

        return {
            "时间范围": f"最近{days}天",
            "用户分析": {
                "总用户数": user_stats[0],
                "A类用户": user_stats[1],
                "B类用户": user_stats[2],
                "C类用户": user_stats[3]
            },
            "评论数据": {
                "总评论数": comment_stats[0],
                "已发布": comment_stats[1],
                "失败": comment_stats[2],
                "获得点赞": comment_stats[3],
                "获得回复": comment_stats[4],
                "私信转化": comment_stats[5],
                "私信转化率": f"{dm_rate:.2f}%"
            },
            "成交数据": {
                "私信总数": conversion_stats[0],
                "获取联系方式": conversion_stats[1],
                "成交订单": conversion_stats[2],
                "成交率": f"{deal_rate:.2f}%",
                "总交易额": conversion_stats[3] or 0,
                "总佣金": conversion_stats[4] or 0
            }
        }


# ==================== 使用示例 ====================

async def main():
    """主流程示例"""
    engine = CommentGuideEngine()

    # 1. 从MediaCrawler获取的数据
    comment_data = {
        "user_id": "user_12345",
        "nickname": "小美爱旅行",
        "comment_text": "好想去大理啊!5月中旬有小伙伴一起吗?预算3000左右",
        "video_id": "video_67890",
        "video_topic": "云南大理旅游攻略",
    }

    # 2. 分析用户
    user_profile = await engine.analyze_user(comment_data)
    print(f"用户评分: {user_profile.score}, 优先级: {user_profile.priority}")

    # 3. 调度评论任务
    tasks = await engine.schedule_comments([user_profile])
    print(f"生成{len(tasks)}个评论任务")

    # 4. 执行发布(定时任务)
    await engine.execute_tasks()

    # 5. 追踪转化
    engine.track_conversion("user_12345", "dm_received")
    engine.track_conversion("user_12345", "contact_exchanged")
    engine.track_conversion("user_12345", "final_deal", deal_amount=5000)

    # 6. 生成报表
    report = engine.generate_report(days=7)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
