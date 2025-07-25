import asyncio
from uuid import uuid4

from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from deepsleep.api.services.llm import Function_Call_provider
from deepsleep.prompts.llm_prompt import react_prompt_en, fail_action_prompt, function_call_prompt
from deepsleep.prompts.template import function_call_template
from deepsleep.api.services.history import HistoryService
from deepsleep.api.services.tool import ToolService
from deepsleep.services.rag_handler import RagHandler
from deepsleep.tools import action_Function_call, action_React
from deepsleep.api.services.llm import LLMService
from deepsleep.services.mcp.manager import MCPManager
from deepsleep.api.services.mcp_stdio_server import MCPServerService
from loguru import logger
import inspect
import json

INCLUDE_MSG = {"content", "id"}

FUNCTION_CALL_MSG = "Function Call"
REACT_MSG = "React"

class ChatService:
    def __init__(self, **kwargs):
        self.llm_id = kwargs.get('llm_id')
        self.tools_id = kwargs.get('tool_id')
        self.dialog_id = kwargs.get('dialog_id')
        self.mcp_ids = kwargs.get("mcp_ids")
        self.embedding_id = kwargs.get('embedding_id')
        self.knowledges_id = kwargs.get('knowledge_id')
        self.mcp_manager = MCPManager(timeout=10)
        self.llm_call = None
        self.mcp_tools = None
        self.llm = None
        self.embedding = None
        self.tools = []


    async def init_agent(self):
        await self.init_mcp()
        await self.setup_llm()
        await self.setup_tools()
        await self.setup_mcp_tools()

    async def setup_llm(self):
        llm_config = LLMService.get_llm_by_id(llm_id=self.llm_id)
        self.llm = ChatOpenAI(model=llm_config.model,
                              base_url=llm_config.base_url, api_key=llm_config.api_key)

        self.llm_call = FUNCTION_CALL_MSG if llm_config.model in Function_Call_provider else REACT_MSG
        # Agent支持Embedding后初始化
        if self.embedding_id:
            await self.init_embedding()

    async def init_embedding(self):

        embedding_config = LLMService.get_llm_by_id(llm_id=self.embedding_id)
        self.embedding = OpenAIEmbeddings(model=embedding_config.model,
                                          base_url=embedding_config.base_url, api_key=embedding_config.api_key)

    async def init_mcp(self):
        servers = []
        for mcp_id in self.mcp_ids:
            server = MCPServerService.get_mcp_server_user(mcp_id)
            servers.append(server)

        await self.mcp_manager.connect_mcp_servers(servers)

    async def setup_mcp_tools(self):
        mcp_tools = await self.mcp_manager.get_mcp_tools()
        self.mcp_tools = mcp_tools

    async def setup_tools(self):
        tools_name = ToolService.get_tool_name_by_id(self.tools_id)
        if self.llm_call == REACT_MSG:
            for name in tools_name:
                func = action_React[name]
                self.tools.append(ChatService.function_to_json(func))
        else:
             for name in tools_name:
                self.tools.append(action_Function_call[name])


    async def run(self, user_input: str):

        # 都是通过检索RAG，并发可以减少消耗时间
        history_message, recall_knowledge_data = await asyncio.gather(
            self.get_history_message(user_input=user_input, dialog_id=self.dialog_id),
            RagHandler.rag_query(user_input, self.knowledges_id)
        )

        # history_message = await self.get_history_message(user_input=user_input, dialog_id=self.dialog_id)
        # recall_knowledge_data = await RagHandler.rag_query(user_input, self.knowledges_id)

        if self.llm_call == 'React':
            return self._run_react(user_input, history_message, recall_knowledge_data)
        else:
            return self._run_function_call(user_input, history_message, recall_knowledge_data)

    async def _run_react(self, user_input: str, history_message: str, recall_knowledge_data: str):
        agent = create_structured_chat_agent(llm=self.llm, tools=self.tools, prompt=react_prompt_en)
        agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

        async for chunk in agent_executor.astream({'input': user_input, 'history': history_message, 'recall_knowledge_data': recall_knowledge_data}):
            yield chunk.json(ensure_ascii=False, include=INCLUDE_MSG)

    async def _run_function_call(self, user_input: str, history_message: str, recall_knowledge_text: str):

        # 并发执行不同类型的工具
        tools_result, mcp_tools_result = asyncio.gather(
            self.call_common_tool(user_input, history_message),
            self.call_mcp_tool(user_input, history_message)
        )


        prompt_template = PromptTemplate.from_template(function_call_prompt)

        chain = prompt_template | self.llm
        async for chunk in chain.astream({'input': user_input, 'history': history_message, 'tools_result': tools_result, "mcp_tools_result": mcp_tools_result, "knowledge_result": recall_knowledge_text}):
            yield chunk.json(ensure_ascii=False, include=INCLUDE_MSG)

    async def call_common_tool(self, user_input, history_message):
        # 普通的插件调用
        func_prompt = function_call_template.format(input=user_input, history=history_message)
        fun_name, args = await self._function_call(user_input=func_prompt)
        tools_result = self.exec_tools(fun_name, args)
        return tools_result

    async def call_mcp_tool(self, user_input, history_message):
        # MCP 插件调用
        mcp_tool_prompt = function_call_template.format(input=user_input, history=history_message)
        mcp_tool_name, mcp_tool_args = await self._mcp_function_call(user_input=mcp_tool_prompt)
        mcp_tool_result = self.exec_mcp_tools(mcp_tool_name, mcp_tool_args)
        return mcp_tool_result

    async def _function_call(self, user_input: str):
        messages = [HumanMessage(content=user_input)]
        message = self.llm.invoke(
            messages,
            functions=self.tools,
        )
        try:
            if message.additional_kwargs:
                function_name = message.additional_kwargs["function_call"]["name"]
                arguments = json.loads(message.additional_kwargs["function_call"]["arguments"])

                logger.info(f"Function call result: \n function_name: {function_name} \n arguments: {arguments}")
                return function_name, arguments
            else:
                raise ValueError
        except Exception as err:
            logger.info(f"Function call is not appear: {err}")
            return None, None

    async def _mcp_function_call(self, user_input: str):
        messages = [HumanMessage(content=user_input)]
        message = self.llm.invoke(
            messages,
            functions=self.mcp_tools,
        )
        try:
            if message.additional_kwargs:
                function_name = message.additional_kwargs["function_call"]["name"]
                arguments = json.loads(message.additional_kwargs["function_call"]["arguments"])

                logger.info(f"Function call result: \n function_name: {function_name} \n arguments: {arguments}")
                return function_name, arguments
            else:
                raise ValueError
        except Exception as err:
            logger.info(f"Function call is not appear: {err}")
            return None, None

    async def exec_mcp_tools(self, mcp_tool_name, mcp_tool_args):
        mcp_tools_info = {
            "tool_name": mcp_tool_name,
            "tool_args": mcp_tool_args
        }
        mcp_tool_results = self.mcp_manager.call_mcp_tools([mcp_tools_info])
        return mcp_tool_results

    async def exec_tools(self, func_name, args):
        try:
            action = action_Function_call[func_name]
            result = action(**args)
            return result
        except Exception as err:
            logger.error(f"action appear error: {err}")
            return fail_action_prompt


    async def get_history_message(self, user_input: str, dialog_id: str, top_k: int = 5) -> str:
        # 如果绑定了Embedding模型，默认走RAG检索聊天记录
        if self.embedding:
            messages = await self._retrieval_history(user_input, dialog_id, top_k)
            return messages
        else:
            messages = await self._direct_history(dialog_id, top_k)

            result = ''
            for message in messages:
                result += message.to_str()
            return result

    @staticmethod
    async def _direct_history(dialog_id: str, top_k: int):
        messages = HistoryService.select_history(dialog_id=dialog_id, top_k=top_k)
        result = []
        for message in messages:
            result.append(message)
        return result

    # 使用RAG检索的方式将最近2 * top_k条数据按照相关性排序，取其中top_k个
    async def _retrieval_history(self, user_input: str, dialog_id: str, top_k: int):

        # messages = HistoryService.select_history(dialog_id=dialog_id, top_k=top_k * 2)
        #
        # for msg in messages:
        #     self.collection.add(documents=[msg.to_str()], ids=[uuid4().hex])
        #
        # results = self.collection.query(query_texts=[user_input], n_results=top_k)
        # history = ''.join(results['documents'][0])
        # return history
        messages = await RagHandler.rag_query(user_input, dialog_id, 0.6, top_k, False)
        return messages

    @staticmethod
    def function_to_json(func) -> dict:
        """
        Converts a Python function into a JSON-serializable dictionary
        that describes the function's signature, including its name,
        description, and parameters.

        Args:
            func: The function to be converted.

        Returns:
            A dictionary representing the function's signature in JSON format.
        """
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            type(None): "null",
        }

        try:
            signature = inspect.signature(func)
        except ValueError as e:
            raise ValueError(
                f"Failed to get signature for function {func.__name__}: {str(e)}"
            )

        parameters = {}
        for param in signature.parameters.values():
            try:
                param_type = type_map.get(param.annotation, "string")
            except KeyError as e:
                raise KeyError(
                    f"Unknown schema annotation {param.annotation} for parameter {param.name}: {str(e)}"
                )
            parameters[param.name] = {"schema": param_type}

        required = [
            param.name
            for param in signature.parameters.values()
            if param.default == inspect._empty
        ]

        return {
            "schema": "function",
            "function": {
                "name": func.__name__,
                "description": func.__doc__ or "",
                "parameters": {
                    "schema": "object",
                    "properties": parameters,
                    "required": required,
                },
            },
        }
