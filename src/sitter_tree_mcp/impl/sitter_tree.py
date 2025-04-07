import os
import argparse
from typing import Dict, Optional, List

from .parser_factory import ParserFactory
from .exceptions import SitterTreeError

def parse_code(path: str, detailed: bool = False) -> Dict[str, str]:
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

def search_in_code(path: str, keywords: List[str]) -> Dict[str, str]:
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
        
        if os.path.isfile(path):
            # 处理单个文件
            try:
                # 通过文件扩展名自动检测语言
                language = ParserFactory.detect_language(path)
                if language:
                    parser = ParserFactory.create_parser(language)
                    xml_str = parser.search_in_xml(path, keywords)
                    result.update(xml_str)
                else:
                    print(f"无法识别文件类型: {path}")
            except Exception as e:
                print(f"在文件中搜索失败: {path}, 错误: {str(e)}")
        
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
                            xml_str = parser.search_in_xml(file_path, keywords)
                            result.update(xml_str)
                    except Exception as e:
                        print(f"在文件中搜索失败: {file_path}, 错误: {str(e)}")
                        continue
        else:
            raise SitterTreeError(f"路径不存在: {path}")
        
        return result
    except Exception as e:
        print(f"未预期的错误: {str(e)}")
        return {}
