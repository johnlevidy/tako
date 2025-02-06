import importlib
from test_types.actor import BakeryActor

module = "test_types.actor"

live_module = importlib.import_module(module)

a = BakeryActor.Produces[0]

def print_keys(a):
    [print(k) for k, v in a.__dict__.items()]
print("*******************************************************************")
print("*******************************************************************")
print("*******************************************************************")
print("*******************************************************************")
print("*******************************************************************")
print("Produces")
print(a)
## This synatx has to be better
print("Version1")
print_keys(BakeryActor.Produces[0].fields['payload'])
print("Version2")
print(BakeryActor.Produces[0].payload)
# b = BakeryActor.Consumes[0]
# 
# print("Consumes")
# print(b)


