.. Tianshou documentation master file, created by
   sphinx-quickstart on Sat Mar 28 15:58:19 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Welcome to Tianshou!
====================

**Tianshou** (`天授 <https://baike.baidu.com/item/%E5%A4%A9%E6%8E%88>`_) is a reinforcement learning platform based on pure PyTorch. Unlike existing reinforcement learning libraries, which are mainly based on TensorFlow, have many nested classes, unfriendly API, or slow-speed, Tianshou provides a fast-speed framework and pythonic API for building the deep reinforcement learning agent. The supported interface algorithms include:

* :class:`~tianshou.algorithm.DQNPolicy` `Deep Q-Network <https://storage.googleapis.com/deepmind-media/dqn/DQNNaturePaper.pdf>`_
* :class:`~tianshou.algorithm.DQNPolicy` `Double DQN <https://arxiv.org/pdf/1509.06461.pdf>`_
* :class:`~tianshou.algorithm.DQNPolicy` `Dueling DQN <https://arxiv.org/pdf/1511.06581.pdf>`_
* :class:`~tianshou.algorithm.BranchingDQNPolicy` `Branching DQN <https://arxiv.org/pdf/1711.08946.pdf>`_
* :class:`~tianshou.algorithm.C51Policy` `Categorical DQN <https://arxiv.org/pdf/1707.06887.pdf>`_
* :class:`~tianshou.algorithm.RainbowPolicy` `Rainbow DQN <https://arxiv.org/pdf/1710.02298.pdf>`_
* :class:`~tianshou.algorithm.QRDQNPolicy` `Quantile Regression DQN <https://arxiv.org/pdf/1710.10044.pdf>`_
* :class:`~tianshou.algorithm.IQNPolicy` `Implicit Quantile Network <https://arxiv.org/pdf/1806.06923.pdf>`_
* :class:`~tianshou.algorithm.FQFPolicy` `Fully-parameterized Quantile Function <https://arxiv.org/pdf/1911.02140.pdf>`_
* :class:`~tianshou.algorithm.PGPolicy` `Policy Gradient <https://papers.nips.cc/paper/1713-policy-gradient-methods-for-reinforcement-learning-with-function-approximation.pdf>`_
* :class:`~tianshou.algorithm.NPGPolicy` `Natural Policy Gradient <https://proceedings.neurips.cc/paper/2001/file/4b86abe48d358ecf194c56c69108433e-Paper.pdf>`_
* :class:`~tianshou.algorithm.A2CPolicy` `Advantage Actor-Critic <https://openai.com/blog/baselines-acktr-a2c/>`_
* :class:`~tianshou.algorithm.TRPOPolicy` `Trust Region Policy Optimization <https://arxiv.org/pdf/1502.05477.pdf>`_
* :class:`~tianshou.algorithm.PPOPolicy` `Proximal Policy Optimization <https://arxiv.org/pdf/1707.06347.pdf>`_
* :class:`~tianshou.algorithm.DDPGPolicy` `Deep Deterministic Policy Gradient <https://arxiv.org/pdf/1509.02971.pdf>`_
* :class:`~tianshou.algorithm.TD3Policy` `Twin Delayed DDPG <https://arxiv.org/pdf/1802.09477.pdf>`_
* :class:`~tianshou.algorithm.SACPolicy` `Soft Actor-Critic <https://arxiv.org/pdf/1812.05905.pdf>`_
* :class:`~tianshou.algorithm.REDQPolicy` `Randomized Ensembled Double Q-Learning <https://arxiv.org/pdf/2101.05982.pdf>`_
* :class:`~tianshou.algorithm.DiscreteSACPolicy` `Discrete Soft Actor-Critic <https://arxiv.org/pdf/1910.07207.pdf>`_
* :class:`~tianshou.algorithm.ImitationPolicy` Imitation Learning
* :class:`~tianshou.algorithm.BCQPolicy` `Batch-Constrained deep Q-Learning <https://arxiv.org/pdf/1812.02900.pdf>`_
* :class:`~tianshou.algorithm.CQLPolicy` `Conservative Q-Learning <https://arxiv.org/pdf/2006.04779.pdf>`_
* :class:`~tianshou.algorithm.TD3BCPolicy` `Twin Delayed DDPG with Behavior Cloning <https://arxiv.org/pdf/2106.06860.pdf>`_
* :class:`~tianshou.algorithm.DiscreteBCQPolicy` `Discrete Batch-Constrained deep Q-Learning <https://arxiv.org/pdf/1910.01708.pdf>`_
* :class:`~tianshou.algorithm.DiscreteCQLPolicy` `Discrete Conservative Q-Learning <https://arxiv.org/pdf/2006.04779.pdf>`_
* :class:`~tianshou.algorithm.DiscreteCRRPolicy` `Critic Regularized Regression <https://arxiv.org/pdf/2006.15134.pdf>`_
* :class:`~tianshou.algorithm.GAILPolicy` `Generative Adversarial Imitation Learning <https://arxiv.org/pdf/1606.03476.pdf>`_
* :class:`~tianshou.algorithm.PSRLPolicy` `Posterior Sampling Reinforcement Learning <https://www.ece.uvic.ca/~bctill/papers/learning/Strens_2000.pdf>`_
* :class:`~tianshou.algorithm.ICMPolicy` `Intrinsic Curiosity Module <https://arxiv.org/pdf/1705.05363.pdf>`_
* :class:`~tianshou.data.PrioritizedReplayBuffer` `Prioritized Experience Replay <https://arxiv.org/pdf/1511.05952.pdf>`_
* :meth:`~tianshou.algorithm.BasePolicy.compute_episodic_return` `Generalized Advantage Estimator <https://arxiv.org/pdf/1506.02438.pdf>`_
* :class:`~tianshou.data.HERReplayBuffer` `Hindsight Experience Replay <https://arxiv.org/pdf/1707.01495.pdf>`_

Here is Tianshou's other features:

* Elegant framework, using only ~3000 lines of code
* State-of-the-art `MuJoCo benchmark <https://github.com/thu-ml/tianshou/tree/master/examples/mujoco>`_
* Support vectorized environment (synchronous or asynchronous) for all algorithms: :ref:`parallel_sampling`
* Support super-fast vectorized environment `EnvPool <https://github.com/sail-sg/envpool/>`_ for all algorithms: :ref:`envpool_integration`
* Support recurrent state representation in actor network and critic network (RNN-style training for POMDP): :ref:`rnn_training`
* Support any type of environment state/action (e.g. a dict, a self-defined class, ...): :ref:`self_defined_env`
* Support :ref:`customize_training`
* Support n-step returns estimation :meth:`~tianshou.algorithm.BasePolicy.compute_nstep_return` and prioritized experience replay :class:`~tianshou.data.PrioritizedReplayBuffer` for all Q-learning based algorithms; GAE, nstep and PER are very fast thanks to numba jit function and vectorized numpy operation
* Support :doc:`/01_tutorials/04_tictactoe`
* Support both `TensorBoard <https://www.tensorflow.org/tensorboard>`_ and `W&B <https://wandb.ai/>`_ log tools
* Support multi-GPU training :ref:`multi_gpu`
* Comprehensive `unit tests <https://github.com/thu-ml/tianshou/actions>`_, including functional checking, RL pipeline checking, documentation checking, PEP8 code-style checking, and type checking

Installation
------------

Tianshou is currently hosted on `PyPI <https://pypi.org/project/tianshou/>`_ and `conda-forge <https://github.com/conda-forge/tianshou-feedstock>`_. New releases
(and the current state of the master branch) will require Python >= 3.11.

You can simply install Tianshou from PyPI with the following command:

.. code-block:: bash

    $ pip install tianshou

If you use Anaconda or Miniconda, you can install Tianshou from conda-forge through the following command:

.. code-block:: bash

    $ conda install tianshou -c conda-forge

You can also install with the newest version through GitHub:

.. code-block:: bash

    $ pip install git+https://github.com/thu-ml/tianshou.git@master --upgrade

After installation, open your python console and type
::

    import tianshou
    print(tianshou.__version__)

If no error occurs, you have successfully installed Tianshou.

Tianshou is still under development, you can also check out the documents in stable version through `tianshou.readthedocs.io/en/stable/ <https://tianshou.readthedocs.io/en/stable/>`_.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
