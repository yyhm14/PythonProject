

# ================= 配置区域 =================
APP_ID = "cli_a9fbc96b89389bc4"
APP_SECRET = "srtnI073jIR8zhSqCDbBRI1fyumJRgOz"
VERIFICATION_TOKEN = "FP4qqknpMjAEitbLAIIyzhAewFo4Rp7m"
ENCRYPT_KEY = ""

# 多维表格配置
BITABLE_APP_TOKEN = "XA5UwrCYEibHjPkMxpWcdajVnLf"
BITABLE_TABLE_ID = "tblKOzJLp2G3y9zt"
import lark_oapi as lark
from lark_oapi import LogLevel
import production_handler
# 引入多维表格模块
from lark_oapi.api.bitable.v1 import *
# 引入通讯录模块 (注意这里引入了 BatchUserRequest)
from lark_oapi.api.contact.v3 import *
from lark_oapi.event.callback.model.p2_card_action_trigger import (
    P2CardActionTrigger,
    P2CardActionTriggerResponse
)
import logging
from datetime import datetime, timezone, timedelta

# ================= 配置区域 =================
APP_ID = "cli_a9fbc96b89389bc4"
APP_SECRET = "srtnI073jIR8zhSqCDbBRI1fyumJRgOz"
VERIFICATION_TOKEN = "FP4qqknpMjAEitbLAIIyzhAewFo4Rp7m"
ENCRYPT_KEY = ""

# 多维表格配置
BITABLE_APP_TOKEN = "VBRqboUT6afMXjsLvRHcWYUKnCg"
BITABLE_TABLE_ID = "tblSYeYC20AwXyxL"

# 初始化 API 客户端
api_client = lark.Client.builder() \
    .app_id(APP_ID) \
    .app_secret(APP_SECRET) \
    .log_level(LogLevel.INFO) \
    .build()


# ================= 1. 写入多维表格函数 =================
def write_to_bitable(linear, device, problem, handler_id, status, classification, cause, measure, push_time,
                     submit_time):
    if not BITABLE_APP_TOKEN or not BITABLE_TABLE_ID:
        return
    try:
        fields = {
            "线体": linear,
            "设备": device,
            "故障信息": problem,
            "处理人": [{"id": handler_id}] if handler_id else None,
            "处理状态": status,
            "故障类别": classification,
            "故障原因": cause,
            "处理措施": measure,
            "推送时间": push_time,
            "提交时间": submit_time
        }
        request = CreateAppTableRecordRequest.builder() \
            .app_token(BITABLE_APP_TOKEN) \
            .table_id(BITABLE_TABLE_ID) \
            .request_body(AppTableRecord.builder().fields(fields).build()) \
            .build()

        response = api_client.bitable.v1.app_table_record.create(request)
        if response.success():
            print("✅ 多维表格同步成功")
        else:
            print(f"❌ 多维表格写入失败: {response.code} - {response.msg}")
    except Exception as e:
        print(f"❌ 多维表格操作异常: {e}")


# ================= 2. 获取姓名函数 (完美适配你的JSON) =================
def get_feishu_user_name(user_open_id):
    """
    使用 BatchUserRequest 接口获取用户姓名
    """
    if not user_open_id:
        return "未知ID"

    try:
        # 构造请求：使用 BatchUserRequest
        request = BatchUserRequest.builder() \
            .user_id_type("open_id") \
            .department_id_type("open_department_id") \
            .user_ids([user_open_id]) \
            .build()

        # 调用 batch 接口
        response = api_client.contact.v3.user.batch(request)

        # 调试打印
        if response.raw:
            # 这里会打印出你刚才发给我的那个 JSON
            print(f"🔍 Batch接口原始响应: {str(response.raw.content, 'utf-8')}")

        # 解析数据
        # 对应 JSON 结构: data -> items -> [0] -> name
        if response.success() and response.data and response.data.items:
            user_info = response.data.items[0]

            # 提取 name
            if hasattr(user_info, 'name') and user_info.name:
                return user_info.name
            elif hasattr(user_info, 'en_name') and user_info.en_name:
                return user_info.en_name

            print("⚠️ 接口调用成功但 name 为空")
            return f"用户({user_open_id})"
        else:
            print(f"⚠️ 获取用户名失败: code={response.code}, msg={response.msg}")
            return f"用户({user_open_id})"

    except Exception as e:
        print(f"❌ 调用通讯录API异常: {e}")
        return f"用户({user_open_id})"


# ================= 3. 构造卡片函数 =================
def create_success_card(handler_name, handler_id, status_text, cause, measure, submit_time,
                        push_time, linear, device, problem, classification):
    if not handler_name: handler_name = "未知用户"

    card_dict = {
        "schema": "2.0",
        "config": {"update_multi": True},
        "header": {
            "title": {"tag": "plain_text", "content": "[已记录] 故障处理报告"},
            "template": "green",
            "icon": {"tag": "standard_icon", "token": "success_filled"}
        },
        "body": {
            "direction": "vertical",
            "padding": "12px 12px 12px 12px",
            "elements": [
                {
                    "tag": "div",
                    "fields": [
                        {"is_short": True, "text": {"tag": "lark_md", "content": f"**线体**: {linear}"}},
                        {"is_short": True, "text": {"tag": "lark_md", "content": f"**设备**: {device}"}}
                    ]
                },
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**故障信息**: {problem}"}
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**处理人**: <at id=\"{handler_id}\"></at>"
                            }
                        },
                        {"is_short": True, "text": {"tag": "lark_md", "content": f"**状态**: {status_text}"}}
                    ]
                },
                {
                    "tag": "div",
                    "fields": [
                        {"is_short": True, "text": {"tag": "lark_md", "content": f"**类别**: {classification}"}},
                        {"is_short": True,
                         "text": {"tag": "lark_md", "content": f"**原因**: {cause if cause else '无'}"}}
                    ]
                },
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**措施**: {measure if measure else '无'}"}
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"<font color='grey'>推送时间: {push_time}\n提交时间: {submit_time}</font>"
                    }
                }
            ]
        }
    }
    return card_dict


# ================= 4. 主逻辑 =================
def do_card_action_trigger(data: P2CardActionTrigger) -> P2CardActionTriggerResponse:
    try:
        event = data.event
        action = event.action
        message_id = event.context.open_message_id
        operator_id = event.operator.open_id

        action_value = action.value if action.value else {}
        form_value = action.form_value if hasattr(action, 'form_value') else {}

        print(f"收到交互: msg_id={message_id}, 操作人ID={operator_id}")

        if action_value.get("action") == "complete_alarm":
            # A. 提取数据
            origin_linear = action_value.get("origin_linear", "未知线体")
            origin_problem = action_value.get("origin_problem", "未知故障")
            origin_time = action_value.get("origin_time", "未知推送时间")
            origin_device = action_value.get("origin_device", "未知设备")

            # B. 获取姓名 (使用 Batch 接口)
            handler_name = get_feishu_user_name(operator_id)
            print(f"👤 识别到处理人: {handler_name}")

            # C. 表单数据
            raw_class = form_value.get("Classification", "")
            class_map = {"1": "电气类", "2": "机械类"}
            classification_text = class_map.get(raw_class, "未分类")

            raw_status = form_value.get("status", "")
            status_map = {"1": "未闭环", "2": "已闭环"}
            status_text = status_map.get(raw_status, "未知状态")

            cause_desc = form_value.get("description", "")
            measure_desc = form_value.get("measure", "")
            submit_time = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')

            # D. 本地记录
            try:
                log_content = (
                    f"推送:{origin_time} | 提交:{submit_time} | "
                    f"线体:{origin_linear} | 设备:{origin_device} | 故障:{origin_problem} | "
                    f"处理人:{handler_name} | 状态:{status_text} | 类别:{classification_text} | "
                    f"原因:{cause_desc} | 措施:{measure_desc}\n"
                )
                with open("process_records.txt", "a", encoding="utf-8") as f:
                    f.write(log_content)
                print("✅ 本地记录成功")
            except Exception as e:
                print(f"❌ 写入文件失败: {e}")
            write_to_bitable(
                origin_linear, origin_device, origin_problem, operator_id,
                status_text, classification_text, cause_desc, measure_desc,
                origin_time, submit_time
            )

            # F. 返回卡片
            new_card_content = create_success_card(
                handler_name, operator_id, status_text, cause_desc, measure_desc,
                submit_time, origin_time, origin_linear, origin_device, origin_problem, classification_text
            )

            return P2CardActionTriggerResponse({
                "toast": {"type": "success", "content": "提交成功"},
                "card": {"type": "raw", "data": new_card_content}
            })

        return P2CardActionTriggerResponse({})

    except Exception as e:
        import traceback
        print(f"❌ 全局异常:\n{traceback.format_exc()}")
        return P2CardActionTriggerResponse({
            "toast": {"type": "error", "content": "系统错误"}
        })


# ================= 启动部分 =================
event_handler = (
    lark.EventDispatcherHandler.builder(VERIFICATION_TOKEN, ENCRYPT_KEY)
    .register_p2_card_action_trigger(do_card_action_trigger)
    .build()
)


def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 服务启动中...")

    ws_client = lark.ws.Client(
        app_id=APP_ID,
        app_secret=APP_SECRET,
        event_handler=event_handler,
        log_level=LogLevel.INFO
    )
    ws_client.start()


if __name__ == "__main__":
    main()

