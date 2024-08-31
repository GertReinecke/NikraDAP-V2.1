def exists(active: list, obj: str):
    for l in active:
        if (l == obj):
            return True
    return False


L = ['John', 'Susan']

print(exists(L, 'John'))