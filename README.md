# Sitter Tree MCP

一个基于 Tree-sitter 的代码语法树解析工具，可以解析代码并生成XML格式的语法树表示。该工具可以作为 Model Context Protocol (MCP) 的服务端使用，为大语言模型提供代码结构分析能力。

## 简介

Sitter Tree MCP 允许用户**分析代码结构、精确搜索特定关键词**，帮助大语言模型理解复杂代码库的结构。通过生成 XML 格式的抽象语法树（AST），工具将代码结构可视化，使模型能够更准确地理解代码组织和关系。

## 功能特点

- 支持解析代码文件和目录
- 支持生成详细和概览两种模式的语法树
- 支持在代码中搜索关键字
- 通过文件扩展名自动识别语言类型
- 支持 C++ 语言（可扩展支持更多语言）
- 提供 MCP 接口，便于集成到 AI 助手工作流程中

## 安装方法

可以使用 pip 进行安装：

```bash
pip install sitter_tree_mcp-0.1.0-py3-none-any.whl
```

或者从源码安装：

```bash
# 本地构建安装包
python setup.py sdist bdist_wheel

# 安装
pip install dist/sitter_tree_mcp-0.1.0-py3-none-any.whl
```

## 使用方法

### MCP 集成

在 MCP 客户端中配置：

```json
"mcpServers": {
  "sitter_tree": {
    "command": "python",
    "args": ["-m", "sitter_tree_mcp.mcp_service"]
  }
}
```

### 提示词示例

可以在 MCP 客户端的 rules 中添加：

``` 
# sitter_tree_mcp

## 功能说明
sitter_tree_mcp工具是一款使用tree-sitter技术，用于分析代码文件语法树的mcp工具，当前支持c\c++代码语法树解析。
- 可以通过parse_code工具快速分析有关的项目语法树，了解代码整体框架。在完整读取文件之前，对文件的语法树进行大体了解，并根据返回的语法树中的行号范围等信息，对感兴趣区域、可能对功能开发有价值的部分信息进行精准读取，防止读取过多内容污染上下文资源
- 可以通过search_in_code查找特定的类、结构体、成员（变量、函数、方法）等信息，快速定位所有需要修改的地方，支持同时查询多个关键字。


## 返回语法树样例
\`\`\`
<?xml version="1.0" ?>
<ast file="./test_samples/basic_example.cpp" language="cpp" mode="overview">
  <translation_unit line_range="1-36">
    <class_specifier line_range="12-28" declaration_text="class Calculator">
      <field_declaration_list line_range="12-28">
        <function_definition line_range="14-14">
          <function_declarator line_range="14-14" text="Calculator()"/>
        </function_definition>
        <function_definition line_range="22-24">
          <function_declarator line_range="22-22" text="int getValue() const"/>
        </function_definition>
        <field_declaration line_range="27-27" text="int value;"/>
      </field_declaration_list>
    </class_specifier>
    <function_definition line_range="31-35">
      <function_declarator line_range="31-31" text="int main()"/>
      <compound_statement>
        <declaration line_range="32-32"/>
      </compound_statement>
    </function_definition>
  </translation_unit>
</ast>
\`\`\`
其中：
    - 标签符合tree-sitter库标准
    - 生成的语法树会省略一些无关紧要的中间节点
    - `language`表示代码语言
    - `line_range="31-35"` 表示当前节点的行号范围为31至35行
    - `text="xxx"` declaration_text\text\template_text字段均表示当前节点的部分代码信息为"xxx"
    - 使用search_in_code工具时，查询到关键字的节点会包含属性字段`match="true"`，并可以通过text字段获悉它匹配到的关键字

## 使用场景
### 场景1:
用户在一个新的任务中，基于原有的代码开发一项功能，希望你在当前已有的框架下开发一项功能，并提示你参考 xxx.h 或 xxxx.cpp，在你完整读取文件之前，你需要率先使用parse_code对文件的语法树进行大体了解，并根据返回的语法树中的行号范围等信息，对你感兴趣的、可能对功能开发有价值的部分信息进行精准读取，防止读取过多内容污染上下文资源。

### 场景2:
当前有c++函数：
\`\`\` c++
int func(int a, int b) {
    return func2(a,b);
}
\`\`\`
当前的需求希望修改这个函数，你希望了解有关`func2`函数的定义和其他位置的使用情况作为示例，你可以使用search_in_code工具，在整个源代码目录中查找`func2`关键字，如果`func2`函数在当前搜索目录的代码中定义过，你可以通过search_in_code结果返回的语法树分析出`func2`函数定义的位置，并且获得其他调用这个函数的位置进行参考。


### 场景3:
当前有c++函数：
\`\`\` c++
int func(int a, int b) {
    return a+b;
}
\`\`\`
你希望修改这个函数的入参个数，将函数改为：
\`\`\` c++
int func(int a, int b, int c) {
    return a+b+c;
}
\`\`\`
你可以使用search_in_code工具，在整个源代码目录中查找`func`关键字，查看所有源代码中，和`func`函数相关的代码，通过其展示的代码语法树中的行号信息，更加局部精确地读取文件，对代码进行分析后对每一处调用进行修改。


以上示例场景，以及其他可能需要使用parse_code或search_in_code工具的场合。

## 注意事项
1. 使用search_in_code工具时，查询到关键字的所在节点，可能存在于某一行代码调用当中，此时可能需要分析他的一系列父节点代码块，寻找出包含这行函数调用的具体代码块行号范围，例如查找名为factorial函数：
```
<function_definition line_range="4-9" declaration_text="int factorial(int n)">
    <function_declarator line_range="4-4" text="int factorial(int n)">
        <identifier match="true" line_range="4-4" text="factorial"/>
    </function_declarator>
    <identifier match="true" line_range="8-8" text="factorial"/>
</function_definition>
```
上方语法树中，`<identifier match="true" line_range="8-8" text="factorial"/>`在第8行查询到factorial，根据语法树分析，实际这一行是一个factorial函数的函数调用，需要向前找到function_definition，可知factorial是在4-9行factorial函数定义中被调用的，类似具体问题需要根据语法树进行具体分析。
2. 在通过语法树获取行号范围后，如果要以该行号范围为依据对文件进行读取，应向行号范围前后多读几行，以确保代码块前后相应的注释部分也能被读到。


```

## 支持的语言

当前支持以下语言：

- C++ (.cpp, .cc, .cxx, .c++, .c, .h, .hpp, .hxx, .h++)

未来计划添加更多语言支持。

## 工作原理

Sitter Tree MCP 基于 Tree-sitter 解析器，将源代码转换为抽象语法树，然后格式化为 XML 结构。

### 解析模式

1. **详细模式**：生成完整的语法树，包含所有代码元素
2. **概览模式**：只保留关键结构元素（如类、函数定义等），提供代码的高层次视图

### XML 格式

生成的 XML 文档使用标签表示代码的不同元素，并包含以下关键信息：

- 元素类型（如 class_specifier、function_definition 等）
- 行号范围
- 声明文本
- 包含的子元素

## MCP 接口

### 工具

#### `parse_code`

解析代码文件或目录，生成 XML 格式的语法树。

**参数**:
- `path`: 文件或目录路径

**返回**:
文件路径到 XML 字符串的映射字典。

#### `search_in_code`

在代码文件或目录中搜索一系列关键字。

**参数**:
- `path`: 文件或目录路径
- `keyword`: 要搜索的关键字

**返回**:
包含搜索结果的 XML 字符串映射字典。

## 示例输出

以下是一个简单 C++ 类的概览模式语法树示例：

```xml
<?xml version="1.0" ?>
<ast file="example.cpp" language="cpp" mode="overview">
  <translation_unit line_range="1-24">
    <function_definition line_range="4-9" declaration_text="int factorial(int n)">
      <!-- Function content -->
    </function_definition>
    <class_specifier line_range="12-22" declaration_text="class Calculator">
      <function_definition line_range="14-14" declaration_text="Calculator() : value(0)">
        <!-- Constructor definition -->
      </function_definition>
      <function_definition line_range="17-19" declaration_text="void computeFactorial(int n)">
        <!-- Method definition -->
      </function_definition>
      <function_definition line_range="22-24" declaration_text="int getValue() const">
        <!-- Method definition -->
      </function_definition>
    </class_specifier>
  </translation_unit>
</ast>
```
