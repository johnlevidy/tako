from tako.core.types import *

class Organism(Protocol):
    Felidae = Struct(num_lives=i8)
    Canidae = Struct(balls_caught=i8)
    Mammalia = HashVariant[li32]([Felidae, Canidae])
    Chordata = Struct(family=Mammalia, symmetry=i8)

    Phylum = HashVariant[li32]([Chordata])
    Animalia = Struct(motility_type=i8, phylum=Phylum)
    # Attempt to make a dynamic length member of a hash variant, does it embed the length somehow?
    Plantae = Struct(seed_count=li32, seeds = Seq(i8, this.seed_count))

    Kingdom = SkippableHashVariant[li32, u8]([Animalia, Plantae])
    Organism = Struct(kingdom=Kingdom)
