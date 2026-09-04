
from statsmodels.tsa.ar_model import AutoReg
import numpy as np
from datetime import datetime
from obspy import UTCDateTime
import matplotlib.pyplot as plt


def AR(data, sampling, start, p_time, s_time, pred_len):
    '''
        https://vitalflux.com/autoregressive-ar-models-with-python-examples/
        对P波到达后的sec_to_decay秒的三份量波形做order阶AR模型，并给出之后对应通道pred_len长度的预测
        @@--需要statsmodels库--@@

        args:
            miniseed_path: seed文件路径
            p_time: P波到达绝对时间 (obspy.core.utcdatetime.UTCDateTime)
            s_time: ...
            pred_len: 预测长度
            sec_to_decay: 经验系数：非天然震动事件Ｐ波能量衰减主要在5s左右完成。 default=5
            order: 阶数 default=2

        return: boolean, problem, map
            状态(bool): 算法计算状态，True表示完成计算未出现问题，False为计算过程中发现问题
            异常(string): 具体异常
            计算结果(set)：对应在BHE BHN BHZ上的计算结果
    '''

    # 检查三个分量的波形数据是否都存在
    if len(data) != 3 or len(sampling)!=3 or len(start)!=3:
        return False, "分量缺失", None  # err: 分量缺失
    utc_dates = []
    for timestamp in start:
        utc_date = UTCDateTime(datetime.utcfromtimestamp(timestamp))
        utc_dates.append(utc_date)

    # 三份量的计算结果
    result = {}

    ptime = UTCDateTime(p_time)
    stime = UTCDateTime(s_time)
    # 这仨分量的长度，起始时间还不一样的，没法concatenate起来一步算完
    for i in range(len(data)):
        wave_data = np.abs(data[i])
        sr = sampling[i]
        a = utc_dates[i]
        idx_p = int((ptime - a) * sr)
        idx_s = int((stime - a) * sr)

        # 判断ps到时时间是否超出某分量的边界
        if idx_p <= 0 or idx_p >= wave_data.__len__() or idx_s <= 0 or idx_s >= wave_data.__len__():
            return False, "时间越界", None  # err: 时间越界

        # 判断ps到时间隔是否小于0
        if idx_s - idx_p <= 0:
            return False, "ps到时间小于0", None  # err: ps到时间小于0

        # 保留P-S之间的数据
        wave_data = wave_data[idx_p:idx_s]
        # plt.plot(wave_data)

        # fit AR模型，并给出预测结果
        ar_model = AutoReg(wave_data[:int(5 * sr)], lags=2).fit()
        pred = ar_model.predict(start=int(5 * sr), end=int(5 * sr) + pred_len)

        if i == 0:
            result['BHE'] = pred.tolist()
        if i == 1:
            result['BHN'] = pred.tolist()
        if i == 2:
            result['BHZ'] = pred.tolist()

    # 返回结果
    return True, "计算成功", result

