from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8", errors="ignore") as fh:
    long_description = fh.read()

setup(
    name="sitter_tree_mcp",
    version="0.2.0",
    author="wxyri",
    author_email="your.email@example.com",
    description="一个用于解析代码生成语法树的工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wxyri/sitter_tree_mcp",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "tree-sitter",
        "tree-sitter-cpp",
    ],
    entry_points={
        "console_scripts": [
            "sitter-tree=sitter_tree_mcp.cli:main",
        ],
    },
    include_package_data=True,
    package_data={},
)
