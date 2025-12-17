from src.rag_service.rag import RagService
from src.config import Config


if __name__ == '__main__':
    rag_service = RagService()

    raw_post = """
    #徵室友
    【雅房出租】
    【要求】：限學生
    【地址】：東區凱旋路31號asdasd
    ... (省略中間) ...
    【室友本人】
    嘿對就是我...我最近還買了一個新的氣炸鍋可以一起使用
    """

    # 2. 抽出來的關鍵 Metadata (用來做絕對過濾)
    metadata = {
        "price": 4700,  # 轉成數字
        "district": "東區",  # 地點
        "pet_allowed": False,  # 轉成布林值
        "role": "student",  # 身份限制
        "gender_restriction": "none",  # 看起來沒寫限男限女
        "has_elevator": True  # 電梯公寓
    }

    # rag_service.insert(raw_post, metadata)

    # result = rag_service.query("東區凱旋路")
    # print(result)

    result = rag_service.query(
        question="東區凱旋路",
        filters={"pet_allowed": False}  # 強制過濾
    )
    print(result)
    if not result['ids'][0]:
        print("測試成功！成功過濾掉不可養寵物的房子。")
    else:
        print("測試失敗，不該出現的房子出現了。")
