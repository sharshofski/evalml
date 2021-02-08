from evalml.data_checks import (
    DataCheck,
    DataCheckMessageCode,
    DataCheckWarning
)
from evalml.problem_types import ProblemTypes, handle_problem_types
from evalml.utils.gen_utils import (
    _convert_to_woodwork_structure,
    _convert_woodwork_types_wrapper
)

warning_too_unique = "Input columns ({}) for {} problem type are too sparse."


class SparsityDataCheck(DataCheck):
    """Checks if there are any columns with sparsely populated values in the input."""

    def __init__(self, problem_type, threshold, unique_count_threshold=10):
        """Checks each column in the input to determine the sparsity of the values in those columns.
        Arguments:
            problem_type (str or ProblemTypes): The specific problem type to data check for.
                'binary', 'multiclass' are the only accepted problem types.
            threshold(float): The threshold value, below which, a data field is considered "sparse."
        """
        self.problem_type = handle_problem_types(problem_type)
        if self.problem_type not in [ProblemTypes.BINARY, ProblemTypes.MULTICLASS, ProblemTypes.TIME_SERIES_BINARY, ProblemTypes.TIME_SERIES_MULTICLASS]:
            raise ValueError("Sparsity is only defined for binary or multiclass problem types.")
        self.threshold = threshold
        if threshold < 0 or threshold > 1:
            raise ValueError("Threshold must be a float between 0 and 1, inclusive.")
        self.unique_count_threshold = unique_count_threshold
        if unique_count_threshold < 0 or not isinstance(unique_count_threshold, int):
            raise ValueError("Unique count threshold must be positive integer.")

    def validate(self, X, y=None):
        """Checks if there are any sparse columns in the input.
        Arguments:
            X (ww.DataTable, pd.DataFrame, np.ndarray): Features
            y (ww.DataColumn, pd.Series, np.ndarray): Ignored.
        Returns:
            dict: dict with a DataCheckWarning if there are any sparse columns.
        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({
            ...    'sparse': [float(x) for x in range(100)],
            ...    'not_sparse': [float(1) for x in range(100)]
            ... })
            >>> sparsity_check = SparsityDataCheck(problem_type="multiclass", threshold=0.5, unique_count_threshold=10)
            >>> assert sparsity_check.validate(df) == {"errors": [],\
                                                         "warnings": [{"message": "Input columns (sparse) for multiclass problem type are too sparse.",\
                                                                 "data_check_name": "SparsityDataCheck",\
                                                                 "level": "warning",\
                                                                 "code": "TOO_SPARSE",\
                                                                 "details": {"column": "sparse", 'sparsity_score': 0.0}}]}
        """
        messages = {
            "warnings": [],
            "errors": []
        }

        X = _convert_to_woodwork_structure(X)
        X = _convert_woodwork_types_wrapper(X.to_dataframe())
        #
        # res = SparsityDataCheck.sparsity_score(X, count_threshold=self.unique_count_threshold)
        res = X.apply(SparsityDataCheck.sparsity_score, count_threshold=self.unique_count_threshold)
        too_sparse_cols = [col for col in res.index[res < self.threshold]]
        messages["warnings"].extend([DataCheckWarning(message=warning_too_unique.format(col_name,
                                                                                        self.problem_type),
                                                      data_check_name=self.name,
                                                      message_code=DataCheckMessageCode.TOO_SPARSE,
                                                      details={"column": col_name, "sparsity_score": res.loc[col_name]}).to_dict()
                                     for col_name in too_sparse_cols])
        return messages

    @staticmethod
    def sparsity_score(col, count_threshold=10):
        """
            This function calculates a sparsity score for the given value counts by finding values with fewer than n=10
            occurrences, normalizing by the number of categories, and subtracting this value from 1.
            :param counts: result of value_counts on column
            :return: calculated sparsity score
        """
        counts = col.value_counts()
        score = 1 - (sum(counts <= count_threshold) / counts.size)

        return score
