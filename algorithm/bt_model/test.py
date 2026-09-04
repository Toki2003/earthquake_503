import tensorflow._api.v2.compat.v1 as tf

tf.disable_v2_behavior()

# --- 用户需要修改的参数 ---
# Checkpoint 文件的 meta 图定义
META_FILE = 'model.ckpt.meta'
# Checkpoint 文件所在的目录和前缀
CHECKPOINT_FILE = 'model.ckpt'
# 最终输出的冻结图 .pb 文件名
OUTPUT_PB_FILE = 'frozen_model.pb'
# 【非常重要】输出节点的名称，替换成你在上一步找到的名称
# 注意：这里只需要提供操作名，不需要后面的 :0
# 例如，如果节点全名是 "output/predictions:0"，这里就填 "output/predictions"
# 如果有多个输出节点，用逗号隔开，例如 ["output1", "output2"]
OUTPUT_NODE_NAMES = "Softmax"  # <--- 修改这里


def freeze_graph():
    """
    Loads a TensorFlow checkpoint and freezes the graph.
    """
    with tf.Session() as sess:
        print("Loading graph definition from meta file...")
        saver = tf.train.import_meta_graph(META_FILE, clear_devices=True)

        print("Restoring weights from checkpoint...")
        saver.restore(sess, CHECKPOINT_FILE)

        graph_def = sess.graph.as_graph_def()

        print("Freezing the graph...")
        # 【CHANGE IS HERE】 Call the function through the main 'tf' module
        output_graph_def = tf.graph_util.convert_variables_to_constants(
            sess=sess,
            input_graph_def=graph_def,
            output_node_names=OUTPUT_NODE_NAMES.split(",")
        )

        with tf.gfile.GFile(OUTPUT_PB_FILE, "wb") as f:
            f.write(output_graph_def.SerializeToString())

        print(f"✅ Graph frozen successfully! Saved to {OUTPUT_PB_FILE}")


if __name__ == '__main__':
    freeze_graph()