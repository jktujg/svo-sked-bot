from pathlib import Path

from .utils import JsonFileLoader

_compare_files_dir = Path(__file__).parent / 'search_data'
compare_mapping = JsonFileLoader(
    co_mapping=_compare_files_dir / 'co.json',
    ap_mapping=_compare_files_dir / 'ap.json',
    ct_mapping=_compare_files_dir / 'ct.json',
)
