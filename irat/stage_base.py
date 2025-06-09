class StageBase:
    """
    Base class for all iRat stage.This class provides a 'get_stage_name' method so subclasses don't have to implement it.
    """
    STAGE: str = "undefined"

    @classmethod
    def get_stage_name(cls) -> str:
        return cls.STAGE