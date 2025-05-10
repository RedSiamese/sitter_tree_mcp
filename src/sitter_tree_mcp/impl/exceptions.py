
class SitterTreeError(Exception):
    """基础异常类，所有自定义异常继承自此类"""
    pass

class ParserError(SitterTreeError):
    """解析器相关错误"""
    pass

class CacheError(SitterTreeError):
    """缓存相关错误"""
    pass

class LanguageNotSupportedError(ParserError):
    """不支持的语言类型错误"""
    pass

class FileNotFoundError(SitterTreeError):
    """文件未找到错误"""
    pass

class SearchError(SitterTreeError):
    """搜索错误"""
    pass