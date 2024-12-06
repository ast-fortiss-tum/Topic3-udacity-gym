import pathlib
import torch
import torchvision
import torchvision.transforms as transforms
from torch import nn

from .action import UdacityAction
from .extras.model.lane_keeping.chauffeur.chauffeur_model import Chauffeur
from .extras.model.lane_keeping.dave.dave_model import Dave2
from .extras.model.lane_keeping.epoch.epoch_model import Epoch
from .extras.model.lane_keeping.vit.vit_model import ViT
from .observation import UdacityObservation


# import pygame
# import torch
# import torchvision


class UdacityAgent:

    def __init__(self, before_action_callbacks=None, after_action_callbacks=None, transform_callbacks=None):
        self.before_action_callbacks = before_action_callbacks if before_action_callbacks is not None else []
        self.after_action_callbacks = after_action_callbacks if after_action_callbacks is not None else []
        self.transform_callbacks = transform_callbacks if transform_callbacks is not None else []

    def on_before_action(self, observation: UdacityObservation, *args, **kwargs):
        for callback in self.before_action_callbacks:
            callback(observation, *args, **kwargs)

    def on_after_action(self, observation: UdacityObservation, *args, **kwargs):
        for callback in self.after_action_callbacks:
            callback(observation, *args, **kwargs)

    def on_transform_observation(self, observation: UdacityObservation, *args, **kwargs):
        for callback in self.transform_callbacks:
            observation = callback(observation, *args, **kwargs)
        return observation

    def action(self, observation: UdacityObservation, *args, **kwargs):
        raise NotImplementedError('UdacityAgent does not implement __call__')

    def __call__(self, observation: UdacityObservation, *args, **kwargs):
        if observation.input_image is None:
            return UdacityAction(steering_angle=0.0, throttle=0.0)
        self.on_before_action(observation)
        observation = self.on_transform_observation(observation)
        action = self.action(observation, *args, **kwargs)
        self.on_after_action(observation, action=action)
        return action


class PIDUdacityAgent(UdacityAgent):

    def __init__(self, kp, kd, ki, before_action_callbacks=None, after_action_callbacks=None):
        super().__init__(before_action_callbacks, after_action_callbacks)
        self.kp = kp  # Proportional gain
        self.kd = kd  # Derivative gain
        self.ki = ki  # Integral gain
        self.prev_error = 0.0
        self.total_error = 0.0

        self.curr_sector = 0
        self.skip_frame = 4
        self.curr_skip_frame = 0

    def action(self, observation: UdacityObservation, *args, **kwargs):

        if observation.sector != self.curr_sector:
            if self.curr_skip_frame < self.skip_frame:
                self.curr_skip_frame += 1
            else:
                self.curr_skip_frame = 0
                self.curr_sector = observation.sector
            error = observation.cte
        else:
            error = (observation.next_cte + observation.cte) / 2
        diff_err = error - self.prev_error

        # Calculate steering angle
        steering_angle = - (self.kp * error) - (self.kd * diff_err) - (self.ki * self.total_error)
        steering_angle = max(-1, min(steering_angle, 1))

        # Calculate throttle
        throttle = (0.22 - 0.5 * abs(steering_angle))

        # Save error for next prediction
        self.total_error += error
        self.total_error = self.total_error * 0.99
        self.prev_error = error

        return UdacityAction(steering_angle=steering_angle, throttle=throttle)

class EndToEndLaneKeepingAgent(UdacityAgent):

    def __init__(self, model_name, checkpoint_path, before_action_callbacks=None, after_action_callbacks=None,
                 transform_callbacks=None):
        super().__init__(before_action_callbacks, after_action_callbacks, transform_callbacks)
        self.checkpoint_path = pathlib.Path(checkpoint_path)
        if model_name == "dave2":
            self.model = Dave2.load_from_checkpoint(self.checkpoint_path)
        if model_name == "epoch":
            self.model = Epoch.load_from_checkpoint(self.checkpoint_path)
        if model_name == "chauffeur":
            self.model = Chauffeur.load_from_checkpoint(self.checkpoint_path)
        if model_name == "vit":
            self.model = ViT.load_from_checkpoint(self.checkpoint_path)

    def action(self, observation: UdacityObservation, *args, **kwargs):

        # Cast input to right shape
        input_image = torchvision.transforms.ToTensor()(observation.input_image).to(self.model.device)

        # Calculate steering angle
        steering_angle = self.model(input_image).item()
        # Calculate throttle
        throttle = 0.22 - 0.5 * abs(steering_angle)

        return UdacityAction(steering_angle=steering_angle, throttle=throttle)


class DaveUdacityAgent(UdacityAgent):

    def __init__(self, checkpoint_path, before_action_callbacks=None, after_action_callbacks=None,
                 transform_callbacks=None):
        super().__init__(before_action_callbacks, after_action_callbacks, transform_callbacks)
        self.checkpoint_path = pathlib.Path(checkpoint_path)
        self.model = Dave2.load_from_checkpoint(self.checkpoint_path)

    def action(self, observation: UdacityObservation, *args, **kwargs):

        # Cast input to right shape
        input_image = torchvision.transforms.ToTensor()(observation.input_image).to(self.model.device)

        # Calculate steering angle
        steering_angle = self.model(input_image).item()
        # Calculate throttle
        throttle = 0.22 - 0.5 * abs(steering_angle)

        return UdacityAction(steering_angle=steering_angle, throttle=throttle)

class ImageBasedUdacityAgent(UdacityAgent):

    def __init__(self, model_path=None, before_action_callbacks=None, after_action_callbacks=None,
                 transform_callbacks=None):
        super().__init__(before_action_callbacks, after_action_callbacks, transform_callbacks)
        # Laden oder Initialisieren des Modells
        if model_path:
            self.model = torch.load(model_path)
        else:
            # Einfaches CNN-Modell zur Demonstration
            self.model = nn.Sequential(
                nn.Conv2d(3, 24, kernel_size=5, stride=2),
                nn.ReLU(),
                nn.Conv2d(24, 36, kernel_size=5, stride=2),
                nn.ReLU(),
                nn.Conv2d(36, 48, kernel_size=5, stride=2),
                nn.ReLU(),
                nn.Flatten(),
                nn.Linear(48 * 2 * 33, 100),
                nn.ReLU(),
                nn.Linear(100, 50),
                nn.ReLU(),
                nn.Linear(50, 10),
                nn.ReLU(),
                nn.Linear(10, 1)
            )
        self.model.eval()
        self.transform = transforms.Compose([
            transforms.Resize((66, 200)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],  # Beispielwerte
                                 std=[0.229, 0.224, 0.225])
        ])

    def action(self, observation: UdacityObservation, *args, **kwargs):
        # Preprocessing des Bildes
        input_image = observation.input_image
        input_tensor = self.transform(input_image).unsqueeze(0)  # Hinzufügen der Batch-Dimension

        # Vorhersage des Lenkwinkels
        with torch.no_grad():
            steering_angle = self.model(input_tensor).item()

        steering_angle = max(-1, min(steering_angle, 1))  # Begrenzen des Lenkwinkels

        # Gassteuerung basierend auf der aktuellen Geschwindigkeit
        throttle = 0.2 if observation.speed < 30 else 0.1

        return UdacityAction(steering_angle=steering_angle, throttle=throttle)
