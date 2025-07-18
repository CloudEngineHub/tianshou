#!/usr/bin/env python3

import argparse
import datetime
import os
import pprint

import gymnasium as gym
import numpy as np
import torch
from torch.utils.tensorboard import SummaryWriter

from examples.offline.utils import load_buffer_d4rl, normalize_all_obs_in_replay_buffer
from tianshou.algorithm import TD3BC
from tianshou.algorithm.algorithm_base import Algorithm
from tianshou.algorithm.modelfree.ddpg import ContinuousDeterministicPolicy
from tianshou.algorithm.optim import AdamOptimizerFactory
from tianshou.data import Collector, CollectStats
from tianshou.env import BaseVectorEnv, SubprocVectorEnv, VectorEnvNormObs
from tianshou.exploration import GaussianNoise
from tianshou.trainer import OfflineTrainerParams
from tianshou.utils import TensorboardLogger, WandbLogger
from tianshou.utils.net.common import Net
from tianshou.utils.net.continuous import ContinuousActorDeterministic, ContinuousCritic
from tianshou.utils.space_info import SpaceInfo


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="HalfCheetah-v2")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--expert_data_task", type=str, default="halfcheetah-expert-v2")
    parser.add_argument("--buffer_size", type=int, default=1000000)
    parser.add_argument("--hidden_sizes", type=int, nargs="*", default=[256, 256])
    parser.add_argument("--actor_lr", type=float, default=3e-4)
    parser.add_argument("--critic_lr", type=float, default=3e-4)
    parser.add_argument("--epoch", type=int, default=200)
    parser.add_argument("--epoch_num_steps", type=int, default=5000)
    parser.add_argument("--n_step", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=256)

    parser.add_argument("--alpha", type=float, default=2.5)
    parser.add_argument("--exploration_noise", type=float, default=0.1)
    parser.add_argument("--policy_noise", type=float, default=0.2)
    parser.add_argument("--noise_clip", type=float, default=0.5)
    parser.add_argument("--update_actor_freq", type=int, default=2)
    parser.add_argument("--tau", type=float, default=0.005)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--norm_obs", type=int, default=1)

    parser.add_argument("--eval_freq", type=int, default=1)
    parser.add_argument("--num_test_envs", type=int, default=10)
    parser.add_argument("--logdir", type=str, default="log")
    parser.add_argument("--render", type=float, default=1 / 35)
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
    )
    parser.add_argument("--resume_path", type=str, default=None)
    parser.add_argument("--resume_id", type=str, default=None)
    parser.add_argument(
        "--logger",
        type=str,
        default="tensorboard",
        choices=["tensorboard", "wandb"],
    )
    parser.add_argument("--wandb_project", type=str, default="offline_d4rl.benchmark")
    parser.add_argument(
        "--watch",
        default=False,
        action="store_true",
        help="watch the play of pre-trained policy only",
    )
    return parser.parse_args()


def test_td3_bc() -> None:
    args = get_args()
    env = gym.make(args.task)
    space_info = SpaceInfo.from_env(env)
    args.state_shape = space_info.observation_info.obs_shape
    args.action_shape = space_info.action_info.action_shape
    args.max_action = space_info.action_info.max_action
    args.min_action = space_info.action_info.min_action
    print("device:", args.device)
    print("Observations shape:", args.state_shape)
    print("Actions shape:", args.action_shape)
    print("Action range:", args.min_action, args.max_action)

    args.state_dim = space_info.observation_info.obs_dim
    args.action_dim = space_info.action_info.action_dim
    print("Max_action", args.max_action)

    test_envs: BaseVectorEnv
    test_envs = SubprocVectorEnv([lambda: gym.make(args.task) for _ in range(args.num_test_envs)])
    if args.norm_obs:
        test_envs = VectorEnvNormObs(test_envs, update_obs_rms=False)

    # seed
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    test_envs.seed(args.seed)

    # model
    # actor network
    net_a = Net(
        state_shape=args.state_shape,
        hidden_sizes=args.hidden_sizes,
    )
    actor = ContinuousActorDeterministic(
        preprocess_net=net_a,
        action_shape=args.action_shape,
        max_action=args.max_action,
    ).to(args.device)
    actor_optim = AdamOptimizerFactory(lr=args.actor_lr)

    # critic network
    net_c1 = Net(
        state_shape=args.state_shape,
        action_shape=args.action_shape,
        hidden_sizes=args.hidden_sizes,
        concat=True,
    )
    net_c2 = Net(
        state_shape=args.state_shape,
        action_shape=args.action_shape,
        hidden_sizes=args.hidden_sizes,
        concat=True,
    )
    critic1 = ContinuousCritic(preprocess_net=net_c1).to(args.device)
    critic1_optim = AdamOptimizerFactory(lr=args.critic_lr)
    critic2 = ContinuousCritic(preprocess_net=net_c2).to(args.device)
    critic2_optim = AdamOptimizerFactory(lr=args.critic_lr)

    policy = ContinuousDeterministicPolicy(
        actor=actor,
        exploration_noise=GaussianNoise(sigma=args.exploration_noise),
        action_space=env.action_space,
    )
    algorithm: TD3BC = TD3BC(
        policy=policy,
        policy_optim=actor_optim,
        critic=critic1,
        critic_optim=critic1_optim,
        critic2=critic2,
        critic2_optim=critic2_optim,
        tau=args.tau,
        gamma=args.gamma,
        policy_noise=args.policy_noise,
        update_actor_freq=args.update_actor_freq,
        noise_clip=args.noise_clip,
        alpha=args.alpha,
        n_step_return_horizon=args.n_step,
    )

    # load a previous policy
    if args.resume_path:
        algorithm.load_state_dict(torch.load(args.resume_path, map_location=args.device))
        print("Loaded agent from: ", args.resume_path)

    # collector
    test_collector = Collector[CollectStats](algorithm, test_envs)

    # log
    now = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    args.algo_name = "td3_bc"
    log_name = os.path.join(args.task, args.algo_name, str(args.seed), now)
    log_path = os.path.join(args.logdir, log_name)

    # logger
    writer = SummaryWriter(log_path)
    writer.add_text("args", str(args))
    logger: WandbLogger | TensorboardLogger
    if args.logger == "tensorboard":
        logger = TensorboardLogger(writer)
    else:
        logger = WandbLogger(
            save_interval=1,
            name=log_name.replace(os.path.sep, "__"),
            run_id=args.resume_id,
            config=args,
            project=args.wandb_project,
        )
        logger.load(writer)

    def save_best_fn(policy: Algorithm) -> None:
        torch.save(policy.state_dict(), os.path.join(log_path, "policy.pth"))

    def watch() -> None:
        if args.resume_path is None:
            args.resume_path = os.path.join(log_path, "policy.pth")

        algorithm.load_state_dict(torch.load(args.resume_path, map_location=torch.device("cpu")))
        collector = Collector[CollectStats](algorithm, env)
        collector.collect(n_episode=1, render=1 / 35)

    if not args.watch:
        replay_buffer = load_buffer_d4rl(args.expert_data_task)
        if args.norm_obs:
            replay_buffer, obs_rms = normalize_all_obs_in_replay_buffer(replay_buffer)
            test_envs.set_obs_rms(obs_rms)
        # train
        result = algorithm.run_training(
            OfflineTrainerParams(
                buffer=replay_buffer,
                test_collector=test_collector,
                max_epochs=args.epoch,
                epoch_num_steps=args.epoch_num_steps,
                test_step_num_episodes=args.num_test_envs,
                batch_size=args.batch_size,
                save_best_fn=save_best_fn,
                logger=logger,
            )
        )
        pprint.pprint(result)
    else:
        watch()

    # Let's watch its performance!
    test_envs.seed(args.seed)
    test_collector.reset()
    collector_stats = test_collector.collect(n_episode=args.num_test_envs, render=args.render)
    print(collector_stats)


if __name__ == "__main__":
    test_td3_bc()
