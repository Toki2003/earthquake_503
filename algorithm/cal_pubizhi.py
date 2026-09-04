import numpy as np
from scipy.integrate import simpson
import argparse
import json

# 返回三分量的谱比值列表[xx, xx, xx]，分别对应E、N、Z三个分量
def calculate_pubizhi(p_time, data, sampling, start): # P_wave_onset: E、N、Z三分量P波到时列表(int)
    # pubizhi_list = []
    # boolean, problem, map = ValidationFile(f_mseed)
    # if boolean:
    #     file = obspy.read(f_mseed)
    #     for (i, tr) in enumerate(file):
    #         noise = np.abs(np.fft.fft(tr.data[:P_wave_onset[i]]))
    #         seismic = np.abs(np.fft.fft(tr.data[P_wave_onset[i]:]))
    #         noise_range = np.arange(noise.shape[0])
    #         seismic_range = np.arange(seismic.shape[0])
    #         # 求积分
    #         inte_noise = simpson(noise, noise_range)
    #         inte_seismic = simpson(seismic, seismic_range)
    #
    #         result = inte_seismic/inte_noise
    #         pubizhi_list.append(result)
    #     return boolean, problem, pubizhi_list
    pubizhi_list = []
    if len(data) != 3:
        return False, "分量缺失", None  # err: 分量缺失
    index = (p_time[0] - start[0]) * sampling[0]
    for i in range(len(data)):
        noise = np.abs(np.fft.fft(data[i][:index]))
        seismic = np.abs(np.fft.fft(data[i][:index]))
        noise_range = np.arange(noise.shape[0])
        seismic_range = np.arange(seismic.shape[0])
        # 求积分
        inte_noise = simpson(noise, noise_range)
        inte_seismic = simpson(seismic, seismic_range)

        result = inte_seismic / inte_noise
        pubizhi_list.append(result)

    return True, "计算成功", pubizhi_list

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Your script description")

    # 添加必填参数
    parser.add_argument("--data_file_path", required=True, help="The data in ENZ order as a 2D array")
    parser.add_argument("--sampling", required=True, help="The sampling rates in ENZ order as a 1D array")
    parser.add_argument("--start", required=True, help="The start_time in ENZ order as a 1D array")
    parser.add_argument("--p_time", required=True, help="The p_time in ENZ order as a 1D array")

    args = parser.parse_args()

    with open(args.data_file_path, 'r') as file:
        data = json.load(file)

        _, _, res = calculate_pubizhi(args.p_time, np.array(data), args.sampling, args.start)
    print(res)


