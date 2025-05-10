// data_structures.cpp
// 数据结构实现示例

#include <iostream>
#include <memory>

struct Node_base {};

// 简单链表节点定义
template<typename T>
struct Node 
: Node_base {
    T data;
    std::shared_ptr<Node<T>> next;
    
    Node(T value) : data(value), next(nullptr) {}

    void print() const {
        std::cout << data << " -> " << (next ? next->data : "nullptr") << std::endl;
    }
};

// 链表类实现
template<typename T>
class LinkedList {
private:
    std::shared_ptr<Node<T>> head;      // 链表头指针
    size_t size;
    
public:
    LinkedList() : head(nullptr), size(0) {}
    
    // 添加元素到链表头部
    void push_front(T value) {
        auto new_node = std::make_shared<Node<T>>(value);
        new_node->next = head;
        head = new_node;
        size++;
    }
    
    // 添加元素到链表尾部
    void push_back(T value) {
        auto new_node = std::make_shared<Node<T>>(value);
        
        if (!head) {
            head = new_node;
        } else {
            auto current = head;
            while (current->next) {
                current = current->next;
            }
            current->next = new_node;
        }
        size++;
    }
    
    // 移除链表头部元素
    void pop_front() {
        if (head) {
            head = head->next;
            size--;
        }
    }
    
    // 获取链表大小
    size_t get_size() const {
        return size;
    }
    
    // 打印链表内容
    void print() const {
        auto current = head;
        while (current) {
            std::cout << current->data << " -> ";
            current = current->next;
        }
        std::cout << "nullptr" << std::endl;
    }
};

// 测试链表
int main() {
    LinkedList<int> list;
    
    // 添加元素
    list.push_back(1);
    list.push_back(2);
    list.push_back(3);
    list.push_front(0);
    
    // 打印链表
    std::cout << "List size: " << list.get_size() << std::endl;
    list.print();
    
    // 移除头部元素
    list.pop_front();
    
    // 再次打印
    std::cout << "After pop_front, list size: " << list.get_size() << std::endl;
    list.print();
    
    return 0;
}
