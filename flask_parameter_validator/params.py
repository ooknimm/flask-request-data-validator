from pydantic.fields import FieldInfo

class Param(FieldInfo):
    pass

class Header(Param):
    pass

class Path(Param):
    pass

class Query(Param):
    pass

class Cookie(Param):
    pass

class Body(Param):
    pass

class Form(Body):
    pass

class File(Form):
    pass

class Depends:
    pass