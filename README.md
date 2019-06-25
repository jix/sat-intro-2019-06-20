# SAT Solver Optimization Demo

This is the source code for the demo application presented during my
"Introduction to SAT Solving" talk at the OR Meetup Leipzig in June 2019.

The code is written in Python 3. Apart from `view_sol.py` the code also works
with PyPy3 (JIT compiled Python). For large problem instances, CNF generation
is a lot faster using PyPy3.

External dependencies are the [CaDiCaL][1] SAT solver, which is used as a library and [Pygame][2] which is used for displaying the solutions.

CaDiCaL needs to be built as a shared library, this can be automatically done
using `./build_libcadical.sh` which will also download the CaDiCaL source code
from GitHub. For non-Linux systems the build script and the `pycadical.py`
bindings need to be adjusted.

To solve the equivalent integer programming formulation of the problem, the Cbc
command line solver is required. A different command line solver that supports
the `.mps` format can be used by changing the last line of the `optimize`
method  in `packing_ip.py`.

## Files

* `demo.py` -- Command line tool to generate and solve problem instances
* `shapes.py` -- Defines the well known shapes used in the example
* `gen_instances.py` -- Generates random problem instances
* `pycadical.py` -- Python bindings to the CaDiCaL SAT solver
* `build_libcadical.sh` -- Build script for CaDiCaL as shared library
* `sorting_network.py` -- Batcher odd–even mergesort sorting networks
* `packing.py` -- Implementation of the model presented during the talk
* `packing_ip.py` -- Implementation of the equivalent IP model
* `view_sol.py` -- Pygame based viewer of `solution_x.json` files
* `build_libcadical.sh` -- Build script for CaDiCaL as shared library
* `sat-intro.pdf` -- Slides of the talk

## Usage

The demo shown during the talk was

`pypy3 demo.py --steps 100 --fill 28 --duration 4 --height 5 --max-width 20 --seed 1`

The `demo.py` script supports several command line options, see `pypy3 demo.py --help`.

Using `python3` instead of `pypy3` also works but takes longer to generate the
SAT instance.

The found solutions will be written to the current directory as
`solution_{width}.json` and can be viewed using `python3 view_sol.py
solution_{width}.json`. Use the escape key to exit and the cursor keys to step
through time. Pressing and holding the space bar automatically steps through
time.

## Larger Instances

This approach scales quite well with an increasing number of time steps. This
10 times larger problem is solved within 10 minutes

`pypy3 demo.py --steps 1000 --fill 28 --duration 4 --height 5 --max-width 20 --seed 1`

Appending the `--verbose` flag makes it less boring to watch :)

## Using Integer Programming

When using integer programming, the extra redundant cardinality constraints
used to speed up SAT solving cause a large slow down. They can be disabled by
passing the option `--no-cardinality` option.

With the Cbc solver, the optimal solution is only found for very small problems
and the solver is not able to rule out better solutions. Commercial MILP
solvers are a lot better at this problem, but as far as I can tell, deliver not
anywhere near the speed that SAT solvers do.

[1]:https://github.com/arminbiere/cadical
[2]:https://www.pygame.org/

