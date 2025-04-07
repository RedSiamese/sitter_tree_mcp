import os
from typing import Dict, Any, Optional
from .exceptions import CacheError

class CacheManager:
    """缓存管理器，用于存储和管理文件解析缓存"""
    
    def __init__(self):
        """初始化缓存管理器"""
        # 缓存结构: {file_path: {"last_modified": timestamp, "language": lang, "tree": tree_obj}}
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get_tree(self, file_path: str) -> Optional[Any]:
        """
        获取文件的缓存语法树
        
        Args:
            file_path: 文件路径
            
        Returns:
            缓存的语法树对象，如果不存在则返回None
        """
        if file_path in self._cache:
            # 检查文件是否已修改
            current_mtime = os.path.getmtime(file_path)
            cache_mtime = self._cache[file_path]["last_modified"]
            
            if current_mtime <= cache_mtime:
                return self._cache[file_path]["tree"]
        
        return None
    
    def set_tree(self, file_path: str, language: str, tree: Any) -> None:
        """
        设置文件的缓存语法树
        
        Args:
            file_path: 文件路径
            language: 语言类型
            tree: 语法树对象
        """
        try:
            current_mtime = os.path.getmtime(file_path)
            self._cache[file_path] = {
                "last_modified": current_mtime,
                "language": language,
                "tree": tree
            }
        except OSError as e:
            raise CacheError(f"无法缓存文件 {file_path}: {str(e)}")
    
    def clear(self, file_path: str = None) -> None:
        """
        清除缓存
        
        Args:
            file_path: 如果提供，则只清除该文件的缓存；否则清除所有缓存
        """
        if file_path:
            if file_path in self._cache:
                del self._cache[file_path]
        else:
            self._cache.clear()
    
    def is_cache_valid(self, file_path: str) -> bool:
        """
        检查文件的缓存是否有效
        
        Args:
            file_path: 文件路径
            
        Returns:
            如果缓存有效则返回True，否则返回False
        """
        if file_path not in self._cache:
            return False
        
        try:
            current_mtime = os.path.getmtime(file_path)
            cache_mtime = self._cache[file_path]["last_modified"]
            return current_mtime <= cache_mtime
        except OSError:
            return False

# 创建全局缓存管理器实例
cache_manager = CacheManager()