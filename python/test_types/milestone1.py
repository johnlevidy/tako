from tako.core.types import *

class Milestone1(Protocol):
    IntegerType = Struct(contained=i8)
    BigIntegerType = Struct(contained=li32)
    SmallIntegerType = Struct(contained=i8)
    MiniIntegerType = Struct(contained=li32)
    ConfusingIntegerType = Variant[i8]({MiniIntegerType: 0, SmallIntegerType: 1})
    InnerVariant = Struct(inner = ConfusingIntegerType)
   
    # For milestone 1, we want to get to a point where I can get all three, but the second
    # and third will return nullopt if the variant received is of unknown type
    Two = Variant[i8]({IntegerType: 0, BigIntegerType: 1, InnerVariant: 2})
    Packet= Struct(one=li32, two=Two, three=lu32)
