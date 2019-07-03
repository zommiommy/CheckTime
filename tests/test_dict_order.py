# The script assumes that the dictionary are ordered.

a = {
    "a":1,
    "d":2,
    "z":6,
    "b":3
}

o = ",".join("%s:%s"%(k) for k in a.items())

print(o)
assert o == "a:1,d:2,z:6,b:3", "The dictionary are not ordered!"