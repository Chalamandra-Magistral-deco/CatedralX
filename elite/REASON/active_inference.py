"""Active-inference diagnostics for market-return surprise and variational free energy.

This module is analysis-only. It does not create signals, authorize trades, or
persist its adaptive prior across process restarts.
"""

from __future__ import annotations

import math
from typing import NamedTuple, Sequence

import numpy as np

MIN_SIGMA = 1e-6
MAX_SIGMA = 5.0
PRIOR_ALPHA = 0.05


class InferenceDiagnostics(NamedTuple):
    """Inspectable components of one Gaussian active-inference update."""

    kl_divergence: float
    variational_free_energy: float
    surprise: float
    posterior_mean: float
    posterior_sigma: float
    observed_log_return: float


class ActiveInferenceEngine:
    """Compare recent Gaussian returns with a bounded adaptive Gaussian prior.

    The prior is updated only after a complete, finite calculation. Its state is
    process-local; callers that need continuity must persist and validate it
    explicitly outside this analysis component.
    """

    def __init__(
        self,
        *,
        prior_mean: float = 0.0,
        prior_sigma: float = 0.01,
        learning_rate: float = PRIOR_ALPHA,
    ) -> None:
        self.mu_p = self._finite_number(prior_mean, "prior_mean")
        self.sigma_p = self._bounded_sigma(prior_sigma)
        self.learning_rate = self._finite_number(learning_rate, "learning_rate")
        if not 0.0 < self.learning_rate <= 1.0:
            raise ValueError("learning_rate debe estar en el intervalo (0, 1].")

    @staticmethod
    def _finite_number(value: float, name: str) -> float:
        if isinstance(value, (bool, np.bool_)):
            raise ValueError(f"{name} debe ser numérico y finito.")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} debe ser numérico y finito.") from exc
        if not math.isfinite(number):
            raise ValueError(f"{name} debe ser numérico y finito.")
        return number

    @staticmethod
    def _bounded_sigma(value: float) -> float:
        sigma = ActiveInferenceEngine._finite_number(value, "sigma")
        if sigma <= 0.0:
            raise ValueError("sigma debe ser estrictamente positiva.")
        return min(MAX_SIGMA, max(MIN_SIGMA, sigma))

    @staticmethod
    def _validated_returns(values: Sequence[float]) -> np.ndarray:
        if isinstance(values, (str, bytes)):
            raise ValueError("retornos_recientes debe ser una secuencia numérica.")
        try:
            raw_values = list(values)
        except TypeError as exc:
            raise ValueError("retornos_recientes debe ser una secuencia numérica.") from exc
        if any(isinstance(value, (bool, np.bool_)) for value in raw_values):
            raise ValueError("Los retornos booleanos no son válidos.")
        try:
            returns = np.asarray(raw_values, dtype=float)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Los retornos deben ser numéricos.") from exc
        if returns.ndim != 1 or returns.size < 2:
            raise ValueError("Se requieren al menos dos retornos en una secuencia 1D.")
        if not np.all(np.isfinite(returns)):
            raise ValueError("Todos los retornos deben ser finitos.")
        return returns

    def inferir_detallado(
        self,
        retornos_recientes: Sequence[float],
        precio_actual: float,
        precio_previo: float,
    ) -> InferenceDiagnostics:
        """Return KL, surprise and free-energy diagnostics, then update the prior."""
        returns = self._validated_returns(retornos_recientes)
        current = self._finite_number(precio_actual, "precio_actual")
        previous = self._finite_number(precio_previo, "precio_previo")
        if current <= 0.0 or previous <= 0.0:
            raise ValueError("Los precios deben ser estrictamente positivos.")

        mu_q = float(np.mean(returns))
        # A variance floor avoids a degenerate Gaussian for constant returns.
        raw_sigma_q = float(np.std(returns))
        if not math.isfinite(raw_sigma_q):
            raise ValueError("La volatilidad posterior no es finita.")
        sigma_q = min(MAX_SIGMA, max(MIN_SIGMA, raw_sigma_q))
        mu_p = self.mu_p
        sigma_p = self.sigma_p

        var_q = sigma_q * sigma_q
        var_p = sigma_p * sigma_p
        mean_delta = mu_q - mu_p
        # KL[N(mu_q,var_q) || N(mu_p,var_p)] for univariate Gaussians.
        d_kl_raw = 0.5 * (
            math.log(var_p / var_q)
            + (var_q + mean_delta * mean_delta) / var_p
            - 1.0
        )
        if not math.isfinite(d_kl_raw):
            raise ValueError("La divergencia KL no pudo calcularse de forma finita.")
        # The exact Gaussian KL is non-negative; clamp only floating-point noise.
        d_kl = max(0.0, d_kl_raw)

        observed_return = math.log(current / previous)
        z_score = (observed_return - mu_p) / sigma_p
        surprise = 0.5 * (z_score * z_score + math.log(2.0 * math.pi * var_p))
        free_energy = max(0.0, d_kl + surprise)
        if not all(math.isfinite(value) for value in (
            observed_return, surprise, free_energy, mu_q, sigma_q
        )):
            raise ValueError("El resultado de inferencia excede el rango numérico finito.")

        diagnostics = InferenceDiagnostics(
            kl_divergence=float(d_kl),
            variational_free_energy=float(free_energy),
            surprise=float(surprise),
            posterior_mean=mu_q,
            posterior_sigma=sigma_q,
            observed_log_return=observed_return,
        )

        alpha = self.learning_rate
        next_mu = (1.0 - alpha) * mu_p + alpha * mu_q
        next_sigma = self._bounded_sigma((1.0 - alpha) * sigma_p + alpha * sigma_q)
        if not math.isfinite(next_mu):
            raise ValueError("La actualización del prior produjo una media no finita.")
        self.mu_p = float(next_mu)
        self.sigma_p = float(next_sigma)
        return diagnostics

    def inferir(
        self,
        retornos_recientes: Sequence[float],
        precio_actual: float,
        precio_previo: float,
    ) -> tuple[float, float]:
        """Backward-compatible API: return (KL divergence, variational free energy)."""
        result = self.inferir_detallado(
            retornos_recientes, precio_actual, precio_previo
        )
        return result.kl_divergence, result.variational_free_energy


engine = ActiveInferenceEngine()
