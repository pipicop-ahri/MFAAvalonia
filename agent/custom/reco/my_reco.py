from datetime import datetime
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition


@AgentServer.custom_recognition("CheckAfterTime")
class CheckAfterTime(CustomRecognition):
    def analyze(
        self,
        context,
        argv: CustomRecognition.AnalyzeArg,
    ):
        now = datetime.now()
        target_hour, target_minute = 15, 50

        is_after = (now.hour, now.minute) >= (target_hour, target_minute)

        detail = (
            f"当前时间 {now.strftime('%H:%M:%S')}，"
            f"{'已过' if is_after else '未到'} {target_hour:02d}:{target_minute:02d}"
        )
        print(f"[CheckAfterTime v2] {detail}")

        # return None 不会立刻走 on_error，框架会按 rate_limit 反复重试，
        # MFA 每秒刷 focus「识别失败」→ 误以为旧代码或卡死。
        if not is_after:
            context.override_next(argv.node_name, ["TimeNotYet"])
        else:
            context.override_next(argv.node_name, ["TimeReached"])

        return CustomRecognition.AnalyzeResult(
            box=(0, 0, 1, 1),
            detail={"msg": detail},
        )
