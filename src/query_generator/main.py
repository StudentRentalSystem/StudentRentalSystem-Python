import sys
import os
import json
import threading
from queue import Queue

# --- 重要：解決 Import 路徑問題 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
llm_data_parser_dir = os.path.join(src_dir, "llm_data_parser")

if src_dir not in sys.path:
    sys.path.append(src_dir)

if llm_data_parser_dir not in sys.path:
    sys.path.append(llm_data_parser_dir)
# -------------------------------

from llm_data_parser.config import LLMConfig, LLMMode
from llm_data_parser.client import LLMClient
from query_generator.app import MiniRagApp
from query_generator.settings import LLM_SERVER_ADDRESS, LLM_SERVER_PORT, LLM_MODEL_TYPE

# 嘗試匯入 API KEY，如果 settings.py 沒有這個變數則設為 None
try:
    from query_generator.settings import LLM_API_KEY
except ImportError:
    LLM_API_KEY = None


# === 攔截器 (Monkey Patch) ===
def install_spy(mini_rag_instance):
    try:
        client = getattr(mini_rag_instance, 'llm_client', None) or getattr(mini_rag_instance, 'client', None)
        if client:
            # 注入 API KEY 到原本的 config (如果是透過 App 初始化)
            if LLM_API_KEY:
                client.config.api_key = LLM_API_KEY
                print(f"🔑 已注入 API Key 到 MiniRagApp Client")

            original_method = client.call_local_model

            def spy_call_local_model(prompt, *args, **kwargs):
                if "JSON" in prompt or "json" in prompt:
                    print(f"\n[🔍 SPY] 攔截到 Prompt 請求:\n{prompt[:100]}...")
                return original_method(prompt, *args, **kwargs)

            client.call_local_model = spy_call_local_model
            print("✅ 已安裝內部監聽器")
    except Exception as e:
        print(f"⚠️ 安裝監聽器失敗: {e}")


def main():
    print(f"🔄 初始化系統中...")
    print(f"📍 連線目標: {LLM_SERVER_ADDRESS}:{LLM_SERVER_PORT} (Model: {LLM_MODEL_TYPE})")
    if LLM_API_KEY:
        print(f"🔑 API Key: 已載入 ({LLM_API_KEY[:4]}***)")
    else:
        print(f"⚠️ API Key: 未設定 (如果遇到 403 錯誤，請在 settings.py 加入 LLM_API_KEY)")

    try:
        mini_rag = MiniRagApp()
        install_spy(mini_rag)
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return

    use_mongodb = True
    print("\n✨ MiniRAG 啟動成功！")
    print("------------------------------------------------------")
    print("指令說明:")
    print("  [文字]   輸入租屋需求查詢")
    print("  rental   切換為 MongoDB 租屋查詢模式 (預設)")
    print("  others   切換為一般聊天模式")
    print("  debug    [新增] 測試模型原始輸出 (檢查 JSON 格式)")
    print("  exit     離開程式")
    print("------------------------------------------------------")

    while True:
        try:
            mode_name = "租屋搜尋(MongoDB)" if use_mongodb else "一般聊天(Chat)"
            prompt_text = f"\n[{mode_name}] 請輸入需求: "
            user_query = input(prompt_text).strip()

            if not user_query:
                continue

            # 指令處理
            if user_query.lower() == "exit":
                break
            elif user_query.lower() == "others":
                use_mongodb = False
                print("🔀 已切換至：一般聊天模式")
                continue
            elif user_query.lower() == "rental":
                use_mongodb = True
                print("🔀 已切換至：租屋搜尋模式")
                continue
            elif user_query.lower() == "debug":
                print("🐛 進入偵錯模式...")
                debug_q = input("   [Debug] 請輸入測試語句 (例如: 一房一廳): ").strip()
                if not debug_q: continue

                print("   [Debug] 正在請求模型生成...")
                print("   [Raw Output Start] -> ", end="", flush=True)

                debug_queue = Queue()
                debug_config = LLMConfig(
                    mode=LLMMode.CHAT,
                    token=LLM_API_KEY,
                    server_address=LLM_SERVER_ADDRESS,
                    server_port=LLM_SERVER_PORT,
                    model_type=LLM_MODEL_TYPE,
                    stream=True,
                    queue=debug_queue
                )

                # 手動注入 API Key
                if LLM_API_KEY:
                    debug_config.api_key = LLM_API_KEY

                debug_client = LLMClient(debug_config)
                test_prompt = f"請將以下需求轉換為 MongoDB 查詢 JSON: {debug_q}。只輸出 JSON，不要包含 Markdown。"

                worker = threading.Thread(target=lambda: debug_client.call_local_model(test_prompt))
                worker.start()

                full_response = ""

                while True:
                    data = debug_queue.get()

                    token = getattr(data, 'token', None)
                    if not token: token = getattr(data, 'text', None)
                    if not token: token = getattr(data, 'content', None)

                    if token:
                        print(token, end="", flush=True)
                        full_response += str(token)

                    if hasattr(data, 'completed') and data.completed:
                        if not full_response and hasattr(data, 'complete_text') and data.complete_text:
                            print(data.complete_text, end="", flush=True)
                            full_response += str(data.complete_text)
                        break

                worker.join()
                print("\n   [Raw Output End] <-")

                if "403" in full_response or "權限錯誤" in full_response:
                    print("🛑 權限錯誤！請檢查您的 API Key 設定。")
                elif not full_response.strip().startswith("{"):
                    print("⚠️  輸出不是以 '{' 開頭，可能包含閒聊文字。")
                else:
                    print("✅ 格式看起來正確。")
                continue

            if use_mongodb:
                print("⏳ 正在分析並生成資料庫查詢語句...")
                json_response = mini_rag.get_mongodb_search_cmd_json(user_query)

                if json_response:
                    fixed_response = mini_rag.get_fixed_mongo_query_cmd(json_response)
                    print("\n✅ 生成結果 (可直接用於 MongoDB):")
                    print(json.dumps(fixed_response, ensure_ascii=False, indent=2))
                else:
                    print("⚠️  無法解析為有效的 JSON 查詢。")

            else:
                print("💬 AI 回應: ", end="", flush=True)
                stream_queue = Queue()
                chat_config = LLMConfig(
                    mode=LLMMode.CHAT,
                    server_address=LLM_SERVER_ADDRESS,
                    server_port=LLM_SERVER_PORT,
                    model_type=LLM_MODEL_TYPE,
                    stream=True,
                    queue=stream_queue
                )
                if LLM_API_KEY:
                    chat_config.api_key = LLM_API_KEY

                chat_client = LLMClient(chat_config)
                worker = threading.Thread(target=lambda: chat_client.call_local_model(user_query))
                worker.start()

                while True:
                    data = stream_queue.get()
                    token = getattr(data, 'token', None)
                    if token:
                        print(token, end="", flush=True)
                    if data.completed:
                        break
                print()
                worker.join()

        except KeyboardInterrupt:
            print("\n👋 程式中斷")
            break
        except Exception as e:
            print(f"\n❌ 發生未預期的錯誤: {e}")
            import traceback
            traceback.print_exc()

    print("👋 再見！")


if __name__ == "__main__":
    main()