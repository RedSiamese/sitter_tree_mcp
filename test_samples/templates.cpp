// templates.cpp
// C++ 模板示例

#include <iostream>
#include <vector>
#include <string>

// 基本函数模板
template<typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}

// 类模板
template<typename T, int Size>
class Array {
private:
    T data[Size];
    
public:
    Array() {
        for (int i = 0; i < Size; i++) {
            data[i] = T();
        }
    }
    
    T& operator[](int index) {
        if (index < 0 || index >= Size) {
            throw std::out_of_range("Index out of range");
        }
        return data[index];
    }
    
    int size() const {
        return Size;
    }
};

// 模板特化
template<>
class Array<bool, 8> {
private:
    unsigned char data;
    
public:
    Array() : data(0) {}
    
    bool operator[](int index) {
        if (index < 0 || index >= 8) {
            throw std::out_of_range("Index out of range");
        }
        return (data & (1 << index)) != 0;
    }
    
    void set(int index, bool value) {
        if (index < 0 || index >= 8) {
            throw std::out_of_range("Index out of range");
        }
        
        if (value) {
            data |= (1 << index);
        } else {
            data &= ~(1 << index);
        }
    }
    
    int size() const {
        return 8;
    }
};

// 变参模板
template<typename... Args>
void print(Args... args) {
    (std::cout << ... << args) << std::endl;
}

int main() {
    // 使用函数模板
    std::cout << "Max of 10 and 20: " << max(10, 20) << std::endl;
    std::cout << "Max of 3.14 and 2.71: " << max(3.14, 2.71) << std::endl;
    std::cout << "Max of 'a' and 'z': " << max('a', 'z') << std::endl;
    
    // 使用类模板
    Array<int, 5> intArray;
    intArray[0] = 10;
    intArray[1] = 20;
    
    std::cout << "intArray[0] = " << intArray[0] << std::endl;
    std::cout << "intArray[1] = " << intArray[1] << std::endl;
    
    // 使用特化的模板
    Array<bool, 8> boolArray;
    boolArray.set(0, true);
    boolArray.set(3, true);
    
    std::cout << "boolArray[0] = " << boolArray[0] << std::endl;
    std::cout << "boolArray[1] = " << boolArray[1] << std::endl;
    std::cout << "boolArray[3] = " << boolArray[3] << std::endl;
    
    // 使用变参模板
    print("Hello", ", ", "world", "! ", 123);
    
    return 0;
}
