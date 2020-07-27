from mip import minimize
from mip import xsum as Σ
from optimal_fantasy.notation import binary, continuous, declare_constraints, remove_constraint_set
from optimal_fantasy.models.mip_complete import model


def budget_model(data):
    # Notation
    R  = data["rounds"]
    P  = data["players"]
    Q_ = data["positions eligible to player p"]
    Ψ_ = data["points scored by player p in round r"]
    v_ = data["value of player p in round r"]
    S_win = data["score to beat"]
    # Create Complete Model
    m = model(data)
    m.name = "Budget" 
    # Variables
    m.variables.update({
        "starting_budget": (β := continuous(m))
    })
    x     = m.variables["in team"]
    x_bar = m.variables["scoring"]
    c     = m.variables["captain"]
    b     = m.variables["budget"]
    # Objective
    m.objective = minimize(β) # (13) Minimise the starting budget
    # Remove redundant constraints
    remove_constraint_set(m, 11)
    # Add additional Constraints
    m.constraints.update(declare_constraints(m, {
        # The number of trades across the season is less than or equal T.
        (14):   [Σ(Ψ_[p, r]*(x_bar[p, r] + c[p, r]) for p in P for r in R[1:]) >= S_win + 1],
        # The starting budget constraint (11) now contains a variable
        (15):   [b[1] + Σ(v_[p,1]*x[p,q,1] for p in P for q in Q_[p]) == β]    
    }))
    return m
