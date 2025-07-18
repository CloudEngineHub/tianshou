#!/usr/bin/env python3

import os
from collections.abc import Sequence

import torch
from sensai.util import logging
from sensai.util.logging import datetime_tag

from examples.mujoco.mujoco_env import MujocoEnvFactory
from tianshou.highlevel.config import OffPolicyTrainingConfig
from tianshou.highlevel.experiment import (
    ExperimentConfig,
    TD3ExperimentBuilder,
)
from tianshou.highlevel.params.algorithm_params import TD3Params
from tianshou.highlevel.params.env_param import MaxActionScaled
from tianshou.highlevel.params.noise import (
    MaxActionScaledGaussian,
)


def main(
    experiment_config: ExperimentConfig,
    task: str = "Ant-v4",
    buffer_size: int = 1000000,
    hidden_sizes: Sequence[int] = (256, 256),
    actor_lr: float = 3e-4,
    critic_lr: float = 3e-4,
    gamma: float = 0.99,
    tau: float = 0.005,
    exploration_noise: float = 0.1,
    policy_noise: float = 0.2,
    noise_clip: float = 0.5,
    update_actor_freq: int = 2,
    start_timesteps: int = 25000,
    epoch: int = 200,
    epoch_num_steps: int = 5000,
    collection_step_num_env_steps: int = 1,
    update_step_num_gradient_steps_per_sample: int = 1,
    n_step: int = 1,
    batch_size: int = 256,
    num_train_envs: int = 1,
    num_test_envs: int = 10,
) -> None:
    log_name = os.path.join(task, "td3", str(experiment_config.seed), datetime_tag())

    training_config = OffPolicyTrainingConfig(
        max_epochs=epoch,
        epoch_num_steps=epoch_num_steps,
        num_train_envs=num_train_envs,
        num_test_envs=num_test_envs,
        buffer_size=buffer_size,
        batch_size=batch_size,
        collection_step_num_env_steps=collection_step_num_env_steps,
        update_step_num_gradient_steps_per_sample=update_step_num_gradient_steps_per_sample,
        start_timesteps=start_timesteps,
        start_timesteps_random=True,
    )

    env_factory = MujocoEnvFactory(task, obs_norm=False)

    experiment = (
        TD3ExperimentBuilder(env_factory, experiment_config, training_config)
        .with_td3_params(
            TD3Params(
                tau=tau,
                gamma=gamma,
                n_step_return_horizon=n_step,
                update_actor_freq=update_actor_freq,
                noise_clip=MaxActionScaled(noise_clip),
                policy_noise=MaxActionScaled(policy_noise),
                exploration_noise=MaxActionScaledGaussian(exploration_noise),
                actor_lr=actor_lr,
                critic1_lr=critic_lr,
                critic2_lr=critic_lr,
            ),
        )
        .with_actor_factory_default(hidden_sizes, torch.nn.Tanh)
        .with_common_critic_factory_default(hidden_sizes, torch.nn.Tanh)
        .build()
    )
    experiment.run(run_name=log_name)


if __name__ == "__main__":
    logging.run_cli(main)
