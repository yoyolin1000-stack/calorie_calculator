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

    # 🌍 安全引入 Font Awesome 圖標與獨立的 style.css 檔案
    st.markdown(
        """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        """,
        unsafe_allow_html=True,
    )
    
    # 讀取剛剛建立的外部 CSS 檔案，確保完全不露出任何明碼字串
    css_path = os.path.join(os.getcwd(), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""

    if not st.session_state["logged_in"]:
        _, center_col, _ = st.columns([1, 1.5, 1])
        with center_col:
            st.markdown('<div class="premium-card" style="margin-top: 100px; text-align: center;">', unsafe_allow_html=True)
            st.markdown('<h2 style="font-weight:700; margin-bottom:10px;">卡路里計算機</h2>', unsafe_allow_html=True)
            st.markdown('<p style="color:#666; font-size:13px; margin-bottom:30px;">請驗證您的成員帳號</p>', unsafe_allow_html=True)
            
            menu = ["登入帳號", "註冊新用戶"]
            choice = st.selectbox("模式切換", menu, label_visibility="collapsed")

            if choice == "註冊新用戶":
                new_user = st.text_input("設定新帳號 ID", key="reg_user", placeholder="請輸入帳號名稱")
                new_password = st.text_input("設定新密碼", type="password", key="reg_pass", placeholder="請輸入密碼")
                if st.button("CREATE ACCOUNT"):
                    if new_user and new_password:
                        if add_user(new_user, new_password):
                            st.success("🎉 註冊成功！請切換至登入模式。")
                        else:
                            st.error("❌ 帳號已被佔用。")
                    else:
                        st.warning("⚠️ 請填妥所有欄位。")

            elif choice == "登入帳號":
                username = st.text_input("帳號 ID", key="login_user", placeholder="Username")
                password = st.text_input("安全密碼", type="password", key="login_pass", placeholder="Password")
                if st.button("LAUNCH SYSTEM"):
                    if login_user(username, password):
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username
                        st.rerun()
                    else:
                        st.error("❌ 認證失敗，請檢查帳號密碼。")
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        with st.sidebar:
            st.markdown(f"<div style='padding:15px; border-radius:10px; background:rgba(255,255,255,0.02); text-align:center;'>👤 當前登入用戶<br><b style='font-size:18px; color:#667eea;'>{st.session_state['username']}</b></div>", unsafe_allow_html=True)
            st.write(" ")
            if st.button("TERMINATE SESSION"):
                st.session_state["logged_in"] = False
                st.session_state["username"] = ""
                st.rerun()

        if st.session_state["username"] == "admin":
            show_advanced_admin_dashboard()
        else:
            st.markdown('<h1 class="main-title">NUTRITION LAB // ⚡</h1>', unsafe_allow_html=True)
            st.markdown('<p class="sub-title">熱量計算與飲食調配系統</p>', unsafe_allow_html=True)

            main_left, main_right = st.columns([1, 1.2], gap="large")

            with main_left:
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='color:#fff; font-weight:600; margin-top:0; margin-bottom:20px;'><i class='fa-solid fa-sliders' style='color:#667eea; margin-right:10px;'></i>01 / 體態配置</h4>", unsafe_allow_html=True)
                
                col_w, col_h, col_a = st.columns(3)
                with col_w:
                    weight = st.number_input("體重 (kg)", min_value=10.0, max_value=300.0, value=70.0)
                with col_h:
                    height = st.number_input("身高 (cm)", min_value=50.0, max_value=250.0, value=170.0)
                with col_a:
                    age = st.number_input("年齡", min_value=1, max_value=120, value=25)
                
                gender = st.radio("生理性別", ["男性", "女性"], horizontal=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='color:#fff; font-weight:600; margin-top:0; margin-bottom:20px;'><i class='fa-solid fa-bullseye' style='color:#764ba2; margin-right:10px;'></i>02 / 活動量與管理目標</h4>", unsafe_allow_html=True)
                
                activity_level = st.select_slider(
                    "日常活動量量表",
                    options=["久坐缺乏運動", "輕度活動", "中度運動量", "高度運動量", "極高運動量"],
                    value="中度運動量"
                )
                activity_mapping = {"久坐缺乏運動": 1.2, "輕度活動": 1.375, "中度運動量": 1.55, "高度運動量": 1.725, "極高運動量": 1.9}
                activity_factor = activity_mapping[activity_level]

                goal = st.radio(
                    "核心目標設定",
                    [
                        "1. 極速減脂模式 (熱量赤字 -500 kcal)",
                        "2. 維持體重模式 (熱量平衡)",
                        "3. 乾淨增肌模式 (熱量盈餘 +300 kcal)"
                    ]
                )
                goal_key = goal[0]
                st.markdown('</div>', unsafe_allow_html=True)
                
                calculate_clicked = st.button("開始計算")

            with main_right:
                if calculate_clicked:
                    if gender == "男性":
                        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
                    else:
                        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

                    tdee = bmr * activity_factor
                    if goal_key == "1":
                        target_calories = tdee - 500
                    elif goal_key == "3":
                        target_calories = tdee + 300
                    else:
                        target_calories = tdee

                    add_weight_record(st.session_state["username"], weight)

                    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                    st.markdown("<h4 style='color:#fff; font-weight:600; margin-top:0; margin-bottom:25px;'><i class='fa-solid fa-chart-simple' style='color:#00d2d3; margin-right:10px;'></i>數據分析報告</h4>", unsafe_allow_html=True)
                    
                    m_col1, m_col2, m_col3 = st.columns(3)
                    with m_col1:
                        st.markdown(f"<p style='margin:0; font-size:12px; color:#888; font-weight:600;'>BMR / 基礎代謝</p><h2 style='margin:5px 0; font-weight:800; color:#fff;'>{round(bmr)}<span style='font-size:12px; color:#666; font-weight:400;'> kcal</span></h2>", unsafe_allow_html=True)
                    with m_col2:
                        st.markdown(f"<p style='margin:0; font-size:12px; color:#888; font-weight:600;'>TDEE / 總熱量消耗</p><h2 style='margin:5px 0; font-weight:800; color:#fff;'>{round(tdee)}<span style='font-size:12px; color:#666; font-weight:400;'> kcal</span></h2>", unsafe_allow_html=True)
                    with m_col3:
                        st.markdown(f"<p style='margin:0; font-size:12px; color:#FF4B4B; font-weight:600;'>TARGET / 目標攝取</p><h2 style='margin:5px 0; font-weight:800; color:#FF4B4B;'>{round(target_calories)}<span style='font-size:12px; color:#ff4b4b44; font-weight:400;'> kcal</span></h2>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                    st.markdown("<h4 style='color:#fff; font-weight:600; margin-top:0; margin-bottom:15px;'><i class='fa-solid fa-utensils' style='color:#ff8f00; margin-right:10px;'></i>配餐建議</h4>", unsafe_allow_html=True)
                    meal_data = generate_dynamic_meal_plan(target_calories, goal_key)
                    df_meals = pd.DataFrame(meal_data)
                    st.dataframe(df_meals, use_container_width=True, hide_index=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                    st.markdown("<h4 style='color:#fff; font-weight:600; margin-top:0; margin-bottom:15px;'><i class='fa-solid fa-chart-line' style='color:#a1c4fd; margin-right:10px;'></i>個人歷史體重趨勢</h4>", unsafe_allow_html=True)
                    history = get_weight_history(st.session_state["username"])
                    if len(history) > 0:
                        df_hist = pd.DataFrame(history, columns=["時間", "體重(kg)"])
                        st.line_chart(df_hist.set_index("時間")["體重(kg)"])
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown(
                        """
                        <div style="border: 2px dashed rgba(255,255,255,0.05); border-radius:20px; padding:60px; text-align:center; color:#666; margin-top:50px;">
                            <i class="fa-solid fa-chart-pie" style="font-size:40px; margin-bottom:20px; color:#333;"></i>
                            <p style="font-size:14px;">等待系統數據啟動中<br>請在左側輸入生理指標，並點擊下方按鈕進行運算報告生成。</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


if __name__ == "__main__":
    main()
