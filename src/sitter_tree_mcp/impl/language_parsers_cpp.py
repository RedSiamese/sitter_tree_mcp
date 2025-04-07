import os
from typing import Dict, Optional, List
from tree_sitter import Language, Parser
import tree_sitter_cpp as tscpp

from .exceptions import ParserError
from .xml_formatter import format_xml
from .language_parsers_base import BaseParser

class CppParser(BaseParser):
    """C++语言解析器"""
    
    # C++语言中的定义节点类型
    DEFINITION_NODE_TYPES = [
        "function_definition", 
        "function_declarator",
        "class_declaration",
        "class_specifier", 
        "enum_specifier", 
        "struct_specifier",
        "namespace_definition",
        "template_declaration",
        "declaration",
        "field_declaration",
        "translation_unit",
        "preproc_include",
        # "type_identifier",
        # "identifier",
    ]
    
    # 注释节点类型
    # COMMENT_NODE_TYPES = ["comment"]
    COMMENT_NODE_TYPES = []
    
    def __init__(self):
        """初始化C++解析器"""
        super().__init__("cpp")
        
        # 修复: 使用正确的方式加载C++语言库
        try:
            # 正确初始化C++语言解析器
            cpp_language = Language(tscpp.language())
            self.parser = Parser(cpp_language)
        except Exception as e:
            raise ParserError(f"初始化C++解析器失败: {str(e)}")
    
    def parse_to_xml(self, path: str, detailed: bool = True) -> Dict[str, str]:
        """
        解析C++文件或目录到XML格式
        
        Args:
            path: 文件或目录路径
            detailed: 是否生成详细语法树
            
        Returns:
            文件路径到XML字符串的映射字典
        """
        result = {}
        
        if os.path.isfile(path):
            # 处理单个文件
            if self._is_cpp_file(path):
                xml_str = self._parse_file_to_xml(path, detailed)
                result[path] = xml_str
        elif os.path.isdir(path):
            # 递归处理目录
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._is_cpp_file(file_path):
                        xml_str = self._parse_file_to_xml(file_path, detailed)
                        result[file_path] = xml_str
        else:
            raise ParserError(f"路径不存在: {path}")
        
        return result
    
    def search_in_xml(self, path: str, keywords: List[str]) -> Dict[str, str]:
        """
        在C++文件或目录的语法树中搜索关键字
        
        Args:
            path: 文件或目录路径
            keywords: 要搜索的关键字列表
            
        Returns:
            文件路径到包含搜索结果的XML字符串的映射字典
        """
        result = {}
        
        if os.path.isfile(path):
            # 处理单个文件
            if self._is_cpp_file(path):
                xml_str = self._search_in_file(path, keywords)
                if xml_str:  # 只添加有搜索结果的文件
                    result[path] = xml_str
        elif os.path.isdir(path):
            # 递归处理目录
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._is_cpp_file(file_path):
                        xml_str = self._search_in_file(file_path, keywords)
                        if xml_str:  # 只添加有搜索结果的文件
                            result[file_path] = xml_str
        else:
            raise ParserError(f"路径不存在: {path}")
        
        return result
    
    def _is_cpp_file(self, file_path: str) -> bool:
        """
        检查文件是否是C++文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            如果是C++文件则返回True，否则返回False
        """
        cpp_extensions = ['.cpp', '.cc', '.cxx', '.c++', '.c', '.h', '.hpp', '.hxx', '.h++']
        _, ext = os.path.splitext(file_path)
        return ext.lower() in cpp_extensions
    
    def _parse_file_to_xml(self, file_path: str, detailed: bool) -> str:
        """
        解析单个C++文件到XML格式
        
        Args:
            file_path: 文件路径
            detailed: 是否生成详细语法树
            
        Returns:
            XML格式的语法树
        """
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            tree = self._parse_file(file_path)
            root_node = tree.root_node
            
            # 将节点转换为字典
            ast_dict = self._node_to_dict(root_node, source_code, detailed)
            
            # 添加文件元信息
            # file_name = os.path.basename(file_path)
            attributes = {
                "file": file_path,
                "language": "cpp"
            }
            
            if not detailed:
                attributes["mode"] = "overview"
            
            tree_dict = {
                "attributes": attributes,
                "children": [ast_dict] if ast_dict else []
            }
            # print(tree_dict)
            # 格式化为XML
            return format_xml(tree_dict)
        except Exception as e:
            raise ParserError(f"解析文件 {file_path} 到XML失败: {str(e)}")
    
    def _search_in_file(self, file_path: str, keywords: List[str]) -> Optional[str]:
        """
        在单个C++文件中搜索关键字
        
        Args:
            file_path: 文件路径
            keywords: 要搜索的关键字列表
            
        Returns:
            包含搜索结果的XML字符串，如果没有找到则返回None
        """
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            tree = self._parse_file(file_path)
            root_node = tree.root_node
            
            # 搜索关键字
            found, ast_dict = self._search_keyword_in_node(root_node, source_code, keywords)
            
            if not found:
                return None
            
            # 添加文件元信息
            attributes = {
                "file": file_path,
                "language": "cpp",
                "search_key": ", ".join(keywords) if isinstance(keywords, list) else keywords
            }
            
            tree_dict = {
                "attributes": attributes,
                "children": [ast_dict] if ast_dict else []
            }
            
            # 格式化为XML
            return format_xml(tree_dict)
        except Exception as e:
            raise ParserError(f"在文件 {file_path} 中搜索关键字失败: {str(e)}")