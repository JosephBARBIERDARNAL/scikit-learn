# Authors: The scikit-learn developers
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np

from sklearn.base import is_classifier

from ...utils._plotting import _BinaryClassifierCurveDisplayMixin


class CapCurveDisplay(_BinaryClassifierCurveDisplayMixin):
    """Cumulative Accuracy Profile (CAP) Curve visualization.

    It is recommended to use
    :func:`~sklearn.metrics.CapCurveDisplay.from_estimator` or
    :func:`~sklearn.metrics.CapCurveDisplay.from_predictions` to create
    a :class:`~sklearn.metrics.CapCurveDisplay`. All parameters are
    stored as attributes.

    Read more in the :ref:`User Guide <visualizations>`.

    Parameters
    ----------
    y_true_cumulative : ndarray
        Cumulative number of true positives.

    cumulative_total : ndarray
        Cumulative number of cases examined.

    estimator_name : str, default=None
        Name of estimator. If None, the estimator name is not shown.

    pos_label : int, float, bool or str, default=None
        The class considered as the positive class when computing the metrics.
        By default, `estimators.classes_[1]` is considered as the positive class.

    Attributes
    ----------
    line_ : matplotlib Artist
        CAP Curve.

    ax_ : matplotlib Axes
        Axes with CAP Curve.

    figure_ : matplotlib Figure
        Figure containing the curve.
    """

    def __init__(
        self,
        *,
        y_true_cumulative,
        cumulative_total,
        estimator_name=None,
        pos_label=None,
    ):
        self.estimator_name = estimator_name
        self.y_true_cumulative = y_true_cumulative
        self.cumulative_total = cumulative_total
        self.pos_label = pos_label

    def plot(
        self,
        ax=None,
        *,
        normalize_scale=True,
        name=None,
        plot_chance_level=True,
        chance_level_kw=None,
        **kwargs,
    ):
        """Plot visualization.

        Extra keyword arguments will be passed to matplotlib's ``plot``.

        Parameters
        ----------
        ax : matplotlib axes, default=None
            Axes object to plot on. If `None`, a new figure and axes is created.

        name : str, default=None
            Name of CAP Curve for labeling. If `None`, use `estimator_name` if
            not `None`, otherwise no labeling is shown.

        **kwargs : dict
            Keyword arguments to be passed to matplotlib's `plot`.

        Returns
        -------
        display : :class:`~sklearn.metrics.CapCurveDisplay`
            Object that stores computed values.
        """

        self.ax_, self.figure_, name = self._validate_plot_params(ax=ax, name=name)

        if normalize_scale:
            self.y_true_cumulative = self.y_true_cumulative / self.y_true_cumulative[-1]
            self.cumulative_total = self.cumulative_total / self.cumulative_total[-1]
            self.ax_.set_xlim(-0.01, 1.01)
            self.ax_.set_ylim(-0.01, 1.01)
        else:
            x_max = self.cumulative_total[-1]
            y_max = self.y_true_cumulative[-1]
            self.ax_.set_xlim(0, x_max * 1.05)
            self.ax_.set_ylim(0, y_max * 1.05)

        line_kwargs = {"label": name} if name is not None else {}
        line_kwargs.update(**kwargs)

        chance_level_line_kw = {
            "label": "Change level",
            "color": "k",
            "linestyle": "--",
        }
        if chance_level_kw is not None:
            chance_level_line_kw.update(**chance_level_kw)

        (self.line_,) = self.ax_.plot(
            self.cumulative_total, self.y_true_cumulative, **line_kwargs
        )

        if plot_chance_level:
            (self.chance_level_,) = self.ax_.plot(
                (0, 1), (0, 1), **chance_level_line_kw
            )
        else:
            self.chance_level_ = None

        xlabel = "Total Cases Examined"
        ylabel = "Cumulative True Positives"
        self.ax_.set(xlabel=xlabel, ylabel=ylabel, aspect="equal")

        if "label" in line_kwargs:
            self.ax_.legend(loc="lower right")

        return self

    @classmethod
    def from_predictions(
        cls,
        y_true,
        y_pred,
        *,
        sample_weight=None,
        pos_label=None,
        normalize_scale=True,
        plot_chance_level=False,
        name=None,
        ax=None,
        **kwargs,
    ):
        """Plot the Cumulative Accuracy Profile.

        This is also known as a (cumulative) gain curve.

        Parameters
        ----------
        y_true : array-like of shape (n_samples,)
            True labels.

        y_pred : array-like of shape (n_samples,)
            Target scores, can either be probability estimates of the positive
            class, confidence values, or non-thresholded measure of decisions
            (as returned by “decision_function” on some classifiers).

        sample_weight : array-like of shape (n_samples,), default=None
            Sample weights.

        pos_label : int, float, bool or str, default=None
            The label of the positive class. When `pos_label=None`, if `y_true`
            is in {-1, 1} or {0, 1}, `pos_label` is set to 1, otherwise an
            error will be raised.

        name : str, default=None
            Name of CAP curve for labeling. If `None`, name will be set to
            `"Classifier"`.

        ax : matplotlib axes, default=None
            Axes object to plot on. If `None`, a new figure and axes is created.

        **kwargs : dict
            Additional keywords arguments passed to matplotlib `plot` function.

        Returns
        -------
        display : :class:`~sklearn.metrics.CapCurveDisplay`
            Object that stores computed values.
        """
        if pos_label is None:
            pos_label = 1
        if sample_weight is None:
            sample_weight = np.ones_like(y_true, dtype=float)

        # ensure y_true is boolean for positive class identification
        y_bool = y_true == pos_label

        # sort predictions and true values based on the predictions
        sorted_indices = np.argsort(y_pred)[::-1]
        y_true_sorted = y_bool[sorted_indices]
        sample_weight_sorted = sample_weight[sorted_indices]

        # compute cumulative sums for true positives and all cases
        y_true_cumulative = np.cumsum(y_true_sorted * sample_weight_sorted)
        cumulative_total = np.cumsum(sample_weight_sorted)

        viz = cls(
            y_true_cumulative=y_true_cumulative,
            cumulative_total=cumulative_total,
            estimator_name=name,
            pos_label=pos_label,
        )

        return viz.plot(
            ax=ax,
            name=name,
            normalize_scale=normalize_scale,
            plot_chance_level=plot_chance_level,
            **kwargs,
        )

    @classmethod
    def from_estimator(
        cls,
        estimator,
        X,
        y,
        *,
        sample_weight=None,
        response_method="auto",
        pos_label=None,
        normalize_scale=True,
        plot_chance_level=False,
        name=None,
        ax=None,
        **kwargs,
    ):
        """Create the Cumulative Accuracy Profile.

        This is also known as a (cumulative) gain curve.

        Parameters
        ----------
        estimator : BaseEstimator
            A fitted estimator object implementing :term:`predict`,
            :term:`predict_proba`, or :term:`decision_function`.
            Multiclass classifiers are not supported.

        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Input values.

        y : array-like of shape (n_samples,)
            Target values.

        sample_weight : array-like of shape (n_samples,), default=None
            Sample weights.

        response_method : {'predict_proba', 'decision_function', 'auto'} \
                default='auto'
            Specifies whether to use :term:`predict_proba` or
            :term:`decision_function` as the target response. For regressors
            this parameter is ignored and the response is always the output of
            :term:`predict`. By default, :term:`predict_proba` is tried first
            and we revert to :term:`decision_function` if it doesn't exist.

        pos_label : int, float, bool or str, default=None
            The class considered as the positive class when computing CAP.
            By default, `estimators.classes_[1]` is considered as the positive class.

        name : str, default=None
            Name of CAP Curve for labeling. If `None`, use the name of the estimator.

        ax : matplotlib axes, default=None
            Axes object to plot on. If `None`, a new figure and axes is created.

        **kwargs : dict
            Keyword arguments to be passed to matplotlib's `plot`.

        Returns
        -------
        display : :class:`~sklearn.metrics.CapCurveDisplay`
            The CAP Curve display.
        """

        if response_method == "auto":
            if hasattr(estimator, "predict_proba"):
                response_method = "predict_proba"
            elif hasattr(estimator, "decision_function"):
                response_method = "decision_function"
            else:
                raise ValueError(
                    "Estimator does not have a predict_proba or decision_function"
                    " method."
                )

        if not is_classifier(estimator):
            y_pred = estimator.predict(X)
        elif response_method == "predict_proba":
            probabilities = estimator.predict_proba(X)
            if pos_label is None:  # assuming positive class is the second column
                pos_label = 1
            class_index = np.where(estimator.classes_ == pos_label)[0][0]
            y_pred = probabilities[:, class_index]
        elif response_method == "decision_function":
            y_pred = estimator.decision_function(X)

        if name is None:
            name = estimator.__class__.__name__

        return cls.from_predictions(
            y_true=y,
            y_pred=y_pred,
            sample_weight=sample_weight,
            name=name,
            normalize_scale=normalize_scale,
            plot_chance_level=plot_chance_level,
            ax=ax,
            pos_label=pos_label,
            **kwargs,
        )
