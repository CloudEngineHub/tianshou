#!/usr/bin/env python3

import os
from collections.abc import Sequence

from sensai.util import logging
from sensai.util.logging import datetime_tag

from examples.mujoco.mujoco_env import MujocoEnvFactory
from tianshou.highlevel.config import OffPolicyTrainingConfig
from tianshou.highlevel.experiment import (
    DDPGExperimentBuilder,
    ExperimentConfig,
)
from tianshou.highlevel.params.algorithm_params import DDPGParams
from tianshou.highlevel.params.noise import MaxActionScaledGaussian


def main(
    experiment_config: ExperimentConfig,
    task: str = "Ant-v4",
    buffer_size: int = 1000000,
    hidden_sizes: Sequence[int] = (256, 256),
    actor_lr: float = 1e-3,
    critic_lr: float = 1e-3,
    gamma: float = 0.99,
    tau: float = 0.005,
    exploration_noise: float = 0.1,
    start_timesteps: int = 25000,
    epoch: int = 200,
    epoch_num_steps: int = 5000,
    collection_step_num_env_steps: int = 1,
    update_per_step: int = 1,
    n_step: int = 1,
    batch_size: int = 256,
    num_train_envs: int = 1,
    num_test_envs: int = 10,
) -> None:
    log_name = os.path.join(task, "ddpg", str(experiment_config.seed), datetime_tag())

    training_config = OffPolicyTrainingConfig(
        max_epochs=epoch,
        epoch_num_steps=epoch_num_steps,
        batch_size=batch_size,
        num_train_envs=num_train_envs,
        num_test_envs=num_test_envs,
        buffer_size=buffer_size,
        collection_step_num_env_steps=collection_step_num_env_steps,
        update_step_num_gradient_steps_per_sample=update_per_step,
        start_timesteps=start_timesteps,
        start_timesteps_random=True,
    )

    env_factory = MujocoEnvFactory(task, obs_norm=False)

    experiment = (
        DDPGExperimentBuilder(env_factory, experiment_config, training_config)
        .with_ddpg_params(
            DDPGParams(
                actor_lr=actor_lr,
                critic_lr=critic_lr,
                gamma=gamma,
                tau=tau,
                exploration_noise=MaxActionScaledGaussian(exploration_noise),
                n_step_return_horizon=n_step,
            ),
        )
        .with_actor_factory_default(hidden_sizes)
        .with_critic_factory_default(hidden_sizes)
        .build()
    )
    experiment.run(run_name=log_name)


if __name__ == "__main__":
    logging.run_cli(main)
