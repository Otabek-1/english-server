from pydantic import BaseModel
from typing import List, Union

AnswerValue = Union[str, int, None]

class CreateReadingMock(BaseModel):
    title: str
    part1: dict
    part2: dict
    part3: dict
    part4: dict
    part5: dict

class CreateReadingAnswers(BaseModel):
    question_id:int
    part1: list
    part2:list
    part3:list
    part4:list
    part5:list

class UpdateReadingAnswers(BaseModel):
    part1: list
    part2:list
    part3:list
    part4:list
    part5:list

class Results(BaseModel):
    question_id: int
    part1: List[AnswerValue]
    part2: List[AnswerValue]
    part3: List[AnswerValue]
    part4MC: List[AnswerValue]
    part4TF: List[AnswerValue]
    part5Mini: List[AnswerValue]
    part5MC: List[AnswerValue]
