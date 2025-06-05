from sqlmodel import SQLModel, create_engine
from deepsleep.database.models.agent import AgentTable
from deepsleep.database.models.history import HistoryTable
from deepsleep.database.models.user import SystemUser
from deepsleep.database.models.knowledge import KnowledgeTable
from deepsleep.database.models.knowledge_file import KnowledgeFileTable
from deepsleep.database.models.tool import ToolTable
from deepsleep.database.models.dialog import DialogTable
from deepsleep.database.models.mcp_server import MCPServerTable, MCPServerStdioTable
from deepsleep.database.models.mcp_agent import MCPAgentTable
from deepsleep.database.models.user_role import UserRole
from deepsleep.database.models.llm import LLMTable
from deepsleep.database.models.message import MessageDownTable, MessageLikeTable
from deepsleep.database.models.role import Role

from deepsleep.settings import app_settings

from dotenv import load_dotenv

# 加载本地的env
load_dotenv(override=True)

engine = create_engine(app_settings.mysql.get('endpoint'), connect_args={"charset": "utf8mb4"})

