def compute_score(values, window=36):
    prev_mean = values.rolling(window).mean().shift(1)
    prev_std = values.rolling(window).std().shift(1)
    score = ((values - prev_mean) / prev_std).abs()
    return score