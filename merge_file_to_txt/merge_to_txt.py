#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test 
import sys
import os
import ast
from pathlib import Path
from datetime import datetime

def read_text_with_fallback(file_path: Path) -> str:
    encodings = ["utf-8", "cp932", "latin-1"]
    last_err = None
    for enc in encodings:
        try:
            return file_path.read_text(encoding=enc, errors="replace")
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Failed to read {file_path} with fallback encodings") from last_err

def parse_block_list(lines_iter):
    items = []
    for line in lines_iter:
        s = line.strip()
        if s == ">>>":
            break
        if not s or s.startswith("#"):
            continue
        items.append(s)
    return items

def try_parse_python_literal(val):
    try:
        return ast.literal_eval(val)
    except Exception:
        return None

def normalize_ext_set(items):
    out = set()
    for it in items:
        s = str(it).strip()
        if not s:
            continue
        if not s.startswith("."):
            s = "." + s
        out.add(s.lower())
    return out

def normalize_name_set(items):
    return {str(it).strip() for it in items if str(it).strip()}

def load_settings(settings_path: Path):
    if not settings_path.exists():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")
    raw = read_text_with_fallback(settings_path).splitlines()
    settings = {}
    i = 0
    n = len(raw)
    while i < n:
        line = raw[i]
        i += 1
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        key, val = s.split("=", 1)
        key = key.strip()
        val = val.strip()
        if val == "<<<":
            block_items = parse_block_list(iter(raw[i:]))
            i += len(block_items) + 1
            settings[key] = block_items
            continue
        lit = try_parse_python_literal(val)
        if isinstance(lit, (list, tuple, set)):
            settings[key] = list(lit) if not isinstance(lit, list) else lit
            continue
        lowered = val.lower()
        if lowered in ("true", "false"):
            settings[key] = lowered == "true"
            continue
        if "," in val:
            parts = [p.strip() for p in val.split(",")]
            settings[key] = [p for p in parts if p]
            continue
        settings[key] = val

    target_exts_raw = settings.get("TARGET_EXTS", [])
    if isinstance(target_exts_raw, str):
        target_exts_raw = [target_exts_raw]
    TARGET_EXTS = normalize_ext_set(target_exts_raw)

    INCLUDE_EXTENSIONLESS = bool(settings.get("INCLUDE_EXTENSIONLESS", False))
    INCLUDE_EXTENSIONLESS_WHITELIST_ONLY = bool(settings.get("INCLUDE_EXTENSIONLESS_WHITELIST_ONLY", False))

    extless_wh_raw = settings.get("EXTENSIONLESS_WHITELIST", [])
    if isinstance(extless_wh_raw, str):
        extless_wh_raw = [extless_wh_raw]
    EXTENSIONLESS_WHITELIST = normalize_name_set(extless_wh_raw)

    in_dir = settings.get("INPUT_DIR", "")
    if not in_dir:
        raise ValueError("INPUT_DIR must be set in setting.txt")
    INPUT_DIR = Path(in_dir)

    excl_raw = settings.get("EXCLUDED_DIRS", [])
    if isinstance(excl_raw, str):
        excl_raw = [excl_raw]
    EXCLUDED_DIRS = normalize_name_set(excl_raw)

    script_dir = Path(__file__).parent.resolve()
    folder_name = INPUT_DIR.name
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_FILE = script_dir / f"{folder_name}_{ts}.txt"

    return {
        "TARGET_EXTS": TARGET_EXTS,
        "INCLUDE_EXTENSIONLESS": INCLUDE_EXTENSIONLESS,
        "INCLUDE_EXTENSIONLESS_WHITELIST_ONLY": INCLUDE_EXTENSIONLESS_WHITELIST_ONLY,
        "EXTENSIONLESS_WHITELIST": EXTENSIONLESS_WHITELIST,
        "INPUT_DIR": INPUT_DIR,
        "OUTPUT_FILE": OUTPUT_FILE,
        "EXCLUDED_DIRS": EXCLUDED_DIRS,
    }

def should_include_file(p: Path, cfg) -> bool:
    if not p.is_file():
        return False
    suf = p.suffix.lower()
    if suf:
        return suf in cfg["TARGET_EXTS"]
    if not cfg["INCLUDE_EXTENSIONLESS"]:
        return False
    if cfg["INCLUDE_EXTENSIONLESS_WHITELIST_ONLY"]:
        return p.name in cfg["EXTENSIONLESS_WHITELIST"]
    return True

def iter_target_files_pruned(root: Path, cfg):
    root_str = str(root.resolve())
    for dirpath, dirnames, filenames in os.walk(root_str):
        dirnames[:] = [d for d in dirnames if d not in cfg["EXCLUDED_DIRS"]]
        for fname in filenames:
            p = Path(dirpath) / fname
            if should_include_file(p, cfg):
                yield p

def merge_folder(cfg) -> None:
    input_dir = cfg["INPUT_DIR"]
    output_file = cfg["OUTPUT_FILE"]
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Input folder not found or not a directory: {input_dir}")
    root = input_dir.resolve()
    files = sorted((p for p in iter_target_files_pruned(root, cfg)), key=lambda x: str(x).lower())
    output_file = output_file.resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header_top = (
        "========================================\n"
        f" MERGE START - {timestamp}\n"
        f" ROOT: {root}\n"
        f" TOTAL FILES: {len(files)}\n"
        "========================================\n\n"
    )
    with output_file.open("w", encoding="utf-8", newline="\n") as out:
        out.write(header_top)
        for f in files:
            rel_dir = str(f.parent.relative_to(root))
            dir_header = f"======== DIRECTORY: {rel_dir if rel_dir else '.'} ========"
            file_header = f"******** FILE: {f.name} ********"
            out.write(dir_header + "\n")
            out.write(file_header + "\n\n")
            try:
                content = read_text_with_fallback(f)
            except Exception as e:
                out.write(f"[READ ERROR] {e}\n\n")
                out.write("-" * 40 + "\n\n")
                continue
            out.write(content.rstrip("\n") + "\n")
            out.write("\n" + "-" * 40 + "\n\n")
        out.write("========================================\n")
        out.write(" MERGE END\n")
        out.write("========================================\n")

def main():
    try:
        settings_path = Path(__file__).with_name("setting.md")
        cfg = load_settings(settings_path)
        merge_folder(cfg)
        print(f"Done. Output written to: {cfg['OUTPUT_FILE'].resolve()}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()