## Example build

To build Bakery:

```
cd python;
nix-shell;
python -m tako.main generate bakery_test/ test_types.bakery.Bakery cpp
```
## Notes on design

The code makes a lot of references to "Root{Type, Visitor, etc.}" as compared to "{Type, Visitor, etc.}".

The difference, as far as I can tell, is that RootTypes are able to be declared in a protocol's top level.

This includes:
- Enum
- Struct
- Variant
- HashVariant
Regular Types include:
- int
- float
- seq
- detached_variant ( not totally sure why )
- virtual
