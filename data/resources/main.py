from concurrent.futures import ThreadPoolExecutor
from concurrent.futures.process import ProcessPoolExecutor
from os import cpu_count
from time import perf_counter
import numpy as np
import pandas as pd
from glob import glob
from statsmodels.tsa.stattools import coint
from math import ceil
from tqdm import tqdm
import warnings
from argument_parser import ArgumentParser, Argument, Flag
from os_flags import get_flag, set_flag, get_bool_flag, set_bool_flag
import sys
import os
from rich import get_console
sys.argv.pop(0)
warnings.filterwarnings("ignore")

N_SELECT = None
THREADS = cpu_count() - 4
FILES = "/root/jasper_20250113/*"
OUT_PATH = "out.xlsx"
result = pd.DataFrame(columns=["id", "coint_t", "pval"])
set_bool_flag("EXIT_ON_ERR", False)

def process_item(i, file):
    try:
        res = compute(file)
        _id = extract_id(file)
        return [_id, res[0], res[1]]
    except Exception as ex:
        c = get_console()
        print("Encountered an error!")
        c.print_exception()

        if get_bool_flag("EXIT_ON_ERR"):
            os._exit(os.EX_SOFTWARE)
        else:
            print("Continuing...")

def process_chunk(start_index, chunk, progress):
    try:
        for offset, item in enumerate(chunk):
            yield process_item(start_index + offset, item)
            progress.update(1)
    except Exception as ex:
        c = get_console()
        print("Failed because of error!")
        c.print_exception()

def process_list_with_threads(items, num_threads):
    chunk_size = ceil(len(items) / num_threads)
    chunks_with_indices = [(i, items[i:i + chunk_size]) for i in range(0, len(items), chunk_size)]

    total_items = len(items)
    with tqdm(total=total_items, desc="Processing Files") as progress:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for resU in executor.map(lambda args: process_chunk(args[0], args[1], progress), chunks_with_indices):
                for resL in resU:
                    if resL is None: continue
                    result.loc[resL[0]] = resL

def compute(path):
    csv = pd.read_csv(path, sep=";", header=None).applymap(lambda x: float(str(x).replace(',', '.')))
    csv.replace([np.inf, -np.inf], np.nan, inplace=True)
    csv.replace(np.nan, 0, inplace=True)
    return coint(csv.loc[0], csv.loc[1])


def extract_id(path):
    return path[25:-10]

def main(inp):
    set_flag("INPUT", inp)
    ld_globals()

    if N_SELECT:
        files = glob(FILES)[:N_SELECT]
    else:
        files = glob(FILES)
    print("Processing", FILES, f"({len(files)})", "with", THREADS, "threads")

    start = perf_counter()
    try:
        process_list_with_threads(files, THREADS)
    except Exception as ex:
        c = get_console()
        print("Failed because of error!")
        c.print_exception()

    end = perf_counter()
    print(f"Time taken: {end-start:.4f}")

    print(result)

    print("Writing result to", OUT_PATH)
    result.to_excel(OUT_PATH)


def ld_globals():
    global THREADS, FILES, OUT_PATH, N_SELECT
    if (n_select := get_flag("SELECT_NUM")) is not None:
        N_SELECT = int(n_select)
    if (n_threads := get_flag("N_THREADS")) is not None:
        THREADS = int(n_threads)
    if (out_path := get_flag("OUTPUT")) is not None:
        OUT_PATH = out_path
    FILES = get_flag("INPUT")


set_flag("PROG_NAME", "DATPROC")
set_flag("VERSION", "1.0")

if __name__ == '__main__':
    ap = ArgumentParser("")
    ap.add_argument(Argument("input", ["input"], main, "Input a dir pattern and start processing", positional=True))
    ap.add_flag(Flag("threads", "t", True, "N_THREADS", f"Set amounts of threads to use (defaults to {THREADS})"))
    ap.add_flag(Flag("output", "o", True, "OUTPUT", "Set output file (defaults to out.xlsx | Different formats are not supported!)"))
    ap.add_flag(Flag("exit", "e", False, "EXIT_ON_ERR", "Set whether to exit on error in thread (Defaults to false)"))
    ap.add_flag(Flag("select", "s", True, "SELECT_NUM", "If provided, limit the amount of files being processed"))
    ap.add_help()
    ap.add_version()
    ap.parse()
