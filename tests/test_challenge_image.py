import base64
import io

from PIL import Image

from hcaptcha_challenger.models import ChallengeImage


def _create_test_image_bytes(width: int = 320, height: int = 240, color: str = "red") -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_challenge_image_from_bytes():
    raw = _create_test_image_bytes(320, 240)
    image = ChallengeImage.from_bytes(raw)

    assert image.raw_bytes == raw
    assert image.dimensions == (320, 240)
    assert image.width == 320
    assert image.height == 240
    assert image.as_base64 == base64.b64encode(raw).decode("utf-8")


def test_challenge_image_lazy_caching():
    raw = _create_test_image_bytes(100, 100)
    image = ChallengeImage(raw_bytes=raw)

    # Calling as_base64 and dimensions multiple times returns identical cached values
    b64_1 = image.as_base64
    b64_2 = image.as_base64
    assert b64_1 is b64_2

    dims_1 = image.dimensions
    dims_2 = image.dimensions
    assert dims_1 == (100, 100)
    assert dims_1 is dims_2


def test_challenge_image_from_file(tmp_path):
    raw = _create_test_image_bytes(250, 150)
    file_path = tmp_path / "test_frame.png"
    file_path.write_bytes(raw)

    image = ChallengeImage.from_file(file_path)
    assert image.raw_bytes == raw
    assert image.dimensions == (250, 150)
    assert image.as_base64 == base64.b64encode(raw).decode("utf-8")


def test_challenge_image_from_base64():
    raw = _create_test_image_bytes(180, 120)
    b64_str = base64.b64encode(raw).decode("utf-8")

    image = ChallengeImage.from_base64(b64_str)
    assert image.raw_bytes == raw
    assert image.dimensions == (180, 120)
    assert image.as_base64 == b64_str


def test_challenge_image_save(tmp_path):
    raw = _create_test_image_bytes(50, 50)
    image = ChallengeImage.from_bytes(raw)

    save_path = tmp_path / "subfolder" / "saved.png"
    saved = image.save(save_path)

    assert saved.is_file()
    assert saved.read_bytes() == raw
