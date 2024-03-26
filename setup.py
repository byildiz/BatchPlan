import inspect
import sys
from pathlib import Path

import cmake_build_extension
import setuptools

init_py = inspect.cleandoc(
    """
    import cmake_build_extension

    with cmake_build_extension.build_extension_env():
        from . import bindings
    """
)

setuptools.setup(
    cmdclass=dict(build_ext=cmake_build_extension.BuildExtension),
    ext_modules=[
        cmake_build_extension.CMakeExtension(
            name="swig",
            install_prefix="batchplan",
            # write_top_level_init=init_py,
            source_dir=str(Path(__file__).parent.absolute()),
            cmake_configure_options=[
                # "--debug-find",
                f"-DPython3_ROOT_DIR={Path(sys.prefix)}",
                "-DCALL_FROM_SETUP_PY:BOOL=ON",
                "-DBUILD_SHARED_LIBS:BOOL=OFF",
                "-DCMAKE_PREFIX_PATH=/opt/build/occt772",
            ],
        ),
    ],
)
