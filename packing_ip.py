from itertools import count, islice, combinations
from sorting_network import sorting_network
import time
import json
import math
import subprocess
import tempfile


class PackingSolverIp:
    def __init__(
            self, schedule, height, max_width, use_cardinality):
        """Generate an IP instance of the block packing example.

        Args:
            schedule: The given time schedule of blocks (see gen_instance.py)
            height: The fixed height of the packing area
            max_width: Upper bound on the width of the packing area
            use_cardinality: Constrain the number of used cells per time step
        """

        self.schedule = schedule

        self.choice_vars = set()

        self.height = height
        self.max_width = max_width

        # map indicator variables to choices
        self.choices = {}
        self.constraints = []

        self.steps = max(end for begin, end, shape in schedule)

        # for each time step and position a list of choices that make use of
        # that position in that step
        blocked = {}

        # for each time step we count how many positions are used
        pos_used = [0] * self.steps

        for item_id, (begin, end, shape) in enumerate(schedule):
            for t in range(begin, end):
                pos_used[t] += len(shape[0])

            # list of all possible coices for this item
            item_choices = []

            for mask_id, mask in enumerate(shape):
                mask_width = max(j for i, j in mask)
                mask_height = max(i for i, j in mask)

                for i in range(0, height - mask_height):
                    for j in range(0, max_width - mask_width):

                        # indicator variable for this item position and
                        # orientation
                        choice = f'c_{item_id}_{i}_{j}_{mask_id}'

                        item_choices.append(choice)

                        # add the choice variable to every time step and
                        # position used by this choice
                        for t in range(begin, end):
                            for di, dj in mask:
                                blocked.setdefault(
                                    (t, i + di, j + dj), []
                                ).append(choice)

            # we need to select exactly one choice for this item
            self.constraints.append(
                ([(1, c) for c in item_choices], 'E', 1)
            )

        if use_cardinality:
            for t, use_count in enumerate(pos_used):
                # for each time step and each position we create the logical or
                # of all choices that use it
                in_use = []
                for j in range(0, max_width):
                    for i in range(0, height):
                        in_use_var = f'f_{t}_{j}_{i}'
                        in_use.append(in_use_var)
                        blocking_choices = blocked[(t, i, j)]
                        for choice in blocking_choices:
                            self.constraints.append(
                                ([(-1, choice), (1, in_use_var)], 'G', 0)
                            )

                        self.constraints.append(([
                            (-1, in_use_var),
                            *[(1, c) for c in blocking_choices]
                        ], 'G', 0))

                self.constraints.append(
                    ([(1, v) for v in in_use], 'E', use_count))

        # to optimize the width used, we add variables that block positions on
        # the right
        self.block_vars = [f'b_{j}' for j in range(max_width)]

        for j, block_var in enumerate(self.block_vars):
            for i in range(0, height):
                for t in range(self.steps):
                    blocked.setdefault((t, i, j), []).append(block_var)

        # we also add impliciations from block_var[i] to block_var[i + 1], so
        # everything to the right of i is also automatically blocked
        for i in range(len(self.block_vars) - 1):
            self.constraints.append((
                [(-1, self.block_vars[i]), (1, self.block_vars[i + 1])],
                'G', 0
            ))

        self.constraints.append((
            [(1, 'b'), *[(1, v) for v in self.block_vars]],
            'E', self.max_width
        ))

        # now we make sure that only one item uses a position and time step
        for blocked_list in blocked.values():
            self.constraints.append(
                ([(1, v) for v in blocked_list], 'L', 1))

    def optimize(self):
        """Optimize the resulting IP instance using the CBC solver."""
        with tempfile.NamedTemporaryFile('w', suffix='.mps') as mps_file:
            def out(*args, **kwargs):
                print(*args, **kwargs, file=mps_file)

            out('NAME TESTPROB')
            out('ROWS')
            out(' N width')
            by_column = {}
            for i, (vs, k, c) in enumerate(self.constraints):
                out(f' {k} R{i}')
                for (v, col) in vs:
                    by_column.setdefault(col, []).append((v, i))
            out('COLUMNS')
            for col, vs in by_column.items():
                # out(f'    {col}', end='')
                for (v, i) in vs:
                    out(f'    {col} R{i} {v}')
                if col == 'b':
                    out('    b width 1')
                # out()
            out('RHS')
            for i, (vs, k, c) in enumerate(self.constraints):
                out(f'    RHS1 R{i} {c}')
            out('BOUNDS')
            for col in by_column.keys():
                if col != 'b':
                    out(f' BV BND1 {col}')
                else:
                    out(f' LI BND1 {col} 0')

            out('ENDATA', flush=True)

            subprocess.check_call(['cbc', mps_file.name])
