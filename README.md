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

## Basic Flow ( could be issues, this is an evolving code archaeology )
| Step | Description | Key Files|
|----------|----------|----------|
| Main | Primary entrypoint via main. Very little code is run before dispatching to compiler. | main.py |
| Ingest / Parsing | Code related to sanity and type checking, making sure root types are respected. The compile_proto function walks through the process of steadily lowering IRs down to the final SIR ( which is just a structification of the LIR ). It does this independently for types, constants, and conversions. In below cells we'll only discuss types, as that's the most complex case, but others follow a similar pattern. | ```compiler/__init__.py::compile_proto``` in compile.py and subsequently ```ingest.py::run``` |
| MIR Construction from Ingest | Take the inputs which are still in a fairly raw format and lower them to MIR through lower.py. |  ```types/__init__.py::compile``` ```lower.py``` |
| LIR Construction from MIR | Series of expansions happen, for example, variants are turned into a determinant tag and a payload. This is all proeparatory work for fuse.py, which ultimately lowers us down to lir properly. Fuse is doing a lot of data enriching to get us ready to generate code, annotating with notions of triviality, digests, and more. | ```fuse.py``` ```lir.py``` |
| Construct SIR from LIR | Back up in ```compiler/__init__.py``` this is a trivial step to hold everything in a single struct, afaict. | ```sir.py``` ```compiler/__init__.py``` |
| Generate target language | Operate on the SIR to do code generation. | ```cpp.py::generate_into``` |


