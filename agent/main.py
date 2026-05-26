import os
import sys

# 保证无论从项目根还是 agent 目录启动，都能 import custom.*
_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _AGENT_DIR not in sys.path:
    sys.path.insert(0, _AGENT_DIR)
os.chdir(_AGENT_DIR)

from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit

def _load_agent_modules() -> None:
    for name in (
        "custom.action.open_explorer",
        "custom.action.star_schedule",
    ):
        try:
            __import__(name)
        except Exception as e:
            print(f"[agent] 加载 {name} 失败: {e}", flush=True)
            raise


_load_agent_modules()


def _parse_socket_id() -> str:
    for arg in sys.argv[1:]:
        if arg.startswith("socket_id="):
            return arg.split("=", 1)[1]
    if len(sys.argv) >= 2 and not sys.argv[1].startswith("instance_"):
        return sys.argv[1]
    print("Usage: python main.py <socket_id>")
    print(f"argv={sys.argv!r}")
    sys.exit(1)


def main():
    Toolkit.init_option("./")
    socket_id = _parse_socket_id()
    print(f"[agent] 启动 socket_id={socket_id!r} cwd={os.getcwd()}", flush=True)
    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()


if __name__ == "__main__":
    main()
