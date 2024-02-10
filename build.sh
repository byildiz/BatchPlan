mkdir -p build
cmake -GNinja -S. -Bbuild
cmake --build build
cp build/{fixes.py,_Fixes.so} batchplan
