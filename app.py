import streamlit as st
import google.generativeai as genai
from PIL import Image

# 页面基础配置
st.set_page_config(page_title="Nano Banana 2 高级终端", layout="wide")

# --- 侧边栏：API 权限与参数 ---
with st.sidebar:
    st.title("🔑 权限配置")
    user_key = st.text_input("填入 Gemini API Key", type="password")
    st.divider()
    st.title("🎛️ 出图参数")
    model_name = "gemini-3.1-flash-image-preview" # 香蕉 API 最新版
    temp = st.slider("Temperature (创意度)", 0.0, 2.0, 1.0)
    st.info("💡 1.0 以上适合参考出图，0.3 适合精准还原。")

# --- 主界面 ---
st.title("🍌 Nano Banana 多图参考处理站")

if not user_key:
    st.warning("👈 请在左侧侧边栏填入 API Key 启动工具。")
else:
    try:
        genai.configure(api_key=user_key)
        model = genai.GenerativeModel(model_name)
        
        # 支持多文件上传
        uploaded_files = st.file_uploader("上传参考图 (支持 20MB+ / 可多选)", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
        
        processed_images = []
        if uploaded_files:
            cols = st.columns(len(uploaded_files))
            for idx, file in enumerate(uploaded_files):
                img = Image.open(file)
                # 针对超大图的核心优化：只要有一边超过 2048px 就自动缩放
                if max(img.size) > 2048:
                    img.thumbnail((2048, 2048))
                
                processed_images.append(img)
                with cols[idx]:
                    st.image(img, caption=f"参考图 {idx+1}", use_container_width=True)
            
            # 指令区域
            prompt = st.text_area("出图指令", placeholder="例如：参考图1的材质和图2的色彩，生成一张新的设计建议图...")
            
            if st.button("🚀 开始出图/分析"):
                with st.spinner("正在调用 Google API 处理超大素材..."):
                    # 构建内容列表：[指令, 图片1, 图片2...]
                    content = [prompt] + processed_images
                    
                    response = model.generate_content(
                        content, 
                        generation_config={"temperature": temp}
                    )
                    st.success("处理完成！")
                    st.markdown("### 🤖 结果预览")
                    st.write(response.text)
                    
    except Exception as e:
        st.error(f"发生错误: {e}")