a = [1,2,3]
b = a
a.append(4)
print(b)  # [1, 2, 3, 4]
def calculate(a, b):
    sum_val = a + b
    diff_val = a - b
    # 返回多个值，Python 自动打包成元组 (15, 5)
    return sum_val, diff_val 
def check_age(age):
    if age < 0:
        return "年龄不能为负数" # 函数在此处结束

    # 只有年龄大于等于 0 才会执行到这里
    return "年龄有效"
def log_data(level, *args, **kwargs):
    print(f"级别: {level}")
    print(f"位置参数 (args): {args}")      # (1, 'user')
    print(f"关键字参数 (kwargs): {kwargs}")  # {'time': '10:00', 'status': 'ok'}

log_data("INFO", 1, 'user', time='10:00', status='ok')
result_tuple = calculate(10, 5) 
print(result_tuple) # 输出: (15, 5)

# 也可以在接收时解包
s, d = calculate(10, 5)
print(f"和: {s}, 差: {d}") # 输出: 和: 15, 差: 5
def fb(b,a=3):
    print(b)
fb(200)
def FUNC(*args):
    print(args)    
FUNC(1)