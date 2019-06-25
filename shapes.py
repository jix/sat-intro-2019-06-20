"""Block shape definitions.

The shape of a block is defined by a list with an entry for each orientation.
The shape of a block in a single orientation is defined by a list of coordinate
tuples. For each component the smallest value used should be 0.
"""
import textwrap


def parse_shape(ascii_shape):
    """Generate a shape definition from a textual representation."""

    ascii_shape = textwrap.dedent(ascii_shape.strip('\n'))
    rows = ascii_shape.split('\n')
    height = len(rows)
    width = max(len(row) for row in rows)

    points = set()

    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            if cell != ' ':
                points.add((i, j))

    orientations = set()

    def move_origin(points):
        min_i = min(i for i, j in points)
        min_j = min(j for i, j in points)
        return set((i - min_i, j - min_j) for i, j in points)

    for i in range(4):
        orientations.add(tuple(sorted(move_origin(points))))
        points = set((-j, i) for i, j in points)

    return sorted(orientations)


def define_shapes(ascii_shapes):
    return list(map(parse_shape, ascii_shapes.split('\n\n')))


well_known_shapes = define_shapes("""
     ##
    ##

    ##
     ##

    #
    ###

     #
    ###

      #
    ###

    ####

    ##
    ##
""")
