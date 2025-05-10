// example.cpp
// 这是一个用于测试语法树解析功能的示例C++文件

int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

// 定义一个简单的类
class Calculator {
public:
    Calculator() : value(0) {}
    
    // 计算阶乘并存储结果
    void computeFactorial(int n) {
        value = factorial(n);
    }
    
    // 获取计算结果
    int getValue() const {
        return value;
    }
    
private:
    int value; // 存储计算结果
};

// 主函数
int main() {
    Calculator calc;
    calc.computeFactorial<Calculator>(5);
    return calc.getValue();
}
