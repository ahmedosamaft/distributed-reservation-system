def test():
    yield 'first' # <------ 1
    # print("After First")
    yield 'second' # <------ 2
    # yield 'third' # <------ 2

generator = test()

print(next(generator)) 
print(next(generator)) 
print(next(generator))
