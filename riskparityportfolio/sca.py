import warnings
import tensorflow as tf
import numpy as np
import osqp
from scipy.sparse import csc_matrix


__all__ = ['RiskParityPortfolio']


class RiskParityPortfolio:

    def __init__(self, covariance, budget=None,
                 equality_constraints=None, inequality_constraints=None):
        self.covariance = covariance
        self.budget = budget
        self.validate_problem()

    @property
    def weights(self):
        return self._weights

    @weights.setter
    def weights(self, value)
        if value is None:
            self._weights = tf.ones(self.number_of_assets) / self.number_of_assets
        try:
            self._weights = tf.convert_to_tensor(weights)
        except e:
            raise e

    @property
    def number_of_assets(self):
        return self.covariance.shape[0]

    @property
    def risk_concentration(self):
        return self._risk_concentration

    @risk_concentration.setter
    def risk_concentration(self, value):
        self._risk_concentration = RiskContribOverBudgetDoubleIndex(weights=self.weights,
                                                                    covariance=self.covariance,
                                                                    budget=self.budget)

    @property
    def budget(self):
        return self._budget

    @budget.setter
    def budget(self, value):
        if value is None:
            self._budget = tf.ones(self.number_of_assets) / self.number_of_assets
        else:
            try:
                self._budget = tf.convert_to_tensor(value)
            except e:
                raise e

    @property
    def covariance(self):
        return self._covariance

    @covariance.setter
    def covariance(self, value):
        if value.shape[0] != value.shape[1]:
            raise ValueError("shape mismatch: covariance matrix is not a square matrix")
        else:
            try:
                self._covariance = tf.convert_to_tensor(value)
            except e:
                raise e
            eigvals = np.linalg.eigvals(self._covariance.numpy())
            eigvals = np.sort(eigvals)
            if abs(eigvals[0] / eigvals[-1]) < 1e-6:
                warnings.warn("covariance matrix maybe singular")

    @property
    def equality_constraints(self):
        return self._equality_constraints

    @property
    def inequality_constraints(self):
        return self._inequality_constraints

    @property
    def box_constraints(self):
        return self._box_constraints

    def validate_problem(self):
        if self.covariance.shape[0] != self.budget.shape[0]:
            raise ValueError("shape mismatch between covariance matrix and budget vector")

    def design(self):
        sca = SucessiveConvexOptimizer(self)
        sca.solve()


class SuccessiveConvexOptimizer:
    """
    Successive Convex Approximation optimizer taylored for the risk parity problem.
    """

    def __init__(self, portfolio, tau = None, gamma = 0.9, zeta = 1E-7, funtol = 1E-6,
                 wtol = 1E-6, maxiter = 5000):

    @property
    def tau(self):
        return self._tau

    @tau.setter
    def tau(self, value):
        if value is None:
            self._tau = 0.05 * np.sum(np.diag(portfolio.covariance.numpy())) / (2 * portfolio.size)


    @property
    def qp_solver(self):
        return self._qp_solver

    @qp_solver.setter
    def qp_solver(self, value)
        if value is None:
            self._qp_solver = osqp.OSQP()

    def iterate(self):
        wk = portfolio.weights
        g = portfolio.formulation.risk_concentration_vector()
        A = portfolio.formulation.jacobian_risk_concentration_vector()
        At = tf.transpose(A)
        Q = 2 * A @ At + self.tau * tf.eye(portfolio.number_of_assets)
        q = 2 * At @ g - Q @ wk
        w_hat = tf.convert_to_tensor(self.qp_solver.setup(P=csc_matrix(Q.numpy()),
                                     q=q.numpy(),
                                     A=csc_matrix(tf.eye(portfolio.size).numpy()),
                                     l=tf.ones(portfolio.number_of_assets).numpy(),
                                     u=tf.ones(portfolio.number_of_assets).numpy()).solve().x)
        portfolio.weights = wk + self.gamma * (w_hat - wk)
        has_converged = (tf.abs(portfolio.weights - wk) <=
                         .5 * self.wtol * (tf.abs(portfolio) + tf.abs(wk))).numpy().all()
        return not has_converged

    def solve(self):
        i = 0
        while(self.iterate() and i < maxiter) i += 1


def project_line_and_box(weights, lower_bound, upper_bound):
    def objective_function(variable, weights):
        pass