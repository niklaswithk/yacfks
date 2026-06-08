class WidgetRepo:
    def get_bonus(self, level: int) -> float:
        return {
            0: 1.0,
            1: 1.0,
            2: 1.05,
            3: 1.05,
            4: 1.075,
            5: 1.075,
            6: 1.10,
            7: 1.10,
            8: 1.125,
            9: 1.125,
            10: 1.15
        }[level]