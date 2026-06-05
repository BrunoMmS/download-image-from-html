from pydantic import BaseModel

class HTMLRenderRequest(BaseModel):
    html: str
    width: int | None = None
    height: int | None = None
    selector: str | None = None