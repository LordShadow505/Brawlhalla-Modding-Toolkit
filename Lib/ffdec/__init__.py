import os
import sys
import struct
import shutil
import subprocess
import jpype

try:
    import _jpype
except ImportError:
    _jpype = None

__all__ = []

def get_resource_path(filename):
    try:
        p = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
        if os.path.exists(p):
            return p
    except Exception:
        pass

    bases = [
        getattr(sys, '_MEIPASS', None),
        os.path.dirname(sys.executable),
        os.path.abspath("."),
    ]
    for base in bases:
        if base:
            for sub in ["", "Lib/ffdec", "Lib\\ffdec", "resources/tools/ffdec", "resources\\tools\\ffdec", "ffdec", "core/ffdec", "core\\ffdec", "core", "assets"]:
                p = os.path.abspath(os.path.join(base, sub, filename))
                if os.path.exists(p):
                    return p
    return os.path.abspath(os.path.join(os.path.dirname(__file__), filename))

PLAYERGLOBAL = get_resource_path("playerglobal32_0.swc")
FFDEC_LIB = get_resource_path("ffdec_lib.jar")
CMYKJPEG_LIB = get_resource_path("cmykjpeg.jar")
JL_LIB = get_resource_path("jl1.0.1.jar")

assert os.path.exists(FFDEC_LIB), f"ffdec_lib.jar doesn't exist at {FFDEC_LIB}"
assert os.path.exists(CMYKJPEG_LIB), f"cmykjpeg.jar doesn't exist at {CMYKJPEG_LIB}"
assert os.path.exists(JL_LIB), f"jl1.0.1.jar doesn't exist at {JL_LIB}"

jvmpath = None

if sys.platform.startswith("win"):
    def is_valid_jvm_arch(jvm_path):
        if not jvm_path or not os.path.isfile(jvm_path):
            return False
        try:
            with open(jvm_path, "rb") as f:
                b = f.read(1024)
                if len(b) < 64:
                    return True
                pe_offset = struct.unpack_from("<I", b, 0x3c)[0]
                if len(b) < pe_offset + 6:
                    return True
                machine = struct.unpack_from("<H", b, pe_offset + 4)[0]
                is_64bit_dll = (machine == 0x8664)  # IMAGE_FILE_MACHINE_AMD64
                is_64bit_python = sys.maxsize > 2**31
                return is_64bit_dll == is_64bit_python
        except Exception:
            return True

    def find_jvm_dll():
        print("[JVM Search] Starting Java Virtual Machine (JVM) search...")

        # 0. Try obtaining Java home from 'java' command in PATH
        print("[JVM Search] Strategy 0: Running command 'java -XshowSettings:properties -version'...")
        try:
            cmd_out = subprocess.check_output(
                ["java", "-XshowSettings:properties", "-version"],
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5
            )
            for line in cmd_out.splitlines():
                if "java.home" in line:
                    home = line.split("=")[-1].strip()
                    print(f"[JVM Search] Strategy 0: Found java.home='{home}' via CLI command")
                    if os.path.isdir(home):
                        for sub in [
                            os.path.join("bin", "server", "jvm.dll"),
                            os.path.join("jre", "bin", "server", "jvm.dll"),
                            os.path.join("lib", "server", "jvm.dll"),
                            os.path.join("bin", "client", "jvm.dll"),
                        ]:
                            p = os.path.join(home, sub)
                            if os.path.exists(p) and is_valid_jvm_arch(p):
                                print(f"[JVM Search] [SUCCESS] Strategy 0 located valid JVM: {p}")
                                return p
        except Exception as e:
            print(f"[JVM Search] Strategy 0: CLI command skipped/failed ({e})")

        # 1. Check environment variables
        print("[JVM Search] Strategy 1: Checking environment variables...")
        for env in ["JAVA_HOME", "JDK_HOME", "JRE_HOME", "BMT_JAVA_HOME"]:
            val = os.getenv(env)
            if val and os.path.isdir(val):
                for sub in [
                    os.path.join("bin", "server", "jvm.dll"),
                    os.path.join("bin", "client", "jvm.dll"),
                    os.path.join("jre", "bin", "server", "jvm.dll"),
                    os.path.join("bin", "default", "jvm.dll"),
                    os.path.join("lib", "server", "jvm.dll"),
                ]:
                    p = os.path.join(val, sub)
                    if os.path.exists(p) and is_valid_jvm_arch(p):
                        print(f"[JVM Search] [SUCCESS] Strategy 1 located valid JVM via {env}: {p}")
                        return p

        # 2. Try jpype's default JVM path finder
        print("[JVM Search] Strategy 2: Checking JPype default JVM path...")
        try:
            default_path = jpype._jvmfinder.getDefaultJVMPath()
            if default_path and os.path.exists(default_path) and is_valid_jvm_arch(default_path):
                print(f"[JVM Search] [SUCCESS] Strategy 2 located valid JVM: {default_path}")
                return default_path
        except Exception:
            pass

        # 3. Check Windows Registry
        print("[JVM Search] Strategy 3: Checking Windows Registry...")
        try:
            import winreg
            for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                for reg_path in [
                    r"SOFTWARE\JavaSoft\Java Runtime Environment",
                    r"SOFTWARE\JavaSoft\JRE",
                    r"SOFTWARE\JavaSoft\Java Development Kit",
                    r"SOFTWARE\JavaSoft\JDK",
                ]:
                    try:
                        with winreg.OpenKey(root_key, reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
                            cur_ver, _ = winreg.QueryValueEx(k, "CurrentVersion")
                            with winreg.OpenKey(k, cur_ver) as vk:
                                reg_java_home, _ = winreg.QueryValueEx(vk, "JavaHome")
                                if reg_java_home and os.path.exists(reg_java_home):
                                    for sub in [
                                        os.path.join("bin", "server", "jvm.dll"),
                                        os.path.join("bin", "client", "jvm.dll"),
                                        os.path.join("jre", "bin", "server", "jvm.dll"),
                                        os.path.join("bin", "default", "jvm.dll"),
                                    ]:
                                        p = os.path.join(reg_java_home, sub)
                                        if os.path.exists(p) and is_valid_jvm_arch(p):
                                            print(f"[JVM Search] [SUCCESS] Strategy 3 located valid JVM: {p}")
                                            return p
                    except Exception:
                        pass
        except Exception:
            pass

        # 4. Search common installation directories
        print("[JVM Search] Strategy 4: Scanning common directories...")
        candidates = []
        pf = os.getenv("ProgramFiles", "C:\\Program Files")
        java_dir = os.path.join(pf, "Java")
        if os.path.exists(java_dir):
            for entry in os.listdir(java_dir):
                candidates.append(os.path.join(java_dir, entry))

        for vendor in ["Eclipse Adoptium", "BellSoft", "Amazon Corretto", "Zulu", "Semeru"]:
            v_dir = os.path.join(pf, vendor)
            if os.path.exists(v_dir):
                for entry in os.listdir(v_dir):
                    candidates.append(os.path.join(v_dir, entry))

        for drive in ["C:", "D:", "E:", "F:", "X:"]:
            for folder in ["JavaJDK", "Java", "JDK", "JRE"]:
                p = os.path.join(drive + "\\", folder)
                if os.path.isdir(p):
                    candidates.append(p)

        for base in candidates:
            for sub in [
                os.path.join("bin", "server", "jvm.dll"),
                os.path.join("bin", "client", "jvm.dll"),
                os.path.join("jre", "bin", "server", "jvm.dll"),
                os.path.join("bin", "default", "jvm.dll"),
                os.path.join("lib", "server", "jvm.dll"),
            ]:
                p = os.path.join(base, sub)
                if os.path.exists(p) and is_valid_jvm_arch(p):
                    print(f"[JVM Search] [SUCCESS] Strategy 4 located valid JVM: {p}")
                    return p
        return None

    jvmpath = find_jvm_dll()

    if jvmpath:
        jvm_dir = os.path.dirname(jvmpath)
        java_bin = os.path.dirname(jvm_dir)
        java_root = os.path.dirname(java_bin)

        if not os.getenv("JAVA_HOME"):
            os.environ["JAVA_HOME"] = java_root

        for pe in [java_bin, jvm_dir]:
            if os.path.exists(pe) and pe not in os.environ.get("PATH", ""):
                os.environ["PATH"] = pe + os.path.pathsep + os.environ.get("PATH", "")

        if hasattr(os, "add_dll_directory"):
            for pe in [java_bin, jvm_dir]:
                if os.path.exists(pe):
                    try:
                        os.add_dll_directory(pe)
                    except Exception:
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

if not jpype.isJVMStarted():
    print(f"[JVM] Starting JVM with path: '{jvmpath}'")
    jpype.startJVM(jvmpath, "-Xmx2048m", "-Xms32m", "-XX:+UseSerialGC", classpath=[FFDEC_LIB, CMYKJPEG_LIB, JL_LIB])
    print("[JVM] [SUCCESS] Java Virtual Machine started successfully!")

from .classes import *
