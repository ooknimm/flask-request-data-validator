# flask-parameter-validator

This package provide function that declare request parameter type and validate them. <br>
Only have to set api function's signature using type hint and pydantic.

<br>

### Path Parameter
``` python
from flask import Flask
from flask_parameter_validator import parameter_validator, Path
from typing import Annotated

app = Flask(__name__)

@app.get("/items/<item_id>")
@parameter_validator
def read_item(item_id: Annotated[int, Path()]):
    return {"item_id": item_id}
```

<br>

### Query Parameter
``` python
from flask import Flask
from flask_parameter_validator import parameter_validator, Query
from typing import Annotated

app = Flask(__name__)

@app.get("/items/")
@parameter_validator
def read_item(skip: Annotated[int, Query()] = 0, limit: Annotated[int, Query(default=10, ge=10)]):
    return {"skip": skip, "limit": limit}
```

<br>

### Request Header
``` python
from flask import Flask
from flask_parameter_validator import parameter_validator, Header
from typing import Annotated

app = Flask(__name__)

@app.get("/items/")
@parameter_validator
def read_item(x_token: Annotated[str, Header()]):
    return {"x_token": x_token}
```

allow request header like that
``` 
header
x-token: woifvnkzcnwQzV
```

<br>

### Request body
#### Json
``` python
from flask import Flask
from flask_parameter_validator import parameter_validator
from typing import Annotated
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

app = Flask(__name__)

@app.get("/items")
@parameter_validator
def create_item(item: Item):
    return {"item": item}
```

allow both request data
``` json
{"name": "apple", "price": 1000}
```

``` json
{"item": {"name": "apple", "price": 1000}}
```

<br>

#### Multiple Parameters
``` python
from flask import Flask
from flask_parameter_validator import parameter_validator, Body
from typing import Annotated
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

app = Flask(__name__)

@app.get("/items")
@parameter_validator
def create_item(item: Item, extra: Annotated[str, Body()]):
    return {"item": item, "extra": extra}
```

<br>

#### Form
``` python
from flask import Flask
from flask_parameter_validator import parameter_validator, Form
from typing import Annotated
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

app = Flask(__name__)

@app.get("/items")
@parameter_validator
def create_item(item: Annotated[Item, Form()], extra: Annotated[str, Form()]):
    return {"item": item, "extra": extra}
```

<br>

### Request body + path + query parameters
``` python
from flask import Flask
from flask_parameter_validator import parameter_validator, Query, Body, Path
from typing import Annotated
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

app = Flask(__name__)

@app.get("/items/<item_id>")
@parameter_validator
def create_item(item_id: Annotated[int, Path()], item: Item, extra: Annotated[str, Body(max_length=10)], q: Annotated[str, Query()] = None):
    result = {"item_id": item_id, "item": Item, "extra": extra}
    if q:
        result.update({"q": q})
    return result
```

<br>

### Param's Extra validation 
- default
- gt
- ge
- lt
- le
- max_length
- min_length

<br>

### Response when invalid parameter
- status code: 422
- media type: application/json
- json_data e.g.
```
{
    "detail": [
        {
            "ctx": {"max_length": 5},
            "input": "abcdef",
            "loc": ["header", "x-token"],
            "msg": "String should have at most 5 characters",
            "type": "string_too_long",
            "url": "https://errors.pydantic.dev/2.1.2/v/string_too_long",
        }
    ]
},
```
