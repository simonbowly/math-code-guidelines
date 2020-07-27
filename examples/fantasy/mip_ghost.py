from mip import Model, maximize
from mip import xsum as Σ
from optimal_fantasy.notation import declare_constraints, binary, continuous
from typing import List

def ghost(data):
    m = Model("Ghost")
    # Notation
    P       = data["players"]
    P_      = data["players eligible in position q"]
    Q       = data["positions"]
    Q_      = data["positions eligible to player p"]
    Q_sub   = data["substitute positions"]
    Q_score = data["scoring positions"]
    S_      = data["slots of position q"]
    R       = data["rounds"]
    C_      = data["players required in position q"]
    X_      = data["scoring positions in round r"]
    B       = data["starting budget"]
    Ψ_      = data["points scored by player p in round r"]
    v_      = data["value of player p in round r"]
    E       = data["emergencies limit"]
    Z       = {"captain", "vice"}    # Captain types
    # Variables
    m.variables = {
                    # 1 iff player p ∈ P is in position q ∈ Q_p in round r ∈ R.
        "in team": (x := {(p, q): binary(m) for p in P for q in Q_[p]}),
                    # 1 iff the points of player p ∈ P in round r ∈ R count to the score.
        "scoring": (x_bar := {(p) : binary(m) for p in P for r in R}),
                    # 1 iff player p ∈ P, is z ∈ (captain, vice)
        "captain": (c := {(z, p): binary(m) for p in P for z in Z}),
                    # 1 iff player p ∈ P is a scoring vice captain in round r ∈ R
        "vice" :   (c_vice := {(p, r): binary(m) for p in P for r in R}),
                    # remaining budget available in round r ∈ R.
        "slot":    (y := {(p,q,r,s): binary(m) for q in Q_sub for p in P_[q] for s in S_[q] for r in R}),
                    # 1 iff player p ∈ P is in slot s ∈ S_q of pos q ∈ Q_sub_p in r ∈ R
        "emergency": (e := {(p,q): binary(m) for q in Q_sub for p in P_[q]})
    }
    # Objective
    m.objective = maximize(
        # (16) Maximise the number of points scored by the team throughout the season.
        Σ(Σ(Ψ_[p, r]*(x_bar[p] + c[z, p]) for z in Z) for r in R for p in P)
        ) 
    # Constriants
    m.constraints = declare_constraints(m, {
        # The team has one captain and one vice captain.
        (17):   [Σ(c[z, p] for p in P) == 1  for z in Z],    
        # The captain must be in a scoring position
        (18):   [c[z,p] <= Σ(x[p,q] for q in Q_[p] & Q_score) for p in P for z in Z],
        # Each position must contain a exact number of players - mimics (7)
        (19):   [Σ(x[p,q] for p in P_[q]) == C_[q]       for q in Q],
        # Each player can only be in one position - mimics (8)
        (20):   [Σ(x[p,q] for q in Q_[p]) <= 1           for p in P],
        # A player can only be an emergency if they are on the bench
        (21):   [e[p,q] <= x[p,q]                        for p in P for q in Q_[p] & Q_sub],
        # The number of emergencies is restricted
        (22):   [Σ(e[p,q] for p in P for q in Q_[p] & Q_sub) <= E],
        # Each slot can have at most one player
        (23):   [Σ(y[p,q,r,s] for p in P_[q]) <= 1           for q in Q_sub for r in R for s in S_[q]],
        # A player can only be a candidate for a slot if they are an emergency.
        (24):   [Σ(y[p,q,r,s] for s in S_[q]) <= e[p,q]  for p in P for q in Q_[p] & Q_sub for r in R],
        # The number of players in a scoring position who scored a zero represent the 
        # maximum number of scoring bench slots in the corresponding substitute position g(q)
        (25):   [Σ(y[p,f"SUB {q}",r,s] for p in P_[q] for s in S_[f"SUB {q}"]) <= Σ(x[p,q] 
                        for p in P_[q] if Ψ_[p,r] == 0)  for q in Q_score for r in R],
        # The lower indexed slots are used before the higher indexed slots
        (26):   [Σ(y[p,q,r,s] - y[p,q,r,s-1] 
                                for p in P_[q]) <= 0     for q in Q_sub for s in S_[q][1:] for r in R],
        # Enforce the ordering on the emergencies in the corresponding slots
        (27):   [Σ(e[p_,q] for p_ in P_[q] if Ψ_[p_,r] < Ψ_[p,r]) + Σ((len(S_[q])-s)*y[p,q,r,s] 
                        for s in S_[q]) <= len(S_[q])    for q in Q_sub for r in R for p in P_[q]],
        # The value of the team is within the initial budget.
        (28):   [Σ(v_[p, 1]*x[p,q] for p in P for q in Q_[p]) <= B],
        # A player’s score can count if they are in a scoring position or a scoring emergency
        (29):   [x_bar[p] <= Σ(x[p,q] for q in Q_[p] & Q_score) + Σ(y[p,q,r,s] 
                    for q in Q_[p] & Q_sub for s in S_[q])    for p in P for r in R],
        # Only the scores of an appropriate number of players count towards the team score
        (30):   [Σ(x_bar[p] for p in P) <= X_[r]       for r in R],
        # a player can only be a scoring vice captain only if they are the vice captain
        (31):   [c_vice[p,r] <= c["vice", p]             for p in P for r in R],
        # The scoring vice captain is counted only if the captain scores zero.
        (32):   [Σ(c_vice[p, r] for p in P) <= Σ(c["captain", p] for p in P if Ψ_[p, r] == 0) for r in R]
        })
    return m

