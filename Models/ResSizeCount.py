from typing import Dict

from Consts import ResState


class ResSizeCount:
    def __init__(self):
        self.min = 0
        self.max = 0
        self.count_map: Dict[int, int] = {}

    def setStateMap(self, state_map: Dict[ResState, int]):
        for state, count in state_map.items():
            self.count_map[state.value] = count

    def toJson(self):
        return {'min': self.min, 'max': self.max, 'count_map': self.count_map}