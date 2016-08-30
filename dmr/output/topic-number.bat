@echo off
SET MALLET_HOME="E:\workspace\Mallet"
for /L %%n in (5,1,20) do (
    mallet run cc.mallet.topics.DMRTopicModel instance.mallet  %%n > process-topic%%n-1.log 2>&1
)
