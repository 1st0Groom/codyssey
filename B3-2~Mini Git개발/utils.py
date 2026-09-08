def merge_sort(arr, key_func=lambda x: x):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2

    left = merge_sort(arr[:mid], key_func)
    right = merge_sort(arr[mid:], key_func)

    return merge(left, right, key_func)


def merge(left, right, key_func):
    result = []
    i, j = 0, 0

    while i < len(left) and j < len(right):
        if key_func(left[i]) <= key_func(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])

    return result
