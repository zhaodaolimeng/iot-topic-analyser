# 包含内容

texts.txt 用于存放从每个文档中剥离tags位之后的文本内容
features.txt

# 使用步骤
## 1. 主题提取，执行mallet工具中的DMR方法
mallet run cc.mallet.topics.tui.DMRLoader texts.txt features.txt instance.mallet
instance.mallet为DMRLoader生成的mallet输入格式  
mallet run cc.mallet.topics.DMRTopicModel instance.mallet 30

## 2. 执行上层目录中的step5_query_batch.py脚本对结果进行测试
