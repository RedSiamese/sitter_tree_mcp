import os,sys
from pathlib import Path
import argparse 

sys.path.append(str(Path(__file__).parent.parent / "src/"))
print(str(Path(__file__).parent.parent)+"/src/")
# from sitter_tree_mcp.impl.sitter_tree import deep_search_in_code
from sitter_tree_mcp.impl.sitter_tree import parse_code, search_in_code, deep_search_in_code, deep_search_context, get_block_context

# 运行方法
# python test.py ./data_structures.cpp --mode overview
# python test.py ./data_structures.cpp --search Node --depth 2
# python test.py ./data_structures.cpp --deep-search LinkedList --depth 2
# python test.py ./data_structures.cpp --context-search Node --depth 2
# python test.py ./data_structures.cpp --context-search Node --depth 2 --start_line 1 --end_line 10

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='代码语法树解析工具')
    parser.add_argument('path', help='代码文件或目录路径')
    parser.add_argument('--mode', choices=['detailed', 'overview'], default='detailed',
                        help='解析模式: detailed(详细) 或 overview(概览)')
    parser.add_argument('--search', nargs='*', help='搜索关键字') # str列表
    parser.add_argument('--deep-search', nargs='*', help='深度搜索关键字，根据广度优先搜索思路递归查找相关标识符')
    parser.add_argument('--context-search', nargs='*', help='上下文搜索关键字，查找标识符的定义、使用场景和相关联的标识符')
    parser.add_argument('--depth', type=int, default=1, help='深度搜索的深度限制，默认为1')
    parser.add_argument('--test', action='store_true', help='运行测试样例')
    parser.add_argument('--block_context', type=str, default="0-500", help='行号范围，格式为 start_line-end_line')
    
    args = parser.parse_args()
    
    # 如果指定了测试标志，则使用测试样例
    if args.test:
        test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_samples')
        if not os.path.exists(test_dir):
            print(f"测试样例目录不存在: {test_dir}")
            return
        args.path = test_dir
        print(f"使用测试样例目录: {test_dir}")
    
    if args.context_search:
        # 上下文搜索模式
        result = deep_search_context([args.path], args.context_search, args.depth)
        if result:
            print(f"在深度为 {args.depth} 的上下文搜索中，共在 {len(result)} 个文件中找到关键字 '{args.context_search}' 及其上下文信息")
            for file_path, xml_str in result.items():
                print(f"\n文件: {file_path}")
                print(xml_str)
        else:
            print(f"在深度 {args.depth} 的上下文搜索中未找到关键字 '{args.context_search}' 及其相关信息")
    elif args.deep_search:
        # 深度搜索模式
        result = deep_search_in_code([args.path], args.deep_search, args.depth)
        if result:
            print(f"在深度为 {args.depth} 的搜索中，共在 {len(result)} 个文件中找到关键字 '{args.deep_search}' 及其相关标识符")
            for file_path, xml_str in result.items():
                print(f"\n文件: {file_path}")
                print(xml_str)
        else:
            print(f"在深度 {args.depth} 的搜索中未找到关键字 '{args.deep_search}' 及其相关标识符")
    elif args.search:
        # 搜索模式
        result = search_in_code([args.path], args.search, args.depth)
        if result:
            print(f"在 {len(result)} 个文件中找到关键字 '{args.search}'")
            for file_path, xml_str in result.items():
                print(f"\n文件: {file_path}")
                print(xml_str)
        else:
            print(f"未找到关键字 '{args.search}'")
    elif args.block_context:
        # 块上下文搜索模式
        start_line, end_line = map(int, args.block_context.split('-'))
        result = get_block_context([args.path], args.path, start_line, end_line, depth=args.depth)
        if result:
            print(f"在 {len(result)} 个文件中找到关键字 '{args.block_context}'")
            for file_path, xml_str in result.items():
                print(f"\n文件: {file_path}")
                print(xml_str)
        else:
            print(f"未找到关键字 '{args.block_context}'")        
    else:
        # 解析模式
        detailed = args.mode == 'detailed'
        result = parse_code([args.path], detailed)
        if result:
            print(f"成功解析 {len(result)} 个文件")
            for file_path, xml_str in result.items():
                print(f"\n文件: {file_path}")
                print(xml_str)
        else:
            print("未解析到任何文件")

if __name__ == '__main__':
    main()