"""识别到目标后，在本机打开 Windows 资源管理器。"""

import subprocess
import sys
import traceback

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction


@AgentServer.custom_action("OpenExplorer")
class OpenExplorer(CustomAction):
    def run(self, context, argv) -> bool:
        try:
            if sys.platform != "win32":
                print("[OpenExplorer] 仅支持 Windows", flush=True)
                return False
            subprocess.Popen(["explorer"])
            print("[OpenExplorer] 已启动资源管理器", flush=True)
            return True
        except Exception:
            print("[OpenExplorer] 失败:", flush=True)
            traceback.print_exc()
            return False
