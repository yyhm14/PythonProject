import json
import threading
import logging
import uuid
import time
from datetime import datetime, timezone, timedelta

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

# 1. 生产记录表 (手动录入的那张表)
PROD_TABLE_ID = "tblSYeYC20AwXyxL"

# 2. 故障报警表 (VBS推送的那张表)
# ⚠️ 注意：如果这两张表是同一个，请确保列名包含所有字段。建议分开两张表。
ALARM_TABLE_ID = "tblSYeYC20AwXyxL"
BITABLE_APP_TOKEN = "VBRqboUT6afMXjsLvRHcWYUKnCg"

# 消息推送配置
RECEIVE_ID_TYPE = "chat_id"
RECEIVE_ID = "oc_0bbf8f78b6564b7b089c6fada4d24b02"
TEMPLATE_ID = "AAqvNycnRIekN"
TEMPLATE_VERSION = "0.0.17"

# 全局缓存 (用于生产记录)
GLOBAL_CACHE = {}

# 防重复推送配置
DUPLICATE_THRESHOLD = 300  # 防重复时间（秒），5分钟=300秒

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


# ==========================================
# 模块 A: 生产记录功能 (手动录入)
# ==========================================

def _build_prod_card(last_data=None, is_success=False):
    """构造生产记录卡片 (回响模式)"""
    if last_data is None: last_data = {}
    suffix = str(uuid.uuid4())[:8]
    current_time = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')
    refresh_time = datetime.now(timezone(timedelta(hours=8))).strftime('%H:%M:%S')

    mold_opts = [{"text": {"tag": "plain_text", "content": v}, "value": v} for v in ["X03", "W02", "W04"]]
    part_opts = [{"text": {"tag": "plain_text", "content": v}, "value": v} for v in
                 ["左侧围", "右侧围", "翼子板", "后门外板", "前门外板"]]
    bench_opts = [{"text": {"tag": "plain_text", "content": v}, "value": v} for v in ["左", "右"]]

    def get_init(key, opts):
        val = last_data.get(key)
        if val: return {"initial_option": {"value": val, "text": {"tag": "plain_text", "content": val}}}
        return {}

    header_color = "green" if is_success else "blue"
    header_title = f"✅ 已保存 ({refresh_time})" if is_success else "🏭 生产问题记录台"

    return {
        "schema": "2.0",
        "header": {"title": {"tag": "plain_text", "content": header_title}, "template": header_color},
        "body": {
            "elements": [
                {"tag": "div",
                 "text": {"tag": "plain_text", "content": "👇 填写后点击提交，系统会自动保留配置并清空问题栏。"}},
                {"tag": "div", "extra": {"tag": "button", "name": f"load_btn_{suffix}",
                                         "text": {"tag": "plain_text", "content": "🔄 加载上次配置"}, "type": "default",
                                         "value": {"action": "load_last_config"}}},
                {"tag": "hr"},
                {
                    "tag": "form",
                    "name": f"form_{suffix}",
                    "elements": [
                        {"tag": "div", "text": {"tag": "plain_text", "content": "上线时间"},
                         "margin": "0px 0px 4px 0px"},
                        {"tag": "picker_datetime", "name": "record_time", "initial_datetime": current_time,
                         "width": "fill"},
                        {
                            "tag": "column_set", "flex_mode": "none", "margin": "12px 0px 0px 0px",
                            "columns": [
                                {"tag": "column", "width": "weighted", "weight": 1, "elements": [
                                    {"tag": "div", "text": {"tag": "plain_text", "content": "模具"},
                                     "margin": "0px 0px 4px 0px"}, {"tag": "select_static", "name": "mold",
                                                                    "placeholder": {"tag": "plain_text",
                                                                                    "content": "请选择"},
                                                                    "options": mold_opts,
                                                                    **get_init("mold", mold_opts)}]},
                                {"tag": "column", "width": "weighted", "weight": 1, "elements": [
                                    {"tag": "div", "text": {"tag": "plain_text", "content": "零件"},
                                     "margin": "0px 0px 4px 0px"}, {"tag": "select_static", "name": "part",
                                                                    "placeholder": {"tag": "plain_text",
                                                                                    "content": "请选择"},
                                                                    "options": part_opts,
                                                                    **get_init("part", part_opts)}]}
                            ]
                        },
                        {
                            "tag": "column_set", "flex_mode": "none", "margin": "12px 0px 0px 0px",
                            "columns": [
                                {"tag": "column", "width": "weighted", "weight": 1, "elements": [
                                    {"tag": "div", "text": {"tag": "plain_text", "content": "工作台"},
                                     "margin": "0px 0px 4px 0px"}, {"tag": "select_static", "name": "workbench",
                                                                    "placeholder": {"tag": "plain_text",
                                                                                    "content": "请选择"},
                                                                    "options": bench_opts,
                                                                    **get_init("workbench", bench_opts)}]},
                                {"tag": "column", "width": "weighted", "weight": 1, "elements": [
                                    {"tag": "div", "text": {"tag": "plain_text", "content": "SPM"},
                                     "margin": "0px 0px 4px 0px"}, {"tag": "input", "name": "spm",
                                                                    "placeholder": {"tag": "plain_text",
                                                                                    "content": "数值"},
                                                                    "default_value": last_data.get("spm", "")}]}
                            ]
                        },
                        {"tag": "div", "text": {"tag": "plain_text", "content": "问题"}, "margin": "12px 0px 4px 0px"},
                        {"tag": "input", "name": f"issue_{suffix}",
                         "placeholder": {"tag": "plain_text", "content": "请输入..."}, "value": ""},
                        {"tag": "button", "name": "submit_btn", "text": {"tag": "plain_text", "content": "提交记录"},
                         "type": "primary", "form_action_type": "submit", "value": {"action": "submit_prod_record"},
                         "margin": "16px 0px 0px 0px"}
                    ]
                }
            ]
        }
    }


def _write_prod_to_bitable(record_time, mold, part, workbench, spm, issue):
    if not BITABLE_APP_TOKEN or not PROD_TABLE_ID: return
    try:
        formatted_time = record_time[:10] if record_time and len(record_time) > 10 else record_time
        fields = {"上线时间": formatted_time, "模具": mold, "零件": part, "工作台": workbench, "SPM": spm,
                  "问题": issue}
        request = CreateAppTableRecordRequest.builder().app_token(BITABLE_APP_TOKEN).table_id(
            PROD_TABLE_ID).request_body(AppTableRecord.builder().fields(fields).build()).build()
        api_client.bitable.v1.app_table_record.create(request)
        print("✅ 生产记录写入成功")
    except Exception as e:
        print(f"❌ 生产记录写入失败: {e}")


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
        request = CreateAppTableRecordRequest.builder().app_token(BITABLE_APP_TOKEN).table_id(
            ALARM_TABLE_ID).request_body(AppTableRecord.builder().fields(fields).build()).build()
        api_client.bitable.v1.app_table_record.create(request)
        print("✅ 故障报警写入成功")
    except Exception as e:
        print(f"❌ 故障报警写入失败: {e}")


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

        # 防重复检测
        should_push, reason = deduplicator.should_push(linear, device, problem)

        if should_push:
            print(f"✓ {reason}")
            # 推送飞书卡片
            push_success = push_feishu_card(device, linear, problem, alarm_time)

            return jsonify({
                "code": 200,
                "msg": "报警已推送",
                "reason": reason,
                "pushed": push_success
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

        action_key = action_value.get("action")
        form_value = action.form_value if hasattr(action, 'form_value') else {}

        print(f"🔍 收到交互: Action={action_key}")

        # --- 分支 1: 生产记录提交 ---
        if action_key == "submit_prod_record" or "mold" in form_value:
            print(f"📝 处理生产记录提交")
            r_time = form_value.get("record_time")
            r_mold = form_value.get("mold")
            r_part = form_value.get("part")
            r_bench = form_value.get("workbench")
            r_spm = form_value.get("spm")
            r_issue = ""
            for key, val in form_value.items():
                if key.startswith("issue_"):
                    r_issue = val
                    break

            global GLOBAL_CACHE
            GLOBAL_CACHE = {"mold": r_mold, "part": r_part, "workbench": r_bench, "spm": r_spm}

            _write_prod_to_bitable(r_time, r_mold, r_part, r_bench, r_spm, r_issue)

            return P2CardActionTriggerResponse({
                "toast": {"type": "success", "content": "✅ 记录已保存"},
                "card": {"type": "raw", "data": _build_prod_card(GLOBAL_CACHE, is_success=True)}
            })

        # --- 分支 2: 生产记录加载 ---
        if action_key == "load_last_config":
            return P2CardActionTriggerResponse({
                "toast": {"type": "success", "content": "已加载"},
                "card": {"type": "raw", "data": _build_prod_card(GLOBAL_CACHE, is_success=False)}
            })

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

            new_card = create_success_card(operator_id, status_text, cause_desc, measure_desc, submit_time, origin_time,
                                           origin_linear, origin_device, origin_problem, classification_text)

            return P2CardActionTriggerResponse({
                "toast": {"type": "success", "content": "处理完成"},
                "card": {"type": "raw", "data": new_card}
            })

        return P2CardActionTriggerResponse({})

    except Exception as e:
        print(f"❌ 异常: {e}")
        return P2CardActionTriggerResponse({})


# ================= 启动 =================
def run_flask():
    # 启动 Flask 服务，监听 5000 端口
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


def main():
    logging.basicConfig(level=logging.INFO)
    print("=" * 60)
    print("🚀 全功能服务启动中...")
    print("1. Flask 接收端口: 5000")
    print("2. 飞书长连接: 正在连接...")
    print(f"3. 防重复推送: 已启用 ({DUPLICATE_THRESHOLD}秒 = {DUPLICATE_THRESHOLD/60}分钟)")
    print("=" * 60)

    # 1. 启动 Flask 线程
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # 2. 启动飞书 WebSocket
    event_handler = lark.EventDispatcherHandler.builder(VERIFICATION_TOKEN, ENCRYPT_KEY) \
        .register_p2_card_action_trigger(do_card_action_trigger).build()

    ws_client = lark.ws.Client(APP_ID, APP_SECRET, event_handler=event_handler, log_level=LogLevel.INFO)
    ws_client.start()


if __name__ == "__main__":
    main()
