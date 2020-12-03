import numpy as np
import pandas as pd

from evalml.model_family import ModelFamily
from evalml.pipelines.components.estimators import Estimator
from evalml.problem_types import ProblemTypes
from evalml.utils.gen_utils import (
    _convert_to_woodwork_structure,
    _convert_woodwork_types_wrapper
)


class TimeSeriesBaselineRegressor(Estimator):
    """Time series regressor that predicts using the naive forecasting approach.

    This is useful as a simple baseline regressor for time series problems
    """
    name = "Time Series Baseline Regressor"
    hyperparameter_ranges = {}
    model_family = ModelFamily.BASELINE
    supported_problem_types = [ProblemTypes.TIME_SERIES_REGRESSION]

    def __init__(self, random_state=0, **kwargs):
        """Baseline time series regressor that predicts using the naive forecasting approach.

        Arguments:
            random_state (int, np.random.RandomState): seed for the random number generator

        """

        self._prediction_value = None
        self._num_features = None
        self.y_hat = None

        parameters = {}
        parameters.update(kwargs)
        super().__init__(parameters=parameters,
                         component_obj=None,
                         random_state=random_state)

    def fit(self, X, y=None):
        if X is None:
            X = pd.DataFrame()
        X = _convert_to_woodwork_structure(X)
        X = _convert_woodwork_types_wrapper(X.to_dataframe())

        self._num_features = X.shape[1]
        return self

    def predict(self, X, y=None):
        if X is None:
            X = pd.DataFrame()
        if y is None:
            raise ValueError("Cannot predict Time Series Baseline Regressor if y is None")
        X = _convert_to_woodwork_structure(X)
        X = _convert_woodwork_types_wrapper(X.to_dataframe())
        y = _convert_to_woodwork_structure(y)
        y = _convert_woodwork_types_wrapper(y.to_series())

        first = y.iloc[0]
        y_hat = y.shift(periods=1)
        y_hat.iloc[0] = first

        return y_hat

    @property
    def feature_importance(self):
        """Returns importance associated with each feature. Since baseline regressors do not use input features to calculate predictions, returns an array of zeroes.

        Returns:
            np.ndarray (float): an array of zeroes

        """
        return np.zeros(self._num_features)