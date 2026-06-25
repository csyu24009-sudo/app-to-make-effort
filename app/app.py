import streamlit as st
import json
import os
from datetime import date, timedelta

# データ保存用のファイル名
DATA_FILE = "task_data.json"

# ------------------------------------------------------------------
# データの読み込み・保存関数
# ------------------------------------------------------------------
def load_data():
    """JSONファイルからタスクデータを読み込む。存在しない場合は初期値を返す。"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 文字列の日付を date オブジェクトに変換
            if data["last_completed_date"]:
                data["last_completed_date"] = date.fromisoformat(data["last_completed_date"])
            return data
    else:
        return {
            "task_name": "毎日の筋トレ・読書など",
            "current_streak": 0,
            "last_completed_date": None,
            "is_locked": False
        }

def save_data(data):
    """タスクデータをJSONファイルに保存する。"""
    # date オブジェクトを文字列に変換して保存
    save_data = data.copy()
    if save_data["last_completed_date"]:
        save_data["last_completed_date"] = save_data["last_completed_date"].isoformat()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=4, ensure_ascii=False)

# ------------------------------------------------------------------
# 日付変更に伴う内部状態の更新ロジック (システム要件 ①)
# ------------------------------------------------------------------
def update_task_status(data):
    today = date.today()
    last_date = data["last_completed_date"]
    
    if last_date is None:
        return data

    # 1. 強制ロック（お休み）中の場合の判定
    if data["is_locked"]:
        # 最後に完了した日（＝3日目達成日）から2日以上経っていれば、お休み日（翌日）が終了したとみなす
        if today >= last_date + timedelta(days=2):
            data["is_locked"] = False
            data["current_streak"] = 0  # カウント0から再開

    # 2. 通常時に、未達成のまま日付が空いた（三日坊主）場合の判定
    elif not data["is_locked"] and today > last_date + timedelta(days=1):
        # 最後に完了したのが「昨日」より前なら、連続記録はストップしてリセット
        # ※ただし、今日すでに完了ボタンを押す前なので、ここでは0に戻す
        if today != last_date:
            data["current_streak"] = 0

    return data

# ------------------------------------------------------------------
# メインアプリケーション画面
# ------------------------------------------------------------------
def main():
    st.set_page_config(page_title="三日坊主防止アプリ", page_icon="🐢", layout="centered")
    
    # データの初期化と状態更新
    data = load_data()
    data = update_task_status(data)
    save_data(data)

    st.title("🐢 三日坊主防止アプリ")
    st.caption("〜 3日頑張ったら、1日全力で休む！ 〜")
    st.write("---")

    # タスク名の変更機能
    new_task_name = st.text_input("習慣化したいタスク名", value=data["task_name"])
    if new_task_name != data["task_name"]:
        data["task_name"] = new_task_name
        save_data(data)

    # 現在の日付情報
    today = date.today()
    
    # 今日すでに報告済みかどうかの判定
    already_completed_today = (data["last_completed_date"] == today)

    # --------------------------------------------------------------
    # キャラクター表示と進捗確認 (ユーザー要件 ②)
    # --------------------------------------------------------------
    st.subheader("現在の進捗と相棒の状態")
    
    # 連続日数に応じたメーター表示
    streak = data["current_streak"]
    st.progress(streak / 3, text=f"3日連続中： {streak} 日達成！")

    # キャラクターの状態分け
    if data["is_locked"]:
        # お休み状態
        st.info("### 😴 カメ先輩：『今日はお休みフラグ発動中！』")
        st.warning("よくやった！規約通り、今日は絶対にタスクをしちゃいけない日だぞ。ゲームでもしてダラダラ過ごすべし！")
    elif streak == 0 and already_completed_today:
        # 3日達成直後（内部カウントは0リセットされているが、今日完了したばかりの状態）
        st.success("### 🎉 カメ先輩：『うおおおお！3日連続達成おめでとう！！！』")
        st.balloons() # クラッカー演出
        st.subheader("✨ 盛大な褒め演出発動中 ✨")
        st.write("君の継続力は本物だ！素晴らしい！さあ、**明日はシステムが強制ロックされる「公式お休み日」**だ。明日に備えて今日は美味いものでも食べなさい！")
    elif streak == 0:
        st.info("### 😐 カメ先輩：『さあ、新しいサイクルの始まりだ』")
        st.write("プレッシャーを感じる必要はない。まずは今日1日、一歩を踏み出してみよう。")
    elif streak == 1:
        st.info("### 🙂 カメ先輩：『よしよし、1日目クリアだな』")
        st.write("良いスタートだ！明日もこの調子で、気楽にいこう。")
    elif streak == 2:
        st.warning("### 🔥 カメ先輩：『おっ、2日連続！明日でご褒美だぞ！』")
        st.write("明日クリアすれば、明後日は強制お休み日だ！あと1日だけ楽しもう！")

    st.write("---")

    # --------------------------------------------------------------
    # タスク完了チェック・強制ロック制御 (ユーザー要件 ①, ③ / システム要件 ②)
    # --------------------------------------------------------------
    st.subheader("今日の報告")

    if data["is_locked"]:
        # 強制ロック状態
        st.button("お休み期間中のためロックされています", disabled=True, key="btn_lock")
    elif already_completed_today:
        # 今日は報告済み
        st.button("今日の報告は完了しています！", disabled=True, key="btn_done")
    else:
        # タスク完了ボタン（有効状態）
        if st.button("報告する：今日のタスクを完了した！", type="primary", key="btn_active"):
            # 完了処理
            data["last_completed_date"] = today
            
            # 連続日数の更新
            if data["current_streak"] < 2:
                data["current_streak"] += 1
            elif data["current_streak"] == 2:
                # 3日連続達成時の処理 (システム要件 ②)
                data["is_locked"] = True
                # 次回のためにカウントは内部で0にリセット
                data["current_streak"] = 0
            
            save_data(data)
            st.rerun()

    # デバッグ用：データを初期状態に戻したい場合（開発時用）
    with st.sidebar:
        st.header("開発用メニュー")
        if st.button("データを完全にリセットする"):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.rerun()

if __name__ == "__main__":
    main()