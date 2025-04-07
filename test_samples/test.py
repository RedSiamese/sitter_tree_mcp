import os
import argparse 
from sitter_tree_mcp.impl.sitter_tree import parse_code, search_in_code

# python test.py ./test_samples/data_structures.cpp --mode overview
# python test.py ./test_samples/data_structures.cpp --search class

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='代码语法树解析工具')
    parser.add_argument('path', help='代码文件或目录路径')
    parser.add_argument('--mode', choices=['detailed', 'overview'], default='detailed',
                        help='解析模式: detailed(详细) 或 overview(概览)')
    parser.add_argument('--search', nargs='*', help='搜索关键字') # str列表
    parser.add_argument('--test', action='store_true', help='运行测试样例')
    
    args = parser.parse_args()
    
    # 如果指定了测试标志，则使用测试样例
    if args.test:
        test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_samples')
        if not os.path.exists(test_dir):
            print(f"测试样例目录不存在: {test_dir}")
            return
        args.path = test_dir
        print(f"使用测试样例目录: {test_dir}")
    
    if args.search:
        # 搜索模式
        result = search_in_code(args.path, args.search)
        if result:
            print(f"在 {len(result)} 个文件中找到关键字 '{args.search}'")
            for file_path, xml_str in result.items():
                print(f"\n文件: {file_path}")
                print(xml_str)
        else:
            print(f"未找到关键字 '{args.search}'")
    else:
        # 解析模式
        detailed = args.mode == 'detailed'
        result = parse_code(args.path, detailed)
        if result:
            print(f"成功解析 {len(result)} 个文件")
            for file_path, xml_str in result.items():
                print(f"\n文件: {file_path}")
                print(xml_str)
        else:
            print("未解析到任何文件")

if __name__ == '__main__':
    main()