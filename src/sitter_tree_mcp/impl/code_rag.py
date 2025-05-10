import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

print(str(Path(__file__).parent.parent.parent.parent / "src/"))
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "src/"))

import chromadb
from chromadb.utils import embedding_functions
from sitter_tree_mcp.impl.parser_factory import ParserFactory
from sitter_tree_mcp.impl.cache_manager import cache_manager

# 初始化 ChromaDB 客户端
client = chromadb.PersistentClient(str(Path(__file__).parent.parent.parent.parent / "db"))
# 使用默认的嵌入函数 - 可以替换为更适合代码的嵌入模型
default_ef = embedding_functions.DefaultEmbeddingFunction()

def get_rag(path: str, collection_name: Optional[str] = None) -> str:
    """
    解析代码文件，提取节点信息，并将其存储到向量数据库中
    
    Args:
        path: 代码文件路径
        collection_name: 向量数据库集合名称，如果为None则使用文件名
        
    Returns:
        成功处理的节点数量信息
    """
    language = ParserFactory.detect_language(path)
    if not language:
        return f"无法识别文件类型: {path}"
    
    parser = ParserFactory.create_parser(language)
    node_dict = parser.node_to_dict(path, False)
    
    if not collection_name:
        collection_name = os.path.basename(path).replace(".", "_")
    
    # 获取或创建集合
    try:
        collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=default_ef,
            metadata={"description": f"Code embeddings for {path}"}
        )
    except Exception as e:
        return f"创建集合失败: {str(e)}"
    
    # 提取节点文本和行号范围
    nodes_info = extract_nodes_with_text(node_dict)
    
    if not nodes_info:
        return "未找到包含文本的节点"
    
    # 将节点信息添加到向量数据库
    try:
        documents = [node["text"] for node in nodes_info]
        ids = [f"{collection_name}_{i}" for i in range(len(nodes_info))]
        metadatas = [{
            "line_range": node["line_range"],
            "node_type": node["node_type"],
            "file_path": path
        } for node in nodes_info]
        
        # 添加到集合中
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        
        return f"成功将 {len(documents)} 个代码节点添加到向量数据库"
    except Exception as e:
        return f"添加到向量数据库失败: {str(e)}"

def extract_nodes_with_text(node_dict: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    递归提取节点中包含文本和行号范围的信息
    
    Args:
        node_dict: 节点字典
        
    Returns:
        包含文本和行号信息的节点列表
    """
    result = []
    
    def _extract_from_node(node):
        if not isinstance(node, dict):
            return
        
        # 提取当前节点的文本和行号信息
        text = None
        line_range = None
        node_type = node.get("type", "unknown")
        
        # 查找文本信息，可能来自text字段或attributes中的多个字段
        if "text" in node:
            text = node["text"]
        elif "attributes" in node:
            attrs = node["attributes"]
            if "text" in attrs:
                text = attrs["text"]
            elif "declaration_text" in attrs:
                text = attrs["declaration_text"]
            elif "template_text" in attrs:
                text = attrs["template_text"]
            
            if "line_range" in attrs:
                line_range = attrs["line_range"]
        
        # 如果存在有效的文本和行号信息，则添加到结果中
        if text and line_range:
            result.append({
                "text": text,
                "line_range": line_range,
                "node_type": node_type
            })
        
        # 递归处理子节点
        children = node.get("children", [])
        for child in children:
            _extract_from_node(child)
    
    # 处理根节点的子节点
    if "children" in node_dict:
        for child in node_dict["children"]:
            _extract_from_node(child)
    else:
        _extract_from_node(node_dict)
    
    return result

def query_rag(collection_name: str, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """
    从向量数据库中查询与给定文本最相似的代码节点
    
    Args:
        collection_name: 集合名称
        query_text: 查询文本
        n_results: 返回结果数量
        
    Returns:
        相似代码节点列表
    """
    try:
        collection = client.get_collection(name=collection_name, embedding_function=default_ef)
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # 格式化结果
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "text": doc,
                    "metadata": results['metadatas'][0][i] if i < len(results['metadatas'][0]) else {},
                    "similarity": results['distances'][0][i] if i < len(results['distances'][0]) else None
                })
                
        return formatted_results
    except Exception as e:
        print(f"查询失败: {str(e)}")
        return []

def index_directory(directory: str, recursive: bool = True) -> Dict[str, str]:
    """
    索引目录中的所有支持的代码文件
    
    Args:
        directory: 目录路径
        recursive: 是否递归处理子目录
        
    Returns:
        每个文件的处理结果
    """
    results = {}
    
    if recursive:
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if ParserFactory.detect_language(file_path):
                    result = get_rag(file_path)
                    results[file_path] = result
    else:
        for entry in os.listdir(directory):
            file_path = os.path.join(directory, entry)
            if os.path.isfile(file_path) and ParserFactory.detect_language(file_path):
                result = get_rag(file_path)
                results[file_path] = result
    
    return results

# 示例用法
if __name__ == "__main__":
    test_file = r"C:\Users\wxyri\Documents\sitter_tree_mcp\test_samples\data_structures.cpp"
    result = get_rag(test_file)
    print(result)
    
    # 索引整个目录
    # results = index_directory(r"C:\Users\wxyri\Documents\sitter_tree_mcp\test_samples")
    # print(json.dumps(results, indent=2))
    
    # 查询示例
    # query_results = query_rag("data_structures_cpp", "linked list node")
    # print(json.dumps(query_results, indent=2))