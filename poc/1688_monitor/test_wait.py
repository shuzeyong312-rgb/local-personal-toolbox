from coverage import wait_product

class Page:
    def __init__(self, states):
        self.states = iter(states)
        self.last = None
    def evaluate(self, script):
        self.last = next(self.states, self.last)
        return self.last

def state(ready, count):
    return {'product': {'title': 'title' if ready else 'unavailable'},
            'product_detected': ready, 'dom_structure': {
                'price_value_count': count, 'color_button_count': 0, 'visible_spec_row_count': 0}}

ticks = [0]
def pause(seconds):
    ticks[0] += seconds

result = wait_product(Page([state(False, 0), state(False, 0), state(True, 1),
                           state(True, 2), state(True, 2)]), '', clock=lambda: ticks[0], pause=pause)
assert result['stable'] and len(result['observations']) == 5
ticks[0] = 0
result = wait_product(Page([state(False, 0)]), '', clock=lambda: ticks[0], pause=pause)
assert not result['stable'] and result['seconds'] == 10
print('Wait checks passed: missing DOM never stable; changed DOM requires two matching observations')
