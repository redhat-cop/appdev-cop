#!/usr/bin/env python3
"""Print CPU, memory, GPU, disk, and the busiest processes on this lab machine."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path


def run(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def section(title: str) -> None:
    print(f"\n== {title}")


def cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def memory_report() -> None:
    meminfo = Path("/proc/meminfo")
    if not meminfo.is_file():
        print("Memory details are available on Linux labs only.")
        return

    wanted = {"MemTotal", "MemAvailable", "MemFree", "SwapTotal", "SwapFree"}
    values = {}
    for line in meminfo.read_text(encoding="utf-8", errors="replace").splitlines():
        key, _, rest = line.partition(":")
        if key in wanted:
            values[key] = rest.strip()

    for key in ("MemTotal", "MemAvailable", "MemFree", "SwapTotal", "SwapFree"):
        raw = values.get(key)
        if raw is None:
            print(f"{key}: unknown")
            continue
        kib = int(raw.split()[0])
        print(f"{key}: {kib / (1024 ** 2):.2f} GiB")


def cuda_report() -> None:
    try:
        import torch
    except ImportError:
        print("🔥 CUDA Availability: False")
        print("🚀 Active GPU Name: unavailable (torch is not installed)")
        print("📦 Total VRAM Available: unavailable")
        return

    available = torch.cuda.is_available()
    print(f"🔥 CUDA Availability: {available}")
    if not available:
        print("🚀 Active GPU Name: none")
        print("📦 Total VRAM Available: 0 GB")
        return

    total_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    print(f"🚀 Active GPU Name: {torch.cuda.get_device_name(0)}")
    print(f"📦 Total VRAM Available: {total_gb:.2f} GB")


def gpu_report() -> None:
    cuda_report()
    print()
    summary = run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.used,memory.total,utilization.gpu",
            "--format=csv,noheader",
        ]
    )
    if not summary:
        print("No NVIDIA GPU detected.")
        return

    print("index, name, memory used, memory total, utilization")
    print(summary)

    processes = run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name,used_memory",
            "--format=csv,noheader",
        ]
    )
    print("\nGPU processes:")
    print(processes or "none")


def process_report() -> None:
    listing = run(["ps", "-eo", "pid,user,pcpu,pmem,rss,comm", "--sort=-rss"])
    if not listing:
        print("Process list is not available.")
        return

    lines = listing.splitlines()
    print("\n".join(lines[:11]))


def main() -> None:
    section("Host")
    print(f"Hostname: {platform.node()}")
    print(f"System: {platform.platform()}")
    print(f"Python: {platform.python_version()}")

    section("CPU")
    print(f"Model: {cpu_model()}")
    print(f"Logical CPUs: {os.cpu_count()}")

    section("Memory")
    memory_report()

    usage = shutil.disk_usage("/")
    section("Disk /")
    print(f"Total: {usage.total // (1024 ** 3)} GiB")
    print(f"Used: {usage.used // (1024 ** 3)} GiB")
    print(f"Free: {usage.free // (1024 ** 3)} GiB")

    section("GPU")
    gpu_report()

    section("Top processes by memory")
    process_report()


if __name__ == "__main__":
    main()
