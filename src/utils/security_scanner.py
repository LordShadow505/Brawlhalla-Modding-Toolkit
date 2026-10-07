"""
BMT Security Scanner & Cryptographic Certifier Module
Provides:
1. Static analysis of UI_MainMenu.swf (and scripts) for dangerous Adobe AIR / AS3 operations:
   - Native process execution (NativeProcess, cmd.exe, powershell, .exe, .bat, etc.)
   - Web / Socket / Remote connections (URLRequest, URLLoader, navigateToURL, Socket, XMLSocket)
   - Dangerous file system writes / reflection
2. BMT Cryptographic Certification (HMAC-SHA256) for official Toolkit mods (ColorModTool & HandModTool).
"""

import os
import re
import json
import zlib
import lzma
import hashlib
import hmac
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Internal HMAC secret salt for BMT certification
_BMT_SIGNING_SALT = b"BMT_TOOLKIT_OFFICIAL_SIGNATURE_KEY_v1.0"

# Dangerous patterns to detect exclusively in UI_MainMenu
DANGEROUS_PATTERNS = [
    # 1. Native process execution & external shells
    (r'flash\.desktop\.NativeProcess', 'NativeProcess execution (Launches external executables)'),
    (r'NativeProcessStartupInfo', 'NativeProcess execution info'),
    (r'process\.start\b', 'External process start call'),
    (r'cmd(?:\.exe)?\s+/[ck]', 'Windows Command Prompt invocation'),
    (r'powershell(?:\.exe)?', 'PowerShell script execution'),
    (r'wscript(?:\.exe)?', 'Windows Script Host invocation'),
    (r'cscript(?:\.exe)?', 'Console Script Host invocation'),
    (r'mshta(?:\.exe)?', 'MSHTA HTML Application execution'),
    (r'fscommand\s*\(\s*["\']exec["\']', 'Flash FSCommand EXEC execution'),
    (r'["\'][\w\-./\\]+\.(?:exe|bat|cmd|vbs|ps1|scr|pif)["\']', 'Direct executable file reference'),

    # 2. Remote network communication, exfiltration & sockets
    (r'flash\.net\.Socket\b', 'Raw TCP Socket connection'),
    (r'flash\.net\.XMLSocket\b', 'XMLSocket remote connection'),
    (r'flash\.net\.DatagramSocket\b', 'UDP Datagram socket'),
    (r'flash\.net\.URLLoader\b', 'Remote URL data loader'),
    (r'flash\.net\.URLRequest\b', 'Remote URL request'),
    (r'navigateToURL\s*\(', 'Browser / Remote URL navigation'),
    (r'sendToURL\s*\(', 'Remote URL data transmission'),
    (r'https?://[a-zA-Z0-9.\-_]+', 'Hardcoded HTTP/HTTPS URL reference'),
    (r'wss?://[a-zA-Z0-9.\-_]+', 'Hardcoded WebSocket URL reference'),
]


def decode_swf_bytes(raw: bytes) -> bytes:
    """Safely decompresses FWS, CWS (Zlib), or ZWS (LZMA) SWF binaries."""
    if len(raw) < 8:
        return raw
    sig = raw[:3]
    if sig == b"FWS":
        return raw[8:]
    if sig == b"CWS":
        try:
            return zlib.decompress(raw[8:])
        except Exception:
            return raw[8:]
    if sig == b"ZWS":
        try:
            if len(raw) < 17:
                return raw[8:]
            props = raw[12:17]
            prop0 = props[0]
            lc = prop0 % 9
            rest = prop0 // 9
            lp = rest % 5
            pb = rest // 5
            dict_size = int.from_bytes(props[1:5], "little") or (1 << 23)
            filters = [{"id": lzma.FILTER_LZMA1, "dict_size": dict_size, "lc": lc, "lp": lp, "pb": pb}]
            expected = max(0, int.from_bytes(raw[4:8], "little") - 8)
            dec = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=filters)
            return dec.decompress(raw[17:], max_length=expected or -1)
        except Exception:
            return raw[8:]
    return raw


def _safe_extract_swf_strings(data: bytes) -> str:
    """Extracts strings from binary data for scanning."""
    try:
        decompressed = decode_swf_bytes(data)
        return decompressed.decode("utf-8", errors="ignore")
    except:
        return str(data)


IGNORED_CERT_FILES = {".bmt_cert.json", "_cache.json", "thumbs.db", ".ds_store"}


def calculate_dir_hashes(dir_path: Path) -> Dict[str, str]:
    """Calculates SHA256 hashes of UI_MainMenu files in a directory relative to root."""
    result = {}
    if not dir_path.exists():
        return result
    for root, _, files in os.walk(dir_path):
        if "_previews" in root.lower():
            continue
        for f in sorted(files):
            if f.lower() in IGNORED_CERT_FILES:
                continue
            p = Path(root) / f
            # Only hash UI_MainMenu related source files
            if "ui_mainmenu" in str(p).lower():
                try:
                    rel = p.relative_to(dir_path).as_posix()
                    h = hashlib.sha256(p.read_bytes()).hexdigest()
                    result[rel] = h
                except Exception:
                    pass
    return result


def generate_bmt_certificate(tool_name: str, mod_name: str, target_dir_or_swf: Path) -> Dict[str, Any]:
    """
    Generates a cryptographically signed BMT certificate for a generated UI_MainMenu mod source or SWF.
    """
    import time
    if target_dir_or_swf.is_dir():
        file_hashes = calculate_dir_hashes(target_dir_or_swf)
        main_swf_hash = file_hashes.get("UI_MainMenu.swf", "")
    else:
        file_hashes = {target_dir_or_swf.name: hashlib.sha256(target_dir_or_swf.read_bytes()).hexdigest()}
        main_swf_hash = file_hashes.get(target_dir_or_swf.name, "")

    payload = {
        "bmt_certified": True,
        "tool": tool_name, # "ColorModTool" or "HandModTool"
        "mod_name": mod_name,
        "timestamp": int(time.time()),
        "target_file": "UI_MainMenu.swf",
        "main_hash": main_swf_hash,
        "file_hashes": file_hashes
    }

    # Generate HMAC-SHA256 signature
    canonical_data = json.dumps(payload, sort_keys=True).encode("utf-8")
    sig = hmac.new(_BMT_SIGNING_SALT, canonical_data, hashlib.sha256).hexdigest()
    payload["signature"] = sig
    return payload


def verify_bmt_certificate(cert_data: Any, target_dir_or_swf: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Verifies that a BMT certificate is genuine, untampered, and matches UI_MainMenu files on disk.
    Extra non-UI files (skins, weapons, languages) in the folder are safely ignored.
    """
    if not isinstance(cert_data, dict):
        return False, "Missing or invalid certificate payload"

    if not cert_data.get("bmt_certified"):
        return False, "Not marked as BMT certified"

    sig = cert_data.get("signature")
    if not sig:
        return False, "Certificate has no digital signature"

    # Verify cryptographic signature
    check_payload = dict(cert_data)
    del check_payload["signature"]
    canonical_data = json.dumps(check_payload, sort_keys=True).encode("utf-8")
    expected_sig = hmac.new(_BMT_SIGNING_SALT, canonical_data, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(sig, expected_sig):
        return False, "Invalid signature: Certificate has been forged or modified"

    # Verify physical file hashes if target path is provided
    if target_dir_or_swf and target_dir_or_swf.exists():
        expected_hashes = cert_data.get("file_hashes", {})
        if target_dir_or_swf.is_dir():
            actual_hashes = calculate_dir_hashes(target_dir_or_swf)
            for f_rel, exp_h in expected_hashes.items():
                if f_rel.lower() in IGNORED_CERT_FILES or "_previews" in f_rel.lower():
                    continue
                # Only check files that belong to UI_MainMenu
                if "ui_mainmenu" not in f_rel.lower():
                    continue
                if f_rel not in actual_hashes:
                    return False, f"File missing from UI_MainMenu mod source: {f_rel}"
                if actual_hashes[f_rel] != exp_h:
                    return False, f"File integrity mismatch for: {f_rel}"
        elif target_dir_or_swf.name.lower() == "ui_mainmenu.swf":
            actual_h = hashlib.sha256(target_dir_or_swf.read_bytes()).hexdigest()
            exp_main_h = cert_data.get("main_hash") or expected_hashes.get(target_dir_or_swf.name)
            if exp_main_h and actual_h != exp_main_h:
                return False, "SWF binary hash does not match certificate"

    return True, "Valid official BMT certificate"


def scan_ui_mainmenu_code(code_text_or_bytes: Any) -> List[Tuple[str, str]]:
    """
    Scans ActionScript 3 text or decompressed SWF byte streams for dangerous patterns.
    Returns: list of (matched_snippet, threat_description)
    """
    findings = []
    if isinstance(code_text_or_bytes, bytes):
        raw_text = _safe_extract_swf_strings(code_text_or_bytes)
    else:
        raw_text = str(code_text_or_bytes)

    for pat, desc in DANGEROUS_PATTERNS:
        matches = re.finditer(pat, raw_text, re.IGNORECASE)
        for m in matches:
            snippet = m.group(0).strip()
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            # Whitelist standard safe game URLs if any
            if "brawlhalla.com" in snippet.lower() or "brawlhalla.wiki.gg" in snippet.lower():
                continue
            findings.append((snippet, desc))

    return findings


def scan_mod_source_or_file(target_path: Path) -> Dict[str, Any]:
    """
    Scans UI_MainMenu.swf or UI_MainMenu source files exclusively for security verification.
    Non-UI assets (skins, sounds, bones, gfx, languages) are completely ignored.
    """
    results = {
        "is_clean": True,
        "is_bmt_certified": False,
        "is_certified": False,
        "has_ui_mainmenu": False,
        "cert_info": {},
        "threats": [],
        "status_code": "CLEAN_UNCERTIFIED"
    }

    if not target_path.exists():
        return results

    # 1. Check if UI_MainMenu is present in this mod
    ui_mainmenu_targets = []
    if target_path.is_dir():
        for root, _, files in os.walk(target_path):
            if "_previews" in root.lower():
                continue
            for f in sorted(files):
                if f.lower() in IGNORED_CERT_FILES:
                    continue
                p = Path(root) / f
                if "ui_mainmenu" in str(p).lower():
                    ui_mainmenu_targets.append(p)
    else:
        if "ui_mainmenu" in target_path.name.lower() or target_path.suffix.lower() == ".bmod":
            ui_mainmenu_targets.append(target_path)

    has_ui = len(ui_mainmenu_targets) > 0
    results["has_ui_mainmenu"] = has_ui

    # If no UI_MainMenu is present in this mod, it has zero UI code risk
    if not has_ui:
        results["status_code"] = "CLEAN_UNCERTIFIED"
        return results

    # 2. Check for BMT certificate if UI_MainMenu is present
    cert_file = target_path / ".bmt_cert.json" if target_path.is_dir() else None
    cert_data = None
    if cert_file and cert_file.exists():
        try:
            cert_data = json.loads(cert_file.read_text(encoding="utf-8"))
        except Exception:
            cert_data = None

    if cert_data:
        valid_cert, cert_msg = verify_bmt_certificate(cert_data, target_path)
        if valid_cert:
            results["is_bmt_certified"] = True
            results["is_certified"] = True
            results["cert_info"] = cert_data
            results["status_code"] = "CERTIFIED"
        else:
            results["threats"].append({"file": "UI_MainMenu.swf", "snippet": "Certificate Validation Error", "description": cert_msg})

    # 3. Scan ONLY UI_MainMenu code and scripts for threats
    for p in ui_mainmenu_targets:
        try:
            if p.suffix.lower() in (".as", ".txt", ".json"):
                content = p.read_text(encoding="utf-8", errors="ignore")
                founds = scan_ui_mainmenu_code(content)
            else:
                raw_bytes = p.read_bytes()
                founds = scan_ui_mainmenu_code(raw_bytes)

            for snippet, desc in founds:
                results["threats"].append({
                    "file": p.name,
                    "snippet": snippet,
                    "description": desc
                })
        except Exception as e:
            print(f"[SecurityScanner] Error scanning {p}: {e}")

    if results["threats"]:
        results["is_clean"] = False
        results["status_code"] = "SUSPICIOUS"
    elif results["is_bmt_certified"]:
        results["status_code"] = "CERTIFIED"
    else:
        results["status_code"] = "CLEAN_UNCERTIFIED"

    return results
