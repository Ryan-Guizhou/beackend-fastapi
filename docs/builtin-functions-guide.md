# Python 内建函数指南

> 面向 Python 开发实践，系统介绍内建函数是什么、能解决什么问题、适合什么场景，并提供完整案例帮助建立真实使用感。

## 1. 什么是内建函数

内建函数，英文是 `built-in functions`。

它们是 Python 解释器默认就提供的函数，不需要 `import` 就能直接使用。

例如：

```python
print("hello")
length = len([1, 2, 3])
number = int("123")
```

这里的：

- `print`
- `len`
- `int`

都是内建函数。

## 2. 为什么内建函数很重要

很多 Python 新手会把注意力放在语法上，但实际项目里，内建函数的使用频率非常高。

因为它们解决的是最基础、最高频的操作：

- 类型转换
- 长度计算
- 最大最小值
- 排序辅助
- 条件判断
- 聚合计算
- 迭代处理
- 对象属性访问

一句话理解：

> 掌握内建函数，本质上是在掌握 Python 最基础、最常用的一套工具箱。

## 3. 内建函数能做什么

常见作用可以分成几类：

1. 输入输出
2. 类型转换
3. 数值计算
4. 迭代处理
5. 真值判断
6. 对象与属性操作
7. 调试和 introspection

## 4. 最常用的一批内建函数

最值得优先掌握的包括：

- `print`
- `len`
- `type`
- `isinstance`
- `int`
- `float`
- `str`
- `list`
- `dict`
- `set`
- `tuple`
- `sum`
- `max`
- `min`
- `sorted`
- `enumerate`
- `zip`
- `range`
- `abs`
- `round`
- `all`
- `any`
- `map`
- `filter`
- `open`
- `getattr`
- `setattr`
- `hasattr`
- `id`

## 5. 按场景理解内建函数

### 5.1 输入输出

#### `print()`

作用：

- 打印调试信息
- 输出运行结果

示例：

```python
name = "Tom"
score = 95

print(name, score)
print(f"学生：{name}，成绩：{score}")
```

使用场景：

- 调试变量
- 命令行脚本输出
- 教学示例

### 5.2 类型转换

#### `int()`

```python
age = int("18")
print(age)
print(type(age))
```

场景：

- 字符串数字转整数
- 请求参数转数值

#### `float()`

```python
price = float("19.99")
print(price)
```

场景：

- 金额处理
- 百分比换算

#### `str()`

```python
user_id = 1001
text = str(user_id)
print(text)
```

场景：

- 拼接字符串
- 日志输出
- 生成键名

#### `list()` / `tuple()` / `set()` / `dict()`

```python
numbers = list((1, 2, 3))
point = tuple([10, 20])
unique_tags = set(["python", "python", "fastapi"])
empty_mapping = dict()

print(numbers)
print(point)
print(unique_tags)
print(empty_mapping)
```

场景：

- 转换容器类型
- 去重
- 初始化集合结构

### 5.3 长度与计数

#### `len()`

```python
users = ["tom", "jack", "lucy"]
print(len(users))
```

场景：

- 统计列表长度
- 判断字符串长度
- 判断分页条数

### 5.4 数值计算

#### `sum()`

```python
prices = [100, 200, 300]
total = sum(prices)
print(total)
```

场景：

- 统计总金额
- 统计总分
- 聚合数量

#### `max()` 和 `min()`

```python
scores = [78, 92, 85, 60]
print(max(scores))
print(min(scores))
```

场景：

- 最高分
- 最低价
- 最大时间戳

#### `abs()`

```python
delta = abs(-12)
print(delta)
```

场景：

- 距离差值
- 偏差值

#### `round()`

```python
value = round(3.1415926, 2)
print(value)
```

场景：

- 保留小数位
- 展示金额

### 5.5 排序与对比

#### `sorted()`

```python
numbers = [5, 2, 9, 1]
print(sorted(numbers))
print(sorted(numbers, reverse=True))
```

场景：

- 排序分数
- 排序订单
- 排序对象列表

对象排序：

```python
users = [
    {"username": "tom", "age": 23},
    {"username": "jack", "age": 19},
    {"username": "lucy", "age": 28},
]

sorted_users = sorted(users, key=lambda item: item["age"])
print(sorted_users)
```

### 5.6 迭代处理

#### `range()`

```python
for num in range(5):
    print(num)
```

场景：

- 固定次数循环
- 生成数字序列

#### `enumerate()`

```python
users = ["tom", "jack", "lucy"]

for index, user in enumerate(users, start=1):
    print(index, user)
```

场景：

- 遍历时带索引
- 生成序号

#### `zip()`

```python
names = ["Tom", "Jack", "Lucy"]
scores = [95, 82, 88]

for name, score in zip(names, scores):
    print(name, score)
```

场景：

- 两个列表一一配对
- 拼装结构化数据

#### `map()`

```python
numbers = ["1", "2", "3"]
result = list(map(int, numbers))
print(result)
```

场景：

- 批量类型转换
- 简单统一处理

#### `filter()`

```python
numbers = [1, 2, 3, 4, 5, 6]
result = list(filter(lambda num: num % 2 == 0, numbers))
print(result)
```

场景：

- 过滤满足条件的数据
- 配合函数式风格处理列表

### 5.7 真值判断

#### `all()`

```python
flags = [True, True, True]
print(all(flags))
```

场景：

- 所有条件都满足才通过
- 批量校验

#### `any()`

```python
flags = [False, False, True]
print(any(flags))
```

场景：

- 任意一个条件成立即可
- 权限匹配

### 5.8 类型判断

#### `type()`

```python
value = [1, 2, 3]
print(type(value))
```

场景：

- 调试
- 了解对象类型

#### `isinstance()`

```python
value = [1, 2, 3]
print(isinstance(value, list))
print(isinstance(value, (list, tuple)))
```

场景：

- 更安全的类型判断
- 参数检查

### 5.9 属性操作

#### `getattr()`

```python
class User:
    def __init__(self, username):
        self.username = username


user = User("tom")
print(getattr(user, "username"))
print(getattr(user, "age", 0))
```

场景：

- 动态读取对象属性
- 给默认值

#### `setattr()`

```python
class User:
    pass


user = User()
setattr(user, "username", "tom")
print(user.username)
```

场景：

- 动态设置属性
- 插件化处理

#### `hasattr()`

```python
class User:
    def __init__(self):
        self.username = "tom"


user = User()
print(hasattr(user, "username"))
print(hasattr(user, "email"))
```

场景：

- 判断对象是否有某个字段
- 兼容不同对象结构

## 6. 项目中最常见的使用场景

### 6.1 请求参数转换

```python
page = int("2")
size = int("20")
offset = (page - 1) * size

print(offset)
```

### 6.2 数据聚合

```python
items = [
    {"price": 100, "count": 2},
    {"price": 50, "count": 3},
]

total_amount = sum(item["price"] * item["count"] for item in items)
print(total_amount)
```

### 6.3 批量组装导出数据

```python
names = ["Tom", "Jack", "Lucy"]
scores = [95, 82, 88]

rows = [
    {"name": name, "score": score}
    for name, score in zip(names, scores)
]

print(rows)
```

### 6.4 校验条件是否全部成立

```python
user = {
    "username": "tom",
    "email": "tom@example.com",
    "is_active": True,
}

is_valid = all([
    bool(user["username"]),
    bool(user["email"]),
    user["is_active"],
])

print(is_valid)
```

## 7. 完整案例一：学生成绩统计系统

需求：

- 统计总分
- 统计最高分和最低分
- 按成绩排序
- 生成排名结果

```python
students = [
    {"name": "Tom", "score": 95},
    {"name": "Jack", "score": 82},
    {"name": "Lucy", "score": 88},
    {"name": "Anna", "score": 73},
]

scores = [student["score"] for student in students]

total_score = sum(scores)
max_score = max(scores)
min_score = min(scores)
average_score = round(total_score / len(scores), 2)

sorted_students = sorted(
    students,
    key=lambda student: student["score"],
    reverse=True,
)

ranked_students = [
    {
        "rank": index,
        "name": student["name"],
        "score": student["score"],
    }
    for index, student in enumerate(sorted_students, start=1)
]

print("总分：", total_score)
print("最高分：", max_score)
print("最低分：", min_score)
print("平均分：", average_score)
print("排名：", ranked_students)
```

这个案例涉及的内建函数：

- `sum`
- `max`
- `min`
- `len`
- `round`
- `sorted`
- `enumerate`

## 8. 完整案例二：订单结算与校验

需求：

- 统计订单总金额
- 判断订单项是否都有效
- 找出最贵商品

```python
order_items = [
    {"name": "键盘", "price": 199, "count": 1, "enabled": True},
    {"name": "鼠标", "price": 99, "count": 2, "enabled": True},
    {"name": "耳机", "price": 299, "count": 1, "enabled": True},
]

total_amount = sum(item["price"] * item["count"] for item in order_items)

all_enabled = all(item["enabled"] for item in order_items)
all_positive = all(item["count"] > 0 and item["price"] > 0 for item in order_items)

most_expensive = max(order_items, key=lambda item: item["price"])

print("总金额：", total_amount)
print("是否全部启用：", all_enabled)
print("数量和价格是否合法：", all_positive)
print("最贵商品：", most_expensive)
```

这个案例体现：

- `sum()` 可以配合生成器表达式做聚合
- `all()` 很适合批量校验
- `max(key=...)` 很适合对象列表比较

## 9. 完整案例三：后端接口返回整理

需求：

- 从接口返回中提取有效用户
- 生成前端下拉框数据
- 按用户名排序

```python
response = {
    "rows": [
        {"id": 3, "username": "lucy", "active": True},
        {"id": 1, "username": "tom", "active": True},
        {"id": 2, "username": "jack", "active": False},
    ]
}

active_users = list(filter(lambda item: item["active"], response["rows"]))

active_users = sorted(active_users, key=lambda item: item["username"])

options = [
    {"label": user["username"], "value": user["id"]}
    for user in active_users
]

print("有效用户：", active_users)
print("下拉框选项：", options)
```

这个案例涉及：

- `filter`
- `list`
- `sorted`

## 10. `map` 和 `filter` 要不要大量使用

可以用，但要看团队风格和可读性。

例如：

```python
numbers = ["1", "2", "3"]
result = list(map(int, numbers))
```

这没有问题。

但很多时候，列推导式更直观：

```python
result = [int(num) for num in numbers]
```

一般经验是：

- 简单转换：列推导式更直观
- 已有函数可直接复用：`map()` 也合适
- 简单过滤：列推导式通常更好读
- 复杂函数式链路：要谨慎，避免过度函数式

## 11. 常见误区

### 11.1 用 `type()` 替代 `isinstance()`

不推荐：

```python
if type(value) == list:
    ...
```

更推荐：

```python
if isinstance(value, list):
    ...
```

原因：

- `isinstance` 能处理继承关系
- 更符合 Python 实践

### 11.2 把 `sorted()` 和 `.sort()` 混淆

`sorted()`：

- 返回新列表
- 不修改原对象

`.sort()`：

- 就地排序
- 直接修改原列表

示例：

```python
numbers = [3, 1, 2]
new_numbers = sorted(numbers)

print(numbers)
print(new_numbers)
```

### 11.3 误以为 `zip()` 会自动补齐

```python
names = ["Tom", "Jack", "Lucy"]
scores = [95, 82]

print(list(zip(names, scores)))
```

输出只会到最短长度。

所以：

- 长度不一致时要注意数据丢失风险

## 12. 使用建议

建议优先掌握这一批：

1. `len`
2. `int`
3. `str`
4. `sum`
5. `max`
6. `min`
7. `sorted`
8. `range`
9. `enumerate`
10. `zip`
11. `all`
12. `any`
13. `isinstance`

因为它们覆盖了大部分日常开发场景。

## 13. 学习和实战结论

内建函数不是零散知识点，而是一整套高频工具。

真正需要掌握的，不只是“记住有哪些函数”，而是：

- 知道它们分别解决什么问题
- 知道什么时候该用
- 知道如何和列表、字典、对象、推导式一起组合

如果继续补 Python 基础专题，下一步通常值得单独展开的是：

1. 迭代器与生成器
2. `sorted`、`map`、`filter` 深入专题
3. 字符串常用方法
4. 字典常用方法
