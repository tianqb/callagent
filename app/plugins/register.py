"""
插件注册模块 - 基于Agently框架
"""
import Agently

from app.utils.logger import Logger
from app.plugins.browser import register_plugin as register_browser_plugin
from app.plugins.python_execute import register_plugin as register_python_execute_plugin
from app.plugins.file_editor import register_plugin as register_file_editor_plugin
from app.plugins.web_search import register_plugin as register_web_search_plugin


def register_all_plugins(agent_factory: Agently.AgentFactory) -> Agently.AgentFactory:
    """注册所有插件"""
    Logger.info("正在注册所有插件...")

    # 注册浏览器插件
    agent_factory = register_browser_plugin(agent_factory)

    # 注册Python执行插件
    agent_factory = register_python_execute_plugin(agent_factory)

    # 注册文件编辑插件
    agent_factory = register_file_editor_plugin(agent_factory)

    # 注册网络搜索插件
    agent_factory = register_web_search_plugin(agent_factory)

    Logger.info("所有插件注册成功")
    return agent_factory
