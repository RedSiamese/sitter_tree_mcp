
import os
from typing import Dict, Optional, List, Set, Any, Tuple
from tree_sitter import Language, Parser, Node
import tree_sitter_cpp as tscpp

from .exceptions import ParserError
from .xml_formatter import format_xml
from .language_parsers_base import BaseParser
from .decode_type import guess_encoder

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
        # "declaration",
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
        
    def find_keywords_in_file(self, file_path: str, keywords: set[str], ignored_keywords: set[str]) -> set[str]:
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

            new_keywords: set[str] = set()
            encoder = guess_encoder(source_code)
            # 搜索关键字
            found, ast_dict = self._search_keyword_in_node(root_node, source_code, keywords, new_keywords, old_keywords, encoder=encoder)

            if not found:
                return set()
            
            return new_keywords
        except Exception as e:
            raise ParserError(f"在文件 {file_path} 中搜索关键字失败: {str(e)}")
        

    def _search_in_file(self, file_path: str, keywords: set[str]) -> Optional[str]:
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
            encoder = guess_encoder(source_code)
            # 搜索关键字
            found, ast_dict = self._search_keyword_in_node(root_node, source_code, keywords, set(), set(), encoder=encoder)

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
        tree = self._parse_file(path)
        root_node = tree.root_node
        with open(path, 'rb') as f:
            source_code = f.read()
        # print(keywords)
        encoder = guess_encoder(source_code)
        result_tree, used_keywords = self._find_def_node(path, root_node, source_code, keywords, old_keywords, encoder=encoder)

        return result_tree, used_keywords

    def _find_def_node(self, path:str, node: Node, source_code: bytes, keywords: set[str], old_keywords: set[str],*, encoder: str) -> Tuple[dict[str,dict], set[str]]:
        """
        遍历+递归，检查树中定义节点且名字在keywords中
        对于是的节点，将他的语法树加入结果语法树，将他涉及的其他关键字加入关键字列表，不搜索他的子节点
        对于不是的节点，继续搜他的子节点
        """
        tree = {}
        new_keywords = set()

        def _get_new_keywords(node: Node) -> set[str]:
            new_keywords = set()
            # print(node.type)
            for child in node.children:
                if child.type in ["primitive_type","type_identifier"] and (nkw := child.text.decode(encoder)) not in old_keywords:
                    new_keywords.add(nkw)
                new_keywords |= _get_new_keywords(child)
            return new_keywords

        def get_class_name(node):
            if node.children:
                for child in node.children:
                    if child.type == "type_identifier":
                        return child.text.decode(encoder)
            return ""
        
        def get_func_name(node):
            if node.children:
                for child in node.children:
                    if child.type == "identifier":
                        return child.text.decode(encoder)
            return ""
        
        def get_field_name(node):
            if node.children:
                for child in node.children:
                    if child.type == "field_identifier":
                        return child.text.decode(encoder)
            return ""
        
        def record(node:Node, name: str):
            nonlocal new_keywords
            ast_dict = self._node_to_dict(node, source_code, False)
            attributes = {
                "file": path,
                "language": "cpp",
                "mode": "overview"
            }

            tree_dict = {
                "attributes": attributes,
                "children": [ast_dict] if ast_dict else []
            }
            tree[f"{path}:{name} at line({node.start_point[0] + 1}-{node.end_point[0]+1})"] = tree_dict
            new_keywords |= _get_new_keywords(node)

        name = ""
        if node.type in ["struct_specifier", "class_specifier"]:
            name = get_class_name(node)
            if name in keywords:
                record(node, name)
        if node.type == "field_declaration":
            name = get_field_name(node)
            if name in keywords:
                record(node, name)
        if node.type == "function_declarator":
            name = get_func_name(node)
            if name in keywords:
                record(node, name)
        # if name:
        #     print(name)

        for child in node.children:
            t, kw = self._find_def_node(path, child, source_code, keywords, old_keywords, encoder=encoder)
            tree |= t
            new_keywords |= kw
        return tree, new_keywords
    
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


    def node_to_dict(self, file_path: str, detailed: bool) -> str:
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
            return tree_dict
        except Exception as e:
            raise ParserError(f"解析文件 {file_path} 到XML失败: {str(e)}")
    
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

        encoder = guess_encoder(source_code)
        
        # 如果是注释节点，只保留标签和行号信息，不添加任何文本内容
        if node_type in self.COMMENT_NODE_TYPES:
            return result
        else:   
            if node_type.endswith("declarator"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.parent.start_byte:node.end_byte].decode(encoder)
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                result["attributes"] |= {"text":text}
            if node_type.endswith("field_declaration"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode(encoder)
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                result["attributes"] |= {"text":text}
            if node_type.endswith("template_declaration"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode(encoder).split('>')[0]
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                result["attributes"] |= {"template_text":text}
            if node_type.endswith("specifier"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode(encoder).split(';')[0].split("{")[0]
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                result["attributes"] |= {"declaration_text":text}
        
        # 如果是叶子节点，添加文本内容
        if len(node.children) == 0:
            text = source_code[node.start_byte:node.end_byte].decode(encoder)
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
    

    
    def _search_keyword_in_node(self, node: Node, source_code: bytes, keywords: set[str], new_keywords: set[str], old_keywords: set[str], *, encoder: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
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
        node_text = source_code[node.start_byte:node.end_byte].decode(encoder)
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
        
        if node_type == "compound_statement":
            # 对于复合语句，直接返回   函数体
            return False, None
        
        # 处理子节点
        matching_children = []
        has_matching_child = False
        
        for child in node.children:
            child_match, child_dict = self._search_keyword_in_node(child, source_code, keywords, new_keywords, old_keywords, encoder=encoder)
            if child_match:
                has_matching_child = True
                matching_children.append(child_dict)
        
        # 如果当前节点或其子节点匹配关键字
        if exact_match or has_matching_child:
            result = {"type": node_type}
            if node_type == "type_identifier" and node_text not in old_keywords:
                # 对于类型标识符节点，添加到新关键字列表中
                new_keywords.add(node_text)
            else:
                for child in node.children:
                    if child.type == "type_identifier" and child.text.decode(encoder) not in old_keywords:
                        # 对于类型标识符节点，添加到新关键字列表中
                        new_keywords.add(child.text.decode(encoder))
            
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
                text = source_code[node.parent.start_byte:node.end_byte].decode(encoder)
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"] |= {"text":text}
            if node_type.endswith("field_declaration"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode(encoder)
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"] |= {"text":text}
            if node_type.endswith("template_declaration"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode(encoder).split('>')[0]
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"] |= {"template_text":text}
            if node_type.endswith("specifier"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode(encoder).split(';')[0].split("{")[0]
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"] |= {"declaration_text":text}
            if node_type.endswith("function_definition"):
                # 读取对应行区间的文本内容作为text
                text = source_code[node.start_byte:node.end_byte].decode(encoder).split('{')[0].split(';')[0]
                # 将所有非文本字符换成空格
                text = ' '.join(text.split())
                if "attributes" not in result:
                    result["attributes"] = {}
                result["attributes"] |= {"declaration_text":text}

            # 优化树结构：如果没有属性且只有一个子节点，直接返回子节点，省略当前节点
            has_attributes = "attributes" in result and len(result["attributes"]) > 0
            if not has_attributes and len(matching_children) == 1 and "attributes" not in matching_children[0]:
                return True, matching_children[0]
                
            return True, result
        
        return False, None
    
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
        kws = set()
        
        if os.path.isfile(src_path):
            # 处理单个文件
            if self._is_cpp_file(src_path):
                with open(src_path, 'rb') as f:
                    source_code = f.read()
                encoder = guess_encoder(source_code)
                # 读取指定行范围内的文本内容
                lines = source_code.decode(encoder).splitlines()
                context_lines = lines[max(start_line - 1, 0):end_line]

                # 将行内容连接成字符串
                context_str = "\n".join(context_lines)
                # print(context_str)
                # 转回为字节
                context_bytes = context_str.encode(encoder)
                tree = self.parser.parse(context_bytes)

                kws = self._find_all_kw(tree.root_node, context_bytes, encoder=encoder)
        return kws

    def _find_all_kw(self, node: Node, source_code: bytes, *, encoder: str) -> set[str]:
        """
        遍历+递归，检查树中定义节点且名字在keywords中
        对于是的节点，将他的语法树加入结果语法树，将他涉及的其他关键字加入关键字列表，不搜索他的子节点
        对于不是的节点，继续搜他的子节点
        """
        new_keywords = set()

        if node.type in ["type_identifier", "identifier", "field_identifier"] \
                and node.parent  \
                and (node.parent.type in ["struct_specifier", "class_specifier", "field_declaration", "function_declarator"]):
            name = node.text.decode(encoder)
            new_keywords.add(name)
        elif node.type in ["type_identifier", "field_identifier"] \
                and node.parent  \
                and (node.parent.type in ["struct_specifier", "class_specifier", "field_declaration", "function_declarator", "field_expression"]
                    or (node.parent.parent and node.parent.parent.type in ["call_expression", "declaration"])):
            name = node.text.decode(encoder)
            new_keywords.add(name)

        for child in node.children:
            kw = self._find_all_kw(child, source_code, encoder=encoder)
            new_keywords |= kw
        return new_keywords