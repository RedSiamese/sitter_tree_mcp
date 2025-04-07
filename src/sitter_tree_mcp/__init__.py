"""
语法树解析模块
提供代码语法树的解析和查询功能

主要组件:
- parse_code: 将源代码解析为语法树
- search_in_code: 在语法树中查找一系列关键字
- serve: 启动标准输入输出模式的MCP服务
"""

import os
import sys
import argparse
import asyncio
from .mcp_service import serve

def main():
    # """解析命令行参数并启动服务"""
    # parser = argparse.ArgumentParser(description='语法树解析服务')
    
    # args = parser.parse_args()
    
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动服务时发生错误: {str(e)}")
        sys.exit(1)

"""
sitter_tree_mcp - 基于 Tree-sitter 的代码语法树解析工具
"""

from .impl.sitter_tree import parse_code, search_in_code

__version__ = '0.1.0'
__all__ = ['parse_code', 'search_in_code']
