from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import gymnasium as gym
import numpy as np

from tianshou.env.utils import gym_new_venv_step_type


class EnvWorker(ABC):
    """An abstract worker for an environment."""

    def __init__(self, env_fn: Callable[[], gym.Env]) -> None:
        self._env_fn = env_fn
        self.is_closed = False
        self.result: gym_new_venv_step_type | tuple[np.ndarray, dict]
        self.action_space = self.get_env_attr("action_space")
        self.is_reset = False

    @abstractmethod
    def get_env_attr(self, key: str) -> Any:
        pass

    @abstractmethod
    def set_env_attr(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def send(self, action: np.ndarray | None) -> None:
        """Send action signal to low-level worker.

        When action is None, it indicates sending "reset" signal; otherwise
        it indicates "step" signal. The paired return value from "recv"
        function is determined by such kind of different signal.
        """

    def recv(self) -> gym_new_venv_step_type | tuple[np.ndarray, dict]:
        """Receive result from low-level worker.

        If the last "send" function sends a NULL action, it only returns a
        single observation; otherwise it returns a tuple of (obs, rew, done,
        info) or (obs, rew, terminated, truncated, info), based on whether
        the environment is using the old step API or the new one.
        """
        return self.result

    @abstractmethod
    def reset(self, **kwargs: Any) -> tuple[np.ndarray, dict]:
        pass

    def step(self, action: np.ndarray) -> gym_new_venv_step_type:
        """Perform one timestep of the environment's dynamic.

        "send" and "recv" are coupled in sync simulation, so users only call
        "step" function. But they can be called separately in async
        simulation, i.e. someone calls "send" first, and calls "recv" later.
        """
        self.send(action)
        return self.recv()  # type: ignore

    @staticmethod
    def wait(
        workers: list["EnvWorker"],
        wait_num: int,
        timeout: float | None = None,
    ) -> list["EnvWorker"]:
        """Given a list of workers, return those ready ones."""
        raise NotImplementedError

    def seed(self, seed: int | None = None) -> list[int] | None:
        """
        Seeds the environment's action space sampler.
        NOTE: This does *not* seed the environment itself.

        :param seed: the random seed
        :return: a list containing the resulting seed used
        """
        return self.action_space.seed(seed)

    @abstractmethod
    def render(self, **kwargs: Any) -> Any:
        """Render the environment."""

    @abstractmethod
    def close_env(self) -> None:
        pass

    def close(self) -> None:
        if self.is_closed:
            return
        self.is_closed = True
        self.close_env()
