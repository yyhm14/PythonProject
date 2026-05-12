import json
import os
import threading
import logging
import uuid
import time
from datetime import datetime, timezone, timedelta
from logging.handlers import TimedRotatingFileHandler

# 脚本所在目录（解决系统定时任务工作目录不一致的问题）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_FILE    = os.path.join(BASE_DIR, "statistics.json")
SUPPRESS_FILE = os.path.join(BASE_DIR, "suppression.json")
LOG_FILE      = os.path.join(BASE_DIR, "alarm_service.log")


def _setup_logger():
    _logger = logging.getLogger("alarm_service")
    _logger.setLevel(logging.INFO)
    if _logger.handlers:
        return _logger
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    fh = TimedRotatingFileHandler(LOG_FILE, when="midnight", interval=1, backupCount=30, encoding="utf-8")
    fh.setFormatter(fmt)
    _logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    _logger.addHandler(sh)
    return _logger


logger = _setup_logger()

from flask import Flask, request, jsonify
import lark_oapi as lark
from lark_oapi import LogLevel
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.im.v1 import *
from lark_oapi.event.callback.model.p2_card_action_trigger import (
    P2CardActionTrigger,
    P2CardActionTriggerResponse
)

# ================= 配置区域 =================
APP_ID = "cli_a9fbc96b89389bc4"
APP_SECRET = "srtnI073jIR8zhSqCDbBRI1fyumJRgOz"
VERIFICATION_TOKEN = "FP4qqknpMjAEitbLAIIyzhAewFo4Rp7m"
ENCRYPT_KEY = ""


# ⚠️ 注意：如果这两张表是同一个，请确保列名包含所有字段。建议分开两张表。
ALARM_TABLE_ID = "tblSYeYC20AwXyxL"

# 3. 报警屏蔽表 (手动屏蔽记录)
# ⬇️ 【需要填写】新建一张多维表，填写 TABLE_ID，字段名参考代码中的 _write_suppression_to_bitable
SUPPRESS_TABLE_ID = "tblL22GE460aPknn"   # 👈 填写屏蔽记录表的 TABLE_ID

BITABLE_APP_TOKEN = "VBRqboUT6afMXjsLvRHcWYUKnCg"

# 消息推送配置
RECEIVE_ID_TYPE = "chat_id"
RECEIVE_ID = "oc_0bbf8f78b6564b7b089c6fada4d24b02"
TEMPLATE_ID = "AAqvNycnRIekN"
TEMPLATE_VERSION = "0.0.17"

# 屏蔽提示推送配置（推到有领导的群）
# ⬇️ 【需要填写】填写群 chat_id
SUPPRESS_RECEIVE_ID = "oc_8d76844598c134da320062aba2ba16c8"     # 👈 填写屏蔽提示要推送的群 chat_id
SUPPRESS_RECEIVE_ID_TYPE = "chat_id"
# 屏蔽提示超时配置（分钟）
SUPPRESS_TIMEOUT_MINUTES = 10


# 防重复推送配置
DUPLICATE_THRESHOLD = 600  # 防重复时间（秒），5分钟=300秒

# 屏蔽表单元数据缓存 {8位短key: {prompt_id, linear, device, problem}}
_suppression_meta_cache = {}

# ================= 初始化 =================
app = Flask(__name__)
api_client = lark.Client.builder().app_id(APP_ID).app_secret(APP_SECRET).log_level(LogLevel.INFO).build()


# ================= 防重复管理器 =================
class AlarmDeduplicator:
    """报警去重管理器"""

    def __init__(self, threshold=300):
        self.threshold = threshold
        self.alarm_cache = {}
        self.lock = threading.Lock()

    def generate_key(self, linear, device, problem):
        """生成报警唯一标识"""
        return f"{linear}|{device}|{problem}"

    def should_push(self, linear, device, problem):
        """判断是否应该推送"""
        alarm_key = self.generate_key(linear, device, problem)
        current_time = time.time()

        with self.lock:
            if alarm_key in self.alarm_cache:
                last_push_time = self.alarm_cache[alarm_key]
                time_diff = current_time - last_push_time

                if time_diff < self.threshold:
                    remaining = self.threshold - time_diff
                    msg = f"跳过重复推送（距上次 {time_diff:.0f}秒，还需 {remaining:.0f}秒）"
                    return False, msg
                else:
                    self.alarm_cache[alarm_key] = current_time
                    msg = f"允许推送（距上次 {time_diff:.0f}秒）"
                    return True, msg
            else:
                self.alarm_cache[alarm_key] = current_time
                msg = "首次报警，允许推送"
                return True, msg

    def get_statistics(self):
        """获取统计信息"""
        with self.lock:
            total_alarms = len(self.alarm_cache)
            current_time = time.time()

            locked_count = 0
            for last_time in self.alarm_cache.values():
                if current_time - last_time < self.threshold:
                    locked_count += 1

            return {
                "total_tracked": total_alarms,
                "currently_locked": locked_count,
                "threshold_seconds": self.threshold
            }

    def clear_old_records(self, max_age=86400):
        """清理超过24小时的旧记录"""
        current_time = time.time()
        with self.lock:
            keys_to_remove = []
            for key, last_time in self.alarm_cache.items():
                if current_time - last_time > max_age:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.alarm_cache[key]

            if keys_to_remove:
                print(f"🧹 清理了 {len(keys_to_remove)} 条旧记录")


# 创建去重管理器实例
deduplicator = AlarmDeduplicator(threshold=DUPLICATE_THRESHOLD)


# ================= 抑制管理器 =================
class AlarmSuppressor:
    """报警屏蔽管理器（暂时解决不了的问题可以屏蔽 24 小时）"""

    def __init__(self, file_path=SUPPRESS_FILE, duration_hours=24):
        self.file_path = file_path
        self.duration = duration_hours * 3600  # 24小时 = 86400秒
        self.lock = threading.Lock()
        self.suppressions = {}  # {"linear|device|problem": {"until": timestamp, "info": {...}}}
        self._load_from_file()

    def generate_key(self, linear, device, problem):
        return f"{linear}|{device}|{problem}"

    def is_suppressed(self, linear, device, problem):
        """检查是否在屏蔽期内"""
        alarm_key = self.generate_key(linear, device, problem)
        current_time = time.time()

        with self.lock:
            if alarm_key in self.suppressions:
                info = self.suppressions[alarm_key]
                if current_time < info["until"]:
                    remaining = (info["until"] - current_time) / 3600
                    return True, f"已屏蔽（剩余 {remaining:.1f} 小时）", info
                else:
                    # 过期删除
                    del self.suppressions[alarm_key]
                    self._save_to_file()
            return False, "", None

    def add_suppression(self, linear, device, problem, operator_id, reason):
        """添加屏蔽记录"""
        alarm_key = self.generate_key(linear, device, problem)
        until_time = time.time() + self.duration

        with self.lock:
            self.suppressions[alarm_key] = {
                "until": until_time,
                "linear": linear,
                "device": device,
                "problem": problem,
                "operator_id": operator_id,
                "reason": reason,
                "created_at": time.time()
            }
            self._save_to_file()

    def _save_to_file(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.suppressions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 屏蔽数据保存失败: {e}")

    def _load_from_file(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.suppressions = json.load(f)
                print(f"✅ 屏蔽数据已恢复: {len(self.suppressions)} 条记录")
            else:
                print("🛡️ 屏蔽文件不存在，从空数据开始")
        except Exception as e:
            print(f"⚠️ 屏蔽数据读取失败，从空数据开始: {e}")
            self.suppressions = {}


# 创建抑制管理器实例
suppressor = AlarmSuppressor()


# ================= 连续报警检测 =================
class AlarmCounter:
    """连续报警计数器（检测一天内同一故障是否连续触发）"""

    def __init__(self, window_hours=24):
        self.window = window_hours * 3600
        self.lock = threading.Lock()
        self.counts = {}  # {"linear|device|problem": {"count": int, "first_time": timestamp}}

    def check_and_increment(self, linear, device, problem):
        """
        检查是否连续报警，返回 (should_warn, current_count)
        should_warn=True 表示是第二次或连续报警，需要提示屏蔽
        """
        alarm_key = f"{linear}|{device}|{problem}"
        current_time = time.time()

        with self.lock:
            if alarm_key in self.counts:
                info = self.counts[alarm_key]
                # 检查是否在时间窗口内
                if current_time - info["first_time"] < self.window:
                    info["count"] += 1
                    should_warn = info["count"] >= 2
                    return should_warn, info["count"]
                else:
                    # 超出窗口，重新计数
                    self.counts[alarm_key] = {"count": 1, "first_time": current_time}
                    return False, 1
            else:
                self.counts[alarm_key] = {"count": 1, "first_time": current_time}
                return False, 1


# 创建计数器实例
counter = AlarmCounter()


# ================= 屏蔽提示超时管理器 =================
class SuppressionTimeoutManager:
    """屏蔽提示超时管理器（10分钟内未处理则自动推送）"""

    def __init__(self, timeout_minutes=10):
        self.timeout = timeout_minutes * 60  # 10分钟=600秒
        self.lock = threading.Lock()
        self.prompts = {}  # {prompt_id: {"linear": ..., "device": ..., "problem": ..., "alarm_time": ..., "created_at": timestamp}}

    def add_prompt(self, linear, device, problem, alarm_time):
        """添加一个待处理的屏蔽提示"""
        prompt_id = str(uuid.uuid4())
        with self.lock:
            self.prompts[prompt_id] = {
                "linear": linear,
                "device": device,
                "problem": problem,
                "alarm_time": alarm_time,
                "created_at": time.time()
            }
        return prompt_id

    def remove_prompt(self, prompt_id):
        """用户已经处理，移除记录"""
        with self.lock:
            if prompt_id in self.prompts:
                del self.prompts[prompt_id]

    def check_timeouts(self):
        """检查并返回超时的屏蔽提示"""
        current_time = time.time()
        timeout_prompts = []

        with self.lock:
            to_remove = []
            for prompt_id, info in self.prompts.items():
                if current_time - info["created_at"] >= self.timeout:
                    timeout_prompts.append(info)
                    to_remove.append(prompt_id)

            for prompt_id in to_remove:
                del self.prompts[prompt_id]

        return timeout_prompts


# 创建超时管理器实例
timeout_manager = SuppressionTimeoutManager(timeout_minutes=SUPPRESS_TIMEOUT_MINUTES)


# ================= 屏蔽提示卡片 =================
def _build_suppression_prompt_card(linear, device, problem, alarm_count, alarm_time, prompt_id):
    """构建屏蔽提示交互卡片"""
    # 用短 key 存元数据到缓存，input name 只传 key（绕过飞书 name ≤100 字符限制）
    cache_key = str(uuid.uuid4())[:8]
    _suppression_meta_cache[cache_key] = {
        "prompt_id": prompt_id, "linear": linear, "device": device, "problem": problem
    }
    reason_field = f"r_{cache_key}"  # 共 10 字符，远低于 100 上限

    return {
        "schema": "2.0",
        "header": {
            "title": {"tag": "plain_text", "content": "⚠️ 连续报警提示"},
            "template": "orange"
        },
        "body": {
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**线体**: {linear} | **设备**: {device}"
                    }
                },
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**故障**: {problem}"}},
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"该故障在今日已连续报警 **{alarm_count}** 次，是否暂时屏蔽？"
                    }
                },
                {"tag": "div", "text": {"tag": "plain_text", "content": "屏蔽后 24 小时内该故障将不再推送。"}},
                {"tag": "hr"},
                {
                    "tag": "form",
                    "name": "suppress_form",
                    "elements": [
                        {
                            "tag": "input",
                            "name": reason_field,
                            "placeholder": {"tag": "plain_text", "content": "屏蔽原因（选填）"}
                        },
                        {
                            "tag": "button",
                            "name": "btn_suppress",
                            "text": {"tag": "plain_text", "content": "屏蔽 24 小时"},
                            "type": "danger",
                            "form_action_type": "submit",
                            "value": {"action": "confirm_suppression"},
                            "margin": "12px 0px 0px 0px"
                        }
                    ]
                },
                {
                    "tag": "button",
                    "name": "btn_ignore",
                    "text": {"tag": "plain_text", "content": "继续推送"},
                    "type": "default",
                    "value": {
                        "action": "ignore_suppression",
                        "prompt_id": prompt_id,
                        "linear": linear,
                        "device": device,
                        "problem": problem,
                        "alarm_time": alarm_time
                    },
                    "margin": "8px 0px 0px 0px"
                }
            ]
        }
    }


def _write_suppression_to_bitable(linear, device, problem, operator_id, reason):
    """将屏蔽记录写入飞书多维表"""
    if not BITABLE_APP_TOKEN or not SUPPRESS_TABLE_ID:
        print("⚠️ 未配置 SUPPRESS_TABLE_ID，跳过屏蔽记录写入")
        return

    try:
        now = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
        # ⬇️ 【需要配置】字段名要与你的屏蔽表列名一致
        fields = {
            "线体": linear,
            "设备": device,
            "故障信息": problem,
            "屏蔽人": [{"id": operator_id}] if operator_id else None,
            "屏蔽原因": reason,
            "屏蔽时间": now
        }
        request = CreateAppTableRecordRequest.builder().app_token(BITABLE_APP_TOKEN).table_id(
            SUPPRESS_TABLE_ID).request_body(AppTableRecord.builder().fields(fields).build()).build()
        api_client.bitable.v1.app_table_record.create(request)
        print("✅ 屏蔽记录写入成功")
    except Exception as e:
        print(f"❌ 屏蔽记录写入失败: {e}")


# ================= 日报统计管理器 =================
class DailyStatistics:
    """每日推送/填写数量统计（持久化到本地文件，重启不丢数据）"""

    def __init__(self):
        self.lock = threading.Lock()
        self.data = {}  # {"2024-03-30": {"push": 5, "submit": 3}}
        self._load_from_file()

    def _get_stat_date(self):
        """8:00 ~ 次日 8:00 归属同一统计日期"""
        now = datetime.now(timezone(timedelta(hours=8)))
        if now.hour < 8:
            return (now - timedelta(days=1)).strftime("%Y-%m-%d")
        return now.strftime("%Y-%m-%d")

    def record_push(self):
        """记录一次卡片推送"""
        date_key = self._get_stat_date()
        with self.lock:
            self.data.setdefault(date_key, {"push": 0, "submit": 0})
            self.data[date_key]["push"] += 1
        self._save_to_file()

    def record_submit(self):
        """记录一次卡片填写"""
        date_key = self._get_stat_date()
        with self.lock:
            self.data.setdefault(date_key, {"push": 0, "submit": 0})
            self.data[date_key]["submit"] += 1
        self._save_to_file()

    def get_last_period_stats(self):
        """获取前一个统计周期的数据（昨日8:00~今日8:00）"""
        now = datetime.now(timezone(timedelta(hours=8)))
        date_key = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        with self.lock:
            stats = self.data.get(date_key, {"push": 0, "submit": 0})
            return date_key, stats["push"], stats["submit"]

    def _save_to_file(self):
        try:
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 统计数据保存失败: {e}")

    def _load_from_file(self):
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                print(f"✅ 统计数据已恢复: {len(self.data)} 天记录")
            else:
                print("📊 统计文件不存在，从空数据开始")
        except Exception as e:
            print(f"⚠️ 统计数据读取失败，从空数据开始: {e}")
            self.data = {}


# 创建统计管理器实例
statistics_manager = DailyStatistics()


# ================= 日报推送 =================
def _build_report_card(date_key, push_count, submit_count):
    """构建日报统计卡片"""
    dt = datetime.strptime(date_key, "%Y-%m-%d")
    date_label = f"{dt.month}月{dt.day}日"
    return {
        "schema": "2.0",
        "header": {
            "title": {"tag": "plain_text", "content": "📊 故障报警日报"},
            "template": "blue"
        },
        "body": {
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"统计日期：**{date_label}**"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "column_set",
                    "flex_mode": "none",
                    "columns": [
                        {
                            "tag": "column", "width": "weighted", "weight": 1,
                            "elements": [{
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**推送卡片**\n<font color='blue'></font> **{push_count}** 条"
                                }
                            }]
                        },
                        {
                            "tag": "column", "width": "weighted", "weight": 1,
                            "elements": [{
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**填写完成**\n<font color='green'></font> **{submit_count}** 张"
                                }
                            }]
                        }
                    ]
                }
            ]
        }
    }


def push_daily_report():
    """推送日报统计到飞书群"""
    try:
        date_key, push_count, submit_count = statistics_manager.get_last_period_stats()
        card_content = _build_report_card(date_key, push_count, submit_count)
        request_obj = CreateMessageRequest.builder() \
            .receive_id_type(RECEIVE_ID_TYPE) \
            .request_body(
                CreateMessageRequestBody.builder()
                    .receive_id(RECEIVE_ID)
                    .msg_type("interactive")
                    .content(json.dumps(card_content))
                    .build()
            ).build()
        api_client.im.v1.message.create(request_obj)
        print(f"✅ 日报推送成功 | 日期: {date_key} | 推送: {push_count}条 | 填写: {submit_count}张")
    except Exception as e:
        print(f"❌ 日报推送失败: {e}")


def _schedule_daily_report():
    """定时任务：每天 08:30 推送日报"""
    while True:
        try:
            now = datetime.now(timezone(timedelta(hours=8)))
            next_run = now.replace(hour=8, minute=30, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"下次日报推送时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(wait_seconds)
            push_daily_report()
        except Exception as e:
            logger.error(f"日报调度线程异常: {e}", exc_info=True)
            time.sleep(60)



# ==========================================
# 模块 B: 故障报警功能 (VBS触发)
# ==========================================

def create_success_card(handler_id, status_text, cause, measure, submit_time,
                        push_time, linear, device, problem, classification):
    """构造故障处理完成的绿色卡片"""
    return {
        "schema": "2.0",
        "config": {"update_multi": True},
        "header": {"title": {"tag": "plain_text", "content": "[已记录] 故障处理报告"}, "template": "green",
                   "icon": {"tag": "standard_icon", "token": "success_filled"}},
        "body": {
            "elements": [
                {"tag": "div",
                 "fields": [{"is_short": True, "text": {"tag": "lark_md", "content": f"**线体**: {linear}"}},
                            {"is_short": True, "text": {"tag": "lark_md", "content": f"**设备**: {device}"}}]},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**故障信息**: {problem}"}},
                {"tag": "hr"},
                {"tag": "div", "fields": [{"is_short": True, "text": {"tag": "lark_md",
                                                                      "content": f"**处理人**: <at id=\"{handler_id}\"></at>"}},
                                          {"is_short": True,
                                           "text": {"tag": "lark_md", "content": f"**状态**: {status_text}"}}]},
                {"tag": "div",
                 "fields": [{"is_short": True, "text": {"tag": "lark_md", "content": f"**类别**: {classification}"}},
                            {"is_short": True, "text": {"tag": "lark_md", "content": f"**原因**: {cause}"}}]},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"**措施**: {measure}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md",
                                        "content": f"<font color='grey'>推送: {push_time}\n提交: {submit_time}</font>",
                                        "text_size": "caption"}}
            ]
        }
    }


def _write_alarm_to_bitable(linear, device, problem, handler_id, status, classification, cause, measure, push_time,
                            submit_time):
    if not BITABLE_APP_TOKEN or not ALARM_TABLE_ID: return
    try:
        # ⚠️ 注意：这里的字段名必须和你的【故障报警表】列名一致
        fields = {
            "线体": linear, "设备": device, "故障信息": problem,
            "处理人": [{"id": handler_id}] if handler_id else None,
            "处理状态": status, "故障类别": classification,
            "故障原因": cause, "处理措施": measure,
            "推送时间": push_time, "提交时间": submit_time
        }
        # 过滤掉 None 值，避免 API 因空字段报错
        fields = {k: v for k, v in fields.items() if v is not None}
        request = CreateAppTableRecordRequest.builder().app_token(BITABLE_APP_TOKEN).table_id(
            ALARM_TABLE_ID).request_body(AppTableRecord.builder().fields(fields).build()).build()
        resp = api_client.bitable.v1.app_table_record.create(request)
        if resp.success():
            logger.info(f"故障报警写入成功 | {linear} | {device} | {problem}")
        else:
            logger.error(f"故障报警写入失败: code={resp.code}, msg={resp.msg} | {linear} | {device} | {problem}")
    except Exception as e:
        logger.error(f"故障报警写入异常: {e} | {linear} | {device} | {problem}")


def push_feishu_card(device, linear_body, problem, alarm_time):
    """推送报警卡片"""
    try:
        card_content = {
            "type": "template",
            "data": {
                "template_id": TEMPLATE_ID,
                "template_version_name": TEMPLATE_VERSION,
                "template_variable": {
                    "device": device, "LinearBody": linear_body, "Problem": problem, "alarm_time": alarm_time
                }
            }
        }
        request_obj = CreateMessageRequest.builder().receive_id_type(RECEIVE_ID_TYPE).request_body(
            CreateMessageRequestBody.builder().receive_id(RECEIVE_ID).msg_type("interactive").content(
                json.dumps(card_content)).build()
        ).build()
        api_client.im.v1.message.create(request_obj)
        print(f"✅ 报警卡片推送成功: {device} - {problem}")
        statistics_manager.record_push()
        return True
    except Exception as e:
        print(f"❌ 推送异常: {e}")
        return False


# ================= Flask 路由 (接收 VBS) =================
@app.route("/receive_data", methods=["POST"])
def receive_data():
    try:
        data = request.get_json()
        # 兼容 VBS 发送的结构 {"value": {...}}
        if "value" in data:
            val = data["value"]
            linear = val.get("LinearBody", "未知")
            device = val.get("Device", "未知")
            problem = val.get("Problem", "未知")
            alarm_time = val.get("alarm_time", "未知")
        else:
            # 兼容直接发送的结构
            linear = data.get("LinearBody", "未知")
            device = data.get("Device", "未知")
            problem = data.get("Problem", "未知")
            alarm_time = data.get("alarm_time", "未知")

        print(f"\n📩 收到VBS数据: {linear} - {device} - {problem}")
        logger.info(f"收到VBS报警 | {linear} | {device} | {problem} | alarm_time={alarm_time}")

        # 1. 检查是否在屏蔽期内
        is_suppressed, suppress_reason, _ = suppressor.is_suppressed(linear, device, problem)
        if is_suppressed:
            print(f"🛡️ {suppress_reason}")
            return jsonify({
                "code": 200,
                "msg": "报警已接收但已屏蔽",
                "reason": suppress_reason,
                "pushed": False
            })

        # 2. 防重复检测
        should_push, reason = deduplicator.should_push(linear, device, problem)

        if should_push:
            print(f"✓ {reason}")

            # 3. 连续报警检测
            should_warn, alarm_count = counter.check_and_increment(linear, device, problem)

            if should_warn:
                # 第二次及以上连续报警，推送屏蔽提示卡片到有领导的群
                print(f"⚠️ 连续报警（第{alarm_count}次），推送屏蔽提示")
                prompt_id = timeout_manager.add_prompt(linear, device, problem, alarm_time)
                card_content = _build_suppression_prompt_card(linear, device, problem, alarm_count, alarm_time, prompt_id)
                request_obj = CreateMessageRequest.builder() \
                    .receive_id_type(SUPPRESS_RECEIVE_ID_TYPE) \
                    .request_body(
                        CreateMessageRequestBody.builder()
                            .receive_id(SUPPRESS_RECEIVE_ID)
                            .msg_type("interactive")
                            .content(json.dumps(card_content))
                            .build()
                    ).build()
                api_client.im.v1.message.create(request_obj)
                print(f"✅ 屏蔽提示推送成功: {device} - {problem}")
            else:
                # 首次报警，正常推送
                push_feishu_card(device, linear, problem, alarm_time)

            return jsonify({
                "code": 200,
                "msg": "报警已推送",
                "reason": reason,
                "pushed": True
            })
        else:
            print(f"⏭️ {reason}")
            return jsonify({
                "code": 200,
                "msg": "报警已接收但跳过推送（防重复）",
                "reason": reason,
                "pushed": False
            })

    except Exception as e:
        print(f"❌ Flask处理异常: {e}")
        logger.error(f"Flask处理异常: {e}")
        return jsonify({"code": 500, "msg": str(e)})


@app.route("/alarm/statistics", methods=["GET"])
def get_statistics():
    """查询防重复统计信息"""
    stats = deduplicator.get_statistics()
    return jsonify({
        "success": True,
        "data": stats
    })


@app.route("/alarm/clear_cache", methods=["POST"])
def clear_cache():
    """清理缓存"""
    deduplicator.clear_old_records(max_age=86400)
    return jsonify({
        "success": True,
        "message": "缓存清理完成"
    })


@app.route("/test/register_suppression_meta", methods=["POST"])
def register_suppression_meta():
    """测试用：预注册屏蔽表单元数据，供 test_suppression.py 使用"""
    data = request.get_json()
    key = data.get("key")
    meta = data.get("meta")
    if key and meta:
        _suppression_meta_cache[key] = meta
        return jsonify({"success": True})
    return jsonify({"success": False, "msg": "缺少 key 或 meta"}), 400


@app.route("/health", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify({
        "success": True,
        "status": "running",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


# ================= 回调主入口 (处理所有点击) =================
def do_card_action_trigger(data: P2CardActionTrigger) -> P2CardActionTriggerResponse:
    try:
        event = data.event
        action = event.action
        operator_id = event.operator.open_id

        action_value = action.value if action.value else {}
        if isinstance(action_value, str):
            try:
                action_value = json.loads(action_value)
            except:
                pass

        # 调试：打印原始 action_value
        print(f"📦 原始 action_value: {action_value}")
        print(f"📦 action_value 类型: {type(action_value)}")

        action_key = action_value.get("action") if action_value else None
        form_value = action.form_value if hasattr(action, 'form_value') and action.form_value else {}

        print(f"🔍 收到交互: Action={action_key}, Form={list(form_value.keys()) if form_value else 'None'}")

        # --- 分支 3: 故障报警闭环 ---
        if action_key == "complete_alarm":
            print(f"🔧 处理故障报警闭环")
            origin_linear = str(action_value.get("origin_linear", "未知"))
            origin_problem = str(action_value.get("origin_problem", "未知"))
            origin_time = str(action_value.get("origin_time", "未知"))
            origin_device = str(action_value.get("origin_device", "未知"))

            raw_class = form_value.get("Classification", "")
            class_map = {"1": "电气类", "2": "机械类"}
            classification_text = class_map.get(raw_class, "未分类")

            raw_status = form_value.get("status", "")
            status_map = {"1": "未闭环", "2": "已闭环"}
            status_text = status_map.get(raw_status, "未知状态")

            cause_desc = str(form_value.get("description", "") or "无")
            measure_desc = str(form_value.get("measure", "") or "无")
            submit_time = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')

            _write_alarm_to_bitable(origin_linear, origin_device, origin_problem, operator_id, status_text,
                                    classification_text, cause_desc, measure_desc, origin_time, submit_time)
            logger.info(f"故障闭环提交 | {origin_linear} | {origin_device} | {origin_problem} | 处理人:{operator_id} | 状态:{status_text} | 类别:{classification_text}")
            statistics_manager.record_submit()

            new_card = create_success_card(operator_id, status_text, cause_desc, measure_desc, submit_time, origin_time,
                                           origin_linear, origin_device, origin_problem, classification_text)

            return P2CardActionTriggerResponse({
                "toast": {"type": "success", "content": "处理完成"},
                "card": {"type": "raw", "data": new_card}
            })

        # --- 分支 4: 屏蔽提示 - 继续推送 ---
        if action_key == "ignore_suppression":
            print(f"🔄 用户选择继续推送")
            prompt_id = str(action_value.get("prompt_id", ""))
            linear = str(action_value.get("linear", "未知"))
            device = str(action_value.get("device", "未知"))
            problem = str(action_value.get("problem", "未知"))
            alarm_time = str(action_value.get("alarm_time", "未知"))

            # 移除超时记录
            if prompt_id:
                timeout_manager.remove_prompt(prompt_id)

            # 推送正常报警卡片
            push_feishu_card(device, linear, problem, alarm_time)

            # 返回已完成的卡片提示
            return P2CardActionTriggerResponse({
                "toast": {"type": "success", "content": "✅ 已继续推送"},
                "card": {
                    "type": "raw",
                    "data": {
                        "schema": "2.0",
                        "header": {
                            "title": {"tag": "plain_text", "content": "✅ 已继续推送"},
                            "template": "green"
                        },
                        "body": {
                            "elements": [
                                {
                                    "tag": "div",
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**故障**: {problem}\n该故障已正常推送到群内。"
                                    }
                                }
                            ]
                        }
                    }
                }
            })

        # --- 分支 5: 屏蔽提示 - 确认屏蔽 ---
        # 飞书 form_action_type:submit 不传 action.value，元数据编码在 form_value 的 key 里（r_<base64>）
        suppress_key = next((k for k in form_value if k.startswith("r_")), None)
        if action_key == "confirm_suppression" or suppress_key:
            print(f"🛡️ 用户选择屏蔽故障")
            if suppress_key:
                cache_key = suppress_key[2:]
                meta = _suppression_meta_cache.pop(cache_key, None)
                if not meta:
                    logger.error(f"屏蔽元数据缓存不存在 key={cache_key}，可能服务已重启")
                    return P2CardActionTriggerResponse({
                        "toast": {"type": "error", "content": "操作已失效，请重新触发"}
                    })
                prompt_id = str(meta.get("prompt_id", ""))
                linear = str(meta.get("linear", "未知"))
                device = str(meta.get("device", "未知"))
                problem = str(meta.get("problem", "未知"))
                reason = str(form_value.get(suppress_key, "") or "未填写")
            else:
                prompt_id = str(action_value.get("prompt_id", ""))
                linear = str(action_value.get("linear", "未知"))
                device = str(action_value.get("device", "未知"))
                problem = str(action_value.get("problem", "未知"))
                reason = str(form_value.get("reason", "") or "未填写")

            # 移除超时记录
            if prompt_id:
                timeout_manager.remove_prompt(prompt_id)

            # 添加屏蔽记录
            suppressor.add_suppression(linear, device, problem, operator_id, reason)

            # 写入飞书表格
            _write_suppression_to_bitable(linear, device, problem, operator_id, reason)

            # 返回已屏蔽的确认卡片
            now_str = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
            return P2CardActionTriggerResponse({
                "toast": {"type": "success", "content": "✅ 已屏蔽 24 小时"},
                "card": {
                    "type": "raw",
                    "data": {
                        "schema": "2.0",
                        "header": {
                            "title": {"tag": "plain_text", "content": "🛡️ 已屏蔽"},
                            "template": "orange"
                        },
                        "body": {
                            "elements": [
                                {
                                    "tag": "div",
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**故障**: {problem}"
                                    }
                                },
                                {"tag": "div", "text": {"tag": "lark_md", "content": f"**屏蔽原因**: {reason}"}},
                                {"tag": "div", "text": {"tag": "lark_md", "content": f"**屏蔽时间**: {now_str}"}},
                                {"tag": "hr"},
                                {
                                    "tag": "div",
                                    "text": {
                                        "tag": "plain_text",
                                        "content": "该故障将在 24 小时内不再推送。"
                                    }
                                }
                            ]
                        }
                    }
                }
            })

        return P2CardActionTriggerResponse({})

    except Exception as e:
        print(f"❌ 异常: {e}")
        logger.error(f"卡片交互异常: {e}")
        return P2CardActionTriggerResponse({})


def _schedule_timeout_check():
    """定时任务：每分钟检查屏蔽提示超时"""
    while True:
        try:
            timeout_prompts = timeout_manager.check_timeouts()
            for prompt in timeout_prompts:
                linear = prompt["linear"]
                device = prompt["device"]
                problem = prompt["problem"]
                alarm_time = prompt["alarm_time"]
                logger.info(f"屏蔽提示超时，自动推送报警: {device} - {problem}")
                push_feishu_card(device, linear, problem, alarm_time)
        except Exception as e:
            logger.error(f"超时检查线程异常: {e}", exc_info=True)
        time.sleep(60)


# ================= 启动 =================
def run_flask():
    # 启动 Flask 服务，监听 5000 端口
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


def main():
    logger.info("=" * 60)
    logger.info("全功能服务启动中...")
    logger.info(f"日志文件: {LOG_FILE}")
    logger.info(f"Flask 接收端口: 5000")
    logger.info(f"防重复推送: 已启用 ({DUPLICATE_THRESHOLD}秒 = {DUPLICATE_THRESHOLD/60}分钟)")
    logger.info(f"屏蔽提示超时: {SUPPRESS_TIMEOUT_MINUTES}分钟后自动推送")
    logger.info("日报定时推送: 已启用 (每天 08:30)")
    logger.info("=" * 60)

    # 1. 启动 Flask 线程
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # 2. 启动日报定时线程
    report_thread = threading.Thread(target=_schedule_daily_report, name="DailyReport")
    report_thread.daemon = True
    report_thread.start()

    # 3. 启动屏蔽提示超时检查线程
    timeout_thread = threading.Thread(target=_schedule_timeout_check, name="TimeoutChecker")
    timeout_thread.daemon = True
    timeout_thread.start()

    # 4. 启动飞书 WebSocket（断线自动重连）
    event_handler = lark.EventDispatcherHandler.builder(VERIFICATION_TOKEN, ENCRYPT_KEY) \
        .register_p2_card_action_trigger(do_card_action_trigger).build()

    while True:
        try:
            ws_client = lark.ws.Client(APP_ID, APP_SECRET, event_handler=event_handler, log_level=LogLevel.INFO)
            ws_client.start()
            logger.warning("WebSocket 连接意外退出，准备重连...")
        except Exception as e:
            logger.error(f"WebSocket 异常: {e}", exc_info=True)
        time.sleep(10)
        logger.info("正在重新连接 WebSocket...")


if __name__ == "__main__":
    main()
