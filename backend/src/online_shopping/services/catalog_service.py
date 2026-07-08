class CatalogService:
    # 搜索商品目录，后续应编排 Catalog 或商品仓储完成实际查询。
    def search(self, query: str) -> list[object]:
        if not query.strip():
            return []
        return []
