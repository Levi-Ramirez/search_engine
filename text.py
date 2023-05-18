dict1 = {'a': 10, 'b':20}
dict2 = {'b':10, 'c':50}

dict3 = {**dict1, **dict2}
print(dict3)