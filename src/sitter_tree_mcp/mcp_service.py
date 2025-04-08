from typing import Annotated
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    ErrorData, Tool, TextContent, Prompt, PromptArgument, 
    GetPromptResult, PromptMessage, INVALID_PARAMS, INTERNAL_ERROR
)
from mcp.shared.exceptions import McpError
from pydantic import BaseModel, Field

from .impl import sitter_tree

# 定义请求模型
class ParseToTreeModel(BaseModel):
    code: Annotated[str, Field(description="要解析的源代码文件或目录")]

class FindNodesByTypeModel(BaseModel):
    code: Annotated[str, Field(description="要解析的源代码文件或目录")]
    keywords: Annotated[list[str], Field(description="待查找的关键字列表，"
                                         "关键字包括类名、结构体名、成员（函数、变量、方法）名、变量名等。"
                                         "每个关键字只能由单个名称组成（如\"func\"、\"Object\"），"
                                         "**不支持**查找表达式（如\"func(\"、\"new int\"等表达式）")]


async def serve():
    """运行语法树解析MCP服务"""
    server = Server("sitter-tree")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="parse_code",
                description="将源代码解析为语法树，返回xml格式的树结构。支持多种编程语言。",
                inputSchema=ParseToTreeModel.model_json_schema(),
            ),
            Tool(
                name="search_in_code",
                description="在源代码中查找一个或多个特定关键字（输入关键字列表，例如[\"func1\"]、[\"func1\", \"func2\"]等），"
                            "包括类名、结构体名、成员（函数、变量、方法）名，变量名等的节点，返回可能包含有相关节点信息的语法树分支。",
                inputSchema=FindNodesByTypeModel.model_json_schema(),
            ),
        ]
    
    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        return [
            Prompt(
                name="parse_code",
                description="将源代码解析为语法树，返回xml格式的树结构。支持多种编程语言。",
                arguments=[
                    PromptArgument(
                        name="code", 
                        description="要解析的源代码文件或目录", 
                        required=True
                    ),
                ],
            ),
            Prompt(
                name="search_in_code",
                description="在源代码中查找一个或多个特定关键字（输入关键字列表，例如[\"func1\"]、[\"func1\", \"func2\"]等），"
                            "包括类名、结构体名、成员（函数、变量、方法）名，变量名等的节点，返回可能包含有相关节点信息的语法树分支。",
                arguments=[
                    PromptArgument(
                        name="code", 
                        description="要解析的源代码文件或目录", 
                        required=True
                    ),
                    PromptArgument(
                        name="keywords", 
                        description="待查找的关键字列表，"
                                         "关键字包括类名、结构体名、成员（函数、变量、方法）名、变量名等。"
                                         "每个关键字只能由单个名称组成（如\"func\"、\"Object\"），"
                                         "**不支持**查找表达式（如\"func(\"、\"new int\"等表达式）", 
                        required=True
                    ),
                ],
            ),
        ]
        
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == "parse_code":
                try:
                    args = ParseToTreeModel(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                try:
                    tree = sitter_tree.parse_code(args.code)
                    return [TextContent(
                        type="text", 
                        text=json.dumps(tree, ensure_ascii=False, indent=2)
                    )]
                except Exception as e:
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"解析语法树失败: {str(e)}"))
            
            elif name == "search_in_code":
                try:
                    args = FindNodesByTypeModel(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                try:
                    nodes = sitter_tree.search_in_code(args.code, args.keywords)
                    return [TextContent(
                        type="text", 
                        text=json.dumps(nodes, ensure_ascii=False, indent=2)
                    )]
                except Exception as e:
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"查找节点失败: {str(e)}"))
            
            else:
                raise McpError(ErrorData(code=INVALID_PARAMS, message=f"未知工具: {name}"))
        except McpError:
            raise
        except Exception as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"服务器错误: {str(e)}"))
    
    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
        try:
            if name == "parse_code":
                if not arguments or "code" not in arguments:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message="code和language参数必须提供"))
                
                code = arguments["code"]
                
                try:
                    tree = sitter_tree.parse_code(code)
                    return GetPromptResult(
                        description="语法树解析结果",
                        messages=[
                            PromptMessage(
                                role="user", 
                                content=TextContent(
                                    type="text", 
                                    text=f"语法树解析结果:\n{json.dumps(tree, ensure_ascii=False, indent=2)}"
                                )
                            )
                        ]
                    )
                except Exception as e:
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"解析语法树失败: {str(e)}"))
            
            elif name == "search_in_code":
                if not arguments or "code" not in arguments or "keywords" not in arguments:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message="code、language和keywords参数必须提供"))
                
                code = arguments["code"]
                keywords = arguments["keywords"]
                
                try:
                    nodes = sitter_tree.search_in_code(code, keywords)
                    return GetPromptResult(
                        description="节点查找结果",
                        messages=[
                            PromptMessage(
                                role="user", 
                                content=TextContent(
                                    type="text", 
                                    text=f"查找到的节点列表:\n{json.dumps(nodes, ensure_ascii=False, indent=2)}"
                                )
                            )
                        ]
                    )
                except Exception as e:
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"查找节点失败: {str(e)}"))
            
            else:
                raise McpError(ErrorData(code=INVALID_PARAMS, message=f"未知提示: {name}"))
        except McpError:
            raise
        except Exception as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"服务器错误: {str(e)}"))

    # 运行服务器
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)
