"""
文件编辑插件 - 基于Agently框架
"""
import asyncio
import os
from typing import Dict, Any, Optional

import Agently

from utils.logger import logger


class FileEditorPlugin:
    """文件编辑插件类"""

    def __init__(self):
        self.lock = asyncio.Lock()

    async def read_file(self, path: str) -> Dict[str, Any]:
        """读取文件内容"""
        async with self.lock:
            try:
                # 确保路径存在
                if not os.path.exists(path):
                    return {
                        "success": False,
                        "error": f"文件未找到: {path}"
                    }

                # 读取文件内容
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                return {
                    "success": True,
                    "content": content,
                    "path": path
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"读取文件失败: {str(e)}"
                }

    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """写入文件内容"""
        async with self.lock:
            try:
                # 确保目录存在
                directory = os.path.dirname(path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)

                # 写入文件内容
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)

                return {
                    "success": True,
                    "message": f"文件写入成功: {path}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"写入文件失败: {str(e)}"
                }

    async def append_file(self, path: str, content: str) -> Dict[str, Any]:
        """追加文件内容"""
        async with self.lock:
            try:
                # 确保目录存在
                directory = os.path.dirname(path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)

                # 追加文件内容
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(content)

                return {
                    "success": True,
                    "message": f"内容已成功追加到: {path}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"追加到文件失败: {str(e)}"
                }

    async def replace_in_file(self, path: str, search: str, replace: str) -> Dict[str, Any]:
        """在文件中替换内容"""
        async with self.lock:
            try:
                # 确保文件存在
                if not os.path.exists(path):
                    return {
                        "success": False,
                        "error": f"文件未找到: {path}"
                    }

                # 读取文件内容
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 替换内容
                new_content = content.replace(search, replace)

                # 如果内容没有变化，返回警告
                if new_content == content:
                    return {
                        "success": True,
                        "warning": f"未进行替换: 在 {path} 中未找到搜索字符串"
                    }

                # 写入新内容
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                return {
                    "success": True,
                    "message": f"替换成功完成于: {path}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"替换文件内容失败: {str(e)}"
                }

    async def list_files(self, directory: str, recursive: bool = False) -> Dict[str, Any]:
        """列出目录中的文件"""
        async with self.lock:
            try:
                # 确保目录存在
                if not os.path.exists(directory):
                    return {
                        "success": False,
                        "error": f"目录未找到: {directory}"
                    }

                if not os.path.isdir(directory):
                    return {
                        "success": False,
                        "error": f"不是一个目录: {directory}"
                    }

                # 列出文件
                if recursive:
                    files = []
                    for root, dirs, filenames in os.walk(directory):
                        for filename in filenames:
                            files.append(os.path.join(root, filename))
                else:
                    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

                return {
                    "success": True,
                    "files": files
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"列出文件失败: {str(e)}"
                }


def register_plugin(agent_factory: Agently.AgentFactory):
    """注册文件编辑插件"""
    file_editor_plugin = FileEditorPlugin()

    # 注册插件
    agent_factory.register_plugin(
        "file_editor",
        {
            "read_file": {
                "func": file_editor_plugin.read_file,
                "description": "读取文件内容",
                "parameters": {
                    "path": {
                        "type": "string",
                        "description": "要读取的文件路径"
                    }
                }
            },
            "write_file": {
                "func": file_editor_plugin.write_file,
                "description": "写入文件内容（覆盖现有内容）",
                "parameters": {
                    "path": {
                        "type": "string",
                        "description": "要写入的文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入文件的内容"
                    }
                }
            },
            "append_file": {
                "func": file_editor_plugin.append_file,
                "description": "追加内容到文件",
                "parameters": {
                    "path": {
                        "type": "string",
                        "description": "要追加内容的文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "要追加到文件的内容"
                    }
                }
            },
            "replace_in_file": {
                "func": file_editor_plugin.replace_in_file,
                "description": "替换文件中的内容",
                "parameters": {
                    "path": {
                        "type": "string",
                        "description": "要修改的文件路径"
                    },
                    "search": {
                        "type": "string",
                        "description": "要搜索的字符串"
                    },
                    "replace": {
                        "type": "string",
                        "description": "要替换成的字符串"
                    }
                }
            },
            "list_files": {
                "func": file_editor_plugin.list_files,
                "description": "列出目录中的文件",
                "parameters": {
                    "directory": {
                        "type": "string",
                        "description": "要列出文件的目录"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "是否递归列出文件"
                    }
                }
            }
        }
    )

    logger.info("文件编辑插件已注册")
    return agent_factory
