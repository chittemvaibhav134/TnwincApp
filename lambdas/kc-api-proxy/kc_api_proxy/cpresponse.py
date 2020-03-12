class CodePipelineHelperResponse( ):
    def __init__(self, InProgress: bool, Success: bool = True, Message: str = "", OutputVariables: dict = None):
        self.InProgress = InProgress
        self.Success = Success
        self.Message = Message
        self.OutputVariables = OutputVariables
    def to_dict(self):
        return {
            'InProgress': self.InProgress,
            'Success': self.Success,
            'Message': self.Message,
            'OutputVariables': self.OutputVariables
        }
    @classmethod
    def in_progress(cls, Message: str="") -> dict:
        return cls(True, True, Message).to_dict()
    @classmethod
    def failed(cls, Message: str) -> dict:
        return cls(False, False, Message).to_dict()
    @classmethod
    def succeeded(cls, Message: str="", OutputVariables: dict = None) -> dict:
        return cls(False, True, Message, OutputVariables).to_dict() 