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
# 區塊二：支援雲端環境的資料庫安全連線與函數
# ==========================================


def get_db_connection():
    """確保在 Streamlit Cloud 雲端 Linux 環境有正確的讀寫路徑"""
    if os.name != "nt" and os.path.exists("/tmp"):
        db_path = "/tmp/users.db"
    else:
        db_path = os.path.join(os.getcwd(), "users.db")
    return sqlite3.connect(db_path)


def init_db():
    """初始化 SQLite 資料庫與資料表"""
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
    """註冊新用戶"""
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
    """登入驗證"""
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
    """新增一筆體重紀錄"""
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
    """讀取使用者的所有體重歷史紀錄"""
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
# 區塊三：✨ 高級感客製化管理員控制台 (不像是 AI 做的排版)
# ==========================================


def show_advanced_admin_dashboard():
    # 注入自訂高級感 CSS：改變字體、卡片陰影與漸層標題
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
            margin-bottom: 20px;
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
            font-size: 48px;
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
        '<p class="gradient-text">🔮 CORE CONTROL // 核心控制台</p>',
        unsafe_allow_html=True,
    )
    st.caption("歡迎回來，最高權限管理員。以下為當前雲端伺服器的即時運作數據。")
    st.write("---")

    # 數據準備（從 SQLite 撈取）
    conn = get_db_connection()
    df_users = pd.read_sql_query("SELECT username FROM users", conn)
    df_weight = pd.read_sql_query("SELECT * FROM weight_history", conn)
    conn.close()

    total_users = len(df_users)
    total_records = len(df_weight)
    avg_weight = (
        round(df_weight["weight"].mean(), 1) if total_records > 0 else 0
    )

    # 橫向三欄式「數據看板網格」
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="dashboard-card">
                <span style="color: #888; font-size: 14px; font-weight: 600;">👥 累計註冊成員</span>
                <div class="giant-number">{total_users} <span style="font-size:18px; color:#555;">人</span></div>
                <span style="color: #2ED573; font-size: 12px;">▲ 運作中 (🟢 Online)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="dashboard-card">
                <span style="color: #888; font-size: 14px; font-weight: 600;">📝 體重總日誌量</span>
                <div class="giant-number" style="color: #FF8F00;">{total_records} <span style="font-size:18px; color:#555;">筆</span></div>
                <span style="color: #888; font-size: 12px;">資料庫讀寫正常</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="dashboard-card">
                <span style="color: #888; font-size: 14px; font-weight: 600;">⚖️ 成員平均體重</span>
                <div class="giant-number" style="color: #00D2D3;">{avg_weight} <span style="font-size:18px; color:#555;">kg</span></div>
                <span style="color: #888; font-size: 12px;">動態加權平均值</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write(" ")

    # 使用雙分頁（Tabs）切換不同的數據分類
    tab1, tab2 = st.tabs(["🔒 成員帳號管理庫", "📈 全站體重數據流"])

    with tab1:
        st.markdown("### 📋 目前活躍用戶清單")
        st.dataframe(
            df_users,
            column_config={
                "username": st.column_config.TextColumn(
                    "使用者帳號 ID",
                    help="成員登入系統時所使用的唯一代碼",
                    width="medium",
                )
            },
            use_container_width=True,
            hide_index=True,
        )

    with tab2:
        st.markdown("### 📊 即時變動日誌流")
        if not df_weight.empty:
            # 極簡高質感折線圖
            st.line_chart(df_weight.set_index("timestamp")["weight"])
            with st.expander("🔍 展開查看原始 SQL 數據明細"):
                st.dataframe(df_weight, use_container_width=True)
        else:
            st.info("目前雲端尚無任何體重紀錄資料。")


# ==========================================
# 區塊四：主程式運作邏輯 (卡路里計算機主體)
# ==========================================


def generate_dynamic_meal_plan(target_calories, goal_key):
    """根據目標熱量與減重/增肌目標，動態產生高自由度飲食推薦選單"""
    dynamic_meals = []
    meal_ratios = {"早餐": 0.30, "午餐": 0.35, "晚餐": 0.35}

    if goal_key == "1":  # 【極速減脂模式】
        cal = target_calories * meal_ratios["早餐"]
        egg_count = max(1, round(cal * 0.0028))
        toast_slice = max(1, round(cal * 0.0022))
        milk_ml = round(cal * 0.35)
        dynamic_meals.append(
            {
                "時段": "早餐",
                "名稱": "高效燃脂活力早餐",
                "食物": f"🥚 水煮蛋 {egg_count} 顆 + 🍞 全麥吐司 {toast_slice} 片 + 🥛 低脂鮮乳 {milk_ml} ml",
                "熱量": round(cal),
            }
        )

        cal = target_calories * meal_ratios["午餐"]
        chicken_g = round(cal * 0.32)
        rice_g = round(cal * 0.25)
        dynamic_meals.append(
            {
                "時段": "午餐",
                "名稱": "低卡高蛋白飽腹纖體餐",
                "食物": f"🐔 舒肥雞胸肉 {chicken_g} g + 🍚 糙米飯 {rice_g} g + 🥦 水煮綜合青菜 1 大盤",
                "熱量": round(cal),
            }
        )

        cal = target_calories * meal_ratios["晚餐"]
        fish_g = round(cal * 0.35)
        sweet_potato_g = round(cal * 0.28)
        dynamic_meals.append(
            {
                "時段": "晚餐",
                "名稱": "輕盈低敏抗氧化調理餐",
                "食物": f"🐟 清蒸鱸魚排 {fish_g} g + 🍠 蒸地瓜 {sweet_potato_g} g + 🥬 大蒜炒時蔬 1 盤",
                "熱量": round(cal),
            }
        )

    elif goal_key == "3":  # 【乾淨增肌模式】
        cal = target_calories * meal_ratios["早餐"]
        whey_scoop = max(1, round(cal * 0.0025))
        banana_count = max(1, round(cal * 0.0022))
        toast_slice = max(1, round(cal * 0.0033))
        dynamic_meals.append(
            {
                "時段": "早餐",
                "名稱": "高碳水高蛋白高效增肌早餐",
                "食物": f"🥤 乳清蛋白 {whey_scoop} 匙 + 🍌 香蕉 {banana_count} 根 + 🍞 全麥吐司 {toast_slice} 片",
                "熱量": round(cal),
            }
        )

        cal = target_calories * meal_ratios["午餐"]
        beef_g = round(cal * 0.35)
        rice_g = round(cal * 0.40)
        dynamic_meals.append(
            {
                "時段": "午餐",
                "名稱": "黃金比例增肌能量便當",
                "食物": f"🥩 嫩煎牛里肌 {beef_g} g + 🍚 白米飯 {rice_g} g + 🍳 荷包蛋 1 顆 + 🥗 鮮蔬沙拉",
                "熱量": round(cal),
            }
        )

        cal = target_calories * meal_ratios["晚餐"]
        pork_g = round(cal * 0.33)
        pasta_g = round(cal * 0.38)
        dynamic_meals.append(
            {
                "時段": "晚餐",
                "名稱": "肌纖維修復高碳水充醣餐",
                "食物": f"🐷 炙烤豬里肌 {pork_g} g + 🍝 義大利麵 {pasta_g} g + 🥦 蒜炒花椰菜",
                "熱量": round(cal),
            }
        )

    else:  # 【維持體重健康飲食模式】
        cal = target_calories * meal_ratios["早餐"]
        toast_slice = max(1, round(cal * 0.0044))
        milk_ml = round(cal * 0.55)
        dynamic_meals.append(
            {
                "時段": "早餐",
                "名稱": "活力均衡網頁早餐",
                "食物": f"🍞 全麥吐司 {toast_slice} 片 + 🍳 荷包蛋 2 顆 + 🥛 牛奶 {milk_ml} ml",
                "熱量": round(cal),
            }
        )

        cal = target_calories * meal_ratios["午餐"]
        pork_g = round(cal * 0.26)
        rice_g = round(cal * 0.32)
        dynamic_meals.append(
            {
                "時段": "午餐",
                "名稱": "上班族輕卡健康便當",
                "食物": f"🐷 炒豬瘦肉片 {pork_g} g + 🍚 五穀飯 {rice_g} g + 🥬 炒季節時蔬 2 樣",
                "熱量": round(cal),
            }
        )

        cal = target_calories * meal_ratios["晚餐"]
        chicken_g = round(cal * 0.28)
        rice_g = round(cal * 0.28)
        dynamic_meals.append(
            {
                "時段": "晚餐",
                "名稱": "家庭溫馨少油低脂餐",
                "食物": f"🐔 香煎雞腿排(去皮) {chicken_g} g + 🍚 糙米飯 {rice_g} g + 🍅 番茄炒蛋 1 大份",
                "熱量": round(cal),
            }
        )

    return dynamic_meals


def main():
    init_db()

    # 1. 網頁基本設定（改為寬敞佈局寬度）
    st.set_page_config(
        page_title="NUTRITION LAB // 體態分析系統", 
        page_icon="⚡", 
        layout="wide"
    )

    # 2. ⚡ 網頁頂級視覺美化魔法 (注入 Google 字體與 Font Awesome 圖標)
    st.markdown(
        """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
        /* 全站字體與背景微調 */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }
        
        /* 高級客製化卡片外框 */
        .premium-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease, border-color 0.3s ease;
        }
        .premium-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
        }
        
        /* 網頁標題與副標題 */
        .main-title {
            font-weight: 800;
            letter-spacing: -1.5px;
            background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 42px;
            margin-bottom: 5px;
        }
        .sub-title {
            color: #8892b0;
            font-size: 14px;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 40px;
        }
        
        /* 完全擺脫 AI 感的極簡按鈕設計 */
        div.stButton > button:first-child {
            background: #ffffff !important;
            color: #000000 !important;
            border-radius: 30px !important;
            border: none !important;
            padding: 12px 35px !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            letter-spacing: 0.5px !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1) !important;
            width: auto !important;
            margin: 20px auto 0 auto !important;
            display: block !important;
        }
        div.stButton > button:first-child:hover {
            background: #667eea !important;
            color: #ffffff !important;
            box-shadow: 0 6px 25px rgba(102, 126, 234, 0.4) !important;
            transform: scale(1.03);
        }

        /* 改造 Streamlit 原生輸入框底色 */
        .stTextInput input, .stNumberInput input {
            background-color: rgba(255, 255, 255, 0.01) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            color: #fff !important;
            padding: 12px !important;
        }
        .stTextInput input:focus, .stNumberInput input:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 1px #667eea !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""

    # ==================== 頁面邏輯開始 ====================
    if not st.session_state["logged_in"]:
        # 🔒 未登入：極簡置中登入卡片
        _, center_col, _ = st.columns([1, 1.5, 1])
        with center_col:
            st.markdown('<div class="premium-card" style="margin-top: 100px; text-align: center;">', unsafe_allow_html=True)
            st.markdown('<h2 style="font-weight:700; margin-bottom:10px;">SYSTEM SIGN IN</h2>', unsafe_allow_html=True)
            st.markdown('<p style="color:#666; font-size:13px; margin-bottom:30px;">請驗證您的雲端成員帳據</p>', unsafe_allow_html=True)
            
            menu = ["登入帳號", "註冊新用戶"]
            choice = st.selectbox("核心操作模式", menu, label_visibility="collapsed")

            if choice == "註冊新用戶":
                new_user = st.text_input("設定新帳號 ID", key="reg_user", placeholder="請輸入帳號名稱")
                new_password = st.text_input("設定新安全密碼", type="password", key="reg_pass", placeholder="請輸入密碼")
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
        # ==================== 登入成功區塊 ====================
        with st.sidebar:
            st.markdown(f"<div style='padding:15px; border-radius:10px; background:rgba(255,255,255,0.02); text-align:center;'>👤 Active Session<br><b style='font-size:18px; color:#667eea;'>{st.session_state['username']}</b></div>", unsafe_allow_html=True)
            st.write(" ")
            if st.button("TERMINATE SESSION"):
                st.session_state["logged_in"] = False
                st.session_state["username"] = ""
                st.rerun()

        # 🎯 系統權限分流
        if st.session_state["username"] == "admin":
            show_advanced_admin_dashboard()
        else:
            # 🟢 一般用戶主頁面：精緻大標題
            st.markdown('<h1 class="main-title">NUTRITION LAB // 💻</h1>', unsafe_allow_html=True)
            st.markdown('<p class="sub-title">Automated Caloric Reductions & Dynamic Meal Engineering</p>', unsafe_allow_html=True)

            # 🛠️ 橫向切分兩大專業區塊 (左邊輸入數據，右邊動態即時顯示結果)
            main_left, main_right = st.columns([1, 1.2], gap="large")

            with main_left:
                # 卡片一：身體特徵
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='color:#fff; font-weight:600; margin-top:0; margin-bottom:20px;'><i class='fa-solid fa-sliders' style='color:#667eea; margin-right:10px;'></i>01 / METRIC CONFIG</h4>", unsafe_allow_html=True)
                
                col_w, col_h, col_a = st.columns(3)
                with col_w:
                    weight = st.number_input("體重 (kg)", min_value=10.0, max_value=300.0, value=70.0)
                with col_h:
                    height = st.number_input("身高 (cm)", min_value=50.0, max_value=250.0, value=170.0)
                with col_a:
                    age = st.number_input("年齡 (Age)", min_value=1, max_value=120, value=25)
                
                gender = st.radio("生理性別 (Gender)", ["男性", "女性"], horizontal=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # 卡片二：目標與活動量
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='color:#fff; font-weight:600; margin-top:0; margin-bottom:20px;'><i class='fa-solid fa-bullseye' style='color:#764ba2; margin-right:10px;'></i>02 / ACTIVITY & GOALS</h4>", unsafe_allow_html=True)
                
                activity_level = st.select_slider(
                    "日常物理活動量層級",
                    options=["久坐缺乏運動", "輕度活動", "中度運動量", "高度運動量", "極高運動量"],
                    value="中度運動量"
                )
                activity_mapping = {"久坐缺乏運動": 1.2, "輕度活動": 1.375, "中度運動量": 1.55, "高度運動量": 1.725, "極高運動量": 1.9}
                activity_factor = activity_mapping[activity_level]

                goal = st.radio(
                    "終極管理目標設定",
                    [
                        "1. 極速減脂模式 (熱量赤字 -500 kcal)",
                        "2. 維持體重健康飲食模式 (熱量平衡)",
                        "3. 乾淨增肌模式 (熱量盈餘 +300 kcal)"
                    ]
                )
                goal_key = goal[0]
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 計算觸發鈕
                calculate_clicked = st.button("EXECUTE ALGORITHM 🚀")

            with main_right:
                # 右側：預設靜態與動態計算報告
                if calculate_clicked:
                    # 執行演算法核心公式
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

                    # 💎 頂級 SaaS 風格的數據面板
                    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                    st.markdown("<h4 style='color:#fff; font-weight:600; margin-top:0; margin-bottom:25px;'><i class='fa-solid fa-chart-simple' style='color:#00d2d3; margin-right:10px;'></i>DIAGNOSTIC REPORT</h4>", unsafe_allow_html=True)
                    
                    m_col1, m_col2, m_col3 = st.columns(3)
                    with m_col1:
                        st.markdown(f"<p style='margin:0; font-size:11px; color:#888; font-weight:600;'>BMR / 基礎代謝</p><h2 style='margin:5px 0; font-weight:800; color:#fff;'>{round(bmr)}<span style='font-size:12px; color:#444; font-weight:400;'> kcal</span></h2>", unsafe_allow_html=True)
                    with m_col2:
                        st.markdown(f"<p style='margin:0; font-size:11px; color:#888; font-weight:600;'>TDEE / 總消耗</p><h2 style='margin:5px 0; font-weight:800; color:#fff;'>{round(tdee)}<span style='font-size:12px; color:#444; font-weight:400;'> kcal</span></h2>", unsafe_allow_html=True)
                    with m_col3:
                        st.markdown(f"<p style='margin:0; font-size:11px; color:#FF4B4B; font-weight:600;'>TARGET / 目標攝取</p><h2 style='margin:5px 0; font-weight:800; color:#FF4B4B;'>{round(target_calories)}<span style='font-size:12px; color:#ff4b4b44; font-weight:400;'> kcal</span></h2>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # 💎 飲食推薦表格卡片
                    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                    st.markdown("<h4 style='color:#fff; font-weight:600; margin-top:0; margin-bottom:15px;'><i class='fa-solid fa-utensils' style='color:#ff8f00; margin-right:10px;'></i>MEAL INGREDIENT RECOMENDATION</h4>", unsafe_allow_html=True)
                    meal_data = generate_dynamic_meal_plan(target_calories, goal_key)
                    df_meals = pd.DataFrame(meal_data)
                    st.dataframe(df_meals, use_container_width=True, hide_index=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # 💎 歷史走勢圖卡片
                    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                    st.markdown("<h4 style='color:#fff; font-weight:600; margin-top:0; margin-bottom:15px;'><i class='fa-solid fa-chart-line' style='color:#a1c4fd; margin-right:10px;'></i>WEIGHT LOGS OVER TIME</h4>", unsafe_allow_html=True)
                    history = get_weight_history(st.session_state["username"])
                    if len(history) > 0:
                        df_hist = pd.DataFrame(history, columns=["時間", "體重(kg)"])
                        st.line_chart(df_hist.set_index("時間")["體重(kg)"])
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # 提示點擊引導
                    st.markdown(
                        """
                        <div style="border: 2px dashed rgba(255,255,255,0.05); border-radius:20px; padding:60px; text-align:center; color:#444; margin-top:50px;">
                            <i class="fa-solid fa-terminal" style="font-size:40px; margin-bottom:20px; color:#222;"></i>
                            <p style="font-size:14px; letter-spacing:0.5px;">Awaiting parameter sequence execution...<br>請在左側配置生理數據，並點擊 "Execute Algorithm" 啟動雲端運算。</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


if __name__ == "__main__":
    main()

