from tako.core.types import *

class Organism(Protocol):
    Felidae = Struct(num_lives=i8)
    Canidae = Struct(balls_caught=i8)
    Mammalia = HashVariant[li32]([Felidae, Canidae])
    Chordata = Struct(family=Mammalia, symmetry=i8)

    Phylum = HashVariant[li32]([Chordata])
    Animalia = Struct(motility_type=i8, phylum=Phylum)
    Plantae = Struct(seed_count=li32)

    Kingdom = HashVariant[li32]([Animalia, Plantae])
    Organism = Struct(kingdom=Kingdom)
