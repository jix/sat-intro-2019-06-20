"""Implementation of the block packing example from the talk.
"""
from pycadical import Solver
from itertools import count, islice, combinations
from sorting_network import sorting_network
import time
import json
import math


class PackingSolver:
    def __init__(
            self, schedule, height, max_width,
            use_cardinality=True, verbose=False,
            at_most_one='product',
            solver=None):
        """Generate an instance of the block packing example.

        Args:
            schedule: The given time schedule of blocks (see gen_instance.py)
            height: The fixed height of the packing area
            max_width: Upper bound on the width of the packing area
            use_cardinality: Whether to generate cardinality constraints
            verbose: Show verbose SAT solver output
            at_most_one: Encoding to use for at_most_one constraints
            solver: Use an existing SAT solver instance
        """
        if solver is None:
            solver = Solver()
            if not verbose:
                solver.set_option("quiet", 1)

        self.schedule = schedule
        self.solver = solver
        self.var = count(1)
        self.height = height
        self.max_width = max_width
        self.blocked_width = self.max_width
        self.clauses = 0
        self.at_most_one_type = at_most_one

        self.upper = max_width + 1
        self.lower = -1

        self.lower_timeout = 5
        self.upper_timeout = 5

        # map indicator variables to choices
        self.choices = {}

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
                        choice = next(self.var)

                        item_choices.append(choice)

                        # remember this variable for processing a found
                        # solution
                        self.choices[choice] = (item_id, i, j, mask_id)

                        # add the choice variable to every time step and
                        # position used by this choice
                        for t in range(begin, end):
                            for di, dj in mask:
                                blocked.setdefault(
                                    (t, i + di, j + dj), []
                                ).append(choice)

            # we need to select exactly one choice for this item
            self.add_clause(item_choices)
            self.at_most_one(item_choices)

        if use_cardinality:
            for t, use_count in enumerate(pos_used):
                # for each time step and each position we create the logical or
                # of all choices that use it
                in_use = []
                for j in range(0, max_width):
                    for i in range(0, height):
                        in_use_var = next(self.var)
                        in_use.append(in_use_var)
                        blocking_choices = blocked[(t, i, j)]
                        for choice in blocking_choices:
                            self.add_clause([-choice, in_use_var])
                        self.add_clause([-in_use_var, *blocking_choices])

                self.cardinality_constraint(in_use, use_count, use_count)

        # to optimize the width used, we add variables that block positions on
        # the right
        self.block_vars = list(islice(self.var, max_width))

        for j, block_var in enumerate(self.block_vars):
            for i in range(0, height):
                for t in range(self.steps):
                    blocked.setdefault((t, i, j), []).append(block_var)

        # we also add impliciations from block_var[i] to block_var[i + 1], so
        # everything to the right of i is also automatically blocked
        for i in range(len(self.block_vars) - 1):
            self.add_clause(
                [-self.block_vars[i], self.block_vars[i + 1]]
            )

        # now we make sure that only one item uses a position and time step
        for blocked_list in blocked.values():
            self.at_most_one(blocked_list)

        print(
            f'used {self.clauses} clauses and {next(self.var) - 1} variables')

    def add_clause(self, clause):
        self.clauses += 1
        self.solver.add_clause(clause)

    def at_most_one(self, variables):
        """Compact and efficient encoding of at most one constraints.
        """

        if self.at_most_one_type == 'binary':
            limit = 4
        elif self.at_most_one_type == 'commander':
            limit = 16
        elif self.at_most_one_type == 'product':
            limit = 16
        else:
            raise ValueError(
                f'unknown at_most_one encoding {self.at_most_one_type}')

        if len(variables) > limit:
            if self.at_most_one_type == 'binary':
                bits = (len(variables) - 1).bit_length()
                index = list(islice(self.var, bits))
                for i, variable in enumerate(variables):
                    for bit, index_bit in enumerate(index):
                        if (i >> bit) & 1:
                            self.add_clause([-variable, index_bit])
                        else:
                            self.add_clause([-variable, -index_bit])
            elif self.at_most_one_type == 'commander':
                group_count = int(math.sqrt(len(variables)))

                commanders = list(islice(self.var, group_count))

                groups = [
                    variables[i::group_count] + [-c]
                    for i, c in enumerate(commanders)
                ]

                for group in groups:
                    self.add_clause(group)
                    self.at_most_one(group)

                self.at_most_one(commanders)
            elif self.at_most_one_type == 'product':
                rows = int(math.sqrt(len(variables)))
                columns = (len(variables) + rows - 1) // rows

                row_vars = list(islice(self.var, rows))
                column_vars = list(islice(self.var, columns))

                for i, row_var in enumerate(row_vars):
                    for j, column_var in enumerate(column_vars):
                        k = i * columns + j
                        if k < len(variables):
                            input_var = variables[k]
                            self.add_clause([-input_var, row_var])
                            self.add_clause([-input_var, column_var])

                self.at_most_one(row_vars)
                self.at_most_one(column_vars)
            else:
                assert False  # unreachable
        else:
            for v1, v2 in combinations(variables, 2):
                self.add_clause([-v1, -v2])

    def cardinality_constraint(self, variables, low, high):
        variables = list(variables)

        for a, b in sorting_network(len(variables)):
            out_low, out_high = next(self.var), next(self.var)

            in_a, in_b = variables[a], variables[b]

            self.add_clause([-in_a, out_high])
            self.add_clause([-in_b, out_high])
            self.add_clause([-in_a, -in_b, out_low])

            self.add_clause([in_a, -out_low])
            self.add_clause([in_b, -out_low])
            self.add_clause([in_a, in_b, -out_high])

            variables[a], variables[b] = out_low, out_high

        for i, var in enumerate(variables[::-1]):
            if i < low:
                self.add_clause([var])
            elif i >= high:
                self.add_clause([-var])

    def optimize(self):
        """Find an optimal solution.

        Solutions are written to ``solution_$width.json`` files in the current
        directory. Those can be viewed using ``view_sol.py``.
        """

        # To find an optimal solution we further constrain the width whenever a
        # new solution was found. Occasionally we also ask the solver for a
        # solution at the lower bound. If no such solution exists we can
        # improve the lower bound. Timeouts are used to schedule these qureies.
        #
        #
        # We're using the same solver instance for all these queries and make
        # use of the assumption features that allow queries that fix certain
        # variables without constraining them for future queries. Thereby we
        # avoid starting over whenever a bound is improvied.
        #
        # Nevertheless using assumptions is not always faster than starting
        # independent searches. A more advanced hybrid approach would likely
        # fare better for larger problems.

        print("optimizing...")
        while self.lower + 1 < self.upper:

            # Only one case left?
            if self.lower + 2 == self.upper:
                self.solve(self.lower + 1, timeout=None)
                break

            progress = self.solve(
                self.upper - 1, timeout=self.upper_timeout)
            if not progress:
                self.upper_timeout *= 2

            if self.lower + 1 >= self.upper:
                break

            progress = self.solve(
                self.lower + 1, timeout=self.lower_timeout)
            if not progress:
                self.lower_timeout *= 1.1

    def solve(self, width, timeout=None):
        if width < self.blocked_width:
            blocked = self.block_vars[width]
            self.solver.assume(blocked)

        if timeout is None:
            self.solver.set_terminate(None)
        else:
            end_time = time.clock_gettime(time.CLOCK_MONOTONIC) + timeout
            self.solver.set_terminate(
                lambda: time.clock_gettime(time.CLOCK_MONOTONIC) >= end_time)

        result = self.solver.solve()

        new_lower = False

        if result is False:
            new_lower = True
            self.lower = width

        while True:
            if self.lower == self.max_width:
                break
            if self.solver.fixed(self.block_vars[self.lower + 1]) is not False:
                break
            self.lower += 1
            new_lower = True

        if new_lower:
            print(f"new lower bound {self.lower + 1}..{self.upper}")

        if result is True:
            width = self.max_width - sum(map(self.solver.val, self.block_vars))
            self.upper = width
            self.save_solution(width)
            self.lower_blocked_width(width - 1)
            print(f"new upper bound {self.lower + 1}..{self.upper}")
            return True

        return result is not None

    def lower_blocked_width(self, width):
        if width < self.blocked_width:
            self.blocked_width = width
            blocked = self.block_vars[width]
            self.add_clause([blocked])

    def save_solution(self, width):
        output = [
            [[None] * width for _ in range(self.height)]
            for _ in range(self.steps)
        ]

        for var, choice in self.choices.items():
            if self.solver.val(var) is True:
                item_id, i, j, mask_id = choice

                begin, end, shape = self.schedule[item_id]

                for di, dj in shape[mask_id]:
                    for t in range(begin, end):
                        assert output[t][i + di][j + dj] is None
                        output[t][i + di][j + dj] = item_id

        with open(f'solution_{width}.json', 'w') as solution_file:
            json.dump(output, solution_file)
