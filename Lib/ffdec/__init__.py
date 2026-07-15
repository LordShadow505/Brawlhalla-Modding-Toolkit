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

JAVA_ERROR_MSG = """Java is missing or incompatible. To fix this:

1. Download and install Windows Offline (64-bit) from: http://java.com/download/manual.jsp
2. Search Windows for "Environment Variables".
3. Add a new System Variable: Name="JAVA_HOME", Value="C:\\Program Files\\Java\\jdk-xxx" (your install path).
4. Edit the System "Path" variable and add: %JAVA_HOME%\\bin
5. Restart your computer."""

import tkinter.messagebox as messagebox

if jvmpath is None:
    try:
        messagebox.showerror("Java Initialization Error", JAVA_ERROR_MSG)
    except:
        pass
    raise ImportError(JAVA_ERROR_MSG)

if not jpype.isJVMStarted():
    try:
        jpype.startJVM(jvmpath, "-Xmx2048m", "-Xms128m", classpath=[FFDEC_LIB, CMYKJPEG_LIB, JL_LIB])
    except Exception as e:
        err_msg = f"Failed to start Java JVM.\n\n{JAVA_ERROR_MSG}\n\nTechnical details:\n{str(e)}"
        try:
            messagebox.showerror("Java Initialization Error", err_msg)
        except:
            pass
        raise ImportError(err_msg)



from .classes import *
