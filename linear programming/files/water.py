import argparse
import os
import json
import pulp
from pulp import LpVariable as Var
from pulp import const


def water_network(nodes, edges, p_lb, p_ub, s_lb, s_ub):
    # UNIMPLEMENTED
    m = pulp.LpProblem()

    # if maximize, the comment above and uncomment below
    #m = pulp.LpProblem(sense=const.LpMaximize)

    """
        Init the variables
    """
    # init the supply variables, the supply node has a s_ub > 0
    s = {i:Var('s_{}'.format(i), lowBound=s_lb[i], upBound=s_ub[i]) for i in range(len(nodes)) if s_ub[i] > 0}

    # init the pressures variables
    p = {i:Var('p_{}'.format(i), lowBound=p_lb, upBound=p_ub) for i in range(len(nodes))}

    # init the flow variables
    # key is a string, different from the above
    f = {"{}_{}".format(edge["fr"], edge["to"]): Var("f_{}_{}".format(edge["fr"], edge["to"]), lowBound=-edge["f_ub"], upBound=edge["f_ub"]) for edge in edges}

    # add dicts to store the edge to/from a single node
    edge_from, edge_to = {}, {}
    for edge in edges:
        fr, to = edge["fr"], edge["to"]
        if fr not in edge_from:
            edge_from[fr] = [edge]
        else:
            edge_from[fr].append(edge)

        if to not in edge_to:
            edge_to[to] = [edge]
        else:
            edge_to[to].append(edge)

    """
        Add the constraints
    """
    for i in range(len(nodes)):
        # the sr variable and demand for a single node
        sr = 0 if i not in s else s[i]
        d = nodes[i]["d"]

        # get the flow in and out of this node
        flow_in = 0
        if i in edge_to:
            for edge in edge_to[i]:
                flow_in += f["{}_{}".format(edge["fr"], i)]

        flow_out = 0
        if i in edge_from:
            for edge in edge_from[i]:
                flow_out += f["{}_{}".format(i, edge["to"])]

        # 1. add the conservation of flow constraint
        m += sr + flow_in - d - flow_out == 0

    for edge in edges:
        fr, to = edge["fr"], edge["to"]

        # 2. add the pressure constraint
        m += p[fr] - p[to] == edge["r"] * f["{}_{}".format(fr, to)]


    """
    Q1.2.1
    """
    w = {i:Var("w_{}".format(i), lowBound=0) for i in range(len(nodes)) if s_ub[i] > 0}

    # # use the simple bounds, so that the lowBound for supply is 0
    # # for equation [3], it should be w[i] - p_lb * s[i] >= 0
    # for i in w:
    #     m += w[i] - p_lb * s[i] >= 0 #[3]
    #     m += w[i] - p_ub * s[i] - p[i] * s_ub[i] + p_ub * s_ub[i] >= 0 #[4]
    #
    # objective = sum(w.values())
    #
    # # add the objective
    # m += objective



    """
        Q1.2.2
        In order to get a tighter bounds for s
        remove the objective relating to the w and constraints [3] and [4]
        then set variable s as the objective to find the feasible min and max values
    """
    #0 ，7 ，9， 10， 18 are the indexes of the supplies
    keys = [0, 7, 9, 10, 18]
    low = [3.5210716, 9.3862895, 8.167482, 8.1455599, 3.5499084]
    up = [9.0, 11.0, 15.945724, 10.0, 6.9791667]
    new_s_lb = {keys[i]: low[i] for i in range(5)}
    new_s_ub = {keys[i]: up[i] for i in range(5)}

    for i in w:
        m += w[i] >= p_lb * s[i] + p[i] * new_s_lb[i] - p_lb * new_s_lb[i]  #[3]
        m += w[i] >= p_ub * s[i] + p[i] * new_s_ub[i] - p_ub * new_s_ub[i]  #[4]
    objective = sum(w.values())
    m += objective


    m.solve()


    """
        Get the answers
        for Q1.1 feasibility
            Total demand is: 44
            Total supply is: 44.0
            Total pumping power is: 3484.9075701436304
    """
    pressures = [p[v].value() for v in range(len(nodes))]
    suppplies = []
    for i in range(len(nodes)):
        if i in s:
            suppplies.append(s[i].value())
        else:
            suppplies.append(0)

    flows = [f["{}_{}".format(edge["fr"], edge["to"])].value() for edge in edges]


    total_demands = sum([node["d"] for node in nodes])
    total_supplies = sum(suppplies)
    pump_powers = cal_pump_power(pressures, suppplies)

    print("Total demand is: {}".format(total_demands), "  Total supply is: {}".format(total_supplies))
    print("Total pumping power is: {}".format(sum(pump_powers)))

    status = m.status

    # set it to None if no objective
    objective_value = m.objective.value()



    # Substitute below the values from your solution
    # Only return values from function (no pulp objects)
    return {"status": status,
            "objective": objective_value,
            "p": pressures,
            "s": suppplies,
            "w": pump_powers,
            "f": flows,
            }



def cal_pump_power(pressures, supplies):
    return [pressures[i] * supplies[i] for i in range(len(pressures))]

if __name__ == "__main__":
    par = argparse.ArgumentParser("Water Network Optimiser")
    par.add_argument("file", help="json instance file")

    args = par.parse_args()

    inst = json.load(open(args.file))
    # Change the supply bounds here as indicated in the assignment.
    s_lb = [0 for n in inst["nodes"]]
    s_ub = [n["s_ub"] for n in inst["nodes"]]
    print(s_lb)
    print(s_ub)
    res = water_network(
        nodes=inst["nodes"],
        edges=inst["edges"],
        p_lb=inst["p_lb"],
        p_ub=inst["p_ub"],
        s_lb=s_lb,
        s_ub=s_ub,
        )

    json.dump(res,
              open(os.path.splitext(args.file)[0] + "-sol.json", "w"),
              indent=2)

    print(f"Status {res['status']}")
    print(f"Relaxation Objective {res['objective']}")
    print(f"Exact Objective {sum(res['w'])}")
    print(f"Pressures {res['p']}")
    print(f"Sources {res['s']}")
    print(f"Flows {res['f']}")
