def nest():
    print("nest")
    def inner():
        print("inner")
    inner()
nest()

def outer_function(factor): # 外部函数
    
    # 内部函数，它可以访问外部函数的局部变量 'factor'
    def inner_function(number): 
        return number * factor
    
    # 外部函数返回内部函数本身
    return inner_function 

# 1. 调用外部函数，它返回了 inner_function，并记住了 factor=5
multiplier = outer_function(5) 
print(multiplier) # <function outer_function.<locals>.inner_function at 0x7f9b8c0c1d30>

# 2. 调用返回的内部函数（即闭包）
result = multiplier(10) # 10 * 5

print(result) # 输出: 50
(lambda x: x * 20)(3) # 60
# 3. 直接调用外部函数并立即调用返回的内部函数
result2 = outer_function(3)(10) # 10 * 3
print(result2) # 输出: 30