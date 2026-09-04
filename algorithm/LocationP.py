import numpy as np
import argparse
import json


def Neudis(weidu_0, jingdu_0, weidu_1, jingdu_1):
    pi = 3.1415926535897932
    weidu_0 = weidu_0 * pi / 180
    jingdu_0 = jingdu_0 * pi / 180
    weidu_1 = weidu_1 * pi / 180
    jingdu_1 = jingdu_1 * pi / 180

    Vector0 = np.array([np.cos(weidu_0) * np.cos(jingdu_0), np.cos(weidu_0) * np.sin(jingdu_0), np.sin(weidu_0)])
    Vector1 = np.array([np.cos(weidu_1) * np.cos(jingdu_1), np.cos(weidu_1) * np.sin(jingdu_1), np.sin(weidu_1)])

    m = Vector1.shape[1]
    dis = np.zeros(m)
    for cnt in range(m):

        Angle = np.arccos(
            np.dot(Vector0, Vector1[:, cnt]) / (np.linalg.norm(Vector0) * np.linalg.norm(Vector1[:, cnt]))) * 180 / pi
        r = 6378.1370
        dis[cnt] = Angle * pi * r / 180
        dis[cnt] = dis[cnt] * 1000
    return dis


def getLocationP(input_data, s, n):
    #s为精细网格密度，n为粗糙网格密度
    input_data = np.array(input_data)
    m, _ = input_data.shape
    if m < 3:
        epicjing = 0
        epicwei = 0
        epicdepth = 0
    else:
        jingmax = np.max(input_data[:, 0]) + 2.5
        weimax = np.max(input_data[:, 1]) + 2.5
        jingmin = np.min(input_data[:, 0]) - 2.5
        weimin = np.min(input_data[:, 1]) - 2.5

        DeltaTpij = np.zeros((m, m))
        for i in range(m):
            for j in range(i, m):
                DeltaTpij[i, j] = input_data[i, 3] - input_data[j, 3]  # Fix index to 4

        dis = Neudis(weimin, jingmin, input_data[:, 1], input_data[:, 0])
        pt = (dis / 6000) * 1000

        Deltatpij = np.zeros((m, m))
        for i in range(m):
            for j in range(i, m):
                Deltatpij[i, j] = pt[i] - pt[j]

        ansT = (DeltaTpij - Deltatpij) ** 2
        errorcache = np.sum(np.sum(ansT))

        if m == 3:
            epicdepth = 255
            for Jingcnt in np.arange(jingmin + n, jingmax, n):
                for weicnt in np.arange(weimin + n, weimax, n):
                    dis = Neudis(weicnt, Jingcnt, input_data[:, 1], input_data[:, 0])
                    pt = (dis / 6000) * 1000

                    Deltatpij = np.zeros((m, m))
                    for i in range(m):
                        for j in range(i, m):
                            Deltatpij[i, j] = pt[i] - pt[j]

                    ansT = (DeltaTpij - Deltatpij) ** 2
                    error = np.sum(np.sum(ansT))
                    epicwei = weicnt
                    epicjing = Jingcnt
                    if error < errorcache:
                        errorcache = error
            jingmax = epicjing + n/2
            weimax = epicwei + n/2
            jingmin = epicjing - n/2
            weimin = epicwei - n/2

            for Jingcnt in np.arange(jingmin, jingmax + s, s):
                for weicnt in np.arange(weimin, weimax + s, s):
                    dis = Neudis(weicnt, Jingcnt, input_data[:, 1], input_data[:, 0])
                    pt = (dis / 6000) * 1000

                    Deltatpij = np.zeros((m, m))
                    for i in range(m):
                        for j in range(i, m):
                            Deltatpij[i, j] = pt[i] - pt[j]

                    ansT = (DeltaTpij - Deltatpij) ** 2
                    error = np.sum(np.sum(ansT))
                    if error < errorcache:
                        epicwei = weicnt
                        epicjing = Jingcnt
                        errorcache = error
        else:
            for Jingcnt in np.arange(jingmin + n, jingmax, n):
                for weicnt in np.arange(weimin + n, weimax, n):
                    for depth in range(0, 31, 1):
                        dis = Neudis(weicnt, Jingcnt, input_data[:, 1], input_data[:, 0])
                        dis = np.sqrt((depth * 1000 + input_data[:, 2]) ** 2 + dis ** 2)  # Fix index to 3
                        pt = (dis / 6000) * 1000

                        Deltatpij = np.zeros((m, m))
                        for i in range(m):
                            for j in range(i, m):
                                Deltatpij[i, j] = pt[i] - pt[j]

                        ansT = (DeltaTpij - Deltatpij) ** 2
                        error = np.sum(np.sum(ansT))
                        if error < errorcache:
                            epicwei = weicnt
                            epicjing = Jingcnt
                            epicdepth = depth
                            errorcache = error
            jingmax = epicjing + n/2
            weimax = epicwei + n/2
            jingmin = epicjing - n/2
            weimin = epicwei - n/2
            depthmax = epicdepth + 5
            depthmin = 0

            for Jingcnt in np.arange(jingmin, jingmax + s, s):
                for weicnt in np.arange(weimin, weimax + s, s):
                    for depth in range(depthmin, depthmax + 1):
                        dis = Neudis(weicnt, Jingcnt, input_data[:, 1], input_data[:, 0])
                        dis = np.sqrt((depth * 1000 + input_data[:, 2]) ** 2 + dis ** 2)  # Fix index to 3
                        pt = (dis / 6000) * 1000

                        Deltatpij = np.zeros((m, m))
                        for i in range(m):
                            for j in range(i, m):
                                Deltatpij[i, j] = pt[i] - pt[j]

                        ansT = (DeltaTpij - Deltatpij) ** 2
                        error = np.sum(np.sum(ansT))
                        if error < errorcache:
                            epicwei = weicnt
                            epicjing = Jingcnt
                            epicdepth = depth
                            errorcache = error
    residual = np.sqrt(error) / m

    return True, '计算成功', epicjing, epicwei, epicdepth, residual


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Your script description")

    # 添加必填参数
    parser.add_argument("--data_file_path", required=True, help="The data in ENZ order as a 2D array")
    parser.add_argument("--s", type=float, required=True)
    parser.add_argument("--n", type=float, required=True)
    args = parser.parse_args()

    with open(args.data_file_path, 'r') as file:
        data = json.load(file)
        _, _, res, res2, res3, res4 = getLocationP(np.array(data), args.s, args.n)
    print(res)
    print(res2)
    print(res3)
    print(res4)

# python .\LocationP.py --data_file_path .\location1.json --s 0.01 --n 0.2
