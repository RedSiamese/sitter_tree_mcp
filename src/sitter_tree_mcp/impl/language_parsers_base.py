import os
from typing import Dict, Any, Optional, Tuple, List, Set
from tree_sitter import Parser, Node

from .exceptions import ParserError
from .cache_manager import cache_manager

class BaseParser:
    """解析器基类，定义接口和通用方法"""
    
    # 节点类型映射，子类需要根据语言特性覆盖它
    # 这些节点类型在概览模式下被保留
    DEFINITION_NODE_TYPES = []
    COMMENT_NODE_TYPES = []
    
    def __init__(self, language_name: str):
        """
        初始化解析器
        
        Args:
            language_name: 语言名称
        """
        self.language_name = language_name
        self.parser = Parser()
        
    def parse_to_xml(self, path: str, detailed: bool = True) -> Dict[str, str]:
        """
        解析文件或目录到XML格式
        
        Args:
            path: 文件或目录路径
            detailed: 是否生成详细语法树
            
        Returns:
            XML格式的语法树
        """
        raise NotImplementedError("子类必须实现parse_to_xml方法")

    def node_to_dict(self, file_path: str, detailed: bool) -> dict[str, Any]:
        pass
    

    def search_in_xml(self, path: str, keywords: List[str]) -> Dict[str, str]:
        """
        在XML语法树中搜索关键字
        
        Args:
            path: 文件或目录路径
            keywords: 要搜索的关键字列表
            
        Returns:
            包含搜索结果的XML
        """
        raise NotImplementedError("子类必须实现search_in_xml方法")
    

    def search_define(self, path: str, keywords: set[str], old_keywords: set[str]) -> Tuple[dict[str,dict], set[str]]:
        """
        找到当前代码文件中，所有keywords的定义节点，组成语法树输出
        找到keywords的定义节点中使用过的别的keywords，组成列表输出
        
        Args:
            path: 文件或目录路径
            keywords: 要搜索的关键字列表
            
        Returns:
            tuple(
                str: 文件中包含的所有keywords的定义节点，组成的语法树
                list[str]: keywords的定义节点中使用过的别的keywords
            )
        """
        raise NotImplementedError("子类必须实现deep_search_in_xml方法")
    
    
    
    def find_keywords_in_file(self, file_path: str, keywords: set[str], ignored_keywords: set[str]) -> set[str]:
        """
        找到文件中所有keywords，忽略ignored_keywords，组成set输出
        """
        pass


    def _parse_file(self, file_path: str) -> Node:
        """
        解析单个文件到tree_sitter节点
        
        Args:
            file_path: 文件路径
            
        Returns:
            tree_sitter节点
        """
        # 检查缓存
        cached_tree = cache_manager.get_tree(file_path)
        if cached_tree:
            return cached_tree
        
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            tree = self.parser.parse(source_code)
            
            # 缓存解析结果
            cache_manager.set_tree(file_path, self.language_name, tree)
            
            return tree
        except Exception as e:
            raise ParserError(f"解析文件 {file_path} 失败: {str(e)}")

    @staticmethod
    def is_supported_file(file_path: str) -> bool:
        """
        检查文件是否受支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            如果文件类型受支持则返回True，否则返回False
        """
        from .parser_factory import ParserFactory
        return ParserFactory.detect_language(file_path) is not None
    
    @staticmethod
    def detect_language(file_path: str) -> Optional[str]:
        """
        从文件路径检测语言
        
        Args:
            file_path: 文件路径
            
        Returns:
            检测到的语言名称，如果无法检测则返回None
        """
        from .parser_factory import ParserFactory
        return ParserFactory.detect_language(file_path)

    def find_all_kw(self, src_path: str, start_line: int, end_line: int) -> set[str]:
        """
        查找指定行范围内的标识符
        
        Args:
            path: 文件路径
            start_line: 起始行号
            end_line: 结束行号
            
        Returns:
            文件路径到标识符字符串的映射字典
        """
        pass