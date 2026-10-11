"""Cheap original count corruptions and complete-JSON lexical role features."""

import re
from random import Random

import numpy as np


def roles(text, offsets):
    labels = [3] * len(text)
    i = 0
    while i < len(text):
        if text[i] == '"':
            start = i
            i += 1
            while i < len(text):
                if text[i] == "\\":
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            labels[start:i] = [1] * (i - start)
        elif text[i] in "{}[],:":
            labels[i] = 0
            i += 1
        elif text[i] == "-" or text[i].isdigit():
            match = re.match(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?", text[i:])
            if match is None:
                raise ValueError("invalid JSON number")
            size = len(match.group())
            labels[i : i + size] = [2] * size
            i += size
        else:
            i += 1
    return np.array([next((c for c in (1, 0, 2) if c in labels[a:b]), 3) for a, b in offsets])


def corruption(seed, n):
    rng = Random(seed)
    k = rng.randrange(1, n + 1)
    mask = np.zeros(n, dtype=bool)
    mask[rng.sample(range(n), k)] = True
    return mask


def features(mask, role):
    ratios = [mask.mean()]
    ratios.extend(mask[role == c].mean() if np.any(role == c) else 0.0 for c in range(4))
    return np.r_[1.0, mask.astype(float), np.square(ratios)]


def fit_proxy(x, y):
    """Fixed ridge and deterministic four-center proxy; no current-score access."""
    scale = np.maximum(y.std(axis=0), 1e-8)
    target = y / scale
    penalty = np.eye(x.shape[1])
    penalty[0, 0] = 0
    beta = np.linalg.solve(x.T @ x + penalty, x.T @ target)
    predicted = x @ beta
    centers = [predicted[0]]
    for _ in range(3):
        distance = np.min(
            np.sum((predicted[:, None] - np.array(centers)[None]) ** 2, axis=-1), axis=1
        )
        centers.append(predicted[np.argmax(distance)])
    centers = np.array(centers)
    for _ in range(20):
        labels = np.argmin(np.sum((predicted[:, None] - centers[None]) ** 2, axis=-1), axis=1)
        for c in range(4):
            if np.any(labels == c):
                centers[c] = predicted[labels == c].mean(axis=0)
    return beta, centers


def classify(x, beta, centers):
    return np.argmin(np.sum((x @ beta - centers) ** 2, axis=-1), axis=-1)
