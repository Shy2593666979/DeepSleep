from fastapi import APIRouter, Form, UploadFile, File, Depends

from deepsleep.api.services.agent import AgentService
from deepsleep.schema.schemas import resp_200, resp_500, UnifiedResponseModel
from deepsleep.settings import app_settings
from deepsleep.prompts.template import code_template, parameter_template
from deepsleep.api.services.user import UserPayload, get_login_user
from typing import List
from loguru import logger
from uuid import uuid4

router = APIRouter()

@router.post("/agent", response_model=UnifiedResponseModel)
async def create_agent(name: str = Form(...),
                       description: str = Form(...),
                       tools_id: List[str] = Form(default=[], description="绑定的工具id"),
                       llm_id: str = Form(None, description="Agent 绑定的LLM ID"),
                       mcp_ids: List[str] = Form(default=[], description="绑定的MCP Server"),
                       knowledges_id: List[str] = Form(default=[], description="绑定的知识库ID"),
                       use_embedding: bool = Form(True),
                       logoFile: UploadFile = File(None),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        # 判断Agent名字是否重复
        if AgentService.check_repeat_name(name=name, user_id=login_user.user_id):
            return resp_500(message="The Agent name is repeated, please change it")

        uid = uuid4().hex
        if logoFile is not None:
            logo = f"img/agent/{uid}.{logoFile.content_type.split('/')[-1]}"
            with open(logo, 'wb') as file:
                file.write(await logoFile.read())
        else:
            logo = app_settings.logo.get('agent')

        AgentService.create_agent(name=name,
                                  description=description,
                                  logo=logo,
                                  tools_id=tools_id,
                                  llm_id=llm_id,
                                  mcp_ids=mcp_ids,
                                  user_id=login_user.user_id,
                                  knowledges_id=knowledges_id,
                                  use_embedding=use_embedding)
        return resp_200()
    except Exception as err:
        logger.error(f"create agent API error: {err}")
        return resp_500(message=str(err))


@router.get("/agent", response_model=UnifiedResponseModel)
async def get_agent(login_user: UserPayload = Depends(get_login_user)):
    try:
        data = AgentService.get_all_agent_by_user_id(user_id=login_user.user_id)
        result = []
        for item in data:
            result.append({"id": item.id,
                           "name": item.name,
                           "description": item.description,
                           "logo": app_settings.logo.get('prefix') + item.logo,
                           "tools_id": item.tools_id,
                           "mcp_ids": item.mcp_ids,
                           "llm_id": item.llm_id,
                           "is_custom": item.is_custom,
                           "use_embedding": item.use_embedding,
                           "create_time": item.create_time})

        return resp_200(data=result)
    except Exception as err:
        logger.error(f"get agent API error: {err}")
        return resp_500(message=str(err))


@router.delete("/agent", response_model=UnifiedResponseModel)
async def delete_agent(agent_id: str = Form(...),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        return AgentService.delete_agent_by_id(id=agent_id, user_id=login_user.user_id)
    except Exception as err:
        logger.error(f"delete agent API error: {err}")
        return resp_500(message=str(err))


@router.put("/agent", response_model=UnifiedResponseModel)
async def update_agent(agent_id: str = Form(...),
                       name: str = Form(None),
                       description: str = Form(None),
                       tools_id: List[str] = Form(None),
                       knowledges_id: List[str] = Form(None),
                       mcp_ids: List[str] = Form(None),
                       llm_id: str = Form(None),
                       use_embedding: bool = Form(True),
                       logoFile: UploadFile = File(None),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        if name and AgentService.check_repeat_name(name, login_user.user_id):
            return resp_500(message='agent name repeated')

        uid = uuid4().hex
        if logoFile is not None:
            logo = f"img/agent/{uid}.{logoFile.content_type.split('/')[-1]}"
            with open(logo, 'wb') as file:
                file.write(await logoFile.read())
        else:
            logo = None

        return AgentService.update_agent_by_id(id=agent_id,
                                        name=name,
                                        description=description,
                                        logo=logo,
                                        knowledges_id=knowledges_id,
                                        user_id=login_user.user_id,
                                        tools_id=tools_id,
                                        llm_id=llm_id,
                                        mcp_ids=mcp_ids,
                                        use_embedding=use_embedding)

    except Exception as err:
        logger.error(f"update agent API error: {err}")
        return resp_500(message=str(err))


@router.post("/agent/search", response_model=UnifiedResponseModel)
async def search_agent(name: str = Form(...),
                       login_user: UserPayload = Depends(get_login_user)):
    try:
        data = AgentService.search_agent_name(name=name, user_id=login_user.user_id)
        result = []
        for item in data:
            result.append({"id": item.id,
                           "name": item.name,
                           "description": item.description,
                           "logo": app_settings.logo.get('prefix') + item.logo,
                           "tools_id": item.tools_id,
                           "llm_id": item.llm_id,
                           "mcp_ids": item.mcp_ids,
                           "use_embedding": item.use_embedding,
                           "is_custom": item.is_custom,
                           "create_time": item.create_time})

        return resp_200(data=result)
    except Exception as err:
        logger.error(f"search agent API error: {err}")
        return resp_500(message=str(err))


@router.get("/default/code", response_model=UnifiedResponseModel)
async def get_default_code(login_user: UserPayload = Depends(get_login_user)):
    return resp_200(data=code_template)


@router.get("/default/parameter", response_model=UnifiedResponseModel)
async def get_default_parameter(login_user: UserPayload = Depends(get_login_user)):
    return resp_200(data=parameter_template)
