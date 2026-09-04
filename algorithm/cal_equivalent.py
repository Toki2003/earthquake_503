import numpy as np
import argparse

def Cal_equivalent(ml):
    # 统一把整数、浮点数、数字字符串转换成float
    try:
        ml = float(ml)
    except (TypeError, ValueError):
        return False, "震级必须为数字", 0, 0

    # 排除NaN和正负无穷大，防止计算结果变成nan/null
    if not np.isfinite(ml):
        return False, "震级必须为有效数字", 0, 0

    if isinstance(ml, int) or isinstance(ml, float):
        x = np.array([4.5,4.1,3.2,3.1,2.6])
        y = np.array([10162,5500,508,450,78])

        # 使用polyfit方法来拟合,并选择多项式,这里先使用2次方程
        z1 = np.polyfit(x, y, 3)
        # 使用poly1d方法获得多项式系数,按照阶数由高到低排列
        p1 = np.poly1d(z1)
        # 在屏幕上打印拟合多项式
        equivalent = p1(ml)

        equivalent_list = p1(x)

#原erro计算公式
        #error = np.mean(np.abs(equivalent_list - y))
#现erro计算公式
        # 计算标定点残差
        residual_list = y - equivalent_list

        # 构建三次多项式的设计矩阵
        design_matrix = np.vander(x, 4)

        # 计算残差方差
        residual_variance = np.sum(residual_list ** 2) / (len(x) - len(z1))

        # 当前输入震级的多项式向量
        current_point = np.array([
            ml ** 3,
            ml ** 2,
            ml,
            1.0
        ])

        # 计算输入震级与标定数据之间的距离影响
        leverage = current_point @ np.linalg.pinv(
            design_matrix.T @ design_matrix
        ) @ current_point.T


        error = np.sqrt(
            residual_variance * leverage
        )


        return True, "计算成功", equivalent, "±"+('{:.3f}'.format(error))
    else:
        return False, "震级必须为数字", 0, 0

if __name__ == "__main__":
    # 默认失败时返回两个None，保证始终输出两行
    res = None
    res2 = None
    try:
        parser = argparse.ArgumentParser(
            description="当量估计算法"
        )
        parser.add_argument(
            "--ml",
            type=float,
            required=True,
            help="需要估算的震级"
        )
        args = parser.parse_args()
        success, message, equivalent, approximation = Cal_equivalent(
            args.ml
        )
        if success:
            res = float(equivalent)
            res2 = approximation

    except Exception:
        res = None
        res2 = None
    print(res)
    print(res2)