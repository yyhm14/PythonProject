import requests

r = requests.post("http://10.232.65.16:5000/receive_data", json={
    "value": {
        "LinearBody": "X03线",
        "Device":     "冲压机A",
        "Problem":    "液压压力过低报警",
        "alarm_time": "2026-05-07 20:00:00"
    }
})
print(r.json())
