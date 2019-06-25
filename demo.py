import argparse

from gen_instance import random_instance
from shapes import well_known_shapes
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)

parser = argparse.ArgumentParser(
    description='generate and solve an example problem')
parser.add_argument('--steps', type=int, help='number of time steps')
parser.add_argument('--fill', type=int,
                    help='limit of blocks present at the same time')
parser.add_argument('--duration', type=int,
                    help='limit of steps an item is present')
parser.add_argument('--height', type=int,
                    help='height of the packing area')
parser.add_argument('--max-width', type=int,
                    help='maximal width of the packing area')
parser.add_argument('--no-cardinality', action='store_true',
                    help='do not use cardinality constraints')
parser.add_argument('--at-most-one', type=str, default='product',
                    choices=['product', 'binary', 'commander'],
                    help='encoding to use for at most one constraints')
parser.add_argument('--verbose', action='store_true',
                    help='verbose solver logging')
parser.add_argument('--ip', action='store_true',
                    help='use the IP formulation and CBC as solver')
parser.add_argument('--seed', type=int, nargs='?',
                    help='random seed for instance generation')

args = parser.parse_args()

items = random_instance(
    well_known_shapes,
    args.steps,
    args.fill,
    args.duration,
    args.seed
)

print(f'placing {len(items)} items')

if args.ip:
    from packing_ip import PackingSolverIp
    solver = PackingSolverIp(
        items,
        args.height, args.max_width,
        use_cardinality=not args.no_cardinality,
    )
else:
    from packing import PackingSolver
    solver = PackingSolver(
        items,
        args.height, args.max_width,
        use_cardinality=not args.no_cardinality,
        at_most_one=args.at_most_one,
        verbose=args.verbose
    )

solver.optimize()
