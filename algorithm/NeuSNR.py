import numpy as np
import argparse
import json
from io import BytesIO
from minio import Minio
from minio.error import S3Error

# 计算信噪比
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

def Neupickwave(wave):
    DetectPoint = -1
    for i in range(3000, len(wave), 100):
        inputData = wave[i - 3000:i]
        result = STALTA(inputData, 500, 3.0)
        if result == 1:
            detrendInput = [value - np.mean(inputData) for value in inputData]
            ST1 = detrendInput[-500:]
            DetectPoint = i - 500 + AICdet(ST1)
            break
    return  DetectPoint
def calc_SNR(a):
    index = Neupickwave(a)
    if index == -1:
        return -1
    if index >= 3000:
        signal = a[index: index+3000]
        noise = a[index-3000: index]

    else:
        signal = a[0: index-1]
        noise = a[index: index*2-1]
    signal_power = np.square(signal).mean()
    noise_power = np.square(noise).mean()
    snr = 10 * np.log10(signal_power / noise_power)
    return snr

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
    except:
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
        args = parser.parse_args()

        success, data = is_valid_json_from_minio(
            file_name=args.file_name,
            file_path=args.file_path,
            bucket_name=args.bucket_name,
            access_key=args.access_key,
            secret_key=args.secret_key
        )
        if success:
            res = calc_SNR(np.array(data))
        else:
            res = None
    except:
        res = None
    print(res)

# python .\NeuSNR.py --file_name "finally.json" --file_path "202.199.6.251:9002" --bucket_name "new" --access_key "minioadmin" --secret_key "minioadmin"
# 输出为信噪比，如果结果为-1，则表示没有检测到震相，无法计算信噪比
