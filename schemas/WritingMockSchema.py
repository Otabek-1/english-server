from pydantic import BaseModel

class CreateMockData(BaseModel):
    images: list
    task1: dict
    task2:dict

class MockResponse(BaseModel):
    task1:str
    task2:str

class Result(BaseModel):
    result:dict