import argparse
import os
from test.determinism_test import AlgorithmDeterminismTest

import gymnasium as gym
import numpy as np
import torch
from torch.utils.tensorboard import SummaryWriter

from tianshou.data import Collector, CollectStats, VectorReplayBuffer
from tianshou.env import DummyVectorEnv
from tianshou.policy import DQNPolicy
from tianshou.policy.base import BasePolicy
from tianshou.trainer import OffpolicyTrainer
from tianshou.utils import TensorboardLogger
from tianshou.utils.net.common import Recurrent
from tianshou.utils.space_info import SpaceInfo


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default="CartPole-v1")
    parser.add_argument("--reward-threshold", type=float, default=None)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--eps-test", type=float, default=0.05)
    parser.add_argument("--eps-train", type=float, default=0.1)
    parser.add_argument("--buffer-size", type=int, default=20000)
    parser.add_argument("--stack-num", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--gamma", type=float, default=0.95)
    parser.add_argument("--n-step", type=int, default=3)
    parser.add_argument("--target-update-freq", type=int, default=320)
    parser.add_argument("--epoch", type=int, default=5)
    parser.add_argument("--step-per-epoch", type=int, default=20000)
    parser.add_argument("--update-per-step", type=float, default=1 / 16)
    parser.add_argument("--step-per-collect", type=int, default=16)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--layer-num", type=int, default=2)
    parser.add_argument("--training-num", type=int, default=16)
    parser.add_argument("--test-num", type=int, default=100)
    parser.add_argument("--logdir", type=str, default="log")
    parser.add_argument("--render", type=float, default=0.0)
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
    )
    return parser.parse_known_args()[0]


def test_drqn(args: argparse.Namespace = get_args(), enable_assertions: bool = True) -> None:
    env = gym.make(args.task)
    assert isinstance(env.action_space, gym.spaces.Discrete)
    space_info = SpaceInfo.from_env(env)
    args.state_shape = space_info.observation_info.obs_shape
    args.action_shape = space_info.action_info.action_shape
    if args.reward_threshold is None:
        default_reward_threshold = {"CartPole-v1": 195}
        args.reward_threshold = default_reward_threshold.get(
            args.task,
            env.spec.reward_threshold if env.spec else None,
        )
    # train_envs = gym.make(args.task)
    # you can also use tianshou.env.SubprocVectorEnv
    train_envs = DummyVectorEnv([lambda: gym.make(args.task) for _ in range(args.training_num)])
    # test_envs = gym.make(args.task)
    test_envs = DummyVectorEnv([lambda: gym.make(args.task) for _ in range(args.test_num)])
    # seed
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    train_envs.seed(args.seed)
    test_envs.seed(args.seed)
    # model
    net = Recurrent(args.layer_num, args.state_shape, args.action_shape, args.device).to(
        args.device,
    )
    optim = torch.optim.Adam(net.parameters(), lr=args.lr)
    policy: DQNPolicy = DQNPolicy(
        model=net,
        optim=optim,
        discount_factor=args.gamma,
        estimation_step=args.n_step,
        action_space=env.action_space,
        target_update_freq=args.target_update_freq,
    )

    # collector
    buffer = VectorReplayBuffer(
        args.buffer_size,
        buffer_num=len(train_envs),
        stack_num=args.stack_num,
        ignore_obs_next=True,
    )
    train_collector = Collector[CollectStats](policy, train_envs, buffer, exploration_noise=True)

    # the stack_num is for RNN training: sample framestack obs
    test_collector = Collector[CollectStats](policy, test_envs, exploration_noise=True)

    # initial data collection
    policy.set_eps(args.eps_train)
    train_collector.reset()
    train_collector.collect(n_step=args.batch_size * args.training_num)

    # log
    log_path = os.path.join(args.logdir, args.task, "drqn")
    writer = SummaryWriter(log_path)
    logger = TensorboardLogger(writer)

    def save_best_fn(policy: BasePolicy) -> None:
        torch.save(policy.state_dict(), os.path.join(log_path, "policy.pth"))

    def stop_fn(mean_rewards: float) -> bool:
        return mean_rewards >= args.reward_threshold

    def train_fn(epoch: int, env_step: int) -> None:
        policy.set_eps(args.eps_train)

    def test_fn(epoch: int, env_step: int | None) -> None:
        policy.set_eps(args.eps_test)

    # trainer
    result = OffpolicyTrainer(
        policy=policy,
        train_collector=train_collector,
        test_collector=test_collector,
        max_epoch=args.epoch,
        step_per_epoch=args.step_per_epoch,
        step_per_collect=args.step_per_collect,
        episode_per_test=args.test_num,
        batch_size=args.batch_size,
        update_per_step=args.update_per_step,
        train_fn=train_fn,
        test_fn=test_fn,
        stop_fn=stop_fn,
        save_best_fn=save_best_fn,
        logger=logger,
    ).run()

    if enable_assertions:
        assert stop_fn(result.best_reward)


def test_drqn_determinism() -> None:
    main_fn = lambda args: test_drqn(args, enable_assertions=False)
    AlgorithmDeterminismTest("discrete_drqn", main_fn, get_args()).run()
