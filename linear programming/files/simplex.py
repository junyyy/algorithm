import argparse
import json
import os
from enum import Enum
import numpy as np


class Status(int, Enum):
    CANDIDATE = 1  # Candidate BFS (but no other information)
    OPTIMAL = 2  # Candidate is optimal
    INFEASIBLE = 3  # Problem is infeasible
    UNBOUNDED = 4  # Problem is unbounded


class LinearProgram:
    def __init__(self, a, b, c):
        """
        Linear program of the form:

        min cT x
         s.t. a x = b
              x >= 0
              b >= 0 (to simplify finding initial feasible solution)

        Using dense matrix and vector representations.
        """

        self.a = a  # m x n
        self.b = b  # m
        self.c = c  # n

    @classmethod
    def load(cls, fn):
        """Loads LP from one of the lp-*.json files"""
        data = json.load(open(fn))
        n = data["n"]
        m = len(data["a"])
        a = np.zeros((m, n))
        b = np.zeros((m))
        c = np.zeros((n))

        for i, con in enumerate(data["a"]):
            for j, a_ij in con[0]:
                a[i, j] = a_ij
            b[i] = con[1]

        for j, c_j in data["c"]:
            c[j] = c_j
        return cls(a, b, c)


def row_operation(matrix, basis):
    for i in range(len(basis)):
        row = i + 1
        col = basis[i]
        row_operation_once(matrix, row, col)


def row_operation_once(matrix, row, col):
    # Use in second time to run simplex
    # row indicates the exiting var
    # col indicates the entering var
    m, n = matrix.shape
    matrix[row] /= matrix[row, col]
    for other_row in range(m):
        if other_row != row:
            matrix[other_row] = matrix[other_row] - matrix[other_row, col] * matrix[row]


def simplex_inner(lp, basis, tol):
    """Solves a LinearProgram given a starting BFS using simplex algorithm"""
    m = len(lp.b)
    n = len(lp.c)
    # Can only handle problems where (otherwise likely overconstrained)
    assert (n >= m)
    # Need same number of basis variables as constraints
    assert (len(basis) == m)

    # concatenate the vectors
    c = np.concatenate((-lp.c, [0])).reshape(1, n + 1)
    Ab = np.concatenate((lp.a, lp.b.reshape(m, 1)), axis=1)

    # In this matrix, the first col is NOT [1, 0, 0, ...] that relates to z
    # so it's shape different is a bit different from what appears in slides
    matrix = np.concatenate((c, Ab))
    matrix_m, matrix_n = matrix.shape

    row_operation(matrix, basis)

    pivots = 0
    while max(matrix[0, 0: matrix_n - 1] > tol):
        # pick one which has the greatest positive coefficient
        col = np.argmax(matrix[0, 0: matrix_n - 1])
        if max(matrix[1:, col]) <= 0:
            # which means that in all rows, all entries are less than or equal to 0
            return {"status": Status.UNBOUNDED, "pivots": pivots}
        row = None
        for i in range(1, matrix_m - 1):
            if matrix[i, col] > tol:
                if not row:
                    row = i
                elif matrix[i, matrix_n - 1] / matrix[i, col] < matrix[row, matrix_n - 1] / matrix[row, col]:
                    row = i

        basis[row - 1] = col
        row_operation_once(matrix, row, col)

        pivots += 1

    opt_val = matrix[0, matrix_n - 1]
    x = np.zeros(matrix_n)
    for i in range(1, matrix_m):
        for j in range(matrix_n - 1):
            if matrix[i, j] == 1:
                x[j] = matrix[i, matrix_n - 1]

    lp.a = matrix[1:,0: n-m]
    lp.b = matrix[1:, matrix_n-1]
    return {"status": Status.OPTIMAL, "pivots": pivots, "x": x, "basis": basis, "objective": opt_val}


def simplex(lp, tol=1e-9):
    """
    Solves a LinearProgram using simplex algorithm

    lp: a LinearProgram
    tol: a tolerance in case you encounter floating point precision errors

    Returns a dict with the following entries:
        status: Status [always]
        bfs_pivots: number of pivots to find BFS [always]
        opt_pivots: number of pivots from BFS onwards [when UNBOUNDED or
            OPTIMAL]
        x: numpy array of variable values in same order as LinearProgram [when
            OPTIMAL]
        basis: variable indices of the current BFS [when OPTIMAL]
        objective: objective value [when OPTIMAL]
    """
    # Solve a modified version of the problem to get a starting BFS
    # UNIMPLEMENTED


    m = len(lp.b)
    n = len(lp.c)
    s = np.identity(m)

    # set the new a and c to run the simplex
    # in order to get the starting bfs
    c = lp.c


    lp.a = np.concatenate((lp.a, s), axis=1)
    lp.c = np.concatenate((np.zeros(n), np.ones(m)))

    slack_basis = [i for i in range(n, n + m)]
    res = simplex_inner(lp, slack_basis, tol)

    # if any slack variable is non-zero, the original problem is infeasible.
    x = res["x"]
    # get the bfs_pivots
    bfs_pivots = res["pivots"]
    # get the basis
    basis = res["basis"]
    # get the objective
    objective = res["objective"]
    if abs(objective) > tol:
        return {"status": Status.INFEASIBLE, "bfs_pivots": bfs_pivots}

    # if the problem is feasible, then run the simplex again
    # change c back to original one
    lp.c = c
    new_res = simplex_inner(lp, basis, tol)
    opt_pivots = new_res["pivots"]
    if new_res["status"] == Status.UNBOUNDED:
        return {"status": Status.UNBOUNDED, "bfs_pivots": bfs_pivots, "opt_pivots": opt_pivots}
    x = new_res["x"]
    basis = new_res["basis"]
    basis.sort()
    objective = new_res["objective"]
    return {"status": Status.OPTIMAL,
            "bfs_pivots": bfs_pivots,
            "opt_pivots": opt_pivots,
            "x": x,
            "basis": basis,
            "objective": objective
            }


if __name__ == "__main__":
    par = argparse.ArgumentParser("Simplex Linear Programming Solver")
    par.add_argument("file", help="json model file")

    args = par.parse_args()

    lp = LinearProgram.load(args.file)
    sol = simplex(lp)
    print(f'Status: {sol["status"]}')
    if sol["status"] == Status.OPTIMAL:
        print(f'Objective: {sol["objective"]}')
        print(f'Variables: {sol["x"]}')
        print(f'Basis: {sol["basis"]}')
    if sol["status"] == Status.INFEASIBLE:
        print(f'Pivots: {sol["bfs_pivots"]}')
    else:
        print(f'Pivots (BFS, OPT): {sol["bfs_pivots"]} {sol["opt_pivots"]}')

    # Can't directly serialise to json numpy objects, so converting first (this
    # will potentially lose precision)
    if "x" in sol:
        sol["x"] = [x.item() for x in sol["x"]]
    if "basis" in sol:
        sol["basis"] = [x.item() for x in sol["basis"]]
    print(sol)
    json.dump(sol, open(os.path.splitext(args.file)[0] + "-sol.json", "w"),
              indent=2)
