import onnxruntime as ort
import numpy as np

# --- 用户需要修改的参数 ---
ONNX_MODEL_PATH = 'model.onnx'

def verify_onnx_model(model_path):
    try:
        print(f"正在加载 ONNX 模型: {model_path}")
        # 1. 创建 ONNX Runtime 推理会话
        session = ort.InferenceSession(model_path)
        print("✅ 模型加载成功！")

        # 2. 获取模型的输入信息
        input_info = session.get_inputs()
        print("\n模型输入节点:")
        for inp in input_info:
            print(f" - 名称: {inp.name}, 形状: {inp.shape}, 类型: {inp.type}")

        input_feed = {}
        for inp in input_info:
            input_shape = [1 if dim is None or isinstance(dim, str) else dim for dim in inp.shape]

            # --- 【代码修正处】---
            # 检查输入是否为标量 (形状为空列表)
            if not input_shape:
                # 如果是标量，创建一个 0 维的 NumPy 数组
                dummy_data = np.array(np.random.rand(), dtype=np.float32)
            else:
                # 否则，按原方式创建张量
                dummy_data = np.random.rand(*input_shape).astype(np.float32)
            # --- 【修正结束】---

            input_feed[inp.name] = dummy_data
            print(f"\n为 '{inp.name}' 生成了形状为 {dummy_data.shape} 的随机数据。")

        output_names = [output.name for output in session.get_outputs()]
        print(f"\n正在执行推理... 输出节点: {output_names}")
        outputs = session.run(output_names, input_feed)

        print("\n✅ 推理执行成功！")
        print("输出结果的形状:")
        for name, out_tensor in zip(output_names, outputs):
            print(f" - {name}: {out_tensor.shape}")

        return True

    except Exception as e:
        print(f"❌ 模型验证失败: {e}")
        return False

if __name__ == '__main__':
    verify_onnx_model(ONNX_MODEL_PATH)