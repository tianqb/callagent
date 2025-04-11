"""
浏览器插件 - 基于Agently框架
"""
import asyncio
import base64
import json
from typing import Dict, Any, Optional

import Agently
from browser_use import Browser as BrowserUseBrowser
from browser_use import BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.dom.service import DomService

from app.config import config
from utils.logger import logger


class BrowserPlugin:
    """浏览器插件类，封装浏览器操作功能"""

    def __init__(self):
        self.lock = asyncio.Lock()
        self.browser = None
        self.context = None
        self.dom_service = None

    async def _ensure_browser_initialized(self) -> BrowserContext:
        """确保浏览器和上下文已初始化"""
        if self.browser is None:
            browser_config_kwargs = {"headless": False, "disable_security": True}

            if config.browser_config:
                from browser_use.browser.browser import ProxySettings

                # 处理代理设置
                if config.browser_config.proxy and config.browser_config.proxy.server:
                    browser_config_kwargs["proxy"] = ProxySettings(
                        server=config.browser_config.proxy.server,
                        username=config.browser_config.proxy.username,
                        password=config.browser_config.proxy.password,
                    )

                browser_attrs = [
                    "headless",
                    "disable_security",
                    "extra_chromium_args",
                    "chrome_instance_path",
                    "wss_url",
                    "cdp_url",
                ]

                for attr in browser_attrs:
                    value = getattr(config.browser_config, attr, None)
                    if value is not None:
                        if not isinstance(value, list) or value:
                            browser_config_kwargs[attr] = value

            self.browser = BrowserUseBrowser(BrowserConfig(**browser_config_kwargs))

        if self.context is None:
            context_config = BrowserContextConfig()

            # 如果配置中有上下文配置，则使用它
            if (
                config.browser_config
                and hasattr(config.browser_config, "new_context_config")
                and config.browser_config.new_context_config
            ):
                context_config = config.browser_config.new_context_config

            self.context = await self.browser.new_context(context_config)
            self.dom_service = DomService(await self.context.get_current_page())

        return self.context

    async def cleanup(self):
        """清理浏览器资源"""
        async with self.lock:
            if self.context is not None:
                await self.context.close()
                self.context = None
                self.dom_service = None
            if self.browser is not None:
                await self.browser.close()
                self.browser = None

    async def go_to_url(self, url: str) -> Dict[str, Any]:
        """导航到指定URL"""
        async with self.lock:
            try:
                context = await self._ensure_browser_initialized()
                page = await context.get_current_page()
                await page.goto(url)
                await page.wait_for_load_state()

                # 获取当前状态
                state = await self.get_current_state()
                return {
                    "success": True,
                    "message": f"已导航到 {url}",
                    "state": state
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"导航到 {url} 失败: {str(e)}"
                }

    async def click_element(self, index: int) -> Dict[str, Any]:
        """点击指定索引的元素"""
        async with self.lock:
            try:
                context = await self._ensure_browser_initialized()
                element = await context.get_dom_element_by_index(index)
                if not element:
                    return {
                        "success": False,
                        "message": f"未找到索引为 {index} 的元素"
                    }

                download_path = await context._click_element_node(element)
                output = f"已点击索引为 {index} 的元素"
                if download_path:
                    output += f" - 已下载文件到 {download_path}"

                # 获取当前状态
                state = await self.get_current_state()
                return {
                    "success": True,
                    "message": output,
                    "state": state
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"点击索引为 {index} 的元素失败: {str(e)}"
                }

    async def input_text(self, index: int, text: str) -> Dict[str, Any]:
        """在指定索引的元素中输入文本"""
        async with self.lock:
            try:
                context = await self._ensure_browser_initialized()
                element = await context.get_dom_element_by_index(index)
                if not element:
                    return {
                        "success": False,
                        "message": f"未找到索引为 {index} 的元素"
                    }

                await context._input_text_element_node(element, text)

                # 获取当前状态
                state = await self.get_current_state()
                return {
                    "success": True,
                    "message": f"已在索引为 {index} 的元素中输入 '{text}'",
                    "state": state
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"输入文本失败: {str(e)}"
                }

    async def scroll_down(self, scroll_amount: Optional[int] = None) -> Dict[str, Any]:
        """向下滚动页面"""
        async with self.lock:
            try:
                context = await self._ensure_browser_initialized()
                amount = scroll_amount if scroll_amount is not None else context.config.browser_window_size["height"]
                await context.execute_javascript(f"window.scrollBy(0, {amount});")

                # 获取当前状态
                state = await self.get_current_state()
                return {
                    "success": True,
                    "message": f"已向下滚动 {amount} 像素",
                    "state": state
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"向下滚动失败: {str(e)}"
                }

    async def scroll_up(self, scroll_amount: Optional[int] = None) -> Dict[str, Any]:
        """向上滚动页面"""
        async with self.lock:
            try:
                context = await self._ensure_browser_initialized()
                amount = scroll_amount if scroll_amount is not None else context.config.browser_window_size["height"]
                await context.execute_javascript(f"window.scrollBy(0, -{amount});")

                # 获取当前状态
                state = await self.get_current_state()
                return {
                    "success": True,
                    "message": f"已向上滚动 {amount} 像素",
                    "state": state
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"向上滚动失败: {str(e)}"
                }

    async def scroll_to_text(self, text: str) -> Dict[str, Any]:
        """滚动到包含指定文本的元素"""
        async with self.lock:
            try:
                context = await self._ensure_browser_initialized()
                page = await context.get_current_page()
                locator = page.get_by_text(text, exact=False)
                await locator.scroll_into_view_if_needed()

                # 获取当前状态
                state = await self.get_current_state()
                return {
                    "success": True,
                    "message": f"已滚动到文本: '{text}'",
                    "state": state
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"滚动到文本失败: {str(e)}"
                }

    async def get_current_state(self) -> Dict[str, Any]:
        """获取当前浏览器状态"""
        try:
            # 使用提供的上下文或回退到self.context
            ctx = self.context
            if not ctx:
                return {"error": "浏览器上下文未初始化"}

            state = await ctx.get_state()

            # 如果不存在viewport_info，则创建一个
            viewport_height = 0
            if hasattr(state, "viewport_info") and state.viewport_info:
                viewport_height = state.viewport_info.height
            elif hasattr(ctx, "config") and hasattr(ctx.config, "browser_window_size"):
                viewport_height = ctx.config.browser_window_size.get("height", 0)

            # 为状态截图
            page = await ctx.get_current_page()

            await page.bring_to_front()
            await page.wait_for_load_state()

            screenshot = await page.screenshot(
                full_page=True, animations="disabled", type="jpeg", quality=100
            )

            screenshot_base64 = base64.b64encode(screenshot).decode("utf-8")

            # 构建状态信息
            state_info = {
                "url": state.url,
                "title": state.title,
                "tabs": [tab.model_dump() for tab in state.tabs],
                "help": "[0], [1], [2] 等表示可点击元素的索引。点击这些索引将导航到或与相应内容交互。",
                "interactive_elements": (
                    state.element_tree.clickable_elements_to_string()
                    if state.element_tree
                    else ""
                ),
                "scroll_info": {
                    "pixels_above": getattr(state, "pixels_above", 0),
                    "pixels_below": getattr(state, "pixels_below", 0),
                    "total_height": getattr(state, "pixels_above", 0)
                    + getattr(state, "pixels_below", 0)
                    + viewport_height,
                },
                "viewport_height": viewport_height,
                "screenshot": screenshot_base64
            }

            return state_info
        except Exception as e:
            return {"error": f"获取浏览器状态失败: {str(e)}"}


def register_plugin(agent_factory: Agently.AgentFactory):
    """注册浏览器插件"""
    browser_plugin = BrowserPlugin()

    # 注册插件
    agent_factory.register_plugin(
        "browser",
        {
            "go_to_url": {
                "func": browser_plugin.go_to_url,
                "description": "导航到指定URL",
                "parameters": {
                    "url": {
                        "type": "string",
                        "description": "要导航到的URL"
                    }
                }
            },
            "click_element": {
                "func": browser_plugin.click_element,
                "description": "点击指定索引的元素",
                "parameters": {
                    "index": {
                        "type": "integer",
                        "description": "要点击的元素索引"
                    }
                }
            },
            "input_text": {
                "func": browser_plugin.input_text,
                "description": "在指定索引的元素中输入文本",
                "parameters": {
                    "index": {
                        "type": "integer",
                        "description": "要输入文本的元素索引"
                    },
                    "text": {
                        "type": "string",
                        "description": "要输入的文本"
                    }
                }
            },
            "scroll_down": {
                "func": browser_plugin.scroll_down,
                "description": "向下滚动页面",
                "parameters": {
                    "scroll_amount": {
                        "type": "integer",
                        "description": "向下滚动的像素数（可选）"
                    }
                }
            },
            "scroll_up": {
                "func": browser_plugin.scroll_up,
                "description": "向上滚动页面",
                "parameters": {
                    "scroll_amount": {
                        "type": "integer",
                        "description": "向上滚动的像素数（可选）"
                    }
                }
            },
            "scroll_to_text": {
                "func": browser_plugin.scroll_to_text,
                "description": "滚动到页面上的文本",
                "parameters": {
                    "text": {
                        "type": "string",
                        "description": "要滚动到的文本"
                    }
                }
            },
            "get_current_state": {
                "func": browser_plugin.get_current_state,
                "description": "获取浏览器的当前状态",
                "parameters": {}
            }
        },
        cleanup_func=browser_plugin.cleanup
    )

    logger.info("浏览器插件已注册")
    return agent_factory
