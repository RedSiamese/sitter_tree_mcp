import os
from typing import Dict, Optional, Type, Any, List

from .language_parsers_base import BaseParser
from .exceptions import LanguageNotSupportedError, ParserError

class ParserManager:
    """解析器管理器，负责创建和管理不同语言的解析器"""
    
    # 语言到解析器类的映射
    _parser_classes: Dict[str, Type[BaseParser]] = {}
    
    # 已创建的解析器实例缓存
    _parser_instances: Dict[str, BaseParser] = {}
    
    @classmethod
    def register_parser(cls, language: str, parser_class: Type[BaseParser]) -> None:
        """
        注册语言解析器
        
        Args:
            language: 语言名称
            parser_class: 对应的解析器类
        """
        cls._parser_classes[language] = parser_class
    
    @classmethod
    def get_parser(cls, file_path: str) -> BaseParser:
        """
        根据文件路径获取对应的解析器实例
        
        Args:
            file_path: 文件路径
            
        Returns:
            对应语言的解析器实例
            
        Raises:
            LanguageNotSupportedError: 如果该文件类型不受支持
        """
        # 通过扩展名自动检测语言类型
        language = BaseParser.detect_language(file_path)
        if not language:
            raise LanguageNotSupportedError(f"不支持的文件类型: {file_path}")
        
        # 如果解析器实例已存在，直接返回
        if language in cls._parser_instances:
            return cls._parser_instances[language]
        
        # 检查是否有对应语言的解析器类
        if language not in cls._parser_classes:
            raise LanguageNotSupportedError(f"没有找到语言 {language} 的解析器")
        
        # 创建新的解析器实例
        parser_class = cls._parser_classes[language]
        parser = parser_class()
        
        # 缓存解析器实例
        cls._parser_instances[language] = parser
        
        return parser
    
    @classmethod
    def parse_to_xml(cls, path: str, detailed: bool = True) -> Dict[str, str]:
        """
        解析文件或目录到XML格式
        
        Args:
            path: 文件或目录路径
            detailed: 是否生成详细语法树
            
        Returns:
            文件路径到XML字符串的映射字典
        """
        result = {}
        
        if os.path.isfile(path):
            # 处理单个文件
            try:
                parser = cls.get_parser(path)
                xml_str = parser._parse_file_to_xml(path, detailed)
                result[path] = xml_str
            except LanguageNotSupportedError:
                # 忽略不支持的文件类型
                pass
            except Exception as e:
                raise ParserError(f"解析文件 {path} 失败: {str(e)}")
        elif os.path.isdir(path):
            # 递归处理目录
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if BaseParser.is_supported_file(file_path):
                            parser = cls.get_parser(file_path)
                            xml_str = parser._parse_file_to_xml(file_path, detailed)
                            result[file_path] = xml_str
                    except Exception as e:
                        print(f"警告: 解析文件 {file_path} 失败: {str(e)}")
                        continue
        else:
            raise ParserError(f"路径不存在: {path}")
        
        return result
    
    @classmethod
    def search_in_xml(cls, path: str, keywords: List[str]) -> Dict[str, str]:
        """
        在代码文件或目录中搜索关键字
        
        Args:
            path: 文件或目录路径
            keywords: 要搜索的关键字列表
            
        Returns:
            文件路径到包含搜索结果的XML字符串的映射字典
        """
        result = {}
        
        if os.path.isfile(path):
            # 处理单个文件
            try:
                parser = cls.get_parser(path)
                xml_str = parser._search_in_file(path, keywords)
                if xml_str:  # 只添加有搜索结果的文件
                    result[path] = xml_str
            except LanguageNotSupportedError:
                # 忽略不支持的文件类型
                pass
            except Exception as e:
                raise ParserError(f"在文件 {path} 中搜索关键字失败: {str(e)}")
        elif os.path.isdir(path):
            # 递归处理目录
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if BaseParser.is_supported_file(file_path):
                            parser = cls.get_parser(file_path)
                            xml_str = parser._search_in_file(file_path, keywords)
                            if xml_str:  # 只添加有搜索结果的文件
                                result[file_path] = xml_str
                    except Exception as e:
                        print(f"警告: 在文件 {file_path} 中搜索关键字失败: {str(e)}")
                        continue
        else:
            raise ParserError(f"路径不存在: {path}")
        
        return result
