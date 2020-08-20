import logging
import re
from typing import List

import pandas as pd
from pandas import DataFrame, Series

from .abstract import AbstractFeatureGenerator
from .binned import BinnedFeatureGenerator
from ..feature_metadata import S_TEXT, S_TEXT_SPECIAL

logger = logging.getLogger(__name__)


class TextSpecialFeatureGenerator(AbstractFeatureGenerator):
    """
    TextSpecialFeatureGenerator generates text specific features from incoming raw text features.
    These include word counts, character counts, symbol counts, capital letter ratios, and much more.
    Features generated by this generator will have 'text_special' as a special type.

    Parameters
    ----------
    symbols : List[str], optional
        List of string symbols to compute counts and ratios for as features.
        If not specified, defaults to ['!', '?', '@', '%', '$', '*', '&', '#', '^', '.', ':', ' ', '/', ';', '-', '=']
    bin_features : bool, default True
        If True, adds a BinnedFeatureGenerator to the front of post_generators such that all features generated from this generator are then binned.
        This is useful for 'text_special' features because it lowers the chance models will overfit on the features and reduces their memory usage.
    post_drop_duplicates : bool, default True
        Identical to AbstractFeatureGenerator's post_drop_duplicates, except it is defaulted to True instead of False.
        This helps to clean the output of this generator when symbols aren't present in the data.
    **kwargs :
        Refer to AbstractFeatureGenerator documentation for details on valid key word arguments.
    """
    def __init__(self, symbols: List[str] = None, bin_features: bool = True, post_drop_duplicates: bool = True, **kwargs):
        super().__init__(post_drop_duplicates=post_drop_duplicates, **kwargs)
        if symbols is None:
            symbols = ['!', '?', '@', '%', '$', '*', '&', '#', '^', '.', ':', ' ', '/', ';', '-', '=']
        self._symbols = symbols  # Symbols to generate count and ratio features for.
        if bin_features:
            self._post_generators = [BinnedFeatureGenerator(inplace=True)] + self._post_generators

    def _fit_transform(self, X: DataFrame, **kwargs) -> (DataFrame, dict):
        X_out = self._transform(X)
        type_family_groups_special = {
            S_TEXT_SPECIAL: list(X_out.columns)
        }
        return X_out, type_family_groups_special

    def _transform(self, X: DataFrame) -> DataFrame:
        return self._generate_features_text_special(X)

    @staticmethod
    def get_default_infer_features_in_args() -> dict:
        return dict(required_special_types=[S_TEXT])

    def _generate_features_text_special(self, X: DataFrame) -> DataFrame:
        if self.features_in:
            X_text_special_combined = []
            for nlp_feature in self.features_in:
                df_text_special = self._generate_text_special(X[nlp_feature], nlp_feature)
                X_text_special_combined.append(df_text_special)
            X_text_special_combined = pd.concat(X_text_special_combined, axis=1)
        else:
            X_text_special_combined = pd.DataFrame(index=X.index)
        return X_text_special_combined

    def _generate_text_special(self, X: Series, feature: str) -> DataFrame:
        X_text_special: DataFrame = DataFrame(index=X.index)
        X_text_special[feature + '.char_count'] = [self.char_count(value) for value in X]
        X_text_special[feature + '.word_count'] = [self.word_count(value) for value in X]
        X_text_special[feature + '.capital_ratio'] = [self.capital_ratio(value) for value in X]
        X_text_special[feature + '.lower_ratio'] = [self.lower_ratio(value) for value in X]
        X_text_special[feature + '.digit_ratio'] = [self.digit_ratio(value) for value in X]
        X_text_special[feature + '.special_ratio'] = [self.special_ratio(value) for value in X]

        for symbol in self._symbols:
            X_text_special[feature + '.symbol_count.' + symbol] = [self.symbol_in_string_count(value, symbol) for value in X]
            X_text_special[feature + '.symbol_ratio.' + symbol] = X_text_special[feature + '.symbol_count.' + symbol] / X_text_special[feature + '.char_count']
            X_text_special[feature + '.symbol_ratio.' + symbol].fillna(0, inplace=True)

        return X_text_special

    @staticmethod
    def word_count(string: str) -> int:
        return len(string.split())

    @staticmethod
    def char_count(string: str) -> int:
        return len(string)

    @staticmethod
    def special_ratio(string: str) -> float:
        string = string.replace(' ', '')
        if not string:
            return 0
        new_str = re.sub(r'[\w]+', '', string)
        return len(new_str) / len(string)

    @staticmethod
    def digit_ratio(string: str) -> float:
        string = string.replace(' ', '')
        if not string:
            return 0
        return sum(c.isdigit() for c in string) / len(string)

    @staticmethod
    def lower_ratio(string: str) -> float:
        string = string.replace(' ', '')
        if not string:
            return 0
        return sum(c.islower() for c in string) / len(string)

    @staticmethod
    def capital_ratio(string: str) -> float:
        string = string.replace(' ', '')
        if not string:
            return 0
        return sum(1 for c in string if c.isupper()) / len(string)

    @staticmethod
    def symbol_in_string_count(string: str, character: str) -> int:
        if not string:
            return 0
        return sum(1 for c in string if c == character)
