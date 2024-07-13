import json
from flask import Flask, render_template, request, jsonify, Response
import urllib.request
from datetime import datetime, timedelta
import time
import pyautogui
import random
import threading

app = Flask(__name__)
coordinates_data = []


def add_error(value, error_range=1):
    return value + random.uniform(-error_range, error_range)


def mouse_move(target_x, target_y, move_duration, error_range, move_duration_error):
    duration_with_error = add_error(move_duration, move_duration_error)
    click_x = add_error(target_x, error_range)
    click_y = add_error(target_y, error_range)

    pyautogui.moveTo(click_x, click_y, duration_with_error)
    pyautogui.click(add_error(target_x, error_range), add_error(target_y, error_range))

    result = {
        "click_x": click_x,
        "click_y": click_y,
        "duration_with_error": duration_with_error,
    }
    coordinates_data.append(result)
    return result


month = {
    "Jan": "01",
    "Feb": "02",
    "Mar": "03",
    "Apr": "04",
    "May": "05",
    "Jun": "06",
    "Jul": "07",
    "Aug": "08",
    "Sep": "09",
    "Oct": "10",
    "Nov": "11",
    "Dec": "12",
}


def execute_macro(
    url, target_minute, coordinates, move_duration, error_range, move_duration_error
):
    results = []
    while True:
        response = urllib.request.urlopen(url)
        date_str = response.headers["Date"][5:-4]
        d, m, y, hour, minute, sec = (
            date_str[:2],
            month[date_str[3:6]],
            date_str[7:11],
            date_str[12:14],
            date_str[15:17],
            date_str[18:],
        )

        current_time = datetime(
            int(y), int(m), int(d), int(hour), int(minute), int(sec)
        )

        print(f"{y}년 {m}월 {d}일 {hour}시 {minute}분 {sec}초")
        print(minute)

        if current_time.minute == target_minute:
            print("매크로실행")
            for index, coord in enumerate(coordinates):
                x, y = coord
                if index == 0:
                    result = mouse_move(x, y, 0.01075202866756409611, error_range, 0)
                else:
                    result = mouse_move(
                        x, y, move_duration, error_range, move_duration_error
                    )
                results.append(result)
            break

    return results


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_server_time", methods=["GET"])
def get_server_time():
    url = request.args.get("url")
    response = urllib.request.urlopen(url)
    date_str = response.headers["Date"][5:-4]
    d, m, y, hour, minute, sec = (
        date_str[:2],
        month[date_str[3:6]],
        date_str[7:11],
        date_str[12:14],
        date_str[15:17],
        date_str[18:],
    )
    current_time = datetime(int(y), int(m), int(d), int(hour), int(minute), int(sec))

    adjusted_time = current_time + timedelta(hours=18)
    return jsonify({"server_time": adjusted_time.strftime("%Y-%m-%d %H:%M:%S")})


@app.route("/start_macro", methods=["POST"])
def start_macro():
    data = request.json
    url = data["url"]
    target_minute = int(data["target_minute"])
    coordinates = [(int(coord["x"]), int(coord["y"])) for coord in data["coordinates"]]
    move_duration = float(data["move_duration"])
    error_range = float(data["error_range"])
    move_duration_error = float(data["move_duration_error"])

    results = []

    def run_macro():
        nonlocal results
        results = execute_macro(
            url,
            target_minute,
            coordinates,
            move_duration,
            error_range,
            move_duration_error,
        )

    macro_thread = threading.Thread(target=run_macro)
    macro_thread.start()
    macro_thread.join()

    return jsonify({"status": "매크로가 완료되었습니다", "results": results})


@app.route("/get_coordinates", methods=["GET"])
def get_coordinates():
    def generate():
        while True:
            x, y = pyautogui.position()
            yield f"data: {json.dumps({'x': x, 'y': y})}\n\n"
            time.sleep(0.1)

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True)
