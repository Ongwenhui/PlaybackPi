#RNG

def randomvector():
    import random
    list = [1, 1, 1, 2, 2, 2, 3, 3, 3]
    random.shuffle(list)
    print(list)
    return list

randomvector()