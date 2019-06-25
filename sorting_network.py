"""Implementation of the batcher odd–even mergesort

Non-power of two sizes are realized by generating the next larger power of two
shrinking the resulting network by removing items at the end. It's safe to
remove them as we can imagine the prefix contains items smaller than any other
and the suffix items larger than any other. In that case no comparator would
ever move those items.
"""


def _sorting_network(indices):
    if len(indices) < 2:
        pass
    elif len(indices) == 2:
        yield (indices[0], indices[1])
    elif len(indices) % 2 != 0:
        raise ValueError('length needs to be even')
    else:
        mid = len(indices) // 2

        yield from _sorting_network(indices[:mid])
        yield from _sorting_network(indices[mid:])

        yield from _merge_network(indices)


def _merge_network(indices):
    if len(indices) < 2:
        pass
    elif len(indices) == 2:
        yield (indices[0], indices[1])
    elif len(indices) % 4 != 0:
        raise ValueError('length needs to be a multiple of four')
    else:

        yield from _merge_network(indices[0::2])
        yield from _merge_network(indices[1::2])

        for x, y in zip(indices[1::2], indices[2::2]):
            yield (x, y)


def sorting_network(size):
    next_pot_size = 1 << (size - 1).bit_length()

    fill = next_pot_size - size

    prefix_len = fill // 2
    suffix_len = (fill + 1) // 2

    network = _sorting_network(
        [None] * prefix_len + list(range(size)) + [None] * suffix_len)

    return [
        (a, b) for (a, b) in network
        if a is not None and b is not None
    ]


def test_network(network, input):
    for (a, b) in network:
        if input[a] > input[b]:
            input[a], input[b] = input[b], input[a]
    return input
