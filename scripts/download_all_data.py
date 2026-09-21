#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue, Empty

# Configuration & Auth
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, ".env")
CONFIG = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                CONFIG[key.strip()] = val.strip()

HARDCODED_TOKEN = "NovL7NzAL8zzsWVKIxC1JFAdVOoQfpI3ej7oyorsHlLVOe0joLeiJ7aopethRcSUrED0p2dqkz1RxfPaZKGV31un15PrdP8Zk4RJ"
HARDCODED_SERVER_ID = "cEuS61sZvNEFS3aB"

TOKEN = os.environ.get("EXAROTON_TOKEN") or CONFIG.get("EXAROTON_TOKEN") or HARDCODED_TOKEN
SERVER_ID = os.environ.get("EXAROTON_SERVER_ID") or CONFIG.get("EXAROTON_SERVER_ID") or HARDCODED_SERVER_ID
DOWNLOAD_DIR = os.path.join(BASE_DIR, "download")

RESOLVE_FLAG = ["--resolve", "api.exaroton.com:443:104.26.12.211"]
LOCK = threading.Lock()
stats = {"downloaded": 0, "skipped": 0, "failed": 0, "bytes": 0}

def encode_path(p):
    return urllib.parse.quote(p.strip('/'), safe='/')

def api_get_info(remote_path):
    """Fetches info about a remote file/directory."""
    encoded = encode_path(remote_path)
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/files/info/{encoded}"
    cmd = [
        "curl", "-s",
        *RESOLVE_FLAG,
        "-X", "GET", url,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "User-Agent: Mozilla/5.0"
    ]
    for attempt in range(7):
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if not res.stdout.strip():
                time.sleep(0.5)
                continue
            data = json.loads(res.stdout)
            if data.get("success"):
                return data.get("data")
            elif "rate limit" in str(data).lower() or res.returncode != 0:
                time.sleep(1.0 + attempt * 1.5)
                continue
            else:
                return None
        except Exception:
            time.sleep(1.0 + attempt * 1.5)
    return None

def download_file(remote_path, local_path, expected_size):
    """Downloads a single file from Exaroton API to local_path."""
    if os.path.exists(local_path):
        if expected_size is not None and expected_size > 0:
            if os.path.getsize(local_path) == expected_size:
                with LOCK:
                    stats["skipped"] += 1
                    stats["bytes"] += expected_size
                return "skipped"
        elif expected_size == 0 and os.path.getsize(local_path) == 0:
            with LOCK:
                stats["skipped"] += 1
            return "skipped"

    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    temp_path = f"{local_path}.tmp.{threading.get_ident()}.{os.getpid()}"
    
    encoded = encode_path(remote_path)
    url = f"https://api.exaroton.com/v1/servers/{SERVER_ID}/files/data/{encoded}"
    cmd = [
        "curl", "-s", "-f",
        *RESOLVE_FLAG,
        "-X", "GET", url,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "User-Agent: Mozilla/5.0",
        "-o", temp_path
    ]
    
    for attempt in range(8):
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=120)
            if res.returncode == 0 and os.path.exists(temp_path):
                downloaded_size = os.path.getsize(temp_path)
                if expected_size is not None and expected_size > 0 and downloaded_size != expected_size:
                    time.sleep(1.0 + attempt * 1.0)
                    continue
                os.replace(temp_path, local_path)
                with LOCK:
                    stats["downloaded"] += 1
                    stats["bytes"] += downloaded_size
                return "downloaded"
            else:
                time.sleep(1.0 + attempt * 1.5)
        except Exception:
            time.sleep(1.0 + attempt * 1.5)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    with LOCK:
        stats["failed"] += 1
    return "failed"

def crawl_remote_parallel(root_path="", max_workers=8):
    """Recursively indexes remote server files with worker threads."""
    print(f"[*] Indexing server directory tree...")
    dir_queue = Queue()
    dir_queue.put(root_path)
    
    files = []
    active_count = 0
    q_lock = threading.Lock()
    all_done = threading.Event()
    
    def worker():
        nonlocal active_count
        while not all_done.is_set():
            try:
                curr_dir = dir_queue.get(timeout=2.0)
            except Empty:
                with q_lock:
                    if active_count == 0 and dir_queue.empty():
                        all_done.set()
                        return
                continue
                
            with q_lock:
                active_count += 1
                
            try:
                data = api_get_info(curr_dir)
                if data:
                    if data.get("isDirectory"):
                        children = data.get("children", [])
                        for child in children:
                            c_name = child.get("name")
                            c_path = f"{curr_dir}/{c_name}".strip("/") if curr_dir else c_name
                            if child.get("isDirectory"):
                                dir_queue.put(c_path)
                            else:
                                with LOCK:
                                    files.append((c_path, child.get("size", 0)))
                    else:
                        with LOCK:
                            files.append((curr_dir, data.get("size", 0)))
            finally:
                dir_queue.task_done()
                with q_lock:
                    active_count -= 1
                    print(f"\r[*] Indexed {len(files)} files (pending directories: {dir_queue.qsize()})...", end="", flush=True)

    threads = []
    for _ in range(max_workers):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)
        
    while not all_done.is_set():
        all_done.wait(timeout=1.0)
        
    for t in threads:
        t.join(timeout=10)
        
    print(f"\n[+] Indexing complete: {len(files)} total files discovered.")
    return files

def main():
    num_workers = 12
    print(f"=== Exaroton Server Downloader ({num_workers} Workers) ===")
    print(f"Destination: {DOWNLOAD_DIR}")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    start_time = time.time()
    files = crawl_remote_parallel("", max_workers=6)
    if not files:
        print("[!] No files found on server.")
        sys.exit(1)
        
    total_size = sum(s for _, s in files)
    print(f"[+] Total files to sync: {len(files)} ({total_size / (1024*1024):.2f} MB)")
    print(f"[*] Starting {num_workers} parallel download workers...")
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {}
        for r_path, r_size in files:
            l_path = os.path.join(DOWNLOAD_DIR, r_path)
            f = executor.submit(download_file, r_path, l_path, r_size)
            futures[f] = r_path
            
        total_tasks = len(futures)
        completed = 0
        for fut in as_completed(futures):
            completed += 1
            path = futures[fut]
            status = fut.result()
            progress = (completed / total_tasks) * 100
            print(f"\r[{completed}/{total_tasks} - {progress:5.1f}%] [{status.upper()}] {path[:45]:<45}", end="", flush=True)

    elapsed = time.time() - start_time
    print(f"\n\n=== Download Complete in {elapsed:.1f}s ===")
    print(f"Downloaded: {stats['downloaded']}")
    print(f"Skipped (already exists): {stats['skipped']}")
    print(f"Failed: {stats['failed']}")
    print(f"Total Data: {stats['bytes'] / (1024*1024):.2f} MB")
    print(f"Saved to: {DOWNLOAD_DIR}")

if __name__ == "__main__":
    main()
