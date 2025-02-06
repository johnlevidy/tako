from test_types.bakery import Bakery
from test_types.bakery.v1 import V1
from test_types.bakery.v2 import V2

class BakeryActor:
    ## TODO fix field access
    ## TODO fix variant access
    ## Today
    Produces = [Bakery.Packet.payload[V2.Message]]
