MAX_PLAYERS = 8
MAX_MAPPINGS = 20

padcache = [[0] * MAX_MAPPINGS for i in range(MAX_PLAYERS)]


def simple_input_poll():
    pass


def simple_input_state(port, device, index, id):
    global padcache
    return padcache[port][id]


def set_input_internal(core):
    core.set_input_poll_cb(simple_input_poll)
    core.set_input_state_cb(simple_input_state)


def set_state(port, device, index, id, state):
    # currently index and device go unused here...
    padcache[port][id] = state


def set_state_digital(port, state):
    global padcache
    for id in range(16):
        padcache[port][id] = state & 1
        state >>= 1
