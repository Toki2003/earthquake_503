import math
import argparse

def distance_azimuth(source_lat, source_lon, station_lat, station_lon):
    # 将经纬度转化为弧度
    source_lat = math.radians(source_lat)
    source_lon = math.radians(source_lon)
    station_lat = math.radians(station_lat)
    station_lon = math.radians(station_lon)

    # 计算震中距
    dlon = station_lon - source_lon
    dlat = station_lat - source_lat
    a = math.sin(dlat/2)**2 + math.cos(source_lat) * math.cos(station_lat) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    R = 6371  # 地球半径，单位为千米
    distance = R * c

    # 计算方位角
    y = math.sin(station_lon - source_lon) * math.cos(station_lat)
    x = math.cos(source_lat) * math.sin(station_lat) - math.sin(source_lat) * math.cos(station_lat) * math.cos(station_lon - source_lon)
    azimuth = math.degrees(math.atan2(y, x))

    return distance, azimuth

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Your script description")

    # 添加必填参数
    parser.add_argument("--source_lat", type=float, required=True)
    parser.add_argument("--source_lon", type=float, required=True)
    parser.add_argument("--station_lat", type=float, required=True)
    parser.add_argument("--station_lon", type=float, required=True)
    args = parser.parse_args()

    res, res2 = distance_azimuth(args.source_lat, args.source_lon, args.station_lat, args.station_lon)
    print(res)
    print(res2)