# udacity_gym/action.py

class UdacityAction:
    def __init__(self, carid: int, steering_angle: float, throttle: float, indicator_direction: str):
        self.carId = carid
        self.steering_angle = steering_angle
        self.throttle = throttle
        self.indicator_direction = indicator_direction

    def __repr__(self):
        return f"UdacityAction(carId={self.carId}, steering_angle={self.steering_angle}, throttle={self.throttle}, indicator_direction={self.indicator_direction})"
