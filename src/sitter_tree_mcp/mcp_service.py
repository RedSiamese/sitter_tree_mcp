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
from .impl.sitter_tree import deep_search_in_code, deep_search_context, get_block_context

# # 定义请求模型
class ParseToTreeModel(BaseModel):
    codes: Annotated[list[str], Field(description="要解析的 源代码文件或目录 的列表，即支持对多个源码文件解析。")]

# class ParentSearchModel(BaseModel):
#     codes: Annotated[list[str], Field(description="要解析的 源代码文件或目录 列表，即支持对多个源码文件解析并搜索。没有特殊需求可以直接传递代码根目录。")]
#     keywords: Annotated[list[str], Field(description="待搜索的标识符列表，"
#                                          "标识符包括类名、结构体名、成员（函数、变量、方法）名、变量名等。"
#                                          "每个标识符只能由单个名称组成（如\"func\"、\"Object\"），"
#                                          "**不支持**搜索表达式（如\"func(\"、\"new int\"等表达式）")]
#     depth: Annotated[int, Field(description="搜索深度，表示要递归解析的层数。0表示只搜索输入标识符，不递归。"
#                                          "1表示除了输入标识符，还扩展到搜索使用过输入标识符的相关标识符，依此类推。（通常填0）")]

# class ChildSearchModel(BaseModel):
#     codes: Annotated[list[str], Field(description="要解析的 源代码文件或目录 列表，即支持在多个源码文件中进行搜索。没有特殊需求可以直接传递代码根目录。")]
#     keywords: Annotated[list[str], Field(description="待搜索的标识符列表，"
#                                          "标识符包括类名、结构体名、成员（函数、变量、方法）名、变量名等。"
#                                          "每个标识符只能由单个名称组成（如\"func\"、\"Object\"），"
#                                          "**不支持**搜索表达式（如\"func(\"、\"new int\"等表达式）")]
#     depth: Annotated[int, Field(description="搜索深度，表示要递归解析的层数。0表示只搜索输入标识符，不递归。"
#                                          "1表示搜索标识符定义中的相关标识符，依此类推。（通常填3）")]

class ContextSearchModel(BaseModel):
    codes: Annotated[list[str], Field(description="要解析的源代码文件或目录列表，即支持在多个源码文件中进行上下文搜索。没有特殊需求可以直接传递代码根目录。")]
    keywords: Annotated[list[str], Field(description="待搜索的标识符列表，"
                                         "标识符包括类名、结构体名、成员（函数、变量、方法）名、变量名等。"
                                         "每个标识符只能由单个名称组成（如\"func\"、\"Object\"），"
                                         "**不支持**搜索表达式（如\"func(\"、\"new int\"等表达式）")]
    depth: Annotated[int, Field(description="上下文搜索深度，表示要递归解析的层数。0表示只搜索输入标识符的直接定义和使用。"
                                         "数字越大，分析的上下文范围越广。（通常填0-1）")]

class BlockContextModel(BaseModel):
    codes: Annotated[list[str], Field(description="要解析的源代码文件或目录列表，用于检索上下文信息。")]
    file_path: Annotated[str, Field(description="包含代码块的文件路径。")]
    start_line: Annotated[int, Field(description="代码块的起始行号。")]
    end_line: Annotated[int, Field(description="代码块的结束行号。")]
    depth: Annotated[int, Field(description="上下文搜索深度，表示要递归解析的层数。(通常填0-1)")]

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
            # Tool(
            #     name="search_child",
            #     description="在tree_sitter生成的源码语法结构中对该标识符所在的节点，进行后继结点（Child Node，该标识符节点所指向的节点）搜索。"
            #                 "根据广度优先搜索原则，先搜索该标识符的节点，再搜索该标识符节点指向的节点，再搜索该标识符节点指向的节点指向的节点，反复执行，直到达到指定的深度限制或图中没有额外的节点为止。"
            #                 "适用于例如已知基类搜派生类、派生类的派生类...，或者已知函数搜定义该函数的类、调用该函数的函数 等场合。"
            #                 "支持搜索一个或多个特定标识符（输入标识符列表，例如[\"func1\"]、[\"func1\", \"func2\"]等），"
            #                 "包括类名、结构体名、成员（函数、变量、方法）名，变量名等的节点，返回可能包含有相关节点信息的语法树分支。",
            #     inputSchema=ChildSearchModel.model_json_schema(),
            # ),
            # Tool(
            #     name="search_parent",
            #     description="在tree_sitter生成的源码语法结构中对该标识符所在的节点，进行前驱结点（Parent Node，指向该标识符的节点）搜索。"
            #                 "根据广度优先搜索原则，先搜索该标识符的节点，再搜索指向该标识符节点的节点，再搜索指向指向该标识符节点的节点，反复执行，直到达到指定的深度限制或图中没有额外的节点为止。" 
            #                 "适用于例如已知派生类搜基类，基类的基类...，或者已知函数搜该函数参数中使用的类 等场合。"
            #                 "支持搜索一个或多个特定标识符（输入标识符列表，例如[\"func1\"]、[\"func1\", \"func2\"]等），"
            #                 "包括类名、结构体名、成员（函数、变量、方法）名，变量名等的节点，返回可能包含有相关节点信息的语法树分支。",
            #     inputSchema=ParentSearchModel.model_json_schema(),
            # ),
            Tool(
                name="search_context",
                description="在源码中查找标识符的上下文信息，包括其定义、使用场景和相关联的其他标识符。"
                            "此工具在整个代码库中进行深度搜索，找出代码间的复杂关系和依赖。"
                            "适用于理解复杂代码结构、追踪标识符在整个项目中的使用情况等场景。",
                inputSchema=ContextSearchModel.model_json_schema(),
            ),
            Tool(
                name="block_context",
                description="分析代码块中使用的所有标识符，并查找它们的相关上下文信息。"
                            "此工具接收文件路径和行号范围，自动提取该范围内的所有标识符，然后查找它们的定义和用法。"
                            "适用于理解特定代码片段中使用的类型、函数和变量的完整上下文。",
                inputSchema=BlockContextModel.model_json_schema(),
            ),
        ]
    
    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        return [
            # Prompt(
            #     name="parse_code",
            #     description="将源代码解析为语法树，返回xml格式的树结构。支持多种编程语言。",
            #     arguments=[
            #         PromptArgument(
            #             name="codes", 
            #             description="要解析的 源代码文件或目录 的列表，即支持对多个源码文件解析。", 
            #             required=True
            #         ),
            #     ],
            # ),
            # Prompt(
            #     name="search_child",
            #     description="在tree_sitter生成的源码语法结构中对该标识符所在的节点，进行后继结点（Child Node，该标识符节点所指向的节点）搜索。"
            #                 "根据广度优先搜索原则，先搜索该标识符的节点，再搜索该标识符节点指向的节点，再搜索该标识符节点指向的节点指向的节点，反复执行，直到达到指定的深度限制或图中没有额外的节点为止。"
            #                 "适用于例如已知基类搜派生类、派生类的派生类...，或者已知函数搜定义该函数的类、调用该函数的函数 等场合。"
            #                 "支持搜索一个或多个特定标识符（输入标识符列表，例如[\"func1\"]、[\"func1\", \"func2\"]等），"
            #                 "包括类名、结构体名、成员（函数、变量、方法）名，变量名等的节点，返回可能包含有相关节点信息的语法树分支。",
            #     arguments=[
            #         PromptArgument(
            #             name="codes", 
            #             description="要解析的 源代码文件或目录 的列表，即支持对多个源码文件解析并搜索。没有特殊需求可以直接传递代码根目录。", 
            #             required=True
            #         ),
            #         PromptArgument(
            #             name="keywords", 
            #             description="待搜索的标识符列表，"
            #                              "标识符包括类名、结构体名、成员（函数、变量、方法）名、变量名等。"
            #                              "每个标识符只能由单个名称组成（如\"func\"、\"Object\"），"
            #                              "**不支持**搜索表达式（如\"func(\"、\"new int\"等表达式）", 
            #             required=True
            #         ),
            #         PromptArgument(
            #             name="depth", 
            #             description="搜索深度，表示要往回解析的层数。0表示只搜索输入标识符，不递归。"
            #                              "1表示除了输入标识符，还扩展到搜索使用过输入标识符的相关标识符，依此类推。（通常填2）", 
            #             required=True
            #         ),
            #     ],
            # ),
            # Prompt(
            #     name="search_parent",
            #     description="在tree_sitter生成的源码语法结构中对该标识符所在的节点，进行前驱结点（Parent Node，指向该标识符的节点）搜索。"
            #                 "根据广度优先搜索原则，先搜索该标识符的节点，再搜索指向该标识符节点的节点，再搜索指向指向该标识符节点的节点，反复执行，直到达到指定的深度限制或图中没有额外的节点为止。" 
            #                 "适用于例如已知派生类搜基类，基类的基类...，或者已知函数搜该函数参数中使用的类 等场合。"
            #                 "支持搜索一个或多个特定标识符（输入标识符列表，例如[\"func1\"]、[\"func1\", \"func2\"]等），"
            #                 "包括类名、结构体名、成员（函数、变量、方法）名，变量名等的节点，返回可能包含有相关节点信息的语法树分支。",
            #     arguments=[
            #         PromptArgument(
            #             name="codes", 
            #             description="要解析的源代码文件或目录列表，即支持在多个源码文件中进行搜索。没有特殊需求可以直接传递代码根目录。", 
            #             required=True
            #         ),
            #         PromptArgument(
            #             name="keywords", 
            #             description="待搜索的标识符列表，"
            #                              "标识符包括类名、结构体名、成员（函数、变量、方法）名、变量名等。"
            #                              "每个标识符只能由单个名称组成（如\"func\"、\"Object\"），"
            #                              "**不支持**搜索表达式（如\"func(\"、\"new int\"等表达式）", 
            #             required=True
            #         ),
            #         PromptArgument(
            #             name="depth", 
            #             description="搜索深度，表示要递归解析的层数。0表示只搜索输入标识符，不递归。"
            #                              "1表示搜索标识符定义中的相关标识符，依此类推。（通常填3）", 
            #             required=True
            #         ),
            #     ],
            # ),
            Prompt(
                name="search_context",
                description="在源码中查找标识符的上下文信息，包括其定义、使用场景和相关联的其他标识符。"
                            "此工具在整个代码库中进行深度搜索，找出代码间的复杂关系和依赖。"
                            "适用于理解复杂代码结构、追踪标识符在整个项目中的使用情况等场景。",
                arguments=[
                    PromptArgument(
                        name="codes", 
                        description="要解析的源代码文件或目录列表，即支持在多个源码文件中进行搜索。没有特殊需求可以直接传递代码根目录。", 
                        required=True
                    ),
                    PromptArgument(
                        name="keywords", 
                        description="待搜索的标识符列表，标识符包括类名、结构体名、成员名、变量名等。", 
                        required=True
                    ),
                    PromptArgument(
                        name="depth", 
                        description="搜索深度，表示要递归解析的层数。通常填0-1。", 
                        required=True
                    ),
                ],
            ),
            Prompt(
                name="block_context",
                description="分析代码块中使用的所有标识符，并查找它们的相关上下文信息。"
                            "此工具接收文件路径和行号范围，自动提取该范围内的所有标识符，然后查找它们的定义和用法。"
                            "适用于理解特定代码片段中使用的类型、函数和变量的完整上下文。",
                arguments=[
                    PromptArgument(
                        name="codes", 
                        description="要解析的源代码文件或目录列表，用于检索上下文信息。", 
                        required=True
                    ),
                    PromptArgument(
                        name="file_path", 
                        description="包含代码块的文件路径。", 
                        required=True
                    ),
                    PromptArgument(
                        name="start_line", 
                        description="代码块的起始行号。", 
                        required=True
                    ),
                    PromptArgument(
                        name="end_line", 
                        description="代码块的结束行号。", 
                        required=True
                    ),
                    PromptArgument(
                        name="depth", 
                        description="上下文搜索深度，通常填0-1。", 
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
                    tree = sitter_tree.parse_code(args.codes)
                    return [TextContent(
                        type="text", 
                        text="\n\n".join([
                            f"文件: {file_path}\n{xml_str}"
                            for file_path, xml_str in tree.items()
                        ]) if tree else "未找到相关节点"
                        # text=json.dumps(tree, ensure_ascii=False, indent=2)
                    )]
                except Exception as e:
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"解析语法树失败: {str(e)}"))
            
            # elif name == "search_parent":
            #     try:
            #         args = ParentSearchModel(**arguments)
            #     except ValueError as e:
            #         raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
            #     try:
            #         nodes = sitter_tree.search_in_code(args.codes, args.keywords, args.depth)
            #         return [TextContent(
            #             type="text", 
            #             text="\n\n".join([
            #                 f"文件: {file_path}\n{xml_str}"
            #                 for file_path, xml_str in nodes.items()
            #             ]) if nodes else "未找到相关节点"
            #             # text=json.dumps(nodes, ensure_ascii=False, indent=2)
            #         )]
            #     except Exception as e:
            #         raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"搜索节点失败: {str(e)}"))
            
            # elif name == "search_child":
            #     try:
            #         args = ChildSearchModel(**arguments)
            #     except ValueError as e:
            #         raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
            #     try:
            #         nodes = deep_search_in_code(args.codes, args.keywords, args.depth)
            #         return [TextContent(
            #             type="text", 
            #             text="\n\n".join([
            #                 f"文件: {file_path}\n{xml_str}"
            #                 for file_path, xml_str in nodes.items()
            #             ]) if nodes else "未找到相关节点"
            #         )]
            #     except Exception as e:
            #         raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"深度搜索失败: {str(e)}"))
                
            elif name == "search_context":
                try:
                    args = ContextSearchModel(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                try:
                    nodes = deep_search_context(args.codes, args.keywords, args.depth)
                    return [TextContent(
                        type="text", 
                        text="\n\n".join([
                            f"文件: {file_path}\n{xml_str}"
                            for file_path, xml_str in nodes.items()
                        ]) if nodes else "未找到相关节点"
                    )]
                except Exception as e:
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"上下文搜索失败: {str(e)}"))
            
            elif name == "block_context":
                try:
                    args = BlockContextModel(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                try:
                    nodes = get_block_context(args.codes, args.file_path, args.start_line, args.end_line, args.depth)
                    return [TextContent(
                        type="text", 
                        text="\n\n".join([
                            f"文件: {file_path}\n{xml_str}"
                            for file_path, xml_str in nodes.items()
                        ]) if nodes else "未找到相关上下文信息"
                    )]
                except Exception as e:
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"代码块上下文分析失败: {str(e)}"))
            
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
                if not arguments or "codes" not in arguments:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message="code和language参数必须提供"))
                
                codes = arguments["codes"]
                
                try:
                    tree = sitter_tree.parse_code(codes)
                    return GetPromptResult(
                        description="语法树解析结果",
                        messages=[
                            PromptMessage(
                                role="user", 
                                content=TextContent(
                                    type="text", 
                                    text="\n\n".join([
                                        f"文件: {file_path}\n{xml_str}"
                                        for file_path, xml_str in tree.items()
                                    ]) if tree else "未找到相关节点"
                                    # text=f"语法树解析结果:\n{json.dumps(tree, ensure_ascii=False, indent=2)}"
                                )
                            )
                        ]
                    )
                except Exception as e:
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"解析语法树失败: {str(e)}"))
            
            # elif name == "search_parent":
            #     if not arguments or "codes" not in arguments or "keywords" not in arguments or "depth" not in arguments:
            #         raise McpError(ErrorData(code=INVALID_PARAMS, message="code、language和keywords参数必须提供"))
                
            #     codes = arguments["codes"]
            #     keywords = arguments["keywords"]
            #     depth = arguments["depth"]
            #     try:
            #         nodes = sitter_tree.search_in_code(codes, keywords, depth)
            #         return GetPromptResult(
            #             description="节点搜索结果",
            #             messages=[
            #                 PromptMessage(
            #                     role="user", 
            #                     content=TextContent(
            #                         type="text", 
            #                         text="\n\n".join([
            #                             f"文件: {file_path}\n{xml_str}"
            #                             for file_path, xml_str in nodes.items()
            #                         ]) if nodes else "未找到相关节点"
            #                         # text=f"搜索到的节点列表:\n{json.dumps(nodes, ensure_ascii=False, indent=2)}"
            #                     )
            #                 )
            #             ]
            #         )
            #     except Exception as e:
            #         raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"搜索节点失败: {str(e)}"))
            
            # elif name == "search_child":
            #     if not arguments or "codes" not in arguments or "keywords" not in arguments or "depth" not in arguments:
            #         raise McpError(ErrorData(code=INVALID_PARAMS, message="code、keywords和depth参数必须提供"))
                
            #     codes = arguments["codes"]
            #     keywords = arguments["keywords"]
            #     depth = arguments["depth"]
                
            #     try:
            #         nodes = deep_search_in_code(codes, keywords, depth)
            #         return GetPromptResult(
            #             description="深度搜索结果",
            #             messages=[
            #                 PromptMessage(
            #                     role="user", 
            #                     content=TextContent(
            #                         type="text", 
            #                         text="\n\n".join([
            #                             f"文件: {file_path}\n{xml_str}"
            #                             for file_path, xml_str in nodes.items()
            #                         ]) if nodes else "未找到相关节点"
            #                     )
            #                 )
            #             ]
            #         )
            #     except Exception as e:
            #         raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"深度搜索失败: {str(e)}"))
                
            elif name == "search_context":
                if not arguments or "codes" not in arguments or "keywords" not in arguments or "depth" not in arguments:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message="codes、keywords和depth参数必须提供"))
                
                codes = arguments["codes"]
                keywords = arguments["keywords"]
                depth = arguments["depth"]
                
                try:
                    nodes = deep_search_context(codes, keywords, depth)
                    return GetPromptResult(
                        description="上下文搜索结果",
                        messages=[
                            PromptMessage(
                                role="user", 
                                content=TextContent(
                                    type="text", 
                                    text="\n\n".join([
                                        f"文件: {file_path}\n{xml_str}"
                                        for file_path, xml_str in nodes.items()
                                    ]) if nodes else "未找到相关节点"
                                )
                            )
                        ]
                    )
                except Exception as e:
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"上下文搜索失败: {str(e)}"))
            
            elif name == "block_context":
                if not arguments or "codes" not in arguments or "file_path" not in arguments or \
                   "start_line" not in arguments or "end_line" not in arguments or "depth" not in arguments:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message="codes、file_path、start_line、end_line和depth参数必须提供"))
                
                codes = arguments["codes"]
                file_path = arguments["file_path"]
                start_line = int(arguments["start_line"])
                end_line = int(arguments["end_line"])
                depth = int(arguments["depth"])
                
                try:
                    nodes = get_block_context(codes, file_path, start_line, end_line, depth)
                    return GetPromptResult(
                        description="代码块上下文分析结果",
                        messages=[
                            PromptMessage(
                                role="user", 
                                content=TextContent(
                                    type="text", 
                                    text="\n\n".join([
                                        f"文件: {file_path}\n{xml_str}"
                                        for file_path, xml_str in nodes.items()
                                    ]) if nodes else "未找到相关上下文信息"
                                )
                            )
                        ]
                    )
                except Exception as e:
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"代码块上下文分析失败: {str(e)}"))
            
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
