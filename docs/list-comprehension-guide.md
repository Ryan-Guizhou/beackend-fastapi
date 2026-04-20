# Python 推导式指南

> 面向 Python 初学到进阶开发者，系统讲清楚 Python 中所有常见推导式分别是什么、能做什么、适合什么场景、它们的相同点和不同点，以及如何在真实项目中组合使用。

## 1. 什么是推导式

推导式，英文通常叫 `comprehension`。

它是一类“用更紧凑的语法，从一个或多个可迭代对象中生成新结果”的写法。

可以把它理解成：

> 用一段表达式，同时描述“遍历什么”“如何处理”“要不要过滤”，最后直接得到新结果。

Python 里最常见的 4 类推导式是：

- 列表推导式
- 字典推导式
- 集合推导式
- 生成器表达式

虽然生成器表达式严格来说不总被单独称作“推导式”，但它和前三者在语法结构、使用方式、思维模型上非常接近，实际开发里通常会一起学习和对比。

## 2. 为什么要学所有推导式

掌握推导式，不只是为了把代码写短，而是为了：

1. 更直接地表达“我要从一批数据生成新结果”
2. 减少样板式的 `for` 循环和 `append()` 代码
3. 在轻量数据处理场景里提升可读性
4. 更自然地和 `sum()`、`sorted()`、`all()`、`any()` 等工具组合

常见适用场景：

- 批量转换数据
- 条件过滤
- 提取字段
- 生成映射结构
- 数据去重
- 惰性计算
- 轻量数据清洗

## 3. Python 中都有哪些推导式

先看一组最直观的对比：

```python
numbers = [1, 2, 3, 4]

list_result = [num * 2 for num in numbers]
dict_result = {num: num * 2 for num in numbers}
set_result = {num % 2 for num in numbers}
generator_result = (num * 2 for num in numbers)
```

它们的区别在于最终产出的结果类型不同：

- `[]` 生成列表
- `{key: value}` 生成字典
- `{value}` 生成集合
- `()` 生成生成器对象

## 4. 它们的相同点

这几类推导式有明显共性。

### 4.1 都基于遍历

它们都依赖 `for` 语法来遍历一个可迭代对象。

### 4.2 都可以做转换

都可以把原始元素处理成新的值。

### 4.3 都可以做条件过滤

都支持 `if` 条件，只保留满足条件的元素。

### 4.4 都可以嵌套

都可以出现多层 `for`，也可以和条件表达式结合。

### 4.5 都适合轻量数据处理

它们都更适合：

- 简单转换
- 简单筛选
- 简单结构生成

而不适合承载特别复杂的业务逻辑。

## 5. 它们的不同点

最核心的差异，是“结果类型”和“使用目标”不同。

| 类型 | 语法 | 结果类型 | 典型用途 |
| --- | --- | --- | --- |
| 列表推导式 | `[expr for x in data]` | `list` | 保留顺序、收集一批结果 |
| 字典推导式 | `{k: v for x in data}` | `dict` | 构造映射、键值索引 |
| 集合推导式 | `{expr for x in data}` | `set` | 去重、生成唯一值集合 |
| 生成器表达式 | `(expr for x in data)` | generator | 惰性计算、节省内存 |

还可以进一步理解为：

- 列表推导式重在“收集结果”
- 字典推导式重在“构建键值映射”
- 集合推导式重在“得到唯一值”
- 生成器表达式重在“按需生成，不一次性全部落地”

## 6. 列表推导式

### 6.1 什么是列表推导式

列表推导式，英文是 `list comprehension`，用来快速生成列表。

最基本写法：

```python
numbers = [1, 2, 3, 4, 5]
result = [num * 2 for num in numbers]

print(result)
```

输出：

```python
[2, 4, 6, 8, 10]
```

### 6.2 基本语法

```python
[表达式 for 变量 in 可迭代对象]
```

带过滤：

```python
[表达式 for 变量 in 可迭代对象 if 条件]
```

带条件分支：

```python
[结果1 if 条件 else 结果2 for 变量 in 可迭代对象]
```

### 6.3 能做什么

- 批量转换数据
- 条件筛选
- 提取字段
- 拍平一层嵌套列表
- 生成结构化列表

### 6.4 常见场景

```python
prices = [100, 200, 300]
discount_prices = [price * 0.9 for price in prices]

print(discount_prices)
```

```python
users = [
    {"id": 1, "username": "tom"},
    {"id": 2, "username": "jack"},
    {"id": 3, "username": "lucy"},
]

usernames = [user["username"] for user in users]
print(usernames)
```

### 6.5 完整案例：学生成绩分级

```python
students = [
    {"name": "Tom", "score": 95},
    {"name": "Jack", "score": 81},
    {"name": "Lucy", "score": 59},
    {"name": "Anna", "score": 73},
]

student_levels = [
    {
        "name": student["name"],
        "score": student["score"],
        "level": (
            "优秀" if student["score"] >= 90
            else "良好" if student["score"] >= 80
            else "及格" if student["score"] >= 60
            else "不及格"
        ),
    }
    for student in students
]

print(student_levels)
```

适用理解：

- 输入是一组记录
- 输出仍然是一组记录
- 只是记录内容被重新组织了

## 7. 字典推导式

### 7.1 什么是字典推导式

字典推导式，英文是 `dict comprehension`，用来快速生成字典。

最基本写法：

```python
numbers = [1, 2, 3, 4]
result = {num: num * 10 for num in numbers}

print(result)
```

输出：

```python
{1: 10, 2: 20, 3: 30, 4: 40}
```

### 7.2 基本语法

```python
{键表达式: 值表达式 for 变量 in 可迭代对象}
```

带过滤：

```python
{键表达式: 值表达式 for 变量 in 可迭代对象 if 条件}
```

### 7.3 能做什么

- 生成键值映射
- 快速建立索引
- 对已有字典做转换
- 过滤不需要的键值

### 7.4 常见场景

#### 按 ID 建立索引

```python
users = [
    {"id": 1, "username": "tom"},
    {"id": 2, "username": "jack"},
    {"id": 3, "username": "lucy"},
]

user_map = {user["id"]: user for user in users}
print(user_map)
```

#### 统一转换字典值

```python
scores = {"tom": 95, "jack": 82, "lucy": 88}
passed_map = {name: score for name, score in scores.items() if score >= 60}

print(passed_map)
```

### 7.5 完整案例：配置项转前端字典

```python
configs = [
    {"key": "site_name", "value": "Demo 系统", "enabled": True},
    {"key": "page_size", "value": 20, "enabled": True},
    {"key": "debug", "value": False, "enabled": False},
]

config_map = {
    item["key"]: item["value"]
    for item in configs
    if item["enabled"]
}

print(config_map)
```

适用理解：

- 输入是一组配置记录
- 输出是方便读取的键值结构
- 后续可以直接 `config_map["site_name"]`

## 8. 集合推导式

### 8.1 什么是集合推导式

集合推导式，英文是 `set comprehension`，用来快速生成集合。

最基本写法：

```python
numbers = [1, 2, 2, 3, 3, 4]
result = {num for num in numbers}

print(result)
```

输出：

```python
{1, 2, 3, 4}
```

### 8.2 基本语法

```python
{表达式 for 变量 in 可迭代对象}
```

带过滤：

```python
{表达式 for 变量 in 可迭代对象 if 条件}
```

### 8.3 能做什么

- 去重
- 提取唯一值集合
- 做集合运算前的数据准备
- 过滤后再保留唯一值

### 8.4 常见场景

```python
tags = ["python", "fastapi", "python", "sqlalchemy", "fastapi"]
unique_tags = {tag for tag in tags}

print(unique_tags)
```

```python
emails = [
    "tom@example.com",
    "jack@example.com",
    "tom@example.com",
]

email_domains = {email.split("@")[1] for email in emails}
print(email_domains)
```

### 8.5 完整案例：统计活跃部门

```python
employees = [
    {"name": "Tom", "department": "研发部", "active": True},
    {"name": "Jack", "department": "测试部", "active": True},
    {"name": "Lucy", "department": "研发部", "active": True},
    {"name": "Anna", "department": "运维部", "active": False},
]

active_departments = {
    employee["department"]
    for employee in employees
    if employee["active"]
}

print(active_departments)
```

适用理解：

- 目标不是保留所有员工记录
- 而是得到“活跃员工涉及了哪些部门”
- 集合天然适合表示“不重复的一组值”

## 9. 生成器表达式

### 9.1 什么是生成器表达式

生成器表达式，英文是 `generator expression`。

它和列表推导式很像，但不会立刻把所有结果都放进内存，而是按需一个一个生成。

最基本写法：

```python
numbers = [1, 2, 3, 4, 5]
result = (num * 2 for num in numbers)

print(result)
print(list(result))
```

### 9.2 基本语法

```python
(表达式 for 变量 in 可迭代对象)
```

带过滤：

```python
(表达式 for 变量 in 可迭代对象 if 条件)
```

### 9.3 能做什么

- 惰性生成数据
- 节省内存
- 和 `sum()`、`all()`、`any()` 直接配合
- 处理大批量数据流

### 9.4 常见场景

```python
numbers = [1, 2, 3, 4, 5]
total = sum(num * 2 for num in numbers)

print(total)
```

```python
users = [
    {"username": "tom", "active": True},
    {"username": "jack", "active": True},
    {"username": "lucy", "active": False},
]

all_active = all(user["active"] for user in users)
print(all_active)
```

### 9.5 完整案例：订单总额惰性计算

```python
orders = [
    {"price": 199, "count": 1},
    {"price": 99, "count": 2},
    {"price": 299, "count": 1},
]

amount_iter = (item["price"] * item["count"] for item in orders)
total_amount = sum(amount_iter)

print(total_amount)
```

适用理解：

- 如果只是为了求和，不一定要先构造一个列表
- 生成器表达式可以边生成边消费
- 在数据量更大时更节省内存

## 10. 它们能否混合使用

可以，而且非常常见。

这里的“混合使用”主要有两层含义：

1. 不同推导式相互嵌套
2. 推导式和内建函数、普通循环、条件判断一起组合

### 10.1 列表推导式里用生成器表达式

```python
orders = [
    {
        "order_no": "A1001",
        "items": [
            {"price": 199, "count": 1},
            {"price": 99, "count": 2},
        ],
    },
    {
        "order_no": "A1002",
        "items": [
            {"price": 299, "count": 1},
        ],
    },
]

order_summary = [
    {
        "order_no": order["order_no"],
        "amount": sum(item["price"] * item["count"] for item in order["items"]),
    }
    for order in orders
]

print(order_summary)
```

这里：

- 外层是列表推导式
- `sum(...)` 里是生成器表达式

### 10.2 字典推导式里嵌套列表推导式

```python
classes = {
    "一班": ["Tom", "Lucy"],
    "二班": ["Jack", "Anna"],
}

class_cards = {
    class_name: [name.lower() for name in names]
    for class_name, names in classes.items()
}

print(class_cards)
```

这里：

- 外层是字典推导式
- 每个键对应的值，是一个列表推导式的结果

### 10.3 集合推导式和列表推导式组合

```python
users = [
    {"username": "Tom", "department": "研发部"},
    {"username": "Lucy", "department": "研发部"},
    {"username": "Jack", "department": "测试部"},
]

departments = {user["department"] for user in users}
labels = [f"部门：{dept}" for dept in departments]

print(departments)
print(labels)
```

### 10.4 混合使用时的原则

可以混合，但不要失控。

推荐：

- 外层结构简单
- 内层职责单一
- 每层都能一眼看懂

不推荐：

- 三层以上复杂嵌套
- 同时混合多个条件表达式
- 读起来比普通 `for` 循环更绕

## 11. 它们和普通 `for` 循环怎么选

推导式更适合：

- 一步生成新结果
- 逻辑短小明确
- 转换和过滤规则简单

普通 `for` 循环更适合：

- 有很多中间步骤
- 要打印日志
- 要异常处理
- 要逐步调试
- 业务逻辑复杂

一个简单判断标准：

> 如果你需要先解释半天这行推导式在做什么，那就应该改回普通循环。

## 12. 完整案例一：接口数据整理

这个案例同时用到列表推导式、字典推导式、集合推导式。

```python
users = [
    {"id": 1, "username": "tom", "department": "研发部", "active": True},
    {"id": 2, "username": "jack", "department": "测试部", "active": False},
    {"id": 3, "username": "lucy", "department": "研发部", "active": True},
    {"id": 4, "username": "anna", "department": "运维部", "active": True},
]

# 1. 有效用户列表
active_users = [user for user in users if user["active"]]

# 2. 用户 ID 索引
user_map = {user["id"]: user for user in active_users}

# 3. 活跃部门集合
active_departments = {user["department"] for user in active_users}

print("active_users =", active_users)
print("user_map =", user_map)
print("active_departments =", active_departments)
```

这个案例体现：

- 同一批数据可以从不同角度生成不同结构
- 列表适合保留完整结果集
- 字典适合快速索引
- 集合适合提取唯一值

## 13. 完整案例二：订单报表生成

这个案例同时用到列表推导式和生成器表达式。

```python
orders = [
    {
        "order_no": "A1001",
        "paid": True,
        "items": [
            {"name": "键盘", "price": 199, "count": 1},
            {"name": "鼠标", "price": 99, "count": 2},
        ],
    },
    {
        "order_no": "A1002",
        "paid": False,
        "items": [
            {"name": "显示器", "price": 999, "count": 1},
        ],
    },
    {
        "order_no": "A1003",
        "paid": True,
        "items": [
            {"name": "耳机", "price": 299, "count": 1},
            {"name": "支架", "price": 89, "count": 1},
        ],
    },
]

paid_order_reports = [
    {
        "order_no": order["order_no"],
        "amount": sum(item["price"] * item["count"] for item in order["items"]),
        "item_count": sum(item["count"] for item in order["items"]),
    }
    for order in orders
    if order["paid"]
]

print(paid_order_reports)
```

这个案例体现：

- 外层列表推导式负责筛选已支付订单并生成报表
- 内层生成器表达式负责金额和数量聚合
- 这种组合在后端代码中非常常见

## 14. 完整案例三：班级统计看板

这个案例把 4 类写法放在一个场景中。

```python
students = [
    {"name": "Tom", "class_name": "一班", "score": 95},
    {"name": "Lucy", "class_name": "一班", "score": 88},
    {"name": "Jack", "class_name": "二班", "score": 81},
    {"name": "Anna", "class_name": "二班", "score": 73},
    {"name": "Bob", "class_name": "二班", "score": 81},
]

# 列表推导式：生成展示列表
student_cards = [
    f'{student["name"]}-{student["class_name"]}-{student["score"]}'
    for student in students
]

# 字典推导式：按姓名建立成绩索引
score_map = {student["name"]: student["score"] for student in students}

# 集合推导式：提取全部班级
class_names = {student["class_name"] for student in students}

# 生成器表达式：计算平均分
average_score = sum(student["score"] for student in students) / len(students)

print("student_cards =", student_cards)
print("score_map =", score_map)
print("class_names =", class_names)
print("average_score =", average_score)
```

这个案例体现：

- 一份原始数据
- 可以根据需求产出不同结构
- 关键在于先想清楚“我最终要什么类型的结果”

## 15. 常见错误写法

### 15.1 逻辑太复杂

不推荐：

```python
result = [
    {
        "id": item["id"],
        "name": item["name"].strip().title(),
        "status": "启用" if item["enabled"] and item["count"] > 0 else "禁用",
        "amount": item["price"] * item["count"] if item["price"] > 0 else 0,
    }
    for item in data
    if item.get("name") and item.get("category") != "deleted" and item["count"] >= 0
]
```

问题：

- 一行承载太多逻辑
- 不好调试
- 不好维护

### 15.2 误把推导式当副作用工具

不推荐：

```python
[print(num) for num in range(5)]
```

原因：

- 推导式的主要目标是生成结果
- 这里只是为了打印，没必要构造一个无用列表

### 15.3 误以为生成器表达式可以反复使用

```python
nums = (num * 2 for num in range(5))

print(list(nums))
print(list(nums))
```

第二次通常会得到空结果，因为生成器已经被消费过了。

## 16. 使用建议

推荐使用推导式的场景：

- 简单转换
- 简单过滤
- 提取字段
- 构建轻量结构
- 聚合前的数据准备

不推荐使用推导式的场景：

- 多层复杂业务逻辑
- 需要大量日志和异常处理
- 需要逐步调试
- 表达式太长，一眼看不懂

## 17. `map`、`filter`、`sorted` 和推导式的对比

前面讲的是“推导式本身”。

但在真实开发里，推导式经常会和这些工具一起出现：

- `map()`
- `filter()`
- `sorted()`

所以真正需要理解的不是“谁能替代谁”，而是：

> 它们分别适合什么场景，和推导式相比各自的优势在哪里。

### 17.1 `map()` 和推导式

`map()` 的核心作用是：

- 对一批数据做统一转换

示例：

```python
numbers = ["1", "2", "3", "4"]

result1 = list(map(int, numbers))
result2 = [int(num) for num in numbers]

print(result1)
print(result2)
```

二者结果相同。

区别在于：

- `map()` 更偏函数式风格
- 列表推导式更偏声明式、直观

什么时候更适合 `map()`：

- 已经有现成函数可直接复用
- 转换逻辑很简单
- 团队能接受函数式写法

什么时候更适合推导式：

- 需要同时带条件
- 表达式里有轻量逻辑
- 希望一眼就看懂数据从哪里来、变成什么

示例对比：

```python
names = [" tom ", " jack ", " lucy "]

result1 = list(map(str.strip, names))
result2 = [name.strip() for name in names]

print(result1)
print(result2)
```

### 17.2 `filter()` 和推导式

`filter()` 的核心作用是：

- 过滤出满足条件的元素

示例：

```python
numbers = [1, 2, 3, 4, 5, 6]

result1 = list(filter(lambda num: num % 2 == 0, numbers))
result2 = [num for num in numbers if num % 2 == 0]

print(result1)
print(result2)
```

二者结果相同。

一般来说：

- 简单过滤时，推导式通常更好读
- 如果过滤规则本身就是一个独立函数，`filter()` 也可以很自然

例如：

```python
def is_active_user(user: dict) -> bool:
    return user["active"]


users = [
    {"username": "tom", "active": True},
    {"username": "jack", "active": False},
    {"username": "lucy", "active": True},
]

active_users_1 = list(filter(is_active_user, users))
active_users_2 = [user for user in users if user["active"]]

print(active_users_1)
print(active_users_2)
```

### 17.3 `sorted()` 和推导式

`sorted()` 和前两者不一样。

它不是“转换工具”，而是“排序工具”。

示例：

```python
users = [
    {"username": "tom", "age": 23},
    {"username": "jack", "age": 19},
    {"username": "lucy", "age": 28},
]

sorted_users = sorted(users, key=lambda item: item["age"])
print(sorted_users)
```

`sorted()` 往往和推导式搭配使用，而不是互相替代。

例如：

```python
users = [
    {"username": "tom", "age": 23, "active": True},
    {"username": "jack", "age": 19, "active": False},
    {"username": "lucy", "age": 28, "active": True},
]

active_users = [user for user in users if user["active"]]
sorted_active_users = sorted(active_users, key=lambda item: item["age"])

print(sorted_active_users)
```

### 17.4 `lambda` 表达式是什么

前面在 `filter()` 和 `sorted()` 里已经多次出现了 `lambda`。

所以这里需要单独把它讲清楚。

`lambda` 表达式本质上是：

> 一种用于快速定义匿名函数的写法。

最基本例子：

```python
add = lambda x, y: x + y

print(add(2, 3))
```

它等价于：

```python
def add(x, y):
    return x + y
```

区别在于：

- `lambda` 是一个表达式
- `def` 是一个完整的函数定义语句

### 17.5 `lambda` 的基本语法

```python
lambda 参数: 返回值表达式
```

示例：

```python
square = lambda x: x * x
is_even = lambda x: x % 2 == 0
format_name = lambda name: name.strip().title()

print(square(4))
print(is_even(6))
print(format_name(" tom "))
```

### 17.6 `lambda` 能做什么

`lambda` 最适合这种场景：

- 函数只会用一次
- 逻辑非常短
- 需要把一个小函数作为参数传给别的函数

最常见搭配对象包括：

- `map()`
- `filter()`
- `sorted()`
- `max()`
- `min()`

### 17.7 `lambda` 和普通函数怎么选

更适合 `lambda` 的场景：

- 逻辑只有一行
- 只在当前局部使用一次
- 作为回调函数传入

更适合 `def` 的场景：

- 逻辑超过一行
- 需要复用
- 需要加注释和更明确的函数名
- 需要单元测试

一个简单判断标准：

> 如果这个 `lambda` 已经长到要停下来读两遍，就应该改成普通函数。

### 17.8 `lambda` 和推导式的关系

`lambda` 不是推导式，但它经常和推导式出现在同一类数据处理场景里。

区别可以这样理解：

- 推导式负责“生成结果结构”
- `lambda` 负责“定义一个临时的小处理规则”

例如：

```python
numbers = [1, 2, 3, 4, 5]

result1 = [num * 2 for num in numbers]
result2 = list(map(lambda num: num * 2, numbers))

print(result1)
print(result2)
```

这里：

- 左边是列表推导式
- 右边是 `map() + lambda`

它们都在做“批量转换”，只是表达方式不同。

### 17.9 `lambda` 的完整案例

```python
users = [
    {"username": " tom ", "age": 23, "active": True},
    {"username": " jack ", "age": 19, "active": False},
    {"username": " lucy ", "age": 28, "active": True},
]

# 1. map + lambda：清洗用户名
clean_names = list(map(lambda user: user["username"].strip(), users))

# 2. filter + lambda：过滤活跃用户
active_users = list(filter(lambda user: user["active"], users))

# 3. sorted + lambda：按年龄排序
sorted_users = sorted(active_users, key=lambda user: user["age"])

print(clean_names)
print(active_users)
print(sorted_users)
```

这个案例体现：

- `lambda` 很适合做一次性的轻量规则
- 和 `map()`、`filter()`、`sorted()` 搭配非常自然
- 但如果规则开始变复杂，就应该及时改回普通函数

### 17.10 一张表看懂 `lambda`

| 对比项 | `lambda` | `def` |
| --- | --- | --- |
| 形式 | 表达式 | 语句 |
| 是否需要函数名 | 不一定 | 需要 |
| 适合逻辑复杂度 | 很短 | 短到复杂都可以 |
| 典型用途 | 临时回调、小型规则 | 可复用函数、明确业务逻辑 |

### 17.11 一张表看懂差异

| 工具 | 主要作用 | 是否常与推导式互相替代 | 常见关系 |
| --- | --- | --- | --- |
| `map()` | 批量转换 | 是 | 简单转换时常可互换 |
| `filter()` | 条件过滤 | 是 | 简单过滤时常可互换 |
| `sorted()` | 排序 | 否 | 通常和推导式组合 |

### 17.12 实战建议

推荐优先顺序通常是：

1. 简单转换和简单过滤，优先考虑推导式
2. 现成函数复用明显时，可以用 `map()` 和 `filter()`
3. 涉及排序时，直接使用 `sorted()`
4. 临时规则很短时，可以使用 `lambda`
5. 不要为了“高级感”堆太多函数式链条

### 17.13 完整案例：用户列表整理

```python
users = [
    {"username": " tom ", "age": 23, "active": True},
    {"username": " jack ", "age": 19, "active": False},
    {"username": " lucy ", "age": 28, "active": True},
]

# 1. map：统一清洗用户名
clean_names = list(map(lambda user: user["username"].strip(), users))

# 2. filter：筛选活跃用户
active_users = list(filter(lambda user: user["active"], users))

# 3. 推导式：生成更适合前端展示的数据
cards = [
    {"label": user["username"].strip(), "value": user["age"]}
    for user in active_users
]

# 4. sorted：按年龄排序
sorted_cards = sorted(cards, key=lambda item: item["value"])

print(clean_names)
print(active_users)
print(cards)
print(sorted_cards)
```

## 18. 生成器、迭代器与 `yield`

前面已经介绍了生成器表达式，但如果想真正理解它，必须把下面 3 个概念串起来：

- 可迭代对象
- 迭代器
- 生成器

### 18.1 什么是可迭代对象

可迭代对象，指的是可以被 `for` 循环遍历的对象。

常见例子：

- 列表
- 元组
- 字符串
- 字典
- 集合
- 生成器

示例：

```python
items = [1, 2, 3]

for item in items:
    print(item)
```

### 18.2 什么是迭代器

迭代器是一个“可以不断取下一个值”的对象。

你可以把它理解成：

> 一个按顺序吐出元素的数据访问器。

示例：

```python
items = [10, 20, 30]
iterator = iter(items)

print(next(iterator))
print(next(iterator))
print(next(iterator))
```

特点：

- 迭代器会记住当前位置
- 取完以后就没有了

### 18.3 什么是生成器

生成器是一种特殊的迭代器。

生成器可以通过两种方式得到：

1. 生成器表达式
2. 带 `yield` 的函数

示例：

```python
gen = (num * 2 for num in range(5))

print(next(gen))
print(next(gen))
```

### 18.4 `yield` 是什么

`yield` 是定义生成器函数的关键字。

带 `yield` 的函数，不再是普通函数，而是生成器函数。

示例：

```python
def count_up_to(n: int):
    current = 1
    while current <= n:
        yield current
        current += 1


gen = count_up_to(5)

print(list(gen))
```

这个函数不会一次性返回整个列表，而是按需一个一个产出结果。

### 18.5 `return` 和 `yield` 的区别

`return`：

- 直接结束函数
- 一次性返回结果

`yield`：

- 暂停函数执行
- 记住当前状态
- 下一次继续从上次位置往下执行

### 18.6 生成器和推导式的关系

生成器表达式本质上是“惰性版的推导式”。

对比：

```python
numbers = [1, 2, 3, 4]

list_result = [num * 2 for num in numbers]
gen_result = (num * 2 for num in numbers)

print(list_result)
print(gen_result)
```

区别：

- 列表推导式立刻生成完整列表
- 生成器表达式按需生成结果

### 18.7 什么时候适合 `yield`

适合：

- 数据量较大
- 想节省内存
- 一边生成一边消费
- 流式处理数据

不一定适合：

- 必须反复遍历结果
- 逻辑本身很简单，只需要一个普通列表

### 18.8 完整案例：日志流式处理

```python
def read_error_lines(lines: list[str]):
    for line in lines:
        if "ERROR" in line:
            yield line.strip()


logs = [
    "INFO service started",
    "ERROR database timeout",
    "INFO retrying",
    "ERROR redis connection lost",
]

error_lines = read_error_lines(logs)

for line in error_lines:
    print(line)
```

这个案例体现：

- 不需要一次性构造全部错误列表
- 可以边遍历边处理
- 很适合日志、文件、流式数据场景

## 19. 字典常用方法专题

字典推导式只是“生成字典”的方式之一。

想真正用好字典，还需要掌握字典对象自身的常用方法。

### 19.1 `get()`

作用：

- 安全取值
- 可设置默认值

```python
user = {"username": "tom", "age": 23}

print(user.get("username"))
print(user.get("email"))
print(user.get("email", "unknown"))
```

适用场景：

- 读取可能不存在的字段
- 避免直接索引触发 `KeyError`

### 19.2 `keys()`、`values()`、`items()`

```python
user = {"username": "tom", "age": 23}

print(user.keys())
print(user.values())
print(user.items())
```

最常见的是配合循环：

```python
for key, value in user.items():
    print(key, value)
```

### 19.3 `update()`

作用：

- 批量更新字典内容

```python
user = {"username": "tom", "age": 23}
user.update({"age": 24, "email": "tom@example.com"})

print(user)
```

### 19.4 `pop()`

作用：

- 删除指定键
- 同时返回被删除的值

```python
user = {"username": "tom", "age": 23}
age = user.pop("age")

print(age)
print(user)
```

### 19.5 `setdefault()`

作用：

- 如果键存在，返回原值
- 如果键不存在，设置默认值并返回

```python
counter = {}

counter.setdefault("python", 0)
counter["python"] += 1

print(counter)
```

### 19.6 字典推导式和字典方法如何配合

这是实战里很常见的写法。

示例：

```python
raw_user = {
    "username": "tom",
    "age": 23,
    "password": "secret",
}

safe_user = {
    key: value
    for key, value in raw_user.items()
    if key != "password"
}

print(safe_user)
print(safe_user.get("email", "not provided"))
```

### 19.7 完整案例：统计文章标签次数

```python
articles = [
    {"title": "Python 基础", "tags": ["python", "basic"]},
    {"title": "FastAPI 入门", "tags": ["python", "fastapi"]},
    {"title": "SQLAlchemy 实战", "tags": ["python", "sqlalchemy"]},
]

tag_counter = {}

for article in articles:
    for tag in article["tags"]:
        tag_counter.setdefault(tag, 0)
        tag_counter[tag] += 1

tag_summary = {
    tag: count
    for tag, count in tag_counter.items()
    if count >= 1
}

print(tag_counter)
print(tag_summary)
```

这个案例体现：

- 字典方法适合做累计和更新
- 字典推导式适合做结果过滤和重新组织

## 20. 集合常用操作专题

集合推导式适合“生成集合”，但集合本身还有很多很实用的操作。

集合最重要的特点有两个：

1. 元素不重复
2. 非常适合做成员判断和集合运算

### 20.1 常见操作：新增、删除、判断成员

```python
tags = {"python", "fastapi"}

tags.add("sqlalchemy")
tags.discard("fastapi")

print("python" in tags)
print(tags)
```

### 20.2 交集、并集、差集

```python
a = {"python", "fastapi", "sqlalchemy"}
b = {"python", "redis", "fastapi"}

print(a & b)  # 交集
print(a | b)  # 并集
print(a - b)  # 差集
```

### 20.3 集合推导式和集合操作配合

```python
team_a = [
    {"username": "tom", "role": "admin"},
    {"username": "jack", "role": "user"},
]

team_b = [
    {"username": "lucy", "role": "admin"},
    {"username": "jack", "role": "user"},
]

roles_a = {user["role"] for user in team_a}
roles_b = {user["role"] for user in team_b}

print(roles_a | roles_b)
print(roles_a & roles_b)
```

### 20.4 什么时候优先考虑集合

适合：

- 去重
- 白名单 / 黑名单
- 快速判断某个值是否存在
- 两批数据的交并差比较

不一定适合：

- 需要保留原始顺序
- 需要按索引访问

### 20.5 完整案例：权限比较

```python
role_permissions = {
    "admin": {"user:add", "user:delete", "user:view", "role:assign"},
    "editor": {"user:view"},
    "auditor": {"user:view", "log:view"},
}

admin_permissions = role_permissions["admin"]
auditor_permissions = role_permissions["auditor"]

common_permissions = admin_permissions & auditor_permissions
admin_only_permissions = admin_permissions - auditor_permissions
all_permissions = admin_permissions | auditor_permissions

print("common_permissions =", common_permissions)
print("admin_only_permissions =", admin_only_permissions)
print("all_permissions =", all_permissions)
```

这个案例体现：

- 集合非常适合表达“权限集合”
- 交集、并集、差集都很自然

## 21. 如何把这些知识串起来

到这里，这份文档已经不只是“介绍推导式语法”，而是在回答一个更实际的问题：

> 当你面对一批数据时，应该选择什么工具把它处理成你想要的结果。

可以用一个简单思路来判断：

1. 如果目标是生成一批结果，优先想推导式
2. 如果目标是批量转换，也可以考虑 `map()`
3. 如果目标是条件筛选，也可以考虑 `filter()`
4. 如果目标是排序，直接用 `sorted()`
5. 如果目标是惰性处理大批量数据，考虑生成器和 `yield`
6. 如果目标是键值组织，重点使用字典和字典方法
7. 如果目标是唯一值、权限、白名单、交并差，重点使用集合

## 22. 最终结论

你可以把 Python 里的这些写法统一理解成：

> 从一批输入数据中，按照某种规则快速生成、过滤、组织或消费另一种结果结构。

真正需要掌握的重点不是死记语法，而是这 6 件事：

1. 先判断最终要的是列表、字典、集合还是惰性结果
2. 再判断该用推导式、`map()`、`filter()`、`sorted()` 还是普通循环
3. 推导式可以混合使用，但必须保持可读性
4. 生成器和 `yield` 适合流式和大数据量场景
5. 字典和集合不仅要会生成，还要会操作
6. 一旦逻辑变复杂，就退回普通 `for` 循环
