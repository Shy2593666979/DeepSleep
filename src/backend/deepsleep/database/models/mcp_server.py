from typing import Optional

from sqlalchemy import Column, VARCHAR, JSON, text, DateTime
from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import uuid4, UUID
from deepsleep.database.models.base import SQLModelSerializable
import pytz

class MCPServerStdioTable(SQLModelSerializable, table=True):
    __tablename__ = "mcp_stdio_server"

    mcp_server_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    mcp_server_path: str = Field(description="MCP Server脚本所在位置")
    mcp_server_command: str = Field(description="MCP Server脚本执行命令, python or npx ...")
    mcp_server_env: str = Field(description="MCP Server脚本环境变量")
    user_id: str = Field(description='MCP Server对应的创建用户')
    name: str = Field(default="MCP Server", description="MCP Server名称")
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))



class MCPServerTable(SQLModelSerializable, table=True):
    __tablename__ = "mcp_server"

    mcp_server_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    mcp_server_name: str = Field(default="MCP Server", description="MCP Server名称")
    user_id: str = Field(description='MCP Server对应的创建用户')
    user_name: str = Field(description="MCP Server创建者的名称")
    url: str = Field(description="MCP Server的连接地址")
    type: str = Field(sa_column=Column(VARCHAR(255), nullable=False),
                      description="连接类型，只允许三种，sse、websocket、stdio")
    config: Optional[dict] = Field(sa_column=Column(JSON), description="配置，如apikey等")
    tools: str = Field(default="", description="MCP Server的工具列表")
    params: Optional[dict] = Field(sa_column=Column(JSON), description="输入参数")
    create_time: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    update_time: Optional[datetime] = Field(
        sa_column=Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'),
                         onupdate=text('CURRENT_TIMESTAMP')), description="修改时间"
    )