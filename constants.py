class ColumnNames:
    DATE = 'date'
    TEXT = 'text'
    COST = 'cost'
    CATEGORY = 'category'

    @classmethod
    def as_list(cls):
        return [cls.DATE, cls.TEXT, cls.COST, cls.CATEGORY]

    @classmethod
    def as_set(cls):
        return {cls.DATE, cls.TEXT, cls.COST, cls.CATEGORY}

    @classmethod
    def as_str(cls):
        # Returns column names as a formatted string with single quotes and commas
        return ", ".join(f"'{name}'" for name in cls.as_list())
