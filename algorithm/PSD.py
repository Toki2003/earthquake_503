import argparse
import json
from io import BytesIO

import numpy as np
from matplotlib import mlab
from minio import Minio
from minio.error import S3Error


# PSD分段长度。
# 100 Hz采样率下，频率间隔约为：
# 100 / 4096 = 0.0244 Hz
NFFT = 4096


# 临时输入换算参数：
# 1个存储数值暂时按照1e-6 V处理。
VOLT_PER_STORED_UNIT = 1.0e-6


# 传感器灵敏度：
# 2000 V/(m/s)
SENSOR_SENSITIVITY = 2000.0


def getPSD(data, sampling):
    """
    计算一个台站E、N、Z三个分量的单边加速度PSD。

    参数：
        data:
            [E分量数组, N分量数组, Z分量数组]

        sampling:
            三个分量共同使用的采样率，例如100

    返回格式

        {
            "BHE": {
                "pxx": [...],  # 加速度PSD的dB数据
                "f": [...]
            },
            "BHN": {
                "pxx": [...],
                "f": [...]
            },
            "BHZ": {
                "pxx": [...],
                "f": [...]
            }
        }
    """

    # sampling采样率数值
    sampling = float(sampling)

    if not np.isfinite(sampling) or sampling <= 0:
        raise ValueError("采样率必须为有效正数")

    # 必须提供E、N、Z三个分量。
    if len(data) < 3:
        raise ValueError("需要提供E、N、Z三个分量")

    channel_data = {
        "BHE": data[0],
        "BHN": data[1],
        "BHZ": data[2]
    }

    # 返回结果。
    res = {}

    # 加速度PSD转换成dB时使用的参考值：
    # 1 (m/s²)²/Hz
    reference_psd = 1.0

    # 分别计算三个分量。
    for key in channel_data:
        # 转换成一维浮点数组。
        component = np.asarray(
            channel_data[key],
            dtype=float
        )

        if component.ndim != 1:
            raise ValueError(
                f"{key}分量必须是一维数组"
            )

        if component.size < 8:
            raise ValueError(
                f"{key}分量数据点数不足"
            )

        if not np.all(np.isfinite(component)):
            raise ValueError(
                f"{key}分量包含NaN或无穷大"
            )

        # 第一步：将存储值转换成电压V。
        #
        # 当前临时假设：
        # 1个存储值 = 1e-6 V
        voltage = (
            component
            * VOLT_PER_STORED_UNIT
        )

        # 第二步：根据传感器灵敏度，
        # 将电压转换成速度m/s。
        #
        # 灵敏度单位为V/(m/s)，所以：
        # 速度 = 电压 / 灵敏度
        velocity = (
            voltage
            / SENSOR_SENSITIVITY
        )

        # 数据长度不足4096点时，
        # 使用当前数据的实际长度作为NFFT。
        nfft = min(
            NFFT,
            component.size
        )

        # 相邻窗口重叠75%。
        noverlap = int(
            nfft * 3 / 4
        )

        # 使用Welch方法计算速度的单边PSD
        # velocity_psd单位：(m/s)²/Hz
        velocity_psd, frequency = mlab.psd(
            velocity,
            NFFT=nfft,
            Fs=sampling,
            detrend=mlab.detrend_mean,
            window=np.hanning(nfft),
            noverlap=noverlap,
            sides="onesided",
            scale_by_freq=True
        )

        # 对数频率坐标不能绘制0 Hz，
        # 因此删除0 Hz，只保留正频率。
        positive = frequency > 0

        frequency = frequency[positive]
        velocity_psd = velocity_psd[positive]

        # 将速度PSD转换成加速度PSD
        # Sa(f) = (2πf)² × Sv(f)
        # acceleration_psd单位：(m/s²)²/Hz
        acceleration_psd = (
            (2.0 * np.pi * frequency) ** 2
            * velocity_psd
        )
        # 将加速度PSD转换成dB。
        # 单位：dB re 1 (m/s²)²/Hz
        pxx_db = 10.0 * np.log10(
            np.maximum(acceleration_psd,np.finfo(float).tiny) / reference_psd
        )

        # 字段虽然叫pxx，但里面保存的是dB数据。
        # 不增加pxx_db字段，避免影响原有调用方。
        res[key] = {
            "pxx": pxx_db.tolist(),
            "f": frequency.tolist()
        }
    return res


def is_valid_json_from_minio(
        file_name,
        file_path,
        bucket_name,
        access_key,
        secret_key
):
    """
    从MinIO读取JSON文件中的wave1三分量数据。
    """

    response = None

    try:
        # 创建MinIO客户端。
        client = Minio(
            file_path,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )

        # 从指定桶中读取文件。
        try:
            response = client.get_object(
                bucket_name,
                file_name
            )

        except S3Error as error:
            return (
                False,
                f"MinIO获取对象失败: {error}"
            )

        # 读取文件的二进制内容。
        file_data = BytesIO(
            response.read()
        )

        # 解析JSON文件。
        try:
            json_data = json.load(
                file_data
            )

        except json.JSONDecodeError as error:
            return (
                False,
                f"JSON解析失败: {error}"
            )

        # 检查wave1字段是否存在。
        if "wave1" not in json_data:
            return (
                False,
                "JSON中不存在'wave1'键"
            )

        # wave1应当保存E、N、Z三个分量。
        wave_data = json_data["wave1"]

        if (
            not isinstance(wave_data, list)
            or len(wave_data) < 3
        ):
            return (
                False,
                "wave1必须包含E、N、Z三个分量"
            )

        return (
            True,
            wave_data
        )

    except S3Error as error:
        return (
            False,
            f"MinIO连接失败: {error}"
        )

    except Exception as error:
        return (
            False,
            f"发生未知错误: {error}"
        )

    finally:
        # 无论成功或失败，都释放MinIO连接。
        if response is not None:
            try:
                response.close()
            except Exception:
                pass

            try:
                response.release_conn()
            except Exception:
                pass


if __name__ == "__main__":
    # 创建命令行参数解析器。
    parser = argparse.ArgumentParser(
        description="PSD算法"
    )

    parser.add_argument(
        "--file_name",
        required=True
    )

    parser.add_argument(
        "--file_path",
        required=True
    )

    parser.add_argument(
        "--bucket_name",
        required=True
    )

    parser.add_argument(
        "--access_key",
        required=True
    )

    parser.add_argument(
        "--secret_key",
        required=True
    )

    parser.add_argument(
        "--sampling",
        required=True,
        type=float,
        help="采样率（Hz）"
    )
    args = parser.parse_args()
    # 从MinIO读取输入数据。
    success, data = is_valid_json_from_minio(
        file_name=args.file_name,
        file_path=args.file_path,
        bucket_name=args.bucket_name,
        access_key=args.access_key,
        secret_key=args.secret_key
    )

    if success:
        try:
            # 计算PSD。
            res = getPSD(
                np.array(data),
                args.sampling
            )
        except Exception:
            res = "计算错误"

    else:
        # MinIO读取失败时返回错误信息。
        res = data

    print(res)