# qis-checker
python script to check for changes on qis

## requirements
- python3
- pip

## installation
```python -m pip install -r requirements.txt```

## usage
- create config file "config.json"
- ```python qis.py```

## config.json
```
{
    "qisLogin": { // username and password to login to qis
        "username": "username",
        "password": "password"
    },
    "sendMail": true/false, // sendMail if new entry
    "receiveMail": "receivemail@abc.de", // email to receive
    "senderMail": { // email to send
        "username": "sendermail@abc.de",
        "password": "emailpassword"
    },
    "notifyEmails": [
        "notify@abc.de"
    ]
}
```