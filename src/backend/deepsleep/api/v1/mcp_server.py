from fastapi import APIRouter, Query, Body, Depends

from deepsleep.api.services.mcp_server import MCPService
from deepsleep.api.services.user import UserPayload, get_login_user
from deepsleep.schema.schemas import resp_500, resp_200
from deepsleep.services.mcp.manager import MCPManager
from loguru import logger

router = APIRouter()


@router.post("/mcp_server")
async def create_mcp_server(mcp_server_name: str = Body(..., description="MCP Server的名称"),
                            url: str = Body(..., description="MCP Server 的URL"),
                            type: str = Body(..., description="MCP Server 的连接方式，SSE、Websocket"),
                            config: str = Body({}, description="MCP Server 的配置信息"),
                            login_user: UserPayload = Depends(get_login_user)):
    try:
        mcp_manager = MCPManager()
        server_info = {
            "server_name": mcp_server_name,
            "type": type,
            "url": url
        }
        await mcp_manager.connect_mcp_servers([server_info])
        tools_params = await mcp_manager.show_mcp_tools()
        tools_name_str = []
        for key, tools in tools_params.items():
            for tool in tools:
                tools_name_str.append(tool["name"])
        MCPService.create_mcp_server(mcp_server_name, login_user.user_id, login_user.user_name,
                                     url, type, config, ",".join(tools_name_str), tools_params)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.get("/mcp_server")
async def get_mcp_servers(login_user: UserPayload = Depends(get_login_user)):
    try:
        mcp_servers = MCPService.get_all_servers(login_user.user_id)
        return resp_200(data=mcp_servers)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))

@router.delete("/mcp_server")
async def delete_mcp_server(mcp_server_id: str = Body(..., description="MCP Server 的ID"),
                            login_user: UserPayload = Depends(get_login_user)):
    try:
        MCPService.delete_server_from_id(mcp_server_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500()

# TODO：目前不支持修改MCP Server
@router.put("/mcp_server")
async def update_mcp_server(mcp_server_id: str = Body(..., description="MCP Server 的ID"),
                            mcp_server_name: str = Body(None, description="MCP Server的名称"),
                            url: str = Body(None, description="MCP Server 的URL"),
                            type: str = Body(None, description="MCP Server 的连接方式，SSE、Websocket"),
                            config: str = Body(None, description="MCP Server 的配置信息"),
                            login_user: UserPayload = Depends(get_login_user)):
    try:
        if url:
            mcp_manager = MCPManager()
            server_info = {
                "server_name": mcp_server_name,
                "type": type,
                "url": url
            }
            await mcp_manager.connect_mcp_servers([server_info])
            tools_params = await mcp_manager.show_mcp_tools()
            tools_str = []
            for key, tools in tools_params:
                for tool in tools:
                    tools_str.append(tool["name"])
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500()