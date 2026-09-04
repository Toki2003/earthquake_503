import argparse
import json
import numpy as np
import math
import obspy
from obspy.core import read, Stream, Trace
from io import BytesIO
from minio import Minio
from minio.error import S3Error

def get_r_mb (dataFile, dist, depth):
    rows = []
    col_index = []
    with open(dataFile, 'r') as f:
        flines = f.readlines()
        rows_index = flines[0].strip().split('.')
        rows_index = list(float(x.strip()) for x in rows_index[:18])
        for fline in flines[1:]:
            row = []
            col = fline.strip().split('. ')
            col_index.append(float(col[0]))
            for value in col[1].split('  '):
                row.append(float(value))
            rows.append(row)  # list of lists
    col = 0
    row = 0
    for col_num in range(1, len(col_index)):
        if dist < col_index[col_num]:
            break
    for row_num in range(1, len(rows_index)):
        if depth < rows_index[row_num]:
            break

    value = rows[col_num-1][row_num]+((rows[col_num][row_num]-rows[col_num-1][row_num])/(col_index[col_num]-col_index[col_num-1])*(dist-col_index[col_num-1]))
    return value


def get_r_ml(dataFile, neww, distance):
    delta = {'BJ':0, 'TJ':0, 'HB':0, 'SX':0, 'NM':0, 'LN':0, 'JL':0, 'HLJ':0, 'GD':1, 'GX':1, 'HN':1, 'FJ':1, 'YN':1, 'GZ':1,'XJ':4,'QH':3,'XZ':3,'SC':3}
    if neww not in delta.keys():
        neww = 2
    else:
        neww = delta[neww]

    dic = {}
    with open(dataFile, 'r') as f:
        flines = f.readlines()
        for line in flines:
            key = line.strip().split(' ')[0]
            value = line.strip().split(' ')[-5:]
            values = []
            for i in value:
                values.append(float(i))
            dic[float(key)] = values
    p = 0
    for key in dic.keys():
        if distance < key:
            p = dic[key][neww]

    return p
def distanc(list_v):
    d = []
    for i in range(len(list_v)):
        if i == 0:
            d.append(0.0)
        else:
            d.append(d[i-1] + (list_v[i] + list_v[i-1])/2*0.01)
    return d
def cul_mb(st_z, distance, depth, sensititvty):
    for trace in st_z:
            # 检查通道名是否匹配您想要的通道名
        if trace.stats.channel[-1] == "Z":  # 假设通道名为 "Z"
            # netw = st_z[0].stats.network
            # print(netw)
            # make a copy to keep our original data
            st_z_orig = st_z.copy()

            z_dtpr = len(st_z[0].data) - 1

            for num in range(z_dtpr):
                if (num < z_dtpr - 1):
                    st_z[0].data[num] = float(st_z[0].data[num]) / float(sensititvty)
            #################################################################################
            ##             this part need to be conform                                    ##
            #################################################################################
            paz_1hz = {
                'poles': [-2.8274 + 5.6111j, -2.8274 - 5.6111j, -88.8442 + 88.8711j,
                          -88.8442 - 88.8711j, -4.545 + 0j],
                'zeros': [0j, 0j],
                'gain': 1,
                'sensitivity': 15791}
            # paz_1hz = cornFreq2Paz(1, damp=0.707)  # 1hz instrument
            # paz_1hz['sensitivity'] = 15791
            #################################################################################
            ##                                                                             ##
            #################################################################################
            # Simulate instrument given poles, zeros and gain of
            # the original and desired instrument
            st_z.simulate(paz_simulate=paz_1hz)
            # st_z_orig.plot()
            # st_z.plot()

            Amax = 0
            z_ampmax = 0
            z_ampmin = 0
            z_max_post = 0
            z_min_post = 0

            for num in range(z_dtpr):
                if (num < z_dtpr - 1):
                    if (st_z[0].data[num] > z_ampmax):
                        z_ampmax = st_z[0].data[num]
                        z_max_post = num
                    if (st_z[0].data[num] < z_ampmin):
                        z_ampmin = st_z[0].data[num]
                        z_min_post = num
            Amax = abs(z_ampmax - z_ampmin) / 2

            ###
            dist = int(float(distance))
            depth = int(float(depth))
            dataFile = 'qpp.dat_new'
            q_val = get_r_mb(dataFile, dist, depth)
            ###

            mb = math.log(float(Amax), 10) + q_val
            return mb - 0.8
    return False, 0

def cul_mb_big(st_z, distance, depth, sensititvty):
    for trace in st_z:
        # 检查通道名是否匹配您想要的通道名
        if trace.stats.channel[-1] == "Z":  # 假设通道名为 "Z"
            st_z_orig = st_z.copy()

            z_dtpr = len(st_z[0].data) - 1

            for num in range(z_dtpr):
                if (num < z_dtpr - 1):
                    st_z[0].data[num] = float(st_z[0].data[num]) / float(sensititvty)

            paz_1hz = {
                'poles': [-0.2233 + 0.4729j, -0.2233 - 0.4729j, -51.8758 + 0j,
                          - 0.4882 + 0j],
                'zeros': [0j, 0j],
                'gain': 1,
                'sensitivity': 52.36}

            st_z.simulate(paz_simulate=paz_1hz)

            Amax = 0
            z_ampmax = 0
            z_ampmin = 0
            z_max_post = 0
            z_min_post = 0
            weiyi_Z = distanc(st_z[0].data)

            for num in range(z_dtpr):
                if (num < z_dtpr - 1):
                    if (weiyi_Z[num] > z_ampmax):
                        z_ampmax = weiyi_Z[num]
                    z_max_post = num
                    if (weiyi_Z[num] < z_ampmin):
                        z_ampmin = weiyi_Z[num]
                        z_min_post = num
            Amax = abs(z_ampmax - z_ampmin) / 2

            ###
            dist = int(float(distance))
            depth = int(float(depth))
            dataFile = 'qpp.dat_new'
            # q_table = read_q.read_q_mb (dataFile)
            q_val = get_r_mb(dataFile, dist, depth)
            ###

            mB = math.log(float(Amax), 10) + q_val

            return mB - 0.8

    return 0

def cul_ml(file1, file2, distance, sensititvty):
    st_e = file1
    st_n = file2
    netw = st_e[0].stats.network
    # print(netw)
    # make a copy to keep our original data
    st_e_orig = st_e.copy()
    st_n_orig = st_n.copy()

    for trace in st_e:
        if trace.stats.channel[-1] == "E":
            # 处理 "E" 通道数据的部分，请根据需要添加代码
            netw = st_e[0].stats.network
            # print(netw)
            # make a copy to keep our original data
            st_e_orig = st_e.copy()
            e_dtpr = len(st_e[0].data) - 1
            for num in range(e_dtpr):
                if (num < e_dtpr - 1):
                    st_e[0].data[num] = float(st_e[0].data[num]) / float(sensititvty)
            #################################################################################
            ##             this part need to be conform                                    ##
            #################################################################################
            paz_1hz = {
                'poles': [-2.8274 + 5.6111j, -2.8274 - 5.6111j, -88.8442 + 88.8711j,
                          -88.8442 - 88.8711j, -4.545 + 0j],
                'zeros': [0j, 0j],
                'gain': 1,
                'sensitivity': 15791}
            # paz_1hz = cornFreq2Paz(1, damp=0.707)  # 1hz instrument
            # paz_1hz['sensitivity'] = 15791
            #################################################################################
            ##                                                                             ##
            #################################################################################
            # Simulate instrument given poles, zeros and gain of
            # the original and desired instrument
            st_e.simulate(paz_simulate=paz_1hz)
            # st_e_orig.plot()
            # st_e.plot()

            e_ampmax = 0
            e_ampmin = 0
            e_max_post = 0
            e_min_post = 0
            n_max_post = 0
            n_min_post = 0
            weiyi_e = distanc(st_e[0].data)
            for num in range(e_dtpr):
                if (num < e_dtpr - 1):
                    if (weiyi_e[num] > e_ampmax):
                        e_ampmax = weiyi_e[num]
                        e_max_post = num
                    if (weiyi_e[num] < e_ampmin):
                        e_ampmin = weiyi_e[num]
                        e_min_post = num
            AEmax = abs(e_ampmax - e_ampmin) / 2

    # 处理 "N" 通道数据
    for trace in st_n:
        if trace.stats.channel[-1] == "N":
            # 处理 "N" 通道数据的部分，请根据需要添加代码
            st_n_orig = st_n.copy()
            n_dtpr = len(st_n[0].data) - 1
            for num in range(n_dtpr):
                if (num < n_dtpr - 1):
                    st_n[0].data[num] = float(st_n[0].data[num]) / float(sensititvty)
            #################################################################################
            ##             this part need to be conform                                    ##
            #################################################################################
            paz_1hz = {
                'poles': [-2.8274 + 5.6111j, -2.8274 - 5.6111j, -88.8442 + 88.8711j,
                          -88.8442 - 88.8711j, -4.545 + 0j],
                'zeros': [0j, 0j],
                'gain': 1,
                'sensitivity': 15791}
            # paz_1hz = cornFreq2Paz(1, damp=0.707)  # 1hz instrument
            # paz_1hz['sensitivity'] = 15791
            #################################################################################
            ##                                                                             ##
            #################################################################################
            # Simulate instrument given poles, zeros and gain of
            # the original and desired instrument
            st_n.simulate(paz_simulate=paz_1hz)
            # st_n_orig.plot()
            # st_n.plot()
            n_ampmax = 0
            n_ampmin = 0
            weiyi_n = distanc(st_n[0].data)
            for num in range(n_dtpr):
                if (num < n_dtpr - 1):
                    if (weiyi_n[num] > n_ampmax):
                        n_ampmax = weiyi_n[num]
                        n_max_post = num
                    if (weiyi_n[num] < n_ampmin):
                        n_ampmin = weiyi_n[num]
                        n_min_post = num
            ANmax = abs(n_ampmax - n_ampmin) / 2

    Amax = (AEmax + ANmax) / 2
    # dist = int((float(distance) * 110 // 5 + 1) * 5)

    ###
    dataFile = 'rfun.dat_new'
    # q_table = read_q.read_q_ml(dataFile)
    # distance没问题，netw为‘XJ’,
    r_val = get_r_ml(dataFile, netw, distance)

    ml = math.log(float(Amax), 10) + r_val
    return ml - 0.8

def cul_ms(st_z, distance, sensititvty):
    delta = {0: 1.8, 5: 1.8, 10: 1.9, 15: 2.0, 20: 2.1, 25: 2.2, 30: 2.5, 35: 2.7, 40: 2.8, 45: 2.9, 50: 3.0, 55: 3.1,
             60: 3.2, 65: 3.2, 70: 3.2, 75: 3.25, 80: 3.3, 85: 3.3, 90: 3.4, 95: 3.4, 100: 3.4, 105: 3.45, 110: 3.5,
             115: 3.5, 120: 3.5, 125: 3.55, 130: 3.6, 135: 3.6, 140: 3.6, 145: 3.65,
             150: 3.7, 155: 3.7, 160: 3.7, 165: 3.75, 170: 3.8,
             175: 3.8, 180: 3.8, 185: 3.85, 190: 3.9, 195: 3.9,
             200: 3.9, 205: 3.95, 210: 4.0, 215: 4.0, 220: 4.0,
             225: 4.05, 230: 4.1, 235: 4.1, 240: 4.1, 245: 4.1,
             250: 4.1, 255: 4.1, 260: 4.1, 265: 4.15, 270: 4.2,
             275: 4.2, 280: 4.2, 285: 4.25, 290: 4.3, 295: 4.3,
             300: 4.3, 305: 4.35, 310: 4.4, 315: 4.4, 320: 4.4,
             325: 4.45, 330: 4.5, 335: 4.5, 340: 4.5, 345: 4.5,
             350: 4.5, 355: 4.5, 355: 4.5, 360: 4.5, 365: 4.5,
             370: 4.5, 375: 4.55, 380: 4.6, 385: 4.6, 390: 4.6,
             395: 4.65, 400: 4.7, 405: 4.7, 410: 4.7, 415: 4.7,
             420: 4.7, 425: 4.725, 430: 4.75, 435: 4.75, 440: 4.75,
             445: 4.75, 450: 4.75, 455: 4.75, 460: 4.75, 465: 4.775,
             470: 4.8, 475: 4.8, 480: 4.8, 485: 4.8, 490: 4.8,
             495: 4.8, 500: 4.8, 505: 4.85, 510: 4.9, 515: 4.9,
             520: 4.9, 525: 4.9, 530: 4.9, 535: 4.9, 540: 4.9,
             545: 4.9, 550: 4.9, 555: 4.9, 560: 4.9, 565: 4.9,
             570: 4.9, 575: 4.9, 580: 4.9, 585: 4.9, 590: 4.9,
             595: 4.9, 600: 4.9, 605: 4.95, 610: 5.0, 615: 5.0,
             620: 5.0, 625: 5.02, 630: 5.03, 635: 5.05, 640: 5.07,
             645: 5.08, 650: 5.1, 655: 5.11, 660: 5.12, 665: 5.13,
             670: 5.14, 675: 5.15, 680: 5.16, 685: 5.17, 690: 5.18,
             695: 5.19, 700: 5.2, 705: 5.2, 710: 5.2, 715: 5.2,
             720: 5.2, 725: 5.2, 730: 5.2, 735: 5.2, 740: 5.2,
             745: 5.2, 750: 5.2, 755: 5.2, 760: 5.2, 765: 5.2,
             770: 5.2, 775: 5.2, 780: 5.2, 785: 5.2, 790: 5.2,
             795: 5.2, 800: 5.2, 805: 5.2, 810: 5.2, 815: 5.2,
             820: 5.2, 825: 5.2, 830: 5.2, 835: 5.2, 840: 5.2,
             845: 5.2, 850: 5.2, 855: 5.21, 860: 5.22, 865: 5.23,
             870: 5.24, 875: 5.25, 880: 5.26, 885: 5.27, 890: 5.28,
             895: 5.29, 900: 5.3, 905: 5.3, 910: 5.3, 915: 5.3,
             920: 5.3, 925: 5.3, 930: 5.3, 935: 5.3, 940: 5.3,
             945: 5.3, 950: 5.3, 955: 5.3, 960: 5.3, 965: 5.3,
             970: 5.3, 975: 5.3, 980: 5.3, 985: 5.3, 990: 5.3,
             995: 5.3, 1000: 5.3
             }

    for trace in st_z:
        # 检查通道名是否匹配您想要的通道名
        if trace.stats.channel[-1] == "Z":

            st_z_orig = st_z.copy()

            z_dtpr = len(st_z[0].data) - 1

            for num in range(z_dtpr):
                if (num < z_dtpr - 1):
                    st_z[0].data[num] = float(st_z[0].data[num]) / float(sensititvty)

            paz_1hz = {
                'poles': [-0.2233 + 0.4729j, -0.2233 - 0.4729j, -51.8758 + 0j,
                              - 0.4882 + 0j],
                'zeros': [0j, 0j],
                'gain': 1,
                'sensitivity': 52.36}
            #st_z是读取的文件数据
            st_z.simulate(paz_simulate=paz_1hz)

            Amax = 0
            z_ampmax = 0
            z_ampmin = 0
            z_max_post = 0
            z_min_post = 0

            for num in range(z_dtpr):
                if (num < z_dtpr - 1):
                    if (st_z[0].data[num] > z_ampmax):
                            z_ampmax = st_z[0].data[num]
                    z_max_post = num
                    if (st_z[0].data[num] < z_ampmin):
                        z_ampmin = st_z[0].data[num]
                        z_min_post = num
            Amax = abs(z_ampmax - z_ampmin) / 2
            q_val = 0
            for key in delta.keys():
                if distance < key:
                    q_val = delta[key]

            ms = math.log(float(Amax), 10) + math.log(float(q_val), 10) + 2.7

            return ms
    return 0
def cul_magnitude(data, distance, depth, sensitivity, network):
    mb = cul_mb(gen_stream(data, network), distance, depth, sensitivity)
    mB = cul_mb_big(gen_stream(data, network), distance, depth, sensitivity)
    ml = cul_ml(gen_stream(data, network), gen_stream(data, network), distance, sensitivity)
    ms = cul_ms(gen_stream(data, network), distance, sensitivity)
    return mb, mB, ml, ms

def gen_stream(data, network):
    stream = Stream()
    trace_X = Trace()
    trace_X.data = np.array(data[0])  # E分量数据
    time = obspy.UTCDateTime('2009-05-25 00:20:00')
    trace_X.stats.starttime = time
    trace_X.stats.sampling_rate = 100  # 采样率
    trace_X.stats.channel = "BHE"  # 分量名称
    trace_X.stats.location = "00"
    trace_X.stats.network = network
    trace_X.stats.station = "CBS"  # 分量名称
    stream.append(trace_X)
    trace_Y = Trace()
    trace_Y.data = np.array(data[1])  # N分量数据
    time = obspy.UTCDateTime('2009-05-25 00:20:00')
    trace_Y.stats.starttime = time
    trace_Y.stats.sampling_rate = 100  # 采样率
    trace_Y.stats.channel = "BHN"  # 分量名称
    trace_Y.stats.location = "00"
    trace_Y.stats.network = network
    trace_Y.stats.station = "CBS"  # 分量名称
    stream.append(trace_Y)
    trace_Z = Trace()
    trace_Z.data = np.array(data[2])  # Z分量数据
    time = obspy.UTCDateTime('2009-05-25 00:20:00')
    trace_Z.stats.starttime = time
    trace_Z.stats.sampling_rate = 100  # 采样率
    trace_Z.stats.channel = "BHZ"  # 分量名称
    trace_Z.stats.location = "00"
    trace_Z.stats.network = network
    trace_Z.stats.station = "CBS"  # 分量名称
    stream.append(trace_Z)
    return stream

# with open('JL.CBS.00.BHZ.json', 'r') as file:
#     data = json.load(file)
# cul_magnitude(np.array(data), 109.81, 1790, 1035)
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
    parser = argparse.ArgumentParser(description="Your script description")

    # 添加必填参数distance, depth, sensititvty
    parser.add_argument("--file_name", required=True)
    parser.add_argument("--file_path", required=True)
    parser.add_argument("--bucket_name", required=True)
    parser.add_argument("--access_key", required=True)
    parser.add_argument("--secret_key", required=True)
    parser.add_argument("--distance", required=True)
    parser.add_argument("--depth", required=True)
    parser.add_argument("--sensitivity", required=True)

    args = parser.parse_args()

    success, data = is_valid_json_from_minio(
        file_name=args.file_name,
        file_path=args.file_path,
        bucket_name=args.bucket_name,
        access_key=args.access_key,
        secret_key=args.secret_key
    )
    if success:
        res1, res2, res3, res4 = cul_magnitude(np.array(data), eval(args.distance), eval(args.depth), eval(args.sensitivity), 'XJ')
    else:
        res = 0
        res2 = 0
        res3 = 0
        res4 = 0
    print(res1)
    print(res2)
    print(res3)
    print(res4)

#python .\cul_magnitude.py --file_name "finally.json" --file_path "202.199.6.251:9002" --bucket_name "new" --access_key "minioadmin" --secret_key "minioadmin" --distance 100 --depth 100 --sensitivity 0.8
