# global_manager.py
from multiprocessing import Manager
from .action import UdacityAction

# Initialize the Manager globally
manager = Manager()

# Initialize the shared simulator state dictionary
simulator_state = manager.dict()
simulator_state['observation'] = None
simulator_state['action'] = UdacityAction(0.0, 0.0)
simulator_state['paused'] = False
simulator_state['track'] = "lake"
simulator_state['events'] = []
simulator_state['episode_metrics'] = None
