import gym
from gym import spaces
from gym.utils import seeding

import autograd.numpy as np


class _CartpoleBase:

    def __init__(self, dt, xw, uw, goal):
        self.nb_xdim = 4
        self.nb_udim = 1

        self._dt = dt
        self._g = goal

        self._xw = xw
        self._uw = uw

        self.xmax = np.array([np.inf, 100., np.inf, 25.0])
        self.umax = 5.0

        self.sigma = 1.e-4 * np.eye(self.nb_xdim)

    def dynamics(self, x, u):
        # x = [x, th, dx, dth]
        g = 9.81
        Mc = 0.37
        Mp = 0.127
        Mt = Mc + Mp
        l = 0.3365

        th = x[1]
        dth2 = np.power(x[3], 2)
        sth = np.sin(th)
        cth = np.cos(th)

        _num = - Mp * l * sth * dth2 + Mt * g * sth - u * cth
        _denom = l * ((4. / 3.) * Mt - Mp * cth ** 2)
        th_acc = _num / _denom
        x_acc = (Mp * l * sth * dth2 - Mp * l * th_acc * cth + u) / Mt

        xn = np.hstack((x[0] + self._dt * (x[2] + self._dt * x_acc),
                       x[1] + self._dt * (x[3] + self._dt * th_acc),
                       x[2] + self._dt * x_acc,
                       x[3] + self._dt * th_acc))
        return xn

    def reward(self, x, u, a):
        if a:
            return (x - self._g).T @ np.diag(self._xw) @ (x - self._g) + u.T @ np.diag(self._uw) @ u
        else:
            return u.T @ np.diag(self._uw) @ u

    def initialize(self):
        # mu, sigma
        return np.array([0., np.pi, 0., 0.]), 1.e-4 * np.eye(self.nb_xdim)


class Cartpole(gym.Env):

    def __init__(self):
        self._dt = 0.01
        self._xw = - self._dt * 1. * np.array([1e-1, 1e1, 1e-1, 1.e-1])
        self._uw = - self._dt * 1. * np.array([1.e-3])
        self._g = np.array([0., 2. * np.pi, 0., 0.])

        self._model = _CartpoleBase(self._dt, self._xw, self._uw, self._g)

        self.low_state = - self.model.xmax
        self.high_state = self.model.xmax

        self.action_space = spaces.Box(low=-self.model.umax,
                                       high=self.model.umax, shape=(1,))

        self.observation_space = spaces.Box(low=self.low_state,
                                            high=self.high_state)

        self.seed()
        self.reset()

    @property
    def model(self):
        return self._model

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, u):
        self.state = self.model.dynamics(self.state, u)
        self.state = self.np_random.multivariate_normal(mean=self.state, cov=self.model.sigma)
        return self.state, [], False, {}

    def reset(self):
        _mu_0, _sigma_0 = self._model.initialize()
        self.state = self.np_random.multivariate_normal(mean=_mu_0, cov=_sigma_0)
        return self.state