from pydantic import BaseModel

class ListeningMockSchema(BaseModel):
    title: str
    data: dict
    audio_part_1:str
    audio_part_2:str
    audio_part_3:str
    audio_part_4:str
    audio_part_5:str
    audio_part_6:str

class ListeningMockAnswersSchema(BaseModel):
    part_1:list
    part_2:list
    part_3:list
    part_4:list
    part_5:list
    part_6:list