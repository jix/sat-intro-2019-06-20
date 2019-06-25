from random import Random


def random_instance(shapes, steps, max_fill, max_duration, seed=None):
    """Generate a random schedule of blocks.

    Args:
        shapes: The list of shapes to pick from (see shapes.py)
        steps: How many time steps the schedule should have in total
        max_fill: Max number of cells that should be required at the same time
        max_duration: Max number of steps a block is scheduled
        seed: Random seed (optional)

    Returns:
        A list of (begin, end, shape) tuples where shape is scheduled for the
        time interval [begin, end)
    """
    random = Random(seed)

    schedule = []

    # We keep track of the number of cells used for each time step
    fill_levels = {i: 0 for i in range(steps)}

    # To know whether we can place a nother block we compute the smallest
    # number of cells used by any block
    min_shape = min(len(shape[0]) for shape in shapes)

    # We can place another block at or below this fill level
    fill_limit = max_fill - min_shape

    while True:
        # Select a single time step that isn't full yet
        try:
            selected = random.choice([
                i for i in range(steps) if fill_levels[i] <= fill_limit
            ])
        except IndexError:
            break

        # Extend the interval as far back as possible
        begin = selected
        try:
            while fill_levels[begin - 1] <= fill_limit:
                begin -= 1
        except KeyError:
            pass

        # And es far forward as possible
        end = selected + 1
        try:
            while fill_levels[end] <= fill_limit:
                end += 1
        except KeyError:
            pass

        # Select a random duration that is a) smaller than the interval we just
        # found and b) smaller than the max duration we want to schedule a
        # block for
        duration = min(random.randint(1, end - begin), max_duration)

        # Select a random sub-interval of the given duration
        block_begin = random.randint(begin, end - duration)
        block_end = block_begin + duration

        # We need the maximum fill level of any step in that interval to know
        # which blocks do fit (in case the blocks have different numbers of
        # cells)
        fill_level = max(
            fill_levels[i] for i in range(block_begin, block_end)
        )

        # Now we select a shape that fits in the margin between the current and
        # the maximum fill level
        margin = max_fill - fill_level

        block_shape = random.choice([
            shape for shape in shapes if len(shape[0]) <= margin
        ])

        # And then update our fill levels
        weight = len(block_shape[0])

        for i in range(block_begin, block_end):
            fill_levels[i] += weight

        schedule.append((block_begin, block_end, block_shape))

    # Sorting is only done to make manual inspection of the schedule easier to
    # aid debugging
    return sorted(schedule)
