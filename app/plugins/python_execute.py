"""
Python执行插件 - 基于Agently框架
"""
import asyncio
import os
import tempfile
from typing import Dict, Any, Optional

import Agently

from app.utils.logger import Logger
from app.sandbox.client import SANDBOX_CLIENT


class PythonExecutePlugin:
    """Python代码执行插件类"""

    def __init__(self):
        self.lock = asyncio.Lock()

    async def execute_python(self, code: str, timeout: Optional[int] = 30) -> Dict[str, Any]:
        """执行Python代码"""
        async with self.lock:
            try:
                # 创建临时文件
                with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
                    f.write(code)
                    temp_file = f.name

                try:
                    # 使用沙箱执行Python代码
                    result = await SANDBOX_CLIENT.execute_python(temp_file, timeout=timeout)

                    return {
                        "success": True,
                        "output": result.output,
                        "error": result.error
                    }
                finally:
                    # 删除临时文件
                    try:
                        os.unlink(temp_file)
                    except Exception as e:
                        Logger.error(f"删除临时文件失败: {str(e)}")
            except Exception as e:
                return {
                    "success": False,
                    "error": f"执行Python代码失败: {str(e)}"
                }


def register_plugin(agent_factory: Agently.AgentFactory):
    """注册Python执行插件"""
    python_execute_plugin = PythonExecutePlugin()

    # 注册插件
    agent_factory.register_plugin(
        "python_execute",
        {
            "execute_python": {
                "func": python_execute_plugin.execute_python,
                "description": "在沙箱环境中执行Python代码",
                "parameters": {
                    "code": {
                        "type": "string",
                        "description": "要执行的Python代码"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "超时时间（秒）（默认: 30）"
                    }
                }
            }
        }
    )

    Logger.info("Python执行插件已注册")
    return agent_factory
