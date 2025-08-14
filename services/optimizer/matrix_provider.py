from typing import List, Tuple
from ..mock_providers.traffic import build_time_matrix

def time_matrix(coords: List[Tuple[float, float]], departure_epoch: int):
    return build_time_matrix(coords, departure_epoch)