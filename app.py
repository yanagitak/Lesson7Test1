# QRコード生成ツール（最小構成）
# Flask + qrcode + Pillow のみ使用
import os
import io
import base64
from flask import Flask, request, Response
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H

app = Flask(__name__)

# デバッグ切替（デフォルトFalse）
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# 制限値
MAX_TEXT_LEN = 500
MAX_SIZE = 1024

ERROR_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


def generate_qr_png_data(text: str, size: int, border: int, level: str) -> str:
    """QRコードを生成し、Data URL（base64 PNG）を返す"""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_LEVELS[level],
        box_size=10,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # サイズ調整（最大 size x size）
    img = img.resize((size, size))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


@app.route("/", methods=["GET", "POST"])
def index():
    error = ""
    img_data = ""

    # デフォルト値
    text = ""
    size = 300
    border = 4
    level = "M"

    if request.method == "POST":
        try:
            text = request.form.get("text", "").strip()
            size = int(request.form.get("size", size))
            border = int(request.form.get("border", border))
            level = request.form.get("level", level)

            # バリデーション
            if not text:
                raise ValueError("テキストを入力してください。")
            if len(text) > MAX_TEXT_LEN:
                raise ValueError(f"テキストは最大 {MAX_TEXT_LEN} 文字までです。")
            if size <= 0 or size > MAX_SIZE:
                raise ValueError(f"サイズは 1〜{MAX_SIZE}px の範囲で指定してください。")
            if border < 0 or border > 10:
                raise ValueError("余白（border）は 0〜10 の範囲で指定してください。")
            if level not in ERROR_LEVELS:
                raise ValueError("誤り訂正レベルが不正です。")

            img_data = generate_qr_png_data(text, size, border, level)

        except Exception as e:
            error = str(e)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <title>QRコード生成ツール</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; }}
    .error {{ color: red; }}
    label {{ display: block; margin-top: 0.5rem; }}
    input, select, button {{ margin-top: 0.25rem; }}
    img {{ margin-top: 1rem; border: 1px solid #ccc; }}
  </style>
</head>
<body>
  <h1>QRコード生成ツール</h1>

  <form method="post">
    <label>
      テキスト（必須）
      <input type="text" name="text" value="{text}" required maxlength="{MAX_TEXT_LEN}" style="width: 100%;">
    </label>

    <label>
      サイズ（px, 最大 {MAX_SIZE}）
      <input type="number" name="size" value="{size}">
    </label>

    <label>
      余白（border）
      <input type="number" name="border" value="{border}">
    </label>

    <label>
      誤り訂正レベル
      <select name="level">
        <option value="L" {"selected" if level=="L" else ""}>L</option>
        <option value="M" {"selected" if level=="M" else ""}>M</option>
        <option value="Q" {"selected" if level=="Q" else ""}>Q</option>
        <option value="H" {"selected" if level=="H" else ""}>H</option>
      </select>
    </label>

    <button type="submit">生成</button>
  </form>

  {"<p class='error'>" + error + "</p>" if error else ""}

  {f'''
    <h2>プレビュー</h2>
    <img src="{img_data}" alt="QRコード">
    <p>
      <a href="{img_data}" download="qr.png">PNGをダウンロード</a>
    </p>
  ''' if img_data else ""}

</body>
</html>
"""
    return Response(html, content_type="text/html; charset=utf-8")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=DEBUG)
