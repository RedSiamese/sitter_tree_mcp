// namespaces.cpp
// C++ 命名空间和作用域示例

#include <iostream>
#include <string>

// 定义命名空间
namespace math {
    const double PI = 3.14159265358979323846;
    
    double square(double x) {
        return x * x;
    }
    
    double cube(double x) {
        return x * x * x;
    }
    
    // 嵌套命名空间
    namespace geometry {
        struct Point {
            double x, y;
            
            Point(double x_val = 0, double y_val = 0) : x(x_val), y(y_val) {}
            
            double distance(const Point& other) const {
                return std::sqrt(square(x - other.x) + square(y - other.y));
            }
        };
        
        struct Circle {
            Point center;
            double radius;
            
            Circle(const Point& c, double r) : center(c), radius(r) {}
            
            double area() const {
                return PI * square(radius);
            }
            
            double circumference() const {
                return 2 * PI * radius;
            }
        };
    }
}

// 另一个命名空间
namespace utils {
    void print_separator() {
        std::cout << "------------------------------" << std::endl;
    }
    
    template<typename T>
    void print_value(const std::string& name, const T& value) {
        std::cout << name << " = " << value << std::endl;
    }
}

// 使用命名空间别名
namespace geo = math::geometry;

int main() {
    // 使用math命名空间
    double val = 3.0;
    std::cout << "Square of " << val << " = " << math::square(val) << std::endl;
    std::cout << "Cube of " << val << " = " << math::cube(val) << std::endl;
    
    utils::print_separator();
    
    // 使用几何命名空间
    geo::Point p1(3, 4);
    geo::Point p2(6, 8);
    
    utils::print_value("Distance between points", p1.distance(p2));
    
    // 创建圆
    geo::Circle circle(p1, 5);
    utils::print_value("Circle area", circle.area());
    utils::print_value("Circle circumference", circle.circumference());
    
    return 0;
}
