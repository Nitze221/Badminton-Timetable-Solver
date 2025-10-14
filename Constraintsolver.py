import minizinc

# Load model
model = minizinc.Model("model.mzn")

# Choose solver (you can replace "gecode" with another installed solver)
gecode = minizinc.Solver.lookup("gecode")

# Create instance and give input
instance = minizinc.Instance(gecode, model)
instance["n"] = 5
instance["values"] = [1, 2, 3, 4, 5]

# Solve
result = instance.solve()

# Access output
text = str(result)
print(text)  # "Total = 15"
total = int(text.split("=")[1])
print(total)