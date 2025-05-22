# ui/app.py

import streamlit as st
from ui.components.buttons import primary_button

def main():
    st.set_page_config(page_title="仕事支援AIシステム", layout="wide")
    st.title("多様なニーズを持つ方の仕事支援AIシステム")
    st.sidebar.header("ナビゲーション")
    if primary_button("ジョブ選択", key="job_select"):
        st.write("ジョブ選択画面へ遷移")
    if primary_button("設定", key="settings"):
        st.write("設定画面へ遷移")
    # ...他の画面遷移や状態管理...

if __name__ == "__main__":
    main()
