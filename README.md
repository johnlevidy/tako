## Example build

To build Bakery:

```
cd python;
nix-shell;
python -m tako.main generate bakery_test/ test_types.bakery.Bakery cpp
```
To build milestone1

cd build
cmake --build .

Purely as a point of interest, it seems that PrimitiveView::parse is only used when it's necessary as the slave key of some bigger type ( struct, etc. ) otherwise it always just renders. 

The parse function on some bigger type doesn't check primitive fields parse, just the complex ones. Although maybe these are functionally equivalent as long as the total size is there

rendering still tries to parse those, but it just calls .value()
