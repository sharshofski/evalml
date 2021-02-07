from unittest.mock import patch

import featuretools as ft
import pandas as pd
import pytest
import woodwork as ww
from pandas.testing import assert_frame_equal

from evalml.pipelines.components import DFSTransformer


def test_index_errors(X_y_binary):
    with pytest.raises(TypeError, match="Index provided must be string"):
        DFSTransformer(index=0)

    with pytest.raises(TypeError, match="Index provided must be string"):
        DFSTransformer(index=None)


def test_numeric_columns(X_y_multi):
    X, y = X_y_multi
    X_pd = pd.DataFrame(X)

    feature = DFSTransformer()
    feature.fit(X_pd, y)
    feature.transform(X_pd)


@patch('evalml.pipelines.components.transformers.preprocessing.featuretools.dfs')
@patch('evalml.pipelines.components.transformers.preprocessing.featuretools.calculate_feature_matrix')
def test_featuretools_index(mock_calculate_feature_matrix, mock_dfs, X_y_multi):
    X, y = X_y_multi
    X_pd = pd.DataFrame(X)
    X_new_index = X_pd.copy()
    index = [i for i in range(len(X))]
    new_index = [i * 2 for i in index]
    X_new_index['index'] = new_index
    mock_calculate_feature_matrix.return_value = pd.DataFrame({})

    # check if _make_entity_set keeps the intended index
    feature = DFSTransformer()
    feature.fit(X_new_index)
    feature.transform(X_new_index)
    arg_es = mock_dfs.call_args[1]['entityset'].entities[0].df['index']
    arg_tr = mock_calculate_feature_matrix.call_args[1]['entityset'].entities[0].df['index']
    assert arg_es.to_list() == new_index
    assert arg_tr.to_list() == new_index

    # check if _make_entity_set fills in the proper index values
    feature.fit(X_pd)
    feature.transform(X_pd)
    arg_es = mock_dfs.call_args[1]['entityset'].entities[0].df['index']
    arg_tr = mock_calculate_feature_matrix.call_args[1]['entityset'].entities[0].df['index']
    assert arg_es.to_list() == index
    assert arg_tr.to_list() == index


def test_transform(X_y_binary, X_y_multi, X_y_regression):
    datasets = locals()
    for dataset in datasets.values():
        X, y = dataset
        X_pd = pd.DataFrame(X)
        X_pd.columns = X_pd.columns.astype(str)
        es = ft.EntitySet()
        es = es.entity_from_dataframe(entity_id="X", dataframe=X_pd, index='index', make_index=True)
        feature_matrix, features = ft.dfs(entityset=es, target_entity="X")

        feature = DFSTransformer()
        feature.fit(X)
        X_t = feature.transform(X)

        assert_frame_equal(feature_matrix, X_t.to_dataframe())
        assert features == feature.features

        feature.fit(X, y)
        feature.transform(X)

        X_ww = ww.DataTable(X_pd)
        feature.fit(X_ww)
        feature.transform(X_ww)


def test_transform_subset(X_y_binary, X_y_multi, X_y_regression):
    datasets = locals()
    for dataset in datasets.values():
        X, y = dataset
        X_pd = pd.DataFrame(X)
        X_pd.columns = X_pd.columns.astype(str)
        X_fit = X_pd.iloc[: len(X) // 3]
        X_transform = X_pd.iloc[len(X) // 3:]

        es = ft.EntitySet()
        es = es.entity_from_dataframe(entity_id="X", dataframe=X_transform, index='index', make_index=True)
        feature_matrix, features = ft.dfs(entityset=es, target_entity="X")

        feature = DFSTransformer()
        feature.fit(X_fit)
        X_t = feature.transform(X_transform)

        assert_frame_equal(feature_matrix, X_t.to_dataframe())


from woodwork.logical_types import Integer, Double, Categorical, NaturalLanguage, Boolean, Datetime
import woodwork as ww
@pytest.mark.parametrize("logical_type, X_df", [(ww.logical_types.Datetime, pd.DataFrame(pd.to_datetime(['20190902', '20200519', '20190607'], format='%Y%m%d'))),
(ww.logical_types.Integer,pd.DataFrame(pd.Series([1, 2, 3], dtype="Int64"))),
(ww.logical_types.Double, pd.DataFrame(pd.Series([1., 2., 3.], dtype="Float64"))),
(ww.logical_types.Categorical, pd.DataFrame(pd.Series(['a', 'b', 'a'], dtype="category"))),
(ww.logical_types.NaturalLanguage, pd.DataFrame(pd.Series(['this will be a natural language column because length', 'yay', 'hay'], dtype="string"))),
])
def test_ft_woodwork_custom_overrides_returned_by_components(logical_type, X_df):
    y = pd.Series([1, 2, 1])
    types_to_test = [Integer, Double, Categorical, NaturalLanguage, Datetime, Boolean]
    for l in types_to_test:
        X = None
        override_dict = {0: l}
        try:
            X = ww.DataTable(X_df.copy(), logical_types=override_dict)
            assert X.logical_types[0] == l
        except TypeError:
            continue
        print ("testing override", logical_type, "with", l)
        dft = DFSTransformer()
        dft.fit(X, y)
        transformed = dft.transform(X, y)
        assert isinstance(transformed, ww.DataTable)
        input_logical_types = {'0':l}
        print ("transformed", transformed.logical_types.items())
        print ("expected", input_logical_types.items())

        assert transformed.logical_types == {'0': l}
