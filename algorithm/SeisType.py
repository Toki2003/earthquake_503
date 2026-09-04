import numpy as np
import argparse
import json
from io import BytesIO
from minio import Minio
from minio.error import S3Error
import onnxruntime as ort

# --- 预处理：去势 + 归一化 ---
def qushi10_guiyihua(ori_list):
    a = np.polyfit(range(len(ori_list)), ori_list[:], 10)
    b = np.poly1d(a)
    c = b(range(len(ori_list)))
    qushi = [ori_list[i] - c[i] for i in range(len(ori_list))]
    mean = np.mean(qushi)
    std = np.std(qushi, ddof=1)
    return [(val - mean) / std for val in qushi]

# --- 加载 ONNX 模型 ---
def load_onnx_model(path):
    return ort.InferenceSession(path)

# --- 通用 ONNX 推理函数 ---
def run_onnx_predict(session, data_list):
    if len(data_list) % 3 != 0:
        raise ValueError("输入数据应为3通道成组")

    input_names = [inp.name for inp in session.get_inputs()]
    output_name = session.get_outputs()[0].name

    use_shape = [1, 1, 10000, 3]
    lsep = np.zeros([1, 10000, 3], dtype=np.float32)
    total_results = []

    for i in range(len(data_list) // 3):
        for ch in range(3):
            index = i * 3 + ch
            signal = qushi10_guiyihua(data_list[index])[:10000]
            lsep[0, :, ch] = np.array(signal)

        x_input = lsep.reshape(use_shape).astype(np.float32)
        input_feed = {}

        for name in input_names:
            if 'kp' in name:
                input_feed[name] = np.array(1.0, dtype=np.float32)
            else:
                input_feed[name] = x_input

        result = session.run([output_name], input_feed)[0]
        total_results.append(result[0])

    return total_results

# --- 识别函数：判断主类型 + 非天然子类 ---
def SeisType(picks, main_session, sub_session):
    try:
        main_results = run_onnx_predict(main_session, picks)
        t, f = 0, 0  # 天然 / 非天然计数

        for out in main_results:
            t_prob, nt_prob = out
            if t_prob >= 0.5:
                t += 1
            else:
                f += 1

        if t >= f:
            return True, "计算成功", "天然地震"
        else:
            # 非天然 → 使用第二个模型分类
            sub_results = run_onnx_predict(sub_session, picks)
            bp, cp = 0, 0
            for out in sub_results:
                bp_prob, cp_prob = out
                if bp_prob >= cp_prob:
                    bp += 1
                else:
                    cp += 1
            if bp >= cp:
                return True, "计算成功", "非天然地震-爆破"
            else:
                return True, "计算成功", "非天然地震-塌陷"

    except Exception as e:
        return False, f"推理异常: {str(e)}", ""

# --- MinIO 数据加载 ---
def is_valid_json_from_minio(file_name, file_path, bucket_name, access_key, secret_key):
    try:
        client = Minio(file_path, access_key=access_key, secret_key=secret_key, secure=False)
        response = client.get_object(bucket_name, file_name)
        data = BytesIO(response.read())
        response.close()
        response.release_conn()

        json_data = json.load(data)
        return True, json_data["wave1"]
    except:
        return False, None

# --- 主程序入口 ---
if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description="SeisType - 双模型 ONNX 推理")
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
        # success, data = is_valid_json_from_minio(
        #     file_name="finally.json",
        #     file_path="202.199.6.251:9002",
        #     bucket_name="new" ,
        #     access_key="minioadmin" ,
        #     secret_key="minioadmin"
        # )

        if success:
            main_session = load_onnx_model('tf_model.onnx')
            sub_session = load_onnx_model('bt_model.onnx')
            _, _, result = SeisType(np.array(data), main_session, sub_session)
        else:
            result = "❌ 数据加载失败"

    except Exception as e:
        result = f"❌ 程序异常: {str(e)}"

    print(result)
#python .\SeisType.py --file_name "finally.json" --file_path "202.199.6.251:9002" --bucket_name "new" --access_key "minioadmin" --secret_key "minioadmin"