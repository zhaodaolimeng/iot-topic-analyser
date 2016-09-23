# 基本步骤  
## 1. 数据提取  
python "../dataprepare.py"  
features.txt为从xively数据集中提取的位置、时间  
texts.txt为从描述信息  

## 2. 生成mallet输入格式  
mallet run cc.mallet.topics.tui.DMRLoader texts.txt features.txt instance.mallet
instance.mallet为DMRLoader生成的mallet输入格式  

## 3. 调用DMR方法  
mallet run cc.mallet.topics.DMRTopicModel --random-seed 1 --output-doc-topics doc-topic30.txt instance.mallet 20 > process-topic30.txt 2>&1
process-0628-topic10-1.txt是一个执行状态和结果的范例，其中包含具体的主题内容  
dmr.state.gz为DMR输出状态，包含每个词对应的主题号
dmr.parameters为DMR最终的参数权重lambda，可以用于计算主题的先验参数alpha  

## 4. 使用python脚本验证查询实例
在dmr/output/文件夹下，从dmr.state.gz解压出dmr.state文件，放入到该目录
删除iot-topic-analyser/dmr文件夹下的step4_word_dict.pickle，执行step4_query.py脚本。

# 注意事项  
topic-number.bat中已经定义了对不同主题数目的测试  
