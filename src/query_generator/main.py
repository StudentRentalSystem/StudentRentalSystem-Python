from src.rag_service.rag import RagService
from src.query_generator.query_generator import MiniRagApp
from src.config import Config


# === 攔截器 (Monkey Patch) ===
def install_spy(mini_rag_instance):
    try:
        client = getattr(mini_rag_instance, 'llm_client', None) or getattr(mini_rag_instance, 'client', None)
        if client:
            # 注入 API KEY 到原本的 config (如果是透過 App 初始化)
            if Config.LLM_CLIENT_TOKEN:
                client.config.api_key = Config.LLM_CLIENT_TOKEN
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
    print(f"📍 連線目標: {Config.LLM_SERVER_ADDRESS}:{Config.LLM_SERVER_PORT} (Model: {Config.LLM_MODEL_TYPE})")
    if Config.LLM_CLIENT_TOKEN:
        print(f"🔑 API Key: 已載入 ({Config.LLM_CLIENT_TOKEN[:4]}***)")
    else:
        print(f"⚠️ API Key: 未設定 (如果遇到 403 錯誤，請在 settings.py 加入 LLM_API_KEY)")

    try:
        mini_rag = MiniRagApp()
        install_spy(mini_rag)
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return

    rag_service = RagService()

    use_chroma = True
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
            mode_name = "租屋搜尋(MongoDB)" if use_chroma else "一般聊天(Chat)"
            prompt_text = f"\n[{mode_name}] 請輸入需求: "
            user_query = input(prompt_text).strip()

            if not user_query:
                continue

            # 指令處理
            if user_query.lower() == "exit":
                break
            elif user_query.lower() == "others":
                use_chroma = False
                print("🔀 已切換至：一般聊天模式")
                continue
            elif user_query.lower() == "rental":
                use_chroma = True
                print("🔀 已切換至：租屋搜尋模式")
                continue

            if use_chroma:
                response = mini_rag.format_query(user_query)

                # result = rag_service.query(user_query, response)
                result = rag_service.collection.query(
                    query_texts=[user_query],
                    where=response,
                    include=["documents", "metadatas"]
                )

                print(result["documents"])
                print(result["metadatas"])

        except Exception as e:
            print(e)

    print("👋 再見！")


if __name__ == "__main__":
    main()