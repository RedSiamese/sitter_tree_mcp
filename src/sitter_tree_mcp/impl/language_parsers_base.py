import os
from typing import Dict, Any, Optional, Tuple, List
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
        
    def parse_to_xml(self, path: str, detailed: bool = True) -> str:
        """
        解析文件或目录到XML格式
        
        Args:
            path: 文件或目录路径
            detailed: 是否生成详细语法树
            
        Returns:
            XML格式的语法树
        """
        raise NotImplementedError("子类必须实现parse_to_xml方法")
    
    def search_in_xml(self, path: str, keywords: List[str]) -> str:
        """
        在XML语法树中搜索关键字
        
        Args:
            path: 文件或目录路径
            keywords: 要搜索的关键字列表
            
        Returns:
            包含搜索结果的XML
        """
        raise NotImplementedError("子类必须实现search_in_xml方法")
    
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
    
    def _contains_definition_node(self, node: Node) -> bool:
        """
        检查节点树中是否包含定义节点
        
        Args:
            node: tree_sitter节点
            
        Returns:
            如果节点树中包含任何定义节点则返回True
        """
        # 如果当前节点是定义节点，直接返回True
        if node.type in self.DEFINITION_NODE_TYPES:
            return True
        
        # 递归检查所有子节点
        for child in node.children:
            if self._contains_definition_node(child):
                return True
        
        return False

    def _node_to_dict(self, node: Node, source_code: bytes, detailed: bool = True) -> Optional[Dict[str, Any]]:
        """
        将tree_sitter节点转换为字典表示
        
        Args:
            node: tree_sitter节点
            source_code: 源代码字节
            detailed: 是否生成详细信息
            
        Returns:
            节点的字典表示，如果节点在概览模式下应该被忽略则返回None
        """
        node_type = node.type
        
        # 在概览模式下的判断逻辑
        if not detailed:
            # 如果是定义节点或注释节点，保留
            if node_type in self.DEFINITION_NODE_TYPES or node_type in self.COMMENT_NODE_TYPES:
                pass  # 继续处理
            # 如果不是定义节点或注释节点，检查子树是否包含定义节点
            elif not self._contains_definition_node(node):
                return None  # 如果不包含定义节点，则忽略此节点
        
        # 创建节点的基本信息
        result = {"type": node_type, "attributes":{}}
        
        # 添加行号范围(对于定义节点、声明节点和注释节点)
        if (node_type in self.DEFINITION_NODE_TYPES or 
            node_type in self.COMMENT_NODE_TYPES or 
            "declarat" in node_type):
            start_line, end_line = node.start_point[0] + 1, node.end_point[0] + 1
            result["attributes"] |= {"line_range": f"{start_line}-{end_line}"}
        
        # 如果是注释节点，只保留标签和行号信息，不添加任何文本内容
        if node_type in self.COMMENT_NODE_TYPES:
            return result
        else:   
            if node_type.endswith("declarator"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.parent.start_byte:node.end_byte].decode('utf-8')
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                result["attributes"] |= {"text":text}
            if node_type.endswith("field_declaration"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode('utf-8')
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                result["attributes"] |= {"text":text}
            if node_type.endswith("template_declaration"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode('utf-8').split('>')[0]
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                result["attributes"] |= {"template_text":text}
            if node_type.endswith("specifier"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode('utf-8').split(';')[0].split("{")[0]
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                result["attributes"] |= {"declaration_text":text}
        
        # 如果是叶子节点，添加文本内容
        if len(node.children) == 0:
            text = source_code[node.start_byte:node.end_byte].decode('utf-8')
            result["text"] = text
            return result
        
        # 处理子节点
        children = []
        for child in node.children:
            child_dict = self._node_to_dict(child, source_code, detailed)
            if child_dict:
                children.append(child_dict)
        
        if children:
            result["children"] = children
        
        return result
    
    def _search_keyword_in_node(self, node: Node, source_code: bytes, keywords: List[str]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        在节点中搜索关键字
        
        Args:
            node: tree_sitter节点
            source_code: 源代码字节
            keywords: 要搜索的关键字列表
            
        Returns:
            (是否找到关键字, 节点的字典表示)
        """
        node_type = node.type
        
        # 检查当前节点是否包含关键字
        node_text = source_code[node.start_byte:node.end_byte].decode('utf-8')
        exact_match = False
        
        # 精确匹配判断
        if node_text in keywords:
            exact_match = True
        
        # 如果是叶子节点且匹配关键字
        if len(node.children) == 0:
            if exact_match:
                # 创建带有match标记的节点
                result = {
                    "type": node_type,
                    "attributes": {
                        "match": "true",
                        "line_range": f"{node.start_point[0]+1}-{node.end_point[0]+1}",
                        "text": node_text
                    }
                }
                return True, result
            return False, None
        
        # 处理子节点
        matching_children = []
        has_matching_child = False
        
        for child in node.children:
            child_match, child_dict = self._search_keyword_in_node(child, source_code, keywords)
            if child_match:
                has_matching_child = True
                matching_children.append(child_dict)
        
        # 如果当前节点或其子节点匹配关键字
        if exact_match or has_matching_child:
            result = {"type": node_type}
            
            # 为所有定义节点和声明节点添加行号信息
            if node_type in self.DEFINITION_NODE_TYPES or "declarat" in node_type:
                start_line, end_line = node.start_point[0] + 1, node.end_point[0] + 1
                result["attributes"] = {"line_range": f"{start_line}-{end_line}"}
            
            # 如果是精确匹配，添加match属性
            if exact_match:
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"]["match"] = "true"
                result["attributes"]["line_range"] = f"{node.start_point[0]+1}-{node.end_point[0]+1}"
            
            # 添加匹配的子节点
            if matching_children:
                result["children"] = matching_children

            if node_type.endswith("declarator"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.parent.start_byte:node.end_byte].decode('utf-8')
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"] |= {"text":text}
            if node_type.endswith("field_declaration"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode('utf-8')
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"] |= {"text":text}
            if node_type.endswith("template_declaration"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode('utf-8').split('>')[0]
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"] |= {"template_text":text}
            if node_type.endswith("specifier"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode('utf-8').split(';')[0].split("{")[0]
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"] |= {"declaration_text":text}
            if node_type.endswith("function_definition"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode('utf-8').split('{')[0].split(';')[0]
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"] |= {"declaration_text":text}

            # 优化树结构：如果没有属性且只有一个子节点，直接返回子节点，省略当前节点
            has_attributes = "attributes" in result and len(result["attributes"]) > 0
            if not has_attributes and len(matching_children) == 1:
                return True, matching_children[0]
                
            return True, result
        
        return False, None

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
