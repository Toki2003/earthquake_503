import obspy
import numpy as np
from obspy.signal import filter
import argparse
import json
from io import BytesIO
from minio import Minio
from minio.error import S3Error

# 巴特沃斯带通滤波器
# data_path – 要过滤数据的mseed文件路径。
# freqmin — 通带低转角频率。
# freqmax – 通带高角频率。
# df – 以 Hz 为单位的采样率。
# corners – 过滤角点/顺序。
# zerophase – 如果为 True，则向前和向后应用一次过滤器。这导致滤波器阶数增加一倍，但所产生的滤波轨迹中的相移为零。
def bandpass(data, freqmin, freqmax, df, corners, zerophase):
    return filter.bandpass(data, freqmin, freqmax, df, corners, zerophase)


# 巴特沃斯高通滤波器
# data_path – 要过滤数据的mseed文件路径。
# freq——滤波器转角频率。
# df – 以 Hz 为单位的采样率。
# corners – 过滤角点/顺序。
# zerophase – 如果为 True，则向前和向后应用一次过滤器。这会导致转角数量增加一倍，但所产生的滤波迹线中的相移为零。
def highpass(data, freq, df, corners, zerophase):
    return obspy.signal.filter.highpass(data, freq, df, corners, zerophase)


# 巴特沃斯低通滤波器
# data_path – 要过滤数据的mseed文件路径。
# freq——滤波器转角频率。
# df – 以 Hz 为单位的采样率。
# corners – 过滤角点/顺序。
# zerophase – 如果为 True，则向前和向后应用一次过滤器。这会导致转角数量增加一倍，但所产生的滤波迹线中的相移为零。
def lowpass(data, freq, df, corners, zerophase):
    return obspy.signal.filter.lowpass(data, freq, df, corners, zerophase)

def is_valid_json_from_minio(file_name: str, file_path: str, bucket_name: str,
                             access_key: str, secret_key: str):

    try:
        client = Minio(
            file_path,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )

        response = client.get_object(bucket_name, file_name)
        data = BytesIO(response.read())
        response.close()
        response.release_conn()

        json_data = json.load(data)  # 尝试解析 JSON
        return True, json_data['wave1'][0]

    except (S3Error, json.JSONDecodeError, Exception):
        return False, None

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description="Your script description")
        # 添加必填参数
        parser.add_argument("--file_name", required=True)
        parser.add_argument("--file_path", required=True)
        parser.add_argument("--bucket_name", required=True)
        parser.add_argument("--access_key", required=True)
        parser.add_argument("--secret_key", required=True)
        parser.add_argument("--freqmin", required=False, type=int, help="freqmin")
        parser.add_argument("--freqmax", required=False, type=int, help="freqmax")
        parser.add_argument("--method", required=True, help="hignpass or lowpass or bandpass")

        args = parser.parse_args()
        success, data = is_valid_json_from_minio(
            file_name=args.file_name,
            file_path=args.file_path,
            bucket_name=args.bucket_name,
            access_key=args.access_key,
            secret_key=args.secret_key
        )
        if success:
            df = 100
            corners = 4
            zerophase = False
            if args.method == "bandpass":
                if args.freqmin is None or args.freqmax is None:
                    res = "缺少低转角频率或高转角频率"
                else:
                    res = bandpass(np.array(data), args.freqmin, args.freqmax, df, corners, zerophase)
            elif args.method == "hignpass":
                if args.freqmax is None:
                    res = "缺少滤波器转角频率，请用freqmax赋值"
                else:
                    res = highpass(np.array(data), args.freqmax, df, corners, zerophase)
            elif args.method == "lowpass":
                if args.freqmin is None:
                    res = "缺少滤波器转角频率，请用freqmin赋值"
                else:
                    res = lowpass(np.array(data), args.freqmin, df, corners, zerophase)
        else:
            res = None
    except:
        res = None
    print(res)

# python Filter.py --file_name "finally.json" --file_path "202.199.6.251:9002" --bucket_name "new" --access_key "minioadmin" --secret_key "minioadmin" --freqmin 1 --method lowpass
# python Filter.py --file_name "finally.json" --file_path "202.199.6.251:9002" --bucket_name "new" --access_key "minioadmin" --secret_key "minioadmin" --freqmax 3 --method hignpass
# python Filter.py --file_name "finally.json" --file_path "202.199.6.251:9002" --bucket_name "new" --access_key "minioadmin" --secret_key "minioadmin" --freqmin 1 --freqmax 3 --method bandpass