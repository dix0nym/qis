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
        "notify@abc.de" // emails to notify
    ],
    "notify_graph": true|false, // include graph in notify emails
    "url": {
        "home_url": "https://qis.hs-albsig.de/qisserver/rds?state=user&type=0",
        "login_url": "https://qis.hs-albsig.de/qisserver/rds?state=user&type=1&category=auth.login&startpage=portal.vm",
        "logout_url": "https://qis.hs-albsig.de/qisserver/rds?state=user&type=4&re=last&category=auth.logout&breadCrumbSource=&topitem=functions",
        "verwaltung_url": "https://qis.hs-albsig.de/qisserver/rds?state=change&type=1&moduleParameter=studyPOSMenu&nextdir=change&next=menu.vm&subdir=applications&xml=menu&purge=y&navigationPosition=functions%2CstudyPOSMenu&breadcrumb=studyPOSMenu&topitem=functions&subitem=studyPOSMenu",
        "notenspiegel_url": "https://qis.hs-albsig.de/qisserver/rds?state=notenspiegelStudent&next=list.vm&nextdir=qispos/notenspiegel/student&createInfos=Y&struct=auswahlBaum&nodeID=auswahlBaum|abschluss:abschl=84,stgnr=1&expand=0&asi={}#auswahlBaum|abschluss:abschl=84,stgnr=1"
    }
}
```