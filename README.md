# CallAgent

## 项目概述
CallAgent 是一个基于 Python 的多智能体系统，允许多个 agent 之间进行通话讨论以完成任务。该系统使用 SQLite 数据库进行长期记忆存储，使用内存进行短期记忆存储，并记录多智能体间的规划、思考和讨论过程。

## 架构设计

### 系统架构

```
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
|    Agent 1        |<--->|    Agent Hub      |<--->|    Agent 2        |
|                   |     |                   |     |                   |
+-------------------+     +-------------------+     +-------------------+
         ^                        ^                        ^
         |                        |                        |
         v                        v                        v
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
|  Short-term Memory|     |  Long-term Memory |     |  Short-term Memory|
|  (Memory)         |     |  (SQLite)         |     |  (Memory)         |
|                   |     |                   |     |                   |
+-------------------+     +-------------------+     +-------------------+
```

### 核心组件

1. **Agent**：基于 Agently 框架实现的智能体，具有独立的思考、规划和执行能力。

2. **Agent Hub**：智能体通信中心，负责协调多个智能体之间的通信和任务分配。

3. **Memory Manager**：
   - **Short-term Memory**：存储在内存中的临时记忆，用于智能体的即时思考和决策。
   - **Long-term Memory**：存储在 SQLite 数据库中的持久记忆，包括历史对话、学习经验和知识库。

4. **Conversation Manager**：管理智能体之间的对话流程，记录对话内容，并将其存储到 SQLite 数据库中。

5. **Task Planner**：负责任务的分解、规划和分配，确保多个智能体能够协同工作。

6. **Database Manager**：管理 SQLite 数据库的连接、查询和更新操作。

## 实现思路

### 1. 多智能体通信机制

基于 Agently 框架的事件驱动模型，实现智能体之间的通信：

```python
# 伪代码示例
class Agent:
    def __init__(self, agent_id, name):
        self.agent_id = agent_id
        self.name = name
        self.short_term_memory = {}
        
    def send_message(self, recipient_id, message):
        # 通过 Agent Hub 发送消息
        AgentHub.send_message(self.agent_id, recipient_id, message)
        
    def receive_message(self, sender_id, message):
        # 处理接收到的消息
        response = self.process_message(sender_id, message)
        # 更新短期记忆
        self.update_short_term_memory(sender_id, message, response)
        return response
```

### 2. 记忆管理系统

#### 短期记忆（内存）

```python
class ShortTermMemory:
    def __init__(self):
        self.memory = {}
        
    def add(self, key, value, ttl=None):
        # 添加到内存中，可设置生存时间
        self.memory[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
        
    def get(self, key):
        # 获取内存中的数据，检查是否过期
        if key in self.memory:
            if self.memory[key]['ttl'] is None or \
               time.time() - self.memory[key]['timestamp'] < self.memory[key]['ttl']:
                return self.memory[key]['value']
        return None
        
    def clear_expired(self):
        # 清理过期的短期记忆
        current_time = time.time()
        keys_to_remove = []
        for key, data in self.memory.items():
            if data['ttl'] is not None and current_time - data['timestamp'] > data['ttl']:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self.memory[key]
```

#### 长期记忆（SQLite）

```python
class LongTermMemory:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()
        
    def init_db(self):
        # 初始化数据库表结构
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建记忆表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            memory_type TEXT,
            content TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建对话记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id TEXT,
            recipient_id TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建任务规划表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS planning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT,
            agent_id TEXT,
            plan_type TEXT,
            content TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        
    def store_memory(self, agent_id, memory_type, content, metadata=None):
        # 存储长期记忆
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO memories (agent_id, memory_type, content, metadata)
        VALUES (?, ?, ?, ?)
        ''', (agent_id, memory_type, content, json.dumps(metadata) if metadata else None))
        
        conn.commit()
        conn.close()
        
    def retrieve_memories(self, agent_id, memory_type=None, limit=10):
        # 检索长期记忆
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM memories WHERE agent_id = ?"
        params = [agent_id]
        
        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)
            
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        conn.close()
        return results
```

### 3. 对话和规划记录

```python
class ConversationManager:
    def __init__(self, db_path):
        self.db_path = db_path
        
    def record_conversation(self, sender_id, recipient_id, message):
        # 记录对话到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO conversations (sender_id, recipient_id, message)
        VALUES (?, ?, ?)
        ''', (sender_id, recipient_id, message))
        
        conn.commit()
        conn.close()
        
    def get_conversation_history(self, agent_id, limit=20):
        # 获取对话历史
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM conversations 
        WHERE sender_id = ? OR recipient_id = ?
        ORDER BY timestamp DESC LIMIT ?
        ''', (agent_id, agent_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        return results
```

```python
class PlanningManager:
    def __init__(self, db_path):
        self.db_path = db_path
        
    def record_planning(self, task_id, agent_id, plan_type, content, status="pending"):
        # 记录规划过程到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO planning (task_id, agent_id, plan_type, content, status)
        VALUES (?, ?, ?, ?, ?)
        ''', (task_id, agent_id, plan_type, content, status))
        
        conn.commit()
        conn.close()
        
    def update_planning_status(self, planning_id, status):
        # 更新规划状态
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE planning 
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (status, planning_id))
        
        conn.commit()
        conn.close()
```

### 4. Agent Hub 实现

```python
class AgentHub:
    def __init__(self, db_path):
        self.agents = {}
        self.db_path = db_path
        self.conversation_manager = ConversationManager(db_path)
        self.long_term_memory = LongTermMemory(db_path)
        
    def register_agent(self, agent):
        # 注册智能体
        self.agents[agent.agent_id] = agent
        
    def send_message(self, sender_id, recipient_id, message):
        # 发送消息并记录
        if recipient_id in self.agents:
            # 记录对话
            self.conversation_manager.record_conversation(sender_id, recipient_id, message)
            # 转发消息
            return self.agents[recipient_id].receive_message(sender_id, message)
        else:
            return f"Agent {recipient_id} not found"
            
    def broadcast_message(self, sender_id, message):
        # 广播消息给所有智能体
        responses = {}
        for agent_id, agent in self.agents.items():
            if agent_id != sender_id:
                # 记录对话
                self.conversation_manager.record_conversation(sender_id, agent_id, message)
                # 发送消息
                responses[agent_id] = agent.receive_message(sender_id, message)
        return responses
```

### 5. 任务规划与执行

```python
class TaskPlanner:
    def __init__(self, agent_hub, db_path):
        self.agent_hub = agent_hub
        self.planning_manager = PlanningManager(db_path)
        
    def create_task(self, task_description):
        # 创建任务
        task_id = str(uuid.uuid4())
        
        # 记录任务创建
        self.planning_manager.record_planning(
            task_id=task_id,
            agent_id="system",
            plan_type="task_creation",
            content=task_description
        )
        
        return task_id
        
    def decompose_task(self, task_id, subtasks):
        # 分解任务为子任务
        for i, subtask in enumerate(subtasks):
            subtask_id = f"{task_id}_{i}"
            self.planning_manager.record_planning(
                task_id=subtask_id,
                agent_id="system",
                plan_type="subtask",
                content=subtask
            )
        
    def assign_task(self, task_id, agent_id):
        # 分配任务给特定智能体
        self.planning_manager.record_planning(
            task_id=task_id,
            agent_id=agent_id,
            plan_type="assignment",
            content=f"Task {task_id} assigned to Agent {agent_id}"
        )
        
    def execute_task(self, task_id):
        # 执行任务
        # 获取任务详情
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM planning WHERE task_id = ? AND plan_type = 'task_creation'
        ''', (task_id,))
        
        task = cursor.fetchone()
        conn.close()
        
        if not task:
            return f"Task {task_id} not found"
            
        # 获取任务分配
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM planning WHERE task_id = ? AND plan_type = 'assignment'
        ''', (task_id,))
        
        assignment = cursor.fetchone()
        conn.close()
        
        if not assignment:
            return f"Task {task_id} not assigned to any agent"
            
        # 解析分配的智能体ID
        agent_id = assignment[2]  # agent_id 在第三列
        
        # 通知智能体执行任务
        message = f"Execute task: {task[4]}"  # content 在第五列
        response = self.agent_hub.send_message("system", agent_id, message)
        
        # 更新任务状态
        self.planning_manager.update_planning_status(task[0], "in_progress")
        
        return response
```

### 6. 基于 Agently 框架的实现

利用 Agently 框架的特性，我们可以实现更加灵活和强大的智能体系统：

```python
import agently
from agently.agent import Agent as AgentlyAgent

class CallAgent(AgentlyAgent):
    def __init__(self, agent_id, name, db_path, **kwargs):
        super().__init__(**kwargs)
        self.agent_id = agent_id
        self.name = name
        self.db_path = db_path
        self.short_term_memory = ShortTermMemory()
        self.long_term_memory = LongTermMemory(db_path)
        
    def think(self, context):
        # 记录思考过程
        thinking = super().think(context)
        
        # 存储思考过程到长期记忆
        self.long_term_memory.store_memory(
            agent_id=self.agent_id,
            memory_type="thinking",
            content=thinking,
            metadata={"context": context}
        )
        
        return thinking
        
    def plan(self, task):
        # 记录规划过程
        planning = super().plan(task)
        
        # 存储规划过程到长期记忆
        self.long_term_memory.store_memory(
            agent_id=self.agent_id,
            memory_type="planning",
            content=planning,
            metadata={"task": task}
        )
        
        return planning
        
    def execute(self, plan):
        # 执行计划
        result = super().execute(plan)
        
        # 存储执行结果到长期记忆
        self.long_term_memory.store_memory(
            agent_id=self.agent_id,
            memory_type="execution",
            content=result,
            metadata={"plan": plan}
        )
        
        return result
```

## 项目结构

```
CallAgent/
├── README.md                 # 项目文档
├── requirements.txt          # 项目依赖
├── main.py                   # 主程序入口
├── config.py                 # 配置文件
├── agents/
│   ├── __init__.py
│   ├── base_agent.py         # 基础智能体类
│   ├── specialized_agent.py  # 特定领域智能体
│   └── agent_factory.py      # 智能体工厂
├── memory/
│   ├── __init__.py
│   ├── short_term.py         # 短期记忆实现
│   └── long_term.py          # 长期记忆实现
├── communication/
│   ├── __init__.py
│   ├── agent_hub.py          # 智能体通信中心
│   └── conversation.py       # 对话管理
├── planning/
│   ├── __init__.py
│   ├── task_planner.py       # 任务规划
│   └── plan_executor.py      # 计划执行器
├── database/
│   ├── __init__.py
│   ├── db_manager.py         # 数据库管理
│   └── models.py             # 数据模型
└── utils/
    ├── __init__.py
    ├── logger.py             # 日志工具
    └── helpers.py            # 辅助函数
```

## 参考 OpenManus

本项目参考了 OpenManus 的多智能体协作模式，特别是在以下方面：

1. **智能体角色定义**：借鉴 OpenManus 中不同角色智能体的设计理念，定义了具有不同专长的智能体。

2. **协作机制**：参考了 OpenManus 的智能体协作机制，实现了基于消息传递的多智能体通信。

3. **记忆管理**：借鉴了 OpenManus 的记忆管理方式，区分短期记忆和长期记忆，并实现了记忆的存储和检索。

4. **任务规划**：参考了 OpenManus 的任务分解和规划方法，实现了任务的创建、分解、分配和执行。

## 实现步骤

1. 安装依赖：
   ```
   pip install agently sqlite3
   ```

2. 创建数据库和表结构：
   ```python
   from database.db_manager import DatabaseManager
   
   db_manager = DatabaseManager('call_agent.db')
   db_manager.init_db()
   ```

3. 创建智能体：
   ```python
   from agents.agent_factory import AgentFactory
   
   agent_factory = AgentFactory('call_agent.db')
   agent1 = agent_factory.create_agent('agent1', 'Research Agent')
   agent2 = agent_factory.create_agent('agent2', 'Planning Agent')
   ```

4. 设置智能体通信：
   ```python
   from communication.agent_hub import AgentHub
   
   hub = AgentHub('call_agent.db')
   hub.register_agent(agent1)
   hub.register_agent(agent2)
   ```

5. 创建和执行任务：
   ```python
   from planning.task_planner import TaskPlanner
   
   planner = TaskPlanner(hub, 'call_agent.db')
   task_id = planner.create_task('Research and summarize recent advancements in AI')
   planner.assign_task(task_id, 'agent1')
   result = planner.execute_task(task_id)
   ```

## 结论

CallAgent 项目通过实现多智能体通信、记忆管理和任务规划，为复杂任务的协作解决提供了一个灵活的框架。基于 Agently 框架的实现使得系统具有强大的扩展性和适应性，能够应对各种复杂场景的需求。

通过将长期记忆存储在 SQLite 数据库中，短期记忆存放在内存中，系统实现了高效的记忆管理。同时，多智能体间的规划、思考和讨论过程也被完整记录在数据库中，为后续的分析和改进提供了宝贵的数据支持。
