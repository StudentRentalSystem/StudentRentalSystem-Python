import re
from typing import List, Dict, Any, Union


class MongoSearchStatementFixer:
    # 建立地名映射表
    DISTRICT_MAP = {
        "台南市": "台南市",
        "臺南市": "台南市",
        "台南": "台南市",
        "臺南": "台南市",
        "高雄市": "高雄市",
        "台北市": "台北市",
        "臺北市": "台北市"
        # 可依需求擴充
    }

    @staticmethod
    def normalize_district(location: str) -> str:
        """
        將地名正規化 (例如: 臺南 -> 台南市)
        """
        # 依照 key 長度排序，長的優先比對
        sorted_keys = sorted(MongoSearchStatementFixer.DISTRICT_MAP.keys(), key=len, reverse=True)

        result = location
        for key in sorted_keys:
            if key in result:
                result = result.replace(key, MongoSearchStatementFixer.DISTRICT_MAP[key])
        return result

    @staticmethod
    def split_address(address: str) -> List[str]:
        """
        根據分隔字元切割地址
        """
        result = []
        delimiters = "市區鄉鎮村路街巷弄"

        start = 0
        for i, char in enumerate(address):
            if char in delimiters:
                part = address[start: i + 1].strip()
                if part:
                    result.append(part)
                start = i + 1

        # 處理最後剩餘的部分 (如號碼)
        if start < len(address):
            tail = address[start:].strip()
            if tail:
                result.append(tail)

        if not result:
            result.append(address)

        return result

    @staticmethod
    def is_single_place_name(address: str) -> bool:
        """判斷是否為短地名"""
        return len(address) <= 4 and not re.search(r"[市區路街巷弄]", address)

    @classmethod
    def fix_address_query(cls, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        修復地址查詢，將長地址字串拆解為多個 regex 條件
        """
        if "$and" not in query:
            return query

        and_array = query["$and"]
        new_and_array = []

        for condition in and_array:
            if "地址" in condition:
                addr_condition = condition["地址"]
                if "$regex" in addr_condition:
                    raw = addr_condition["$regex"]

                    # 正規化
                    raw = cls.normalize_district(raw)

                    # 長地址才拆解
                    # 檢查是否包含地名關鍵字且長度 > 4
                    if len(raw) > 4 and re.search(r"[市區鄉鎮村路街巷弄]+", raw):
                        parts = cls.split_address(raw)

                        for part in parts:
                            if len(part) >= 2:  # 避免拆出單字
                                new_regex = {
                                    "地址": {
                                        "$regex": part.replace("市", ""),  # 特殊處理：移除市以增加模糊匹配率
                                        "$options": "i"
                                    }
                                }
                                new_and_array.append(new_regex)
                        continue  # 原本的長地址條件已被拆解，不加入

            # 其他條件直接保留
            new_and_array.append(condition)

        return {"$and": new_and_array}

    @staticmethod
    def fix_rental_query(query: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        修復租金查詢格式，將舊的 'rental' 欄位轉換為 '租金.minRental' 格式
        """
        if isinstance(query, str):
            import json
            try:
                query = json.loads(query)
            except:
                return {}  # Return empty dict on error

        # 處理 rental 物件
        if "rental" in query:
            rental = query["rental"]

            # Case 1: 直接包含 $gte/$lte
            if "$gte" in rental or "$lte" in rental:
                if "$gte" in rental:
                    query["租金.minRental"] = {"$gte": rental["$gte"]}
                if "$lte" in rental:
                    query["租金.maxRental"] = {"$lte": rental["$lte"]}
                del query["rental"]

            # Case 2: $elemMatch (雖然 prompt 叫它不要用，但 LLM 有時還是會用)
            elif "$elemMatch" in rental:
                elem_match = rental["$elemMatch"]
                if "$and" in elem_match:
                    conditions = elem_match["$and"]
                    for cond in conditions:
                        if "minRental" in cond:
                            query["租金.minRental"] = cond["minRental"]
                        if "maxRental" in cond:
                            query["租金.maxRental"] = cond["maxRental"]
                    del query["rental"]

        # 處理 key 包含 "rental" 的情況 (例如 "rental.minRental" -> "租金.minRental")
        # Python 字典在迭代時不能修改大小，所以先轉換為字串處理再轉回
        import json
        query_str = json.dumps(query, ensure_ascii=False)
        if "rental" in query_str:
            query_str = query_str.replace("rental", "租金")
            return json.loads(query_str)

        return query

    @classmethod
    def fix_query(cls, query: Dict[str, Any]) -> Dict[str, Any]:
        """主修復入口"""
        query = cls.fix_rental_query(query)
        query = cls.fix_address_query(query)
        return query