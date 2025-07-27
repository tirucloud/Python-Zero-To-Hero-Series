l = ['a', 'b', 'a', 'c', 'b', 'd']
res = []
seen = []

for item in l:
    if item not in seen:
        res.append(item)
        seen.append(item)

print(res)
