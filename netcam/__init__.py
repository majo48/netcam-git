from flask import Flask
from flask import render_template
from flask import url_for

app = Flask(__name__)


@app.route("/")
@app.route("/home")
def home():
    return render_template(
        template_name_or_list='home.html',
        navigation={
            "icon": "hamburger",
            "url": url_for("home", _external=True) }
    )


if __name__ == "__main__":
    app.run()
