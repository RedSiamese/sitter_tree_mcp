from typing import Dict, Any
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import re

def format_xml(tree_dict: Dict[str, Any]) -> str:
    """
    格式化XML树为字符串
    
    Args:
        tree_dict: 包含XML元素信息的字典
        
    Returns:
        格式化后的XML字符串
    """
    # 创建XML根元素
    root = ET.Element("ast")
    for attr, value in tree_dict.get("attributes", {}).items():
        root.set(attr, value)
    
    # 递归创建XML树
    _build_xml_tree(root, tree_dict.get("children", []))
    
    # 将XML转换为字符串
    xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')
    
    # 使用minidom美化XML输出
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    # 移除额外的空行
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    
    return pretty_xml

def _sanitize_xml_name(name: str) -> str:
    """
    清理XML标签名称，确保其符合XML规范
    
    Args:
        name: 原始标签名称
        
    Returns:
        符合XML规范的标签名称
    """
    # 移除不合规的字符，仅保留字母、数字、下划线、连字符和点
    sanitized = re.sub(r'[^\w\-\.]', '_', name)
    # 确保标签名不以数字、连字符、点或下划线开头
    if sanitized and (sanitized[0].isdigit() or sanitized[0] in '-._'):
        sanitized = 'n_' + sanitized
    # 确保标签名不为空
    if not sanitized:
        sanitized = 'node'
    return sanitized

def _build_xml_tree(parent: ET.Element, children: list) -> None:
    """
    递归构建XML树
    
    Args:
        parent: 父XML元素
        children: 子节点列表
    """
    for child_dict in children:
        # 确保节点类型符合XML标签命名规则
        node_type = _sanitize_xml_name(child_dict["type"])
        child = ET.SubElement(parent, node_type)
        
        # 添加属性
        for attr, value in child_dict.get("attributes", {}).items():
            child.set(attr, value)
        
        # 设置文本内容(如果有)
        if "text" in child_dict:
            child.text = child_dict["text"]
        
        # 递归处理子节点
        _build_xml_tree(child, child_dict.get("children", []))

def create_ast_node(node_type: str, text: str = None, attributes: Dict[str, str] = None, 
                   children: list = None) -> Dict[str, Any]:
    """
    创建一个AST节点字典
    
    Args:
        node_type: 节点类型
        text: 节点文本内容
        attributes: 节点属性
        children: 子节点列表
        
    Returns:
        表示节点的字典
    """
    node = {"type": node_type}
    if text:
        node["text"] = text
    if attributes:
        node["attributes"] = attributes
    if children:
        node["children"] = children
    else:
        node["children"] = []
    return node