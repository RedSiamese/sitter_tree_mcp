import os
import argparse
from typing import Dict, Optional, List

from .parser_factory import ParserFactory
from .exceptions import SitterTreeError
from .xml_formatter import format_xml

def parse_code(paths: list[str], detailed: bool = False) -> Dict[str, str]:
    """
    解析代码文件或目录，生成XML格式的语法树
    
    Args:
        path: 文件或目录路径
        detailed: 是否生成详细语法树
        
    Returns:
        文件路径到XML字符串的映射字典
    """
    try:
        result = {}
        print(paths)
        for path in paths:
            if os.path.isfile(path):
                # 处理单个文件
                try:
                    # 通过文件扩展名自动检测语言
                    language = ParserFactory.detect_language(path)
                    if language:
                        parser = ParserFactory.create_parser(language)
                        xml_str = parser.parse_to_xml(path, detailed)
                        result.update(xml_str)
                    else:
                        print(f"无法识别文件类型: {path}")
                except Exception as e:
                    print(f"解析文件失败: {path}, 错误: {str(e)}")
            
            elif os.path.isdir(path):
                # 递归处理目录中的每个文件
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            # 通过文件扩展名自动检测语言
                            language = ParserFactory.detect_language(file_path)
                            if language:
                                parser = ParserFactory.create_parser(language)
                                xml_str = parser.parse_to_xml(file_path, detailed)
                                result.update(xml_str)
                        except Exception as e:
                            print(f"解析文件失败: {file_path}, 错误: {str(e)}")
                            continue
            else:
                raise SitterTreeError(f"路径不存在: {path}")
        
        return result
    except Exception as e:
        print(f"未预期的错误: {str(e)}")
        return {}

def search_in_code(paths: list[str], keywords: List[str], depth:int = 0) -> Dict[str, str]:
    """
    在代码文件或目录中搜索关键字
    
    Args:
        path: 文件或目录路径
        keyword: 要搜索的关键字
        
    Returns:
        文件路径到包含搜索结果的XML字符串的映射字典
    """
    try:
        result = {}
        _paths = []
        for path in paths:
            if os.path.isfile(path):
                _paths.append(path)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        _paths.append(file_path)
        _keywords = set(keywords)
        deep = 0
        next_keywords = set()
        old_keywords = set(keywords)
        
        while _keywords and deep < depth:
            for file_path in _paths:
                language = ParserFactory.detect_language(file_path)
                if language:
                    parser = ParserFactory.create_parser(language)
                    new_keywords = parser.find_keywords_in_file(file_path, _keywords, old_keywords)
                    next_keywords.update(new_keywords)

            old_keywords.update(next_keywords)
            _keywords = next_keywords
            next_keywords = set()
            deep += 1

        for path in _paths:
            try:
                # 通过文件扩展名自动检测语言
                language = ParserFactory.detect_language(path)
                if language:
                    parser = ParserFactory.create_parser(language)
                    xml_str = parser.search_in_xml(path, old_keywords)
                    result.update(xml_str)
                else:
                    print(f"无法识别文件类型: {path}")
            except Exception as e:
                print(f"在文件中搜索失败: {path}, 错误: {str(e)}")
        
        return result
    except Exception as e:
        print(f"未预期的错误: {str(e)}")
        return {}

def deep_search_in_code(paths: List[str], keywords: List[str], depth: int=0) -> Dict[str, str]:
    """
    在代码文件或目录中进行深度关键字搜索
    
    根据广度优先搜索思想，搜索给定关键字并递归查找相关标识符：
    - 如果关键字是函数，将其返回值类型、输入参数类型各节点标识符加入到关键字列表
    - 如果关键字是变量，将其类型中的各节点标识符加入到关键字列表
    - 如果关键字是类，将其成员函数名、函数返回值类型、输入参数类型、成员变量的类型中的各节点标识符加入到关键字列表
    
    Args:
        path: 文件或目录路径
        keywords: 要搜索的初始关键字列表
        depth: 搜索深度限制，0表示只搜索输入的关键字，不递归查找
        
    Returns:
        文件路径到包含搜索结果的XML字符串的映射字典
    """
    try:
        
        result = {}
        _paths = []
        for path in paths:
            if os.path.isfile(path):
                _paths.append(path)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        _paths.append(file_path)
        _keywords = set(keywords)
        deep = 0
        next_keywords = set()
        old_keywords = set()

        while _keywords and deep < depth + 1:
            for file_path in _paths:
                language = ParserFactory.detect_language(file_path)
                if language:
                    parser = ParserFactory.create_parser(language)
                    tree, new_kw = parser.search_define(file_path, _keywords, old_keywords)
                    next_keywords.update(new_kw)
                    result |= tree
            old_keywords.update(_keywords)
            _keywords = next_keywords
            next_keywords = set()
            deep += 1

        print(f"old_keywords: {old_keywords}")

        return {k:format_xml(d) for  k, d in result.items()}

        # result = [f"## {k}\n{format_xml(d)}" for k, d in result.items()]
                 
        # return "\n\n".join(result)
    except Exception as e:
        print(f"未预期的错误: {str(e)}")
        return {}





def deep_search_context(paths: List[str], keywords: List[str], depth: int=0) -> Dict[str, str]:
    """
    在代码文件或目录中查找关键字的上下文
    
    根据广度优先搜索思想，搜索给定关键字并递归查找相关标识符：
    - 如果关键字是函数，将其返回值类型、输入参数类型各节点标识符加入到关键字列表
    - 如果关键字是变量，将其类型中的各节点标识符加入到关键字列表
    - 如果关键字是类，将其成员函数名、函数返回值类型、输入参数类型、成员变量的类型中的各节点标识符加入到关键字列表
    
    Args:
        path: 文件或目录路径
        keywords: 要搜索的初始关键字列表
        depth: 搜索深度限制，0表示只搜索输入的关键字，不递归查找
        
    Returns:
        文件路径到包含搜索结果的XML字符串的映射字典
    """
    try:
        
        result = {}
        _paths = []
        for path in paths:
            if os.path.isfile(path):
                _paths.append(path)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        _paths.append(file_path)
        _keywords = set(keywords)
        deep = 0
        next_keywords = set()
        old_keywords = set()

        while _keywords and deep < depth + 1:
            for file_path in _paths:
                language = ParserFactory.detect_language(file_path)
                if language:
                    parser = ParserFactory.create_parser(language)
                    tree, new_kw = parser.search_define(file_path, _keywords, old_keywords)
                    next_keywords.update(new_kw)
                    result |= tree
            old_keywords.update(_keywords)
            _keywords = next_keywords
            next_keywords = set()
            deep += 1
        defined_old_keywords = old_keywords

        _keywords = set(keywords)
        deep = 0
        next_keywords = set()
        old_keywords = set()
        while _keywords and deep < depth: 
            for file_path in _paths:
                language = ParserFactory.detect_language(file_path)
                if language:
                    parser = ParserFactory.create_parser(language)
                    new_keywords = parser.find_keywords_in_file(file_path, _keywords, old_keywords)
                    next_keywords.update(new_keywords)

            old_keywords.update(next_keywords)
            _keywords = next_keywords
            next_keywords = set()
            deep += 1

        _keywords = old_keywords - defined_old_keywords
        for file_path in _paths:
            language = ParserFactory.detect_language(file_path)
            if language:
                parser = ParserFactory.create_parser(language)
                tree, new_kw = parser.search_define(file_path, _keywords, old_keywords)
                next_keywords.update(new_kw)
                result |= tree

        return {k:format_xml(d) for  k, d in result.items()}

        # result = [f"## {k}\n{format_xml(d)}" for k, d in result.items()]
                 
        # return "\n\n".join(result)
    except Exception as e:
        print(f"未预期的错误: {str(e)}")
        return {}


def get_block_context(paths:list[str], src_path: str, start_line: int, end_line: int, depth: int) -> Dict[str, str]:
    """
    解析代码文件或目录，得到所有上下文信息
    
    Args:
        paths: 文件或目录路径
        path: 代码块文件
        start_line: 代码块起始行号
        end_line: 代码块结束行号
        
    Returns:
        所有上下文信息
    """
    try:
        if os.path.isfile(src_path):
            # 处理单个文件
            try:
                # 通过文件扩展名自动检测语言
                language = ParserFactory.detect_language(src_path)
                if language:
                    parser = ParserFactory.create_parser(language)
                    kws = parser.find_all_kw(src_path, start_line, end_line)
                else:
                    print(f"无法识别文件类型: {src_path}")
            except Exception as e:
                print(f"解析文件失败: {src_path}, 错误: {str(e)}")
        else:
            raise SitterTreeError(f"路径不存在: {src_path}")
        print(kws)
        return deep_search_context(paths, kws, depth)
    except Exception as e:
        print(f"未预期的错误: {str(e)}")
        return {}