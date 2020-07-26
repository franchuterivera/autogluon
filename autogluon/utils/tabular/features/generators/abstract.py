import logging

from ..types import get_type_family_groups_df
from ..feature_types_metadata import FeatureTypesMetadata

logger = logging.getLogger(__name__)


class AbstractFeatureGenerator:
    def __init__(self, features_in=None):
        # TODO TODO TODO TODO: Add name_prefix, name_suffix
        # TODO TODO TODO TODO: Add post_generators
        # TODO TODO TODO TODO: Add y to fit calls
        self._is_fit = False
        self.feature_types_metadata: FeatureTypesMetadata = None
        self.features_in = features_in
        self.features_out = None

    def fit(self, X):
        raise NotImplementedError

    def fit_transform(self, X):
        if self._is_fit:
            raise AssertionError('FeatureGenerator is already fit.')
        if self.features_in is None:
            self.features_in = list(X.columns)
        X_out, type_family_groups_special = self._fit_transform(X[self.features_in])
        self.features_out = list(X_out.columns)
        type_family_groups_raw = get_type_family_groups_df(X_out)
        self.feature_types_metadata = FeatureTypesMetadata(feature_types_raw=type_family_groups_raw, feature_types_special=type_family_groups_special)
        self._is_fit = True
        return X_out

    def transform(self, X):
        if not self._is_fit:
            raise AssertionError('FeatureGenerator is not fit.')
        return self._transform(X[self.features_in])

    def _fit_transform(self, X):
        raise NotImplementedError

    def _transform(self, X):
        raise NotImplementedError