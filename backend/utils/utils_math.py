import math
import numpy as np


def haversine(lat1, lon1, lat2, lon2):
    """
    计算两点之间的球面距离（单位：公里）
    使用 Haversine 公式
    """
    R = 6371  # 地球半径（单位：公里）

    # 角度转换为弧度
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # 计算差值
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine 公式计算
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # 计算距离
    distance = R * c
    return distance


def haversine_vectorized(lat1: float, lon1: float,
                         lat2: np.ndarray, lon2: np.ndarray):
    """
    计算两组经纬度之间的球面距离（单位：公里）
    使用 NumPy 进行矢量化加速计算
    @param lat1: current latitude
    @param lon1: current longitude
    @param lat2: target latitude
    @param lon2: target longitude
    @return: distance between two points in km
    """
    R = 6371  # 地球半径（km）

    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return R * c