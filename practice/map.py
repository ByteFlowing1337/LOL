map = {1:1,2:1,3:1}
print(map[3])
score:int=1;print(score)
def force_params(a, /, b, *, c):
    # a: 只能是位置参数
    # b: 可以是位置或关键字参数
    # c: 只能是关键字参数
    print(a, b, c)

force_params(10, 20, c=30)  # 正确