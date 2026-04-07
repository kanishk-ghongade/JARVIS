from jarvis.utils import detect_language, now_time_string


def test_detect_language():
    assert detect_language("क्या समय है") == "hi"
    assert detect_language("time batao") == "hi"
    assert detect_language("what is the time") == "en"


def test_time_string():
    assert "time" in now_time_string("en").lower()
    assert "समय" in now_time_string("hi")
