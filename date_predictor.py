import pandas as pd
import numpy as np
from typing import Iterable, Union, Sequence

DateLike = Union[str, pd.Timestamp, np.datetime64, "datetime.datetime"]

class DatePredictor:
    """
    Enveloppe un modèle déjà entraîné et expose .predict(date ou [dates]).
    Nécessite: model (déjà fit), features (liste de colonnes), history (Series indexée par date).
    """
    def __init__(self, model, features, history, lags: Sequence[int]=(364, 728, 1092)):
        self.model = model
        self.features = list(features)
        if not isinstance(history.index, pd.DatetimeIndex):
            raise ValueError("history doit être indexé par DatetimeIndex.")
        self.history = history.sort_index().astype(float).copy()
        self.lags = tuple(lags)

    @staticmethod
    def _coerce_dates(dates: Union[DateLike, Iterable[DateLike]]) -> pd.DatetimeIndex:
        if isinstance(dates, (str, pd.Timestamp, np.datetime64)):
            idx = pd.DatetimeIndex([pd.to_datetime(dates, dayfirst=True)])
        else:
            idx = pd.DatetimeIndex(pd.to_datetime(list(dates), dayfirst=True))
        return idx.normalize()

    @staticmethod
    def _feat(idx: pd.DatetimeIndex) -> pd.DataFrame:
        X = pd.DataFrame(index=idx)
        X["jour"] = idx.day
        X["mois"] = idx.month
        X["annee"] = idx.year
        X["jour_de_la_semaine"] = idx.dayofweek
        return X

    def _add_lags(self, X: pd.DataFrame, history: pd.Series) -> pd.DataFrame:
        m = history.to_dict()
        for i, delta in enumerate(self.lags, start=1):
            X[f"lag{i}"] = (X.index - pd.Timedelta(days=delta)).map(m)
        return X

    def predict(self, dates: Union[DateLike, Iterable[DateLike]]):
        req_idx = self._coerce_dates(dates)
        hist = self.history.asfreq('D').ffill().copy()
        out = {}

        for current in sorted(req_idx):
            
            if current > hist.index.max():
                step = hist.index.max() + pd.Timedelta(days=1)
                while step <= current:
                    Xs = self._add_lags(self._feat(pd.DatetimeIndex([step])), hist)
                    if Xs.filter(like="lag").isna().any(axis=None):
                        missing = []
                        for d in self.lags:
                            back = step - pd.Timedelta(days=d)
                            if back not in hist.index: missing.append(back.strftime("%Y-%m-%d"))
                        raise ValueError(f"Impossible de prédire {step.date()}: lags manquants {missing}.")
                    yhat = float(self.model.predict(Xs[self.features])[0])
                    hist.loc[step] = yhat
                    step += pd.Timedelta(days=1)

            X = self._add_lags(self._feat(pd.DatetimeIndex([current])), hist)
            if X.filter(like="lag").isna().any(axis=None):
                missing = []
                for d in self.lags:
                    back = current - pd.Timedelta(days=d)
                    if back not in hist.index: missing.append(back.strftime("%Y-%m-%d"))
                raise ValueError(f"Lags manquants pour {current.date()}: {missing}.")
            out[current] = float(self.model.predict(X[self.features])[0])

        return list(out.values())[0] if len(req_idx) == 1 else pd.Series(out).sort_index()
