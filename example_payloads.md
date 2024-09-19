# get session

GET /{id}

reponse
```json
{
"users": [
    {"name": "Seth", "role":"Wizard"},
    {"name": "Hank", "role":"Warrior"},
    
],
"dialogue": [
    {"user": "system", "msg": "Welcome to the adventure"},
    {"user": "seth", "msg": "I use my magic elixir to grow gigantic"},
    {"user": "system", "msg": "You roll a 3. the elixir back faires and you shrink to half size"}
]
}
```

# add entry
POST /{id}

request
```json
{
    #optional
    "users": [
        {"name": "Seth", "role":"Wizard"},
        {"name": "Hank", "role":"Warrior"},
        
    ],
    {"user": "Hank", "msg": "I pick Seth up and through him at the giant"}
    
}
```

response
```json
{"You roll a 20. Seth lands on the giant's head. The giant is confused"}
```