"""
网络搜索插件 - 基于Agently框架
"""
import asyncio
from typing import Dict, Any, List, Optional

import Agently

from app.utils.logger import Logger
from app.tools.web_search import WebSearch


class WebSearchPlugin:
    """网络搜索插件类"""

    def __init__(self):
        self.lock = asyncio.Lock()
        self.web_search = WebSearch()

    async def search(self, query: str, num_results: int = 5, fetch_content: bool = False) -> Dict[str, Any]:
        """执行网络搜索"""
        async with self.lock:
            try:
                # 执行搜索
                result = await self.web_search.execute(
                    query=query,
                    num_results=num_results,
                    fetch_content=fetch_content
                )

                # 格式化结果
                formatted_results = []
                for item in result.results:
                    formatted_result = {
                        "title": item.title,
                        "url": item.url,
                        "snippet": item.snippet
                    }
                    if fetch_content and hasattr(item, "content"):
                        formatted_result["content"] = item.content

                    formatted_results.append(formatted_result)

                return {
                    "success": True,
                    "query": query,
                    "results": formatted_results
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"执行网络搜索失败: {str(e)}"
                }


def register_plugin(agent_factory: Agently.AgentFactory):
    """注册网络搜索插件"""
    web_search_plugin = WebSearchPlugin()

    # 注册插件
    agent_factory.register_plugin(
        "web_search",
        {
            "search": {
                "func": web_search_plugin.search,
                "description": "执行网络搜索",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "返回结果数量（默认: 5）"
                    },
                    "fetch_content": {
                        "type": "boolean",
                        "description": "是否获取搜索结果的完整内容（默认: false）"
                    }
                }
            }
        }
    )

    Logger.info("网络搜索插件已注册")
    return agent_factory
