from ortools.linear_solver import pywraplp
from ortools.linear_solver import pywraplp
from math import ceil
from random import randint
import json
import random
import time


def newSolver(name, integer=False):
    return pywraplp.Solver(name, pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING if integer else pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)


def SolVal(x):
    if type(x) is not list:
        return 0 if x is None \
            else x if isinstance(x, (int, float)) \
            else x.SolutionValue() if x.Integer() is False \
            else int(x.SolutionValue())
    elif type(x) is list:
        return [SolVal(e) for e in x]


def ObjVal(x):
    return x.Objective().Value()


def gen_data(num_orders):
    R = []
    list_objects = [random.randrange(10, 99) for i in range(num_orders)]
    for i in list_objects:
        R.append([list_objects.count(i), i])
        while i in list_objects:
            list_objects.remove(i)
    return R


def solve_model(demands, parent_width=100, cutStyle='minWaste'):
    num_orders = len(demands)
    solver = newSolver('Cutting Stock', True)
    k, b = bounds(demands, parent_width)
    y = [solver.IntVar(0, 1, f'y_{i}') for i in range(k[1])]
    x = [[solver.IntVar(0, b[i], f'x_{i}_{j}') for j in range(k[1])] \
         for i in range(num_orders)]
    unused_widths = [solver.NumVar(0, parent_width, f'w_{j}') \
                     for j in range(k[1])]
    nb = solver.IntVar(k[0], k[1], 'nb')
    for i in range(num_orders):
        if cutStyle == 'minWaste':
            solver.Add(sum(x[i][j] for j in range(k[1])) >= demands[i][0])
        else:
            solver.Add(sum(x[i][j] for j in range(k[1])) == demands[i][0])
    for j in range(k[1]):
        solver.Add(sum(demands[i][1] * x[i][j] for i in range(num_orders)) <= parent_width * y[j])
        solver.Add(parent_width * y[j] - sum(demands[i][1] * x[i][j] for i in range(num_orders)) == unused_widths[j])
        if j < k[1] - 1:
            solver.Add(sum(x[i][j] for i in range(num_orders)) >= sum(x[i][j + 1] for i in range(num_orders)))
    solver.Add(nb == solver.Sum(y[j] for j in range(k[1])))
    Cost = solver.Sum((j + 1) * y[j] for j in range(k[1]))
    solver.Minimize(Cost)
    status = solver.Solve()
    numRollsUsed = SolVal(nb)
    return status, \
        numRollsUsed, \
        rolls(numRollsUsed, SolVal(x), SolVal(unused_widths), demands), \
        SolVal(unused_widths), \
        solver.WallTime()


def bounds(demands, parent_width=100):
    num_orders = len(demands)
    b = []
    T = 0
    k = [0, 1]
    TT = 0
    for i in range(num_orders):
        quantity, width = demands[i][0], demands[i][1]
        b.append(min(quantity, int(round(parent_width / width))))
        if T + quantity * width <= parent_width:
            T, TT = T + quantity * width, TT + quantity * width
        else:
            while quantity:
                if T + width <= parent_width:
                    T, TT, quantity = T + width, TT + width, quantity - 1
                else:
                    k[1], T = k[1] + 1, 0  # use next roll (k[1] += 1)
    k[0] = int(round(TT / parent_width + 0.5))
    return k, b


def rolls(nb, x, w, demands):
    consumed_big_rolls = []
    num_orders = len(x)
    for j in range(len(x[0])):
        RR = [abs(w[j])] + [int(x[i][j]) * [demands[i][1]] for i in range(num_orders) if x[i][j] > 0]
        consumed_big_rolls.append(RR)

    return consumed_big_rolls


def solve_large_model(demands, parent_width=100, cutStyle='minWaste'):
    num_orders = len(demands)
    iter = 0
    patterns = initial_patterns(demands)
    quantities = [demands[i][0] for i in range(num_orders)]
    while iter < 20:
        status, y, l = solve_master(patterns, quantities, parent_width=parent_width, cut_style=cutStyle)
        iter += 1
        widths = [demands[i][1] for i in range(num_orders)]
        new_pattern, objectiveValue = get_new_pattern(l, widths, parent_width=parent_width)
        for i in range(num_orders):
            patterns[i].append(new_pattern[i])
    status, y, l = solve_master(patterns, quantities, parent_width=parent_width, integer=True, cut_style=cutStyle)
    return status, \
        patterns, \
        y, \
        make_rolls_patterns(patterns, y, demands, parent_width=parent_width)


def solve_master(patterns, quantities, parent_width=100, integer=False, cut_style='minWaste'):
    title = 'Cutting stock master problem'
    num_patterns = len(patterns)
    n = len(patterns[0])
    constraints = []
    solver = newSolver(title, integer)
    y = [solver.IntVar(0, 1000, '') for j in range(n)]  # right bound?
    Cost = sum(y[j] for j in range(n))
    solver.Minimize(Cost)
    for i in range(num_patterns):
        if cut_style == 'minWaste':
            constraints.append(solver.Add(sum(patterns[i][j] * y[j] for j in range(n)) >= quantities[i]))
        else:
            constraints.append(solver.Add(sum(patterns[i][j] * y[j] for j in range(n)) == quantities[i]))
    status = solver.Solve()
    y = [int(ceil(e.SolutionValue())) for e in y]
    l = [0 if integer else constraints[i].DualValue() for i in range(num_patterns)]
    toreturn = status, y, l
    return toreturn


def get_new_pattern(l, w, parent_width=100):
    solver = newSolver('Cutting stock sub-problem', True)
    n = len(l)
    new_pattern = [solver.IntVar(0, parent_width, '') for i in range(n)]
    Cost = sum(l[i] * new_pattern[i] for i in range(n))
    solver.Maximize(Cost)
    solver.Add(sum(w[i] * new_pattern[i] for i in range(n)) <= parent_width)
    status = solver.Solve()
    return SolVal(new_pattern), ObjVal(solver)


def initial_patterns(demands):
    num_orders = len(demands)
    return [[0 if j != i else 1 for j in range(num_orders)] \
            for i in range(num_orders)]


def make_rolls_patterns(patterns, y, demands, parent_width=100):
    R, m, n = [], len(patterns), len(y)
    for j in range(n):
        for _ in range(y[j]):
            RR = []
            for i in range(m):
                if patterns[i][j] > 0:
                    RR.extend([demands[i][1]] * int(patterns[i][j]))
            used_width = sum(RR)
            R.append([parent_width - used_width, RR])

    return R


def check_widths(demands, parent_width):
    for quantity, width in demands:
        if width > parent_width:
            return False
    return True


def stock_cutting(child_rolls, parent_rolls, output_json=True, large_model=True, cut_style='minWaste'):
    parent_width = parent_rolls[0][1]
    if not check_widths(demands=child_rolls, parent_width=parent_width):
        return []
    print('Список предметов (список заказов): ', child_rolls)
    print('Количество полотен шириной 1 и длиной {0}: {1}'.format(parent_rolls[0][1], parent_rolls[0][0]))
    if not large_model:
        status, numRollsUsed, consumed_big_rolls, unused_roll_widths, wall_time = \
            solve_model(demands=child_rolls, parent_width=parent_width, cutStyle=cut_style)
        new_consumed_big_rolls = []
        for big_roll in consumed_big_rolls:
            if len(big_roll) < 2:
                consumed_big_rolls.remove(big_roll)
                continue
            unused_width = big_roll[0]
            subrolls = []
            for subitem in big_roll[1:]:
                if isinstance(subitem, list):
                    subrolls = subrolls + subitem
                else:
                    subrolls.append(subitem)
            new_consumed_big_rolls.append([unused_width, subrolls])
        consumed_big_rolls = new_consumed_big_rolls
    else:
        status, A, y, consumed_big_rolls = solve_large_model(demands=child_rolls, parent_width=parent_width,
                                                             cutStyle=cut_style)
    num_rolls_used = len(consumed_big_rolls)
    STATUS_NAME = ['OPTIMAL',
                   'FEASIBLE',
                   'INFEASIBLE',
                   'UNBOUNDED',
                   'ABNORMAL',
                   'NOT_SOLVED'
                   ]
    output = {
        "statusName": STATUS_NAME[status],
        "numSolutions": '1',
        "numUniqueSolutions": '1',
        "numRollsUsed": num_rolls_used,
        "solutions": consumed_big_rolls  # unique solutions
    }
    print('Количество использованных рулонов', num_rolls_used)
    if output_json:
        return json.dumps(output)
    else:
        return consumed_big_rolls


if __name__ == '__main__':
    # child_rolls = [
    #     # [quantity, width],
    #     [269, 90],
    #     [274, 180],
    #     [277, 270],
    #     [286, 360],
    #     [298, 540],
    # ]
    # child_rolls = [random.randrange(3, 4) for i in range(2000)]
    child_rolls = gen_data(2000)
    # parent_rolls = [[10, 120]]
    # parent_rolls = [[10, 8]]
    # zakazov = 630
    # w = 300
    # child_rolls = [[zakazov, w]]
    parent_rolls = [[80, 4300]]
    start_time = time.time()
    consumed_big_rolls = stock_cutting(child_rolls, parent_rolls, output_json=False, large_model=False)
    end_time = time.time()
    # print(consumed_big_rolls)
    len_result = len(consumed_big_rolls)
    ost = 0
    n = 4300
    for idx, roll in enumerate(consumed_big_rolls):
        print(f'Раскрой #{idx+1}:', roll)
        sum_object = sum(roll[1])
        print(sum_object)
        ost+=roll[0]
    print("Суммарный остаток после раскроя (отходы): {0}".format(ost))
    print("Процент отходов от использования полотен после раскроя: {0}".format(100 * ost / (n * len_result)))
    print("Время выполнения алгоритма: {0} секунд".format(end_time-start_time))
