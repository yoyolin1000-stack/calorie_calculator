

import hashlib
from datetime import datetime
import os
import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# 區塊一：密碼加密與安全設定
# ==========================================


def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text


# ==========================================
# 區塊二：資料庫安全連線與函數
# ==========================================


def get_db_connection():
    if os.name != "nt" and os.path.exists("/tmp"):
        db_path = "/tmp/users.db"
    else:
        db_path = os.path.join(os.getcwd(), "users.db")
    return sqlite3.connect(db_path)


def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS weight_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            weight REAL NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    """
    )
    conn.commit()
    conn.close()


def add_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users(username, password) VALUES (?, ?)",
            (username, make_hashes(password)),
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success


def login_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT password FROM users WHERE username = ?", (username,)
    )
    data = c.fetchone()
    conn.close()
    if data:
        return check_hashes(password, data[0])
    return False


def add_weight_record(username, weight):
    conn = get_db_connection()
    c = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute(
        "INSERT INTO weight_history (username, timestamp, weight) VALUES (?, ?, ?)",
        (username, now_str, weight),
    )
    conn.commit()
    conn.close()


def get_weight_history(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT timestamp, weight FROM weight_history WHERE username = ? ORDER BY timestamp ASC",
        (username,),
    )
    data = c.fetchall()
    conn.close()
    return data


# ==========================================
# 區塊三：管理員控制台
# ==========================================


def show_advanced_admin_dashboard():
    st.markdown(
        """
        <style>
        .gradient-text {
            background: linear-gradient(135deg, #FF4B4B, #FF8F00);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 5px;
        }
        .dashboard-card {
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
        .giant-number {
            font-size: 42px;
            font-weight: 900;
            color: #FF4B4B;
            line-height: 1;
            margin: 10px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p class="gradient-text">CORE CONTROL // 核心控制台</p>',
        unsafe_allow_html=True,
    )
    st.write("---")

    conn = get_db_connection()
    df_users = pd.read_sql_query("SELECT username FROM users", conn)
    df_weight = pd.read_sql_query("SELECT * FROM weight_history", conn)
    conn.close()

    total_users = len(df_users)
    total_records = len(df_weight)
    avg_weight = (
        round(df_weight["weight"].mean(), 1) if total_records > 0 else 0
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="dashboard-card">
                <span style="color: #888; font-size: 14px; font-weight: 600;">👥 累計註冊成員</span>
                <div class="giant-number">{total_users} <span style="font-size:16px; color:#888; font-weight:400;">人</span></div>
                <span style="color: #2ED573; font-size: 12px;">● 系統運作正常</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="dashboard-card">
                <span style="color: #888; font-size: 14px; font-weight: 600;">📝 體重總日誌量</span>
                <div class="giant-number" style="color: #FF8F00;">{total_records} <span style="font-size:16px; color:#888; font-weight:400;">筆</span></div>
                <span style="color: #888; font-size: 12px;">資料庫同步正常</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="dashboard-card">
                <span style="color: #888; font-size: 14px; font-weight: 600;">⚖️ 成員平均體重</span>
                <div class="giant-number" style="color: #00D2D3;">{avg_weight} <span style="font-size:16px; color:#888; font-weight:400;">kg</span></div>
                <span style="color: #888; font-size: 12px;">數據即時動態加權</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write(" ")

    tab1, tab2 = st.tabs(["成員帳號管理", "全站體重趨勢"])

    with tab1:
        st.dataframe(
            df_users,
            column_config={
                "username": st.column_config.TextColumn(
                    "使用者帳號 ID",
                    width="medium",
                )
            },
            use_container_width=True,
            hide_index=True,
        )

    with tab2:
        if not df_weight.empty:
            st.line_chart(df_weight.set_index("timestamp")["weight"])
            with st.expander("展開查看原始數據明細"):
                st.dataframe(df_weight, use_container_width=True)
        else:
            st.info("目前尚無任何體重紀錄資料。")


# ==========================================
# 區塊四：飲食建議生成與主程式
# ==========================================


def generate_dynamic_meal_plan(target_calories, goal_key):
    dynamic_meals = []
    meal_ratios = {"早餐": 0.30, "午餐": 0.35, "晚餐": 0.35}

    if goal_key == "1":
        cal = target_calories * meal_ratios["早餐"]
        egg_count = max(1, round(cal * 0.0028))
        toast_slice = max(1, round(cal * 0.0022))
        milk_ml = round(cal * 0.35)
        dynamic_meals.append(
            {
                "時段": "早餐",
                "名稱": "高效燃脂活力早餐",
                "建議食物": f"🥚 水煮蛋 {egg_count} 顆 + 🍞 全麥吐司 {toast_slice} 片 + 🥛 低脂鮮乳 {milk_ml} ml",
                "熱量": f"{round(cal)} kcal",
            }
        )

        cal = target_calories * meal_ratios["午餐"]
        chicken_g = round(cal * 0.32)
        rice_g = round(cal * 0.25)
        dynamic_meals.append(
            {
                "時段": "午餐",
                "名稱": "低卡高蛋白飽腹纖體餐",
                "建議食物": f"🐔 舒肥雞胸肉 {chicken_g} g + 🍚 糙米飯 {rice_g} g + 🥦 水煮綜合青菜 1 大盤",
                "熱量": f"{round(cal)} kcal",
            }
        )

        cal = target_calories * meal_ratios["晚餐"]
        fish_g = round(cal * 0.35)
        sweet_potato_g = round(cal * 0.28)
        dynamic_meals.append(
            {
                "時段": "晚餐",
                "名稱": "輕盈低敏抗氧化調理餐",
                "建議食物": f"🐟 清蒸鱸魚排 {fish_g} g + 🍠 蒸地瓜 {sweet_potato_g} g + 🥬 大蒜炒時蔬 1 盤",
                "熱量": f"{round(cal)} kcal",
            }
        )

    elif goal_key == "3":
        cal = target_calories * meal_ratios["早餐"]
        whey_scoop = max(1, round(cal * 0.0025))
        banana_count = max(1, round(cal * 0.0022))
        toast_slice = max(1, round(cal * 0.0033))
        dynamic_meals.append(
            {
                "時段": "早餐",
                "名稱": "高碳水高蛋白高效增肌早餐",
                "建議食物": f"🥤 乳清蛋白 {whey_scoop} 匙 + 🍌 香蕉 {banana_count} 根 + 🍞 全麥吐司 {toast_slice} 片",
                "熱量": f"{round(cal)} kcal",
            }
        )

        cal = target_calories * meal_ratios["午餐"]
        beef_g = round(cal * 0.35)
        rice_g = round(cal * 0.40)
        dynamic_meals.append(
            {
                "時段": "午餐",
                "名稱": "黃金比例增肌能量便當",
                "建議食物": f"🥩 嫩煎牛里肌 {beef_g} g + 🍚 白米飯 {rice_g} g + 🍳 荷包蛋 1 顆 + 🥗 鮮蔬沙拉",
                "熱量": f"{round(cal)} kcal",
            }
        )

        cal = target_calories * meal_ratios["晚餐"]
        pork_g = round(cal * 0.33)
        pasta_g = round(cal * 0.38)
        dynamic_meals.append(
            {
                "時段": "晚餐",
                "名稱": "肌纖維修復高碳水充醣餐",
                "建議食物": f"🐷 炙烤豬里肌 {pork_g} g + 🍝 義大利麵 {pasta_g} g + 🥦 蒜炒花椰菜",
                "熱量": f"{round(cal)} kcal",
            }
        )

    else:
        cal = target_calories * meal_ratios["早餐"]
        toast_slice = max(1, round(cal * 0.0044))
        milk_ml = round(cal * 0.55)
        dynamic_meals.append(
            {
                "時段": "早餐",
                "名稱": "活力均衡營養早餐",
                "建議食物": f"🍞 全麥吐司 {toast_slice} 片 + 🍳 荷包蛋 2 顆 + 🥛 牛奶 {milk_ml} ml",
                "熱量": f"{round(cal)} kcal",
            }
        )

        cal = target_calories * meal_ratios["午餐"]
        pork_g = round(cal * 0.26)
        rice_g = round(cal * 0.32)
        dynamic_meals.append(
            {
                "時段": "午餐",
                "名稱": "個人輕卡健康便當",
                "建議食物": f"🐷 炒豬瘦肉片 {pork_g} g + 🍚 五穀飯 {rice_g} g + 🥬 炒季節時蔬 2 樣",
                "熱量": f"{round(cal)} kcal",
            }
        )

        cal = target_calories * meal_ratios["晚餐"]
        chicken_g = round(cal * 0.28)
        rice_g = round(cal * 0.28)
        dynamic_meals.append(
            {
                "時段": "晚餐",
                "名稱": "溫馨少油低脂餐",
                "建議食物": f"🐔 香煎雞腿排(去皮) {chicken_g} g + 🍚 糙米飯 {rice_g} g + 🍅 番茄炒蛋 1 大份",
                "熱量": f"{round(cal)} kcal",
            }
        )

    return dynamic_meals


def main():
    init_db()

    st.set_page_config(
        page_title="NUTRITION LAB // 體態分析系統", 
        page_icon="⚡", 
        layout="wide"
    )

    st.markdown(
        """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        html, body,
