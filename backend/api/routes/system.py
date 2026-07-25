import asyncio
import time

import psutil
from fastapi import APIRouter

router = APIRouter(prefix="/system", tags=["system"])

_last_net: dict = {"bytes": None, "t": None}


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "asta-os-backend"}


async def _gpu_metrics() -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            "nvidia-smi",
            "--query-gpu=utilization.gpu,memory.used,memory.total",
            "--format=csv,noheader,nounits",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3)
        gpu_pct, mem_used, mem_total = (v.strip() for v in stdout.decode().split(","))
        vram_pct = round(100 * float(mem_used) / float(mem_total), 1) if float(mem_total) else None
        return {"gpu_percent": float(gpu_pct), "vram_percent": vram_pct}
    except Exception:
        return {"gpu_percent": None, "vram_percent": None}


def _network_mbps() -> float | None:
    counters = psutil.net_io_counters()
    now = time.monotonic()
    total_bytes = counters.bytes_sent + counters.bytes_recv

    prev_bytes, prev_t = _last_net["bytes"], _last_net["t"]
    _last_net["bytes"], _last_net["t"] = total_bytes, now

    if prev_bytes is None or prev_t is None:
        return None

    elapsed = now - prev_t
    if elapsed <= 0:
        return None

    return round(((total_bytes - prev_bytes) / elapsed) * 8 / 1_000_000, 2)  # Mbps


@router.get("/metrics")
async def metrics() -> dict:
    gpu = await _gpu_metrics()
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "ram_percent": psutil.virtual_memory().percent,
        "network_mbps": _network_mbps(),
        **gpu,
    }
