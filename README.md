多个 ASR 模型的效果对比 Tool:
Paraformer v2, 
Fun-ASR-nano-2512,  
qwen3-ASR-1.7B, 
cohere-transcribe-03-2026，
可以对这几个模型进行 ASR功能的对比测试， 录入语音或者上传语音文件（支持长语音文件）进行几个模型的识别和效果对比。

对如下模型进行效果对比，
Paraformer 离线 Large 长音频版：
https://www.modelscope.cn/models/iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch/files

https://huggingface.co/Qwen/Qwen3-ASR-1.7B
https://modelscope.cn/models/FunAudioLLM/Fun-ASR-Nano-2512
https://huggingface.co/CohereLabs/cohere-transcribe-03-2026


测试结果：Fun-ASR-Nano-2512 — 极轻量 Nano 版，中英文效果的体感比其他几个模型的更好。
