import minizinc
from parse_excel import minizinc_data

# Load model
model = minizinc.Model("model.mzn")

'''
data = {
    "strong_collision": strong_collision,
    "weak_collision": weak_collision,
    "matches": matches_minizic,
    "class_index": class_index,
    "round_index": round_index
}
'''

data = minizinc_data()



# Choose solver (you can replace "gecode" with another installed solver)
gecode = minizinc.Solver.lookup("gecode")

# Create instance and give input
instance = minizinc.Instance(gecode, model)
instance["nof_matches"] = len(data["matches"])
instance["nof_classes"] = len(data["class_index"])
instance["nof_rounds"] = len(data["round_index"])
instance["nof_strong_collisions"] = len(data["strong_collision"])
instance["nof_weak_collisions"] = len(data["weak_collision"])

instance["class_index"] = data["class_index"]
instance["round_index"] = data["round_index"]

instance["timeslots"] = data["timeslots"]
instance["fields"] = data["fields"]
instance["matchslots"] = data["matchslots"]

instance["strong_collision"] = data["strong_collision"]
instance["weak_collision"] = data["weak_collision"]
instance["last_of_day1"] = data["last_of_day1"]

# Solve
result = instance.solve(statistics=True, verbose=True)
instance
# Access output
print(result)