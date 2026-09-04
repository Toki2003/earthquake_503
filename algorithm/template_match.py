import numpy as np
import argparse
import json
from io import BytesIO
from minio import Minio
from minio.error import S3Error

def template_matching(template, data, threshold):
    # 计算模板和数据的相关性
    correlation = np.correlate(data, template, mode='same')

    # 找到相关性的峰值
    peak_index = np.argmax(correlation)


    # 判断峰值是否超过阈值
    if correlation[peak_index] > threshold:
        return peak_index
    else:
        return None

def templateMatch(template_stream, data_stream,threshold):
    # 读取模板数据
    # template_file = "test.mseed"
    #template_stream = obspy.read(template_file)

    # 读取待检测数据
    # data_file = "test.mseed"
    #data_stream = obspy.read(data_file)

    # 初始化结果列表和最相似片段索引
    results = []
    most_similar_index = None
    most_similar_correlation = None

    # 对每个通道进行地震事件检测
    template = template_stream
    data = data_stream

    peak_index = template_matching(template, data, threshold)
    results.append(peak_index)

    if peak_index is not None:
        correlation = np.correlate(data, template, mode='same')
        if most_similar_index is None or correlation[peak_index] > most_similar_correlation:
            most_similar_index = peak_index
            most_similar_correlation = correlation[peak_index]

    # 提取最相似的片段数据
    data = {}
    if most_similar_index is not None:
        most_similar_data = data_stream[most_similar_index:most_similar_index + len(template)]
        return most_similar_data
    else:
        return []

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
def is_valid_json_from_minio2(file_name: str, file_path: str, bucket_name: str,
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
        return True, json_data['wave2'][0]

    except:
        return False, None
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Your script description")

    # 添加必填参数
    parser.add_argument("--file_name", required=True)
    parser.add_argument("--file_path", required=True)
    parser.add_argument("--bucket_name", required=True)
    parser.add_argument("--access_key", required=True)
    parser.add_argument("--secret_key", required=True)
    parser.add_argument("--threshold", required=True, help="freqmin")
    args = parser.parse_args()
    success1, data1 = is_valid_json_from_minio(
        file_name=args.file_name,
        file_path=args.file_path,
        bucket_name=args.bucket_name,
        access_key=args.access_key,
        secret_key=args.secret_key
    )
    success2, data2 = is_valid_json_from_minio2(
        file_name=args.file_name,
        file_path=args.file_path,
        bucket_name=args.bucket_name,
        access_key=args.access_key,
        secret_key=args.secret_key
    )
    # success, data1 = is_valid_json_from_minio(
    #         file_name='output.json',
    #         file_path='202.199.6.251:9002',
    #         bucket_name='new',
    #         access_key='minioadmin',
    #         secret_key='minioadmin'
    # )
    # success, data2 = is_valid_json_from_minio(
    #     file_name='output.json',
    #     file_path='202.199.6.251:9002',
    #     bucket_name='new',
    #     access_key='minioadmin',
    #     secret_key='minioadmin'
    # )
    if success1 &success2:
        res = templateMatch(data1, data2, eval(args.threshold))
    else:
        res = None
    print(res)
#python .\template_match.py --file_name "finally.json" --file_path "202.199.6.251:9002" --bucket_name "new" --access_key "minioadmin" --secret_key "minioadmin" --threshold 0.6