class Normalizer:
    def __init__(self, start=0, stop=100):
        self.start, self.stop = start, stop
        self.min, self.max = 0, 0

        self._width = self.stop - self.start
        self._nm_ratio = 0

    def _refresh_nm_ratio(self):
        self._nm_ratio = self._width / (self.max - self.min)

    def _refresh_limits(self, input_value):
        if input_value < self.min:
            self.min = input_value
            self._refresh_nm_ratio()
        elif input_value > self.max:
            self.max = input_value
            self._refresh_nm_ratio()

    def normalize(self, input_value):
        self._refresh_limits(input_value)
        return (input_value - self.min) * self._nm_ratio + self.start


def linspace(start, stop, num):
    delta = (stop - start) / (num - 1)
    return [start + (delta * i) for i in range(num)]


def _gen_dial_zones(start, stop, count, deadzone):
    if count < 2:
        raise ValueError(
            '"output_pts" must have at least `2` values for DialMap to work.'
        )

    midpts = linspace(start, stop, count + 1)
    deadzone_size = (midpts[1] - midpts[0]) * (deadzone / 100)

    for i, left in enumerate(midpts[:-2]):
        right = midpts[i + 1]
        yield range(int(left), int(right - deadzone_size))

    left, right = midpts[-2], midpts[-1]
    if not deadzone_size >= right - left:
        yield range(int(left), int(right) + 1)


def _gen_dial_points(dial_zones, output_items):
    for i, dial_points in enumerate(dial_zones):
        for dial_point in dial_points:
            yield dial_point, output_items[i]


class DialMap:
    def __init__(self, output_items, deadzone=0, autosort=False):
        self._store = output_items[0]

        count = len(output_items)
        self._nm = Normalizer(stop=count * 2 if count > 50 else 100)
        if autosort:
            output_items = sorted(output_items)
        self.mapping = {
            dial_point: output_item
            for dial_point, output_item in _gen_dial_points(
                _gen_dial_zones(self._nm.start, self._nm.stop, count, deadzone),
                output_items,
            )
        }

    def __getitem__(self, dial_input):
        dial_point = int(self._nm.normalize(dial_input))
        try:
            self._store = self.mapping[dial_point]
        except KeyError:
            pass
        return self._store
