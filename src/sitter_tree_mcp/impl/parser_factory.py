from typing import Dict, Optional
from .exceptions import LanguageNotSupportedError
from .language_parsers_cpp import BaseParser, CppParser

class ParserFactory:
    """解析器工厂，负责创建不同语言的解析器"""
    
    # 语言到文件扩展名的映射
    LANGUAGE_EXTENSIONS = {
        "cpp": ['.cpp', '.cc', '.cxx', '.c++', '.c', '.h', '.hpp', '.hxx', '.h++'],
        # 未来可以添加更多语言
    }
    
    # 扩展名到语言的映射（由LANGUAGE_EXTENSIONS反向生成）
    EXTENSION_TO_LANGUAGE = {}
    
    # 语言解析器注册表
    _parsers = {}
    
    @classmethod
    def initialize(cls):
        """初始化工厂"""
        # 注册解析器
        cls.register_parser("cpp", CppParser)
        
        # 构建扩展名到语言的映射
        for lang, exts in cls.LANGUAGE_EXTENSIONS.items():
            for ext in exts:
                cls.EXTENSION_TO_LANGUAGE[ext] = lang
    
    @classmethod
    def register_parser(cls, language: str, parser_class):
        """
        注册新的语言解析器
        
        Args:
            language: 语言名称
            parser_class: 解析器类
        """
        cls._parsers[language] = parser_class
    
    @classmethod
    def create_parser(cls, language: str) -> BaseParser:
        """
        创建解析器
        
        Args:
            language: 语言名称
            
        Returns:
            语言解析器实例
            
        Raises:
            LanguageNotSupportedError: 如果语言不受支持
        """
        # 确保工厂已初始化
        if not cls._parsers:
            cls.initialize()
        
        # 获取解析器类
        parser_class = cls._parsers.get(language)
        if not parser_class:
            raise LanguageNotSupportedError(f"不支持的语言: {language}")
        
        # 创建解析器实例
        return parser_class()
    
    @classmethod
    def detect_language(cls, file_path: str) -> Optional[str]:
        """
        从文件路径检测语言
        
        Args:
            file_path: 文件路径
            
        Returns:
            检测到的语言名称，如果无法检测则返回None
        """
        # 确保工厂已初始化
        if not cls.EXTENSION_TO_LANGUAGE:
            cls.initialize()
            
        import os
        _, ext = os.path.splitext(file_path)
        return cls.EXTENSION_TO_LANGUAGE.get(ext.lower())