import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# --- 1. 页面设置 ---
st.set_page_config(page_title="Nano Banana 2 旗舰控制台", layout="wide")

# --- 2. 初始化多任务存储 ---
if "all_chats" not in st.session_state:
    # 结构：{ "任务名": [ {"role": "user", "content": "..."}, ... ] }
    st.session_state.all_chats = {"默认任务": []}
if "current_chat_name" not in st.session_state:
    st.session_state.current_chat_name = "默认任务"

# --- 3. 侧边栏：多任务管理与参数 ---
with st.sidebar:
    st.title("📂 任务管理")
    
    # 新建任务
    new_chat_name = st.text_input("新建任务名称", placeholder="例如：面料还原A")
    if st.button("➕ 创建并切换"):
        if new_chat_name and new_chat_name not in st.session_state.all_chats:
            st.session_state.all_chats[new_chat_name] = []
            st.session_state.current_chat_name = new_chat_name
            st.rerun()

    # 任务切换器
    st.session_state.current_chat_name = st.selectbox(
        "当前进行中的任务", 
        options=list(st.session_state.all_chats.keys()),
        index=list(st.session_state.all_chats.keys()).index(st.session_state.current_chat_name)
    )

    st.divider()
    
    # 💾 保存按钮：将当前任务记录导出为文本
    st.title("💾 数据导出")
    chat_history = st.session_state.all_chats[st.session_state.current_chat_name]
    if chat_history:
        # 将对话历史转换为纯文本格式
        history_text = ""
        for msg in chat_history:
            history_text += f"{msg['role'].upper()}:\n{msg['content']}\n\n"
        
        st.download_button(
            label="📥 下载当前任务记录 (.txt)",
            data=history_text,
            file_name=f"{st.session_state.current_chat_name}_记录.txt",
            mime="text/plain"
        )
    else:
        st.info("暂无记录可导出")

    st.divider()
    
    # 模型与参数
    st.title("⚙️ 模型配置")
    user_key = st.text_input("API Key", type="password")
    temp = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    model_choice = st.selectbox("选择模型", ["gemini-1.5-flash", "gemini-1.5-pro"])

# --- 4. 主界面：对话区 ---
st.title(f"🚀 {st.session_state.current_chat_name}")

if not user_key:
    st.warning("👈 请在左侧侧边栏填入 API Key。")
else:
    genai.configure(api_key=user_key)
    model = genai.GenerativeModel(model_choice)
    
    # 渲染当前选中的任务历史
    current_history = st.session_state.all_chats[st.session_state.current_chat_name]
    for msg in current_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- 输入区 (底部固定) ---
    prompt = st.chat_input("输入指令或上传图片...")
    uploaded_file = st.file_uploader("上传图片参考", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")

    if prompt or uploaded_file:
        # 1. 处理用户输入并显示
        user_display = prompt if prompt else "[仅上传了图片]"
        with st.chat_message("user"):
            st.markdown(user_display)
        
        # 2. 调用 API
        with st.spinner("Nano Banana 正在处理..."):
            try:
                inputs = []
                if prompt: inputs.append(prompt)
                if uploaded_file:
                    img = Image.open(uploaded_file)
                    # 自动缩放防止超大图卡顿 (针对你20MB+的需求)
                    if max(img.size) > 2048:
                        img.thumbnail((2048, 2048))
                    inputs.append(img)
                
                # 注入历史记忆：取当前任务最近5轮对话
                history_context = ""
                for m in current_history[-10:]: # 5轮对话=10条记录
                    history_context += f"{m['role']}: {m['content']}\n"
                
                final_payload = inputs
                if history_context:
                    final_payload.insert(0, f"以下是之前的对话背景：\n{history_context}")

                response = model.generate_content(final_payload, generation_config={"temperature": temp})
                
                # 3. 显示 AI 回复并存入历史
                with st.chat_message("assistant"):
                    st.markdown(response.text)
                
                # 更新 session_state 里的记录
                st.session_state.all_chats[st.session_state.current_chat_name].append({"role": "user", "content": user_display})
                st.session_state.all_chats[st.session_state.current_chat_name].append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"处理失败: {e}")