#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试深度搜索功能

此脚本用于测试sitter_tree_mcp模块中的深度搜索功能，它会：
1. 对test_samples中的C++文件执行不同深度的搜索
2. 测试不同类型的标识符(函数、类、变量)的搜索
3. 打印搜索结果和时间统计

使用方法:
    python test_deep_search.py
"""

import os
import time
import sys
from pathlib import Path

# 确保可以导入sitter_tree_mcp模块
sys.path.append(str(Path(__file__).parent.parent / "src/"))
print(str(Path(__file__).parent.parent)+"/src/")
from sitter_tree_mcp.impl.sitter_tree import deep_search_in_code

# 测试样例目录
SAMPLES_DIR = Path(__file__).parent.parent / "test_samples"

# 测试项目
TEST_CASES = [
    {
        "name": "简单节点搜索 - 深度1",
        "file": SAMPLES_DIR / "data_structures.cpp",
        "keywords": ["Node"],
        "depth": 1
    },
    {
        "name": "链表类搜索 - 深度1",
        "file": SAMPLES_DIR / "data_structures.cpp",
        "keywords": ["LinkedList"],
        "depth": 3
    },
    # {
    #     "name": "多关键字搜索 - 深度1",
    #     "file": SAMPLES_DIR / "data_structures.cpp",
    #     "keywords": ["Node", "LinkedList"],
    #     "depth": 1
    # },
    # {
    #     "name": "类型参数搜索 - 深度2",
    #     "file": SAMPLES_DIR / "data_structures.cpp",
    #     "keywords": ["T"],
    #     "depth": 2
    # },
    # {
    #     "name": "函数递归搜索 - 深度2",
    #     "file": SAMPLES_DIR / "basic_example.cpp",
    #     "keywords": ["factorial"],
    #     "depth": 2
    # },
    # {
    #     "name": "模板类递归搜索 - 深度2",
    #     "file": SAMPLES_DIR / "templates.cpp",
    #     "keywords": ["Array"],
    #     "depth": 2
    # },
    # {
    #     "name": "命名空间递归搜索 - 深度2",
    #     "file": SAMPLES_DIR / "namespaces.cpp",
    #     "keywords": ["math"],
    #     "depth": 2
    # }
]


def run_test(test_case):
    """运行单个测试"""
    print(f"\n{'=' * 80}")
    print(f"测试: {test_case['name']}")
    print(f"文件: {test_case['file']}")
    print(f"关键字: {test_case['keywords']}")
    print(f"深度: {test_case['depth']}")
    print(f"{'-' * 80}")
    
    start_time = time.time()
    result = deep_search_in_code([str(test_case['file'])], test_case['keywords'], test_case['depth'])
    end_time = time.time()
    
    if result:
        print(f"找到 {len(result)} 个匹配文件，用时: {end_time - start_time:.4f}秒")
        for file_path, xml_str in result.items():
            print(f"\n文件: {file_path}")
            # 为了输出简洁，只打印xml的前200个字符
            print(f"{xml_str[:20000]}...\n[XML输出已截断，共{len(xml_str)}字符]")
    else:
        print(f"未找到匹配结果，用时: {end_time - start_time:.4f}秒")


def run_all_tests():
    """运行所有测试"""
    print("开始深度搜索功能测试...")
    
    total_start = time.time()
    for test_case in TEST_CASES:
        run_test(test_case)
    total_end = time.time()
    
    print(f"\n{'=' * 80}")
    print(f"所有测试完成，总用时: {total_end - total_start:.4f}秒")


if __name__ == "__main__":
    run_all_tests()