from tako.core.types import *

class Milestone1(Protocol):
    IntegerType = Struct(contained=i8)
    BigIntegerType = Struct(contained=li32)
   
    # For milestone 1, we want to get to a point where I can get all three, but the second
    # and third will return nullopt if the variant received is of unknown type
    Two = Variant[i8]({IntegerType: 0, BigIntegerType: 1})
    Packet= Struct(one=li32, two=Two, three=lu32)
