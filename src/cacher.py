

# TODO make a good cacher decorator to cache the queries
def cacher(f):
    cache = {}
    def wrapper(*args, **kwargs):
        _hash = hash(str(args) + str(kwargs))

        cached = cache.get(_hash, None)

        if not cached:
            cached = f(*args, **kwargs)
            cache[_hash] = cached

         return cached
    return wrapped