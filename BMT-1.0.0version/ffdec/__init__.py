import os
import sys
import jpype

__all__ = []

PLAYERGLOBAL = os.path.abspath(os.path.join(os.path.dirname(__file__), "playerglobal32_0.swc"))
FFDEC_LIB = os.path.abspath(os.path.join(os.path.dirname(__file__), "ffdec_lib.jar"))
CMYKJPEG_LIB = os.path.abspath(os.path.join(os.path.dirname(__file__), "cmykjpeg.jar"))
JL_LIB = os.path.abspath(os.path.join(os.path.dirname(__file__), "jl1.0.1.jar"))

assert os.path.exists(FFDEC_LIB), "ffdec_lib.jar doesn't exist"
assert os.path.exists(CMYKJPEG_LIB), "cmykjpeg.jar doesn't exist"
assert os.path.exists(JL_LIB), "jl1.0.1.jar doesn't exist"

jvmpath = None

if sys.platform.startswith("win"):
    try:
        jvmpath = jpype._jvmfinder.getDefaultJVMPath()
    except jpype._jvmfinder.JVMNotFoundException:
        pass

    flashlibFolder = os.path.join(os.getenv("APPDATA"), "JPEXS", "FFDec", "flashlib")
    flashlibFile = os.path.join(flashlibFolder, "playerglobal32_0.swc")

    if not os.path.exists(flashlibFile):
        if not os.path.exists(flashlibFolder):
            os.makedirs(flashlibFolder, exist_ok=True)

        with open(PLAYERGLOBAL, "rb") as orig:
            with open(flashlibFile, "wb") as new:
                new.write(orig.read())

elif sys.platform == "darwin":
    jvmpath = "/Library/Internet Plug-Ins/JavaAppletPlugin.plugin/Contents/Home/lib/jli/libjli.dylib"

else:
    pass

if jvmpath is None:
    raise ImportError("Java not found!")

jpype.startJVM(jvmpath, "-Xmx512m", "-Xms32m", classpath=[FFDEC_LIB, CMYKJPEG_LIB, JL_LIB])



from .classes import *
