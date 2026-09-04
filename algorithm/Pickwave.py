import numpy as np
import argparse
import json
from io import BytesIO
from minio import Minio
from minio.error import S3Error

def STALTA(data, shortTimeLength, threshold):
    detectResult = 0
    detrendLT = [value - np.mean(data) for value in data]
    LT = detrendLT.copy()
    ST = detrendLT[-shortTimeLength:]
    sunLongTimeWindow = sum(data)

    if sunLongTimeWindow == 0:
        detectResult = 0
    else:
        meanST = np.mean(np.abs(ST))
        meanLT = np.mean(np.abs(LT))
        meanST2 = np.mean(np.square(ST))
        meanLT2 = np.mean(np.square(LT))
        thres1 = meanST / meanLT
        thres2 = meanST2 / meanLT2
        if thres1 > threshold and thres2 > threshold:
            detectResult = 1
        elif thres1 <= threshold and thres2 <= threshold:
            detectResult = 0
    return detectResult


def AICdet(data):
    outidx = 0
    residuals = [value - np.mean(data) for value in data]
    threshold = 0.0
    residuals_mean = np.mean(residuals)
    for value in residuals:
        threshold += (value - residuals_mean) ** 2

    threshold /= len(residuals)
    threshold = np.sqrt(threshold)

    outliers = [index for index, value in enumerate(residuals) if abs(value) > threshold]
    if outliers:
        outidx = min(outliers)

    return outidx


def Neupickwave(waves, startTime, samplingRate):
    # 修改1：默认没有检测到P波
    # 防止循环没有触发时DetectPoint未赋值而报错
    DetectPoint = -1
    for i in range(3000, len(waves[2]), 100):
        inputData = waves[2][ i - 3000:i]
        result = STALTA(inputData,500,3.0 )
        if result == 1:
            detrendInput = [value - np.mean(inputData) for value in inputData]
            ST1 = detrendInput[-500:]
            DetectPoint =  i - 500 + AICdet(ST1)
            break
    # 修改2：没有检测到P波时正常返回
    if DetectPoint == -1:
        return None, -1
    # 修改3：采样点除以采样率转换成秒
    # startTime当前使用的是10位秒级时间戳
    Ptime = startTime[2] + DetectPoint / samplingRate[2]
    return Ptime, DetectPoint
"""
def Neupickwave(waves, startTime, samplingRate):
    for i in range(3000, len(waves[2]), 100):
        inputData = waves[2][i - 3000:i]
        result = STALTA(inputData, 500, 3.0)
        if result == 1:
            detrendInput = [value - np.mean(inputData) for value in inputData]
            ST1 = detrendInput[-500:]
            DetectPoint = i - 500 + AICdet(ST1)
            break
    Ptime = startTime[2] + DetectPoint * 1000 / samplingRate[2]
    return Ptime, DetectPoint# P波时间为13位时间戳，单位ms
"""
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
        return True, json_data['wave1']
    except:
        return False, None

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description="Your script description")
        parser.add_argument("--file_name", required=True)
        parser.add_argument("--file_path", required=True)
        parser.add_argument("--bucket_name", required=True)
        parser.add_argument("--access_key", required=True)
        parser.add_argument("--secret_key", required=True)
        parser.add_argument("--sampling", required=True, help="The sampling rates in ENZ order as a 1D array")
        parser.add_argument("--start", required=True)
        args = parser.parse_args()
        success, data = is_valid_json_from_minio(
            file_name=args.file_name,
            file_path=args.file_path,
            bucket_name=args.bucket_name,
            access_key=args.access_key,
            secret_key=args.secret_key
        )
        if success:
            res, res2 = Neupickwave(np.array(data), eval(args.start), eval(args.sampling))
        else:
            res = None
            res2 = None
    except:
        res = None
        res2 = None
    print(res)
    print(res2)
#python .\Pickwave.py --file_name "finally.json" --file_path "202.199.6.251:9002" --bucket_name "new" --access_key "minioadmin" --secret_key "minioadmin" --sampling "[100, 100, 100]" --start "[1567266852,1567266852,1567266852]"